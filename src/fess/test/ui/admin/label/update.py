import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
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
    logger.info("Starting label update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Step 1: Navigate to label page
    logger.info("Step 1: Navigating to label page")
    page.click("text=クローラー")
    page.click("text=ラベル")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 2: Open label details
    logger.info("Step 2: Opening label details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/labeltype/details/4/"))

    # Step 3: Test back button
    logger.info("Step 3: Testing edit and back button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/labeltype/"))
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 4: Open edit form
    logger.info("Step 4: Opening edit form")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 5: Update form fields
    logger.info("Step 5: Updating form fields")
    page.fill("input[name=\"sortOrder\"]", "10")
    page.fill("textarea[name=\"includedPaths\"]", "https://example.com/updated/.*")

    # Step 6: Submit update
    logger.info("Step 6: Submitting update")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 7: Verify update
    logger.info("Step 7: Verifying update")
    page.wait_for_load_state("domcontentloaded")
    table_content = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not found in table after update")

    logger.info("Label update test completed successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
