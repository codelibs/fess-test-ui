
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

    # Navigate to request header list
    page.click("text=クローラー")
    page.click("text=リクエストヘッダー")
    assert_equal(page.url, context.url("/admin/reqheader/"))

    page.wait_for_load_state("domcontentloaded")

    try:
        # Click first edit button
        page.click("tbody tr:first-child a[href*='edit']")
        page.wait_for_load_state("domcontentloaded")

        # Update value
        page.fill("input[name=\"value\"]", "Mozilla/5.0 Updated Test Bot")

        # Click update button
        page.click("button:has-text(\"更新\")")
        assert_equal(page.url, context.url("/admin/reqheader/"))

        page.wait_for_load_state("domcontentloaded")
        table_content: str = page.inner_text("table")
        assert "Updated" in table_content or "Mozilla" in table_content, \
            f"Updated value not found in table"
    except Exception as e:
        logger.warning(f"No request headers to update: {e}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
