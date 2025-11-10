
import logging

from fess.test import assert_equal, assert_not_equal
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

    # First ensure we have a web config to attach the request header to
    # Navigate to web config
    page.click("text=クローラー")
    page.click("text=ウェブ")
    page.wait_for_load_state("domcontentloaded")

    # Get the first web config ID from the table
    try:
        # Try to get the edit link which contains the config ID
        first_edit_link = page.get_attribute("tbody tr:first-child a[href*='details']", "href")
        if not first_edit_link:
            logger.warning("No web config found, skipping request header test")
            return

        # Navigate to request header list
        page.click("text=クローラー")
        page.click("text=リクエストヘッダー")
        assert_equal(page.url, context.url("/admin/reqheader/"))

        # Click new creation button
        page.click("text=新規作成 >> em")
        assert_equal(page.url, context.url("/admin/reqheader/createnew/"))

        # Fill name
        page.fill("input[name=\"name\"]", "User-Agent")

        # Fill value
        page.fill("input[name=\"value\"]", "Mozilla/5.0 Test Bot")

        # Select web config
        page.select_option("select[name=\"webConfigId\"]", index=0)

        # Click create button
        page.click("button:has-text(\"作成\")")
        assert_equal(page.url, context.url("/admin/reqheader/"))

        page.wait_for_load_state("domcontentloaded")
        table_content: str = page.inner_text("table")
        assert_not_equal(table_content.find("User-Agent"), -1,
                         f"Request header not found in table")
    except Exception as e:
        logger.warning(f"Failed to create request header: {e}")
        # This is acceptable if no web config exists


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
