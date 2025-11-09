
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
    logger.info(f"start")

    page: "Page" = context.get_admin_page()

    # Click text=システム
    page.click("text=システム")

    # Click text=パスマッピング
    page.click("text=パスマッピング")
    assert_equal(page.url, context.url("/admin/pathmap/"))

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/pathmap/createnew/"))

    # Fill input[name="regex"]
    page.fill("input[name=\"regex\"]", "http://example\\.com/(.*)")

    # Fill input[name="replacement"]
    page.fill("input[name=\"replacement\"]", "https://newdomain.com/$1")

    # Fill select[name="processType"]
    page.select_option("select[name=\"processType\"]", "C")

    # Fill input[name="sortOrder"]
    page.fill("input[name=\"sortOrder\"]", "1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/pathmap/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find("example.com"), -1,
                     f"Path mapping not found in table")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
