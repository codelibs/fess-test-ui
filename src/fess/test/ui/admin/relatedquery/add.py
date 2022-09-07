
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
    label_name: str = context.create_label_name()

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=関連クエリー
    page.click("text=関連クエリー")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/relatedquery/createnew/"))

    # Fill input[name="term"]
    page.fill("input[name=\"term\"]", label_name)

    # Fill textarea[name="queries"]
    page.fill("textarea[name=\"queries\"]", "n2sm")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/relatedquery/"))


    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
