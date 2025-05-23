
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

    # Click text=新しいジョブの作成
    page.click("text=新しいジョブの作成")
    assert_startswith(
        page.url, context.url("/admin/scheduler/createnewjob/file_crawling/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ファイルシステム
    page.click("text=ファイルシステム")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    # Click text=N2SM
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/fileconfig/details/4/"))

    # Click text=新しいジョブの作成
    page.click("text=新しいジョブの作成")
    assert_startswith(
        page.url, context.url("/admin/scheduler/createnewjob/file_crawling/"))

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    # Click text=N2SM
    page.click(f"text=File Crawler - {label_name}")
    assert_startswith(
        page.url, context.url("/admin/scheduler/details/4/"))

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル
    page.click("text=キャンセル")

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
