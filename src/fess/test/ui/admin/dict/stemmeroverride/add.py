
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
    logger.info("Starting stemmeroverride dictionary add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=システム
    logger.info("Step 1: Navigate to System menu")
    page.click("text=システム")

    # Click text=辞書
    logger.info("Step 2: Navigate to Dictionary page")
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=en/stemmer_override.txt
    logger.info("Step 3: Open stemmeroverride dictionary")
    page.click("text=en/stemmer_override.txt")
    assert_equal(page.url, context.url("/admin/dict/stemmeroverride/?dictId=ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ="))

    # Click text=新規作成
    logger.info("Step 4: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/dict/stemmeroverride/createnew/ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ%3D/"))

    # Fill input[name="input"]
    logger.info("Step 5: Fill form fields")
    page.fill("input[name=\"input\"]", label_name)

    # Fill input[name="output"]
    page.fill("input[name=\"output\"]", "run")

    # Click button:has-text("作成")
    logger.info("Step 6: Submit form to create new entry")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/dict/stemmeroverride/list/1?dictId=ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ="))

    logger.info("Step 7: Verify entry was created successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Stemmeroverride dictionary add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
