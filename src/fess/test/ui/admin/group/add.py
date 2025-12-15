
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
    logger.info("Starting group add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test group: {label_name}")

    # Step 1: Navigate to group page
    logger.info("Step 1: Navigating to group page")
    page.click("text=ユーザー")
    page.click("text=グループ")
    assert_equal(page.url, context.url("/admin/group/"))

    # Step 2: Open create form
    logger.info("Step 2: Opening create form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/group/createnew/"))

    # Step 3: Fill group information
    logger.info("Step 3: Filling group information")
    page.fill("input[name=\"name\"]", label_name)
    page.fill("input[name=\"attributes.gidNumber\"]", "100")

    # Step 4: Submit form
    logger.info("Step 4: Submitting form")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/group/"))

    # Step 5: Verify group was created
    logger.info("Step 5: Verifying group was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Group add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
