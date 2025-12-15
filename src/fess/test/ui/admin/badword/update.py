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
    logger.info("Starting badword update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    new_label_name: str = context.generate_str()
    logger.debug(f"Using test label: {label_name}")
    logger.debug(f"Using new test label: {new_label_name}")

    # Step 1: Navigate to badword page
    logger.info("Step 1: Navigating to badword page")
    page.click("text=サジェスト")
    page.click("text=除外ワード")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 2: Open badword details
    logger.info("Step 2: Opening badword details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/badword/details/4/"))

    # Step 3: Test edit button and back button
    logger.info("Step 3: Testing edit button and back button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/badword/"))
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 4: Edit badword with new name
    logger.info("Step 4: Editing badword with new name")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/badword/"))
    page.fill("input[name=\"suggestWord\"]", new_label_name)

    # Step 5: Update badword
    logger.info("Step 5: Updating badword")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 6: Verify updated badword
    logger.info("Step 6: Verifying updated badword")
    page.click(f"text={new_label_name}")
    assert_startswith(
        page.url, context.url("/admin/badword/details/4/"))

    # Step 7: Restore original name
    logger.info("Step 7: Restoring original name")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/badword/"))
    page.fill("input[name=\"suggestWord\"]", label_name)
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/badword/"))

    logger.info("Badword update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
