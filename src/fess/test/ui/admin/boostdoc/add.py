
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
    logger.info("Starting boostdoc add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Generated test label: {label_name}")

    # Step 1: Navigate to boostdoc page
    logger.info("Step 1: Navigating to boostdoc page")
    page.click("text=クローラー")
    page.click("text=ドキュメントブースト")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Step 2: Open new boostdoc creation form
    logger.info("Step 2: Opening new boostdoc creation form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/boostdoc/createnew/"))

    # Step 3: Fill in boostdoc details
    logger.info("Step 3: Filling in boostdoc details")
    page.fill("textarea[name=\"urlExpr\"]",
              f"url.matches(\"https://{label_name}/.*\")")
    page.fill("textarea[name=\"boostExpr\"]", "100")

    # Step 4: Create boostdoc
    logger.info("Step 4: Creating boostdoc")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Step 5: Verify boostdoc was created
    logger.info("Step 5: Verifying boostdoc was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Boostdoc add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
