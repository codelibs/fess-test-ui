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
    logger.info(f"start")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()

    # Click text=システム
    page.click("text=システム")

    # Click text=辞書
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click :nth-match(:text("mapping.txt"), 3)
    page.click(":nth-match(:text(\"mapping.txt\"), 3)")
    assert_equal(page.url, context.url("/admin/dict/mapping/?dictId=bWFwcGluZy50eHQ="))

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/dict/mapping/createnew/bWFwcGluZy50eHQ%3D/"))

    # Fill textarea[name="inputs"]
    page.fill("textarea[name=\"inputs\"]", label_name)

    # Fill input[name="output"]
    page.fill("input[name=\"output\"]", "1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="))

    page.wait_for_load_state("domcontentloaded")

    # Go to last page
    page_info: str = page.inner_text("div.col-sm-2")
    last_page = int(re.search(r'(\d+)/(\d+)', page_info).group(2)) if re.search(r'(\d+)/(\d+)', page_info) else None
    page.goto(page.url.replace("/list/1", f"/list/{last_page}"))
    
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
