"""Search for an impossible query and assert the no-result UI renders."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains
from fess.test.ui import FessContext

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
    page.wait_for_load_state("domcontentloaded")

    body_text = page.inner_text("body")
    assert_contains(body_text, "に一致する情報は見つかりませんでした",
                    f"expected no-result message for q={IMPOSSIBLE_QUERY}")

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
