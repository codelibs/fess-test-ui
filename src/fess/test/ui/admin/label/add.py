
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
    logger.info("Starting label add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Generated test label: {label_name}")

    # Step 1: Navigate to label page
    logger.info("Step 1: Navigating to label page")
    page.click("text=クローラー")
    page.click("text=ラベル")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 2: Open create form
    logger.info("Step 2: Opening create form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/labeltype/createnew/"))

    # Step 3: Fill form fields
    logger.info("Step 3: Filling form fields")
    page.fill("input[name=\"name\"]", label_name)
    page.fill("input[name=\"value\"]", label_name.lower())
    page.fill("textarea[name=\"includedPaths\"]", "https://example.com/.*")
    page.fill("input[name=\"sortOrder\"]", "1")

    # Step 4: Submit form
    logger.info("Step 4: Submitting form")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 5: Verify label in list
    logger.info("Step 5: Verifying label in list")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    # Step 6: Verify label details
    logger.info("Step 6: Verifying label details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/labeltype/details/4/"))

    name_value = page.input_value("input[name=\"name\"]")
    assert_equal(name_value, label_name, f"name value '{name_value}' != expected '{label_name}'")

    value_value = page.input_value("input[name=\"value\"]")
    assert_equal(value_value, label_name.lower(), f"value value '{value_value}' != expected '{label_name.lower()}'")

    logger.info("Label add test completed successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
