"""Search for 'intro' and assert at least one result renders."""
import logging
import re

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_contains
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "intro"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _no_results_signature(template: str) -> str:
    """Locale-neutral signature from the did_not_match template.

    Mirrors the helper in search/no_results.py: strips HTML and the {0}
    placeholder, returns the longest remaining text segment.
    """
    no_html = re.sub(r"<[^>]+>", "", template)
    parts = [p.strip() for p in no_html.split("{0}") if p.strip()]
    if not parts:
        return no_html.strip()
    return max(parts, key=len)


def run(context: FessContext) -> None:
    logger.info("Starting search/query")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_load_state("domcontentloaded")

    body_text = page.inner_text("body")
    assert_contains(body_text, "sampledata01",
                    f"expected 'sampledata01' in search results body for q={QUERY}")
    no_results_sig = _no_results_signature(t(Labels.SEARCH_DID_NOT_MATCH))
    assert_true(no_results_sig not in body_text,
                f"no-result message ({no_results_sig!r}) appeared for q={QUERY}")

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
