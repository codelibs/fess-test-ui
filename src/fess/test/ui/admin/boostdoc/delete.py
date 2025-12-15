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
    logger.info("Starting boostdoc delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Step 1: Navigate to boostdoc page
    logger.info("Step 1: Navigating to boostdoc page")
    page.click("text=クローラー")
    page.click("text=ドキュメントブースト")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Step 2: Open boostdoc details
    logger.info("Step 2: Opening boostdoc details")
    page.click(rf"text=/.*url\.matches\(\"https://{label_name}/\.\*\"\).*/")
    assert_startswith(
        page.url, context.url("/admin/boostdoc/details/4/"))

    # Step 3: Test delete button and cancel
    logger.info("Step 3: Testing delete button and cancel")
    page.click("text=削除")
    page.click("text=キャンセル")

    # Step 4: Delete boostdoc
    logger.info("Step 4: Deleting boostdoc")
    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Step 5: Verify boostdoc was deleted
    logger.info("Step 5: Verifying boostdoc was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Boostdoc delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
