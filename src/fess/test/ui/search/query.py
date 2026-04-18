"""Search for 'intro' and assert at least one result renders."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_contains
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "intro"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/query")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_load_state("domcontentloaded")

    body_text = page.inner_text("body")
    assert_contains(body_text, "sampledata01",
                    f"expected 'sampledata01' in search results body for q={QUERY}")
    assert_true("に一致する情報は見つかりませんでした" not in body_text,
                f"no-result message appeared for q={QUERY}")

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
