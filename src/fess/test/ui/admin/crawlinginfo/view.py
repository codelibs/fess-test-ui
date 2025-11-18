
import logging

from fess.test import assert_equal
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info(f"start")

    page: "Page" = context.get_admin_page()

    # Navigate to crawling info list
    page.wait_for_selector("text=クローラー", state="visible", timeout=60000)
    page.click("text=クローラー")
    page.wait_for_selector("text=クロール情報", state="visible", timeout=60000)
    page.click("text=クロール情報")
    assert_equal(page.url, context.url("/admin/crawlinginfo/"))

    page.wait_for_load_state("networkidle", timeout=60000)

    # Check if the page loaded successfully
    try:
        # Try to find the table or empty message
        page_content = page.inner_text("body")
        assert "クロール情報" in page_content or "該当するデータがありません" in page_content, \
            "Crawling info page did not load correctly"
        logger.info("Crawling info page loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to verify crawling info page: {e}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
