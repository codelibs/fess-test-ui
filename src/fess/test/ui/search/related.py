"""Verify the results page renders cleanly regardless of related-content state."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/related")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/search/?q=intro"))
    page.wait_for_load_state("domcontentloaded")

    body_text = page.inner_text("body")
    assert_true(len(body_text) > 100, "results page body suspiciously short")

    related = page.query_selector(".related-content, .related-queries, #relatedSearch")
    if related is not None:
        items = related.query_selector_all("a, li")
        logger.info(f"related block rendered with {len(items)} items")
    else:
        logger.info("no related block rendered (expected when no config exists)")

    logger.info("search/related completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try: run(ctx)
        finally: destroy(ctx)
