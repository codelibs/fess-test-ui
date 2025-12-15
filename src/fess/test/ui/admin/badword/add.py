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
    logger.info("Starting badword add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Generated test label: {label_name}")

    # Step 1: Navigate to badword page
    logger.info("Step 1: Navigating to badword page")
    page.click("text=サジェスト")
    page.click("text=除外ワード")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 2: Open new badword creation form
    logger.info("Step 2: Opening new badword creation form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/badword/createnew/"))

    # Step 3: Fill in badword details
    logger.info("Step 3: Filling in badword details")
    page.fill("input[name=\"suggestWord\"]", label_name)

    # Step 4: Create badword
    logger.info("Step 4: Creating badword")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 5: Verify badword was created
    logger.info("Step 5: Verifying badword was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Badword add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
