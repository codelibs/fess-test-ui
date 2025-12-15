import logging
import re

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
    logger.info("Starting mapping dictionary add test")

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

    # Click :nth-match(:text("mapping.txt"), 3)
    logger.info("Step 3: Open mapping dictionary")
    page.click(":nth-match(:text(\"mapping.txt\"), 3)")
    assert_equal(page.url, context.url("/admin/dict/mapping/?dictId=bWFwcGluZy50eHQ="))

    # Click text=新規作成
    logger.info("Step 4: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/dict/mapping/createnew/bWFwcGluZy50eHQ%3D/"))

    # Fill textarea[name="inputs"]
    logger.info("Step 5: Fill form fields")
    page.fill("textarea[name=\"inputs\"]", label_name)

    # Fill input[name="output"]
    page.fill("input[name=\"output\"]", "1")

    # Click button:has-text("作成")
    logger.info("Step 6: Submit form to create new entry")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="))

    page.wait_for_load_state("domcontentloaded")

    # Go to last page
    logger.info("Step 7: Navigate to last page")
    page_info: str = page.inner_text("div.col-sm-2")
    last_page = int(re.search(r'(\d+)/(\d+)', page_info).group(2)) if re.search(r'(\d+)/(\d+)', page_info) else None
    page.goto(page.url.replace("/list/1", f"/list/{last_page}"))

    logger.info("Step 8: Verify entry was created successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Mapping dictionary add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
