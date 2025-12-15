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
    logger.info("Starting duplicatehost add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=クローラー
    logger.info("Step 1: Navigate to Crawler menu")
    page.click("text=クローラー")

    # Click text=重複ホスト
    logger.info("Step 2: Navigate to Duplicate Host page")
    page.click("text=重複ホスト")
    assert_equal(page.url, context.url("/admin/duplicatehost/"))

    # Click text=新規作成
    logger.info("Step 3: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/duplicatehost/createnew/"))

    # Fill input[name="regularName"]
    logger.info("Step 4: Fill in duplicate host form")
    page.fill("input[name=\"regularName\"]", f"{label_name}")

    # Fill input[name="duplicateHostName"]
    page.fill("input[name=\"duplicateHostName\"]", "fess.codelibs.org")

    # Click button:has-text("作成")
    logger.info("Step 5: Submit form to create duplicate host")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/duplicatehost/"))

    logger.info("Step 6: Verify duplicate host was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Duplicatehost add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
