
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
    logger.info("Starting accesstoken add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Generated test label: {label_name}")

    # Step 1: Navigate to accesstoken page
    logger.info("Step 1: Navigating to accesstoken page")
    page.click("text=システム")
    page.click("text=アクセストークン")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Step 2: Open new accesstoken creation form
    logger.info("Step 2: Opening new accesstoken creation form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/accesstoken/createnew/"))

    # Step 3: Fill in accesstoken details
    logger.info("Step 3: Filling in accesstoken details")
    page.fill("input[name=\"name\"]", label_name)
    page.fill("textarea[name=\"permissions\"]", "{role}admin-api")
    page.fill("input[name=\"parameterName\"]", "testpram")
    page.fill("input[name=\"expires\"]", "2025-12-31T23:59:59")

    # Step 4: Create accesstoken
    logger.info("Step 4: Creating accesstoken")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Step 5: Verify accesstoken was created
    logger.info("Step 5: Verifying accesstoken was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Accesstoken add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
