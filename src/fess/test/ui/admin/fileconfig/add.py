
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
    logger.info("Starting fileconfig add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    logger.info("Step 1: Navigate to file system configuration page")
    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ファイルシステム
    page.click("text=ファイルシステム")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    logger.info("Step 2: Open create new configuration form")
    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/fileconfig/createnew/"))

    logger.info("Step 3: Fill in file configuration details")
    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", label_name)

    # Fill textarea[name="paths"]
    page.fill("textarea[name=\"paths\"]", "file:/srv/fess-testdata/")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "5")

    # Fill textarea[name="description"]
    page.fill("textarea[name=\"description\"]", "fess-testdata")

    logger.info("Step 4: Submit new file configuration")
    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    logger.info("Step 5: Verify configuration appears in list")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Step 6: Verify configuration details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/fileconfig/details/4/"))

    # Verify that the value entered in the "name" field is displayed
    name_value = page.input_value("input[name=\"name\"]")
    assert_equal(name_value, label_name, f"name value '{name_value}' != expected '{label_name}'")

    # Verify that the value entered in the "description" field is displayed
    desc_value = page.input_value("input[name=\"description\"]")
    assert_equal(desc_value, "fess-testdata", f"description value '{desc_value}' != expected 'fess-testdata'")

    logger.info("Fileconfig add test completed successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
