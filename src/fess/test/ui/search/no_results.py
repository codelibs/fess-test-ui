"""Search for an impossible query and assert the no-result UI renders.

Since fess#3460, /search is the bootstrap static-theme SPA, which renders
the no-result message from its own bundle (search.did_not_match) into
#empty-did-not-match.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt

logger = logging.getLogger(__name__)

IMPOSSIBLE_QUERY = "zzxxqq-nonexistent-xyz-9876543210"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/no_results")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={IMPOSSIBLE_QUERY}"))
    # search.js reveals #empty-state only once /api/v2/search has answered
    # with zero hits; before that the results view is empty either way.
    page.wait_for_selector("#empty-state:not(.d-none)")

    # The theme fills search.did_not_match with the query as plain text, so
    # the whole sentence is predictable, not just the part around {0}.
    expected = tt(context, ThemeKeys.SEARCH_DID_NOT_MATCH, IMPOSSIBLE_QUERY)
    actual = page.inner_text("#empty-did-not-match").strip()
    assert_equal(actual, expected,
                 f"expected the no-result message {expected!r} for "
                 f"q={IMPOSSIBLE_QUERY}, got {actual!r}")

    logger.info("search/no_results completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
