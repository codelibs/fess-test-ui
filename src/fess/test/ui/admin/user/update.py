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
    logger.info("Starting user update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test user: {label_name}")

    # Step 1: Navigate to user page
    logger.info("Step 1: Navigating to user page")
    page.click("text=ユーザー")
    page.click("text=ユーザー ロール グループ >> p")
    assert_equal(page.url, context.url("/admin/user/"))

    # Step 2: Open user details
    logger.info("Step 2: Opening user details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/user/details/4/"))

    # Step 3: Test edit and cancel
    logger.info("Step 3: Testing edit and cancel")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/user/"))
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/user/"))

    # Step 4: Open edit form
    logger.info("Step 4: Opening edit form")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/user/"))

    # Step 5: Update password
    logger.info("Step 5: Updating password")
    page.fill("input[name=\"password\"]", "taro1234")
    page.fill("input[name=\"confirmPassword\"]", "taro1234")

    # Step 6: Submit update
    logger.info("Step 6: Submitting update")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/user/"))

    logger.info("User update test completed successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
