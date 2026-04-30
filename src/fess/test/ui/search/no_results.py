"""Search for an impossible query and assert the no-result UI renders."""
import logging
import re

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

IMPOSSIBLE_QUERY = "zzxxqq-nonexistent-xyz-9876543210"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _no_results_signature(template: str) -> str:
    """Return a locale-neutral search signature from the did_not_match template.

    The label looks like e.g. "<b>{0}</b> に一致する情報は見つかりませんでした。"
    or "Your search - <b>{0}</b> - did not match any documents."

    We strip HTML tags and the {0} placeholder, then return the longest
    remaining text segment (which becomes our substring assertion target).
    This avoids false negatives on languages where the rendered query is
    interpolated mid-sentence.
    """
    no_html = re.sub(r"<[^>]+>", "", template)
    parts = [p.strip() for p in no_html.split("{0}") if p.strip()]
    if not parts:
        # Defensive: fall back to the whole template minus html
        return no_html.strip()
    return max(parts, key=len)


def run(context: FessContext) -> None:
    logger.info("Starting search/no_results")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={IMPOSSIBLE_QUERY}"))
    page.wait_for_load_state("domcontentloaded")

    body_text = page.inner_text("body")
    expected = _no_results_signature(t(Labels.SEARCH_DID_NOT_MATCH))
    assert_contains(body_text, expected,
                    f"expected no-result signature {expected!r} for q={IMPOSSIBLE_QUERY}")

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
