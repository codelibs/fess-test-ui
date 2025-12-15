import logging

from fess.test import assert_equal, assert_startswith
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
    logger.info("Starting accesstoken delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Step 1: Navigate to accesstoken page
    logger.info("Step 1: Navigating to accesstoken page")
    page.click("text=システム")
    page.click("text=アクセストークン")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Step 2: Open accesstoken details
    logger.info("Step 2: Opening accesstoken details")
    page.click(f"text={label_name}X")
    assert_startswith(page.url, context.url("/admin/accesstoken/details/4/"))

    # Step 3: Test delete button and cancel
    logger.info("Step 3: Testing delete button and cancel")
    page.click("text=削除")
    page.click("text=キャンセル")

    # Step 4: Delete accesstoken
    logger.info("Step 4: Deleting accesstoken")
    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Step 5: Verify accesstoken was deleted
    logger.info("Step 5: Verifying accesstoken was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Accesstoken delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
