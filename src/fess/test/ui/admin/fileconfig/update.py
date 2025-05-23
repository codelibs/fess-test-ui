import logging

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
    logger.info(f"start")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ファイルシステム
    page.click("text=ファイルシステム")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    # Click text=N2SM
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/fileconfig/details/4/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    # Fill text=N2SMのサイト
    page.fill("textarea[name=\"description\"]", "fess-testdata update")

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/fileconfig/details/4/"))

    # Verify that the value entered in the "description" field is displayed
    desc_value = page.input_value("input[name=\"description\"]")
    assert_equal(desc_value, "fess-testdata update", f"description value '{desc_value}' != expected 'fess-testdata update'")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
