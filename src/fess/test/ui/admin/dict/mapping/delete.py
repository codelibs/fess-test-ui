import logging
import re

from fess.test import assert_equal, assert_startswith
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
    logger.info("Starting mapping dictionary delete test")

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

    # Go to last page
    logger.info("Step 4: Navigate to last page")
    page_info: str = page.inner_text("div.col-sm-2")
    last_page = int(re.search(r'(\d+)/(\d+)', page_info).group(2)) if re.search(r'(\d+)/(\d+)', page_info) else None

    # Go to http://localhost:8080/admin/dict/mapping/list/49?dictId=bWFwcGluZy50eHQ=
    page.goto(page.url.replace("/admin/dict/mapping/?dictId=", f"/admin/dict/mapping/list/{last_page}?dictId="))
    assert_equal(page.url, context.url(f"/admin/dict/mapping/list/{last_page}?dictId=bWFwcGluZy50eHQ="))

    page.wait_for_load_state("domcontentloaded")

    # Click text=[二]
    logger.info("Step 5: Open entry details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/dict/mapping/details/bWFwcGluZy50eHQ%3D/4/"))

    # Click text=削除
    logger.info("Step 6: Click delete button")
    page.click("text=削除")

    # Click text=キャンセル
    logger.info("Step 7: Test cancel button")
    page.click("text=キャンセル")

    # Click text=削除
    logger.info("Step 8: Click delete button again")
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    logger.info("Step 9: Confirm deletion")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="))

    page.wait_for_load_state("domcontentloaded")

    # Go to last page
    logger.info("Step 10: Navigate to last page to verify deletion")
    page_info: str = page.inner_text("div.col-sm-2")
    last_page = int(re.search(r'(\d+)/(\d+)', page_info).group(2)) if re.search(r'(\d+)/(\d+)', page_info) else None
    page.goto(page.url.replace("/list/1", f"/list/{last_page}"))

    logger.info("Step 11: Verify entry was deleted successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Mapping dictionary delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
