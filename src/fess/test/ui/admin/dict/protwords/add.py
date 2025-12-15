
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
    logger.info("Starting protwords dictionary add test")

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

    # Click text=en/protwords.txt
    logger.info("Step 3: Open protwords dictionary")
    page.click("text=en/protwords.txt")
    assert_equal(page.url, context.url("/admin/dict/protwords/?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))

    # Click text=新規作成
    logger.info("Step 4: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/dict/protwords/createnew/ZW4vcHJvdHdvcmRzLnR4dA%3D%3D/"))

    # Fill input[name="input"]
    logger.info("Step 5: Fill form field")
    page.fill("input[name=\"input\"]", label_name)

    # Click button:has-text("作成")
    logger.info("Step 6: Submit form to create new entry")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/dict/protwords/list/1?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))

    logger.info("Step 7: Verify entry was created successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Protwords dictionary add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
