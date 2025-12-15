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
    logger.info("Starting boostdoc update test")

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

    # Step 3: Test edit button and back button
    logger.info("Step 3: Testing edit button and back button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/boostdoc/"))
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Step 4: Edit boostdoc details
    logger.info("Step 4: Editing boostdoc details")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/boostdoc/"))
    page.fill("input[name=\"sortOrder\"]", "1")

    # Step 5: Update boostdoc
    logger.info("Step 5: Updating boostdoc")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    logger.info("Boostdoc update test completed successfully")
    # TODO check content


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
