"""Search for 'intro' and assert at least one result renders.

Since fess#3460, /search is the bootstrap static-theme SPA: the results are
rendered after /api/v2/search answers, so the check waits for them.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_contains
from fess.test.ui import FessContext
from fess.test.ui.search import query_jsp
from fess.test.ui.version import run_jsp_variant

logger = logging.getLogger(__name__)

QUERY = "intro"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    if run_jsp_variant(context, query_jsp):
        return
    logger.info("Starting search/query")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_selector("#result0")

    results_text = page.inner_text("#results")
    assert_contains(results_text, "sampledata01",
                    f"expected 'sampledata01' in the search results for q={QUERY}")
    assert_true(page.is_hidden("#empty-state"),
                f"the no-result state is shown for q={QUERY}")

    logger.info("search/query completed")


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
