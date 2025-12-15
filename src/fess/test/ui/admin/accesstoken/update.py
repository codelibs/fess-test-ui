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
    logger.info("Starting accesstoken update test")

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
    page.click(f"text={label_name}")
    assert_startswith(page.url, context.url("/admin/accesstoken/details/4/"))

    # Step 3: Test edit button and back button
    logger.info("Step 3: Testing edit button and back button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/accesstoken/"))
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Step 4: Edit accesstoken details
    logger.info("Step 4: Editing accesstoken details")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/accesstoken/"))
    page.fill("input[name=\"name\"]", f"{label_name}X")

    # Step 5: Update accesstoken
    logger.info("Step 5: Updating accesstoken")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    logger.info("Accesstoken update test completed successfully")
    # TODO check content


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
