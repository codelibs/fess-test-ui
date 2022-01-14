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

    # Click text=ドキュメントブースト
    page.click("text=ドキュメントブースト")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    # Click text=/.*url\.matches\("https://www\.n2sm\.net/\.\*"\).*/
    page.click(f"text=/.*url\.matches\(\"https://{label_name}/\.\*\"\).*/")
    assert_startswith(
        page.url, context.url("/admin/boostdoc/details/4/"))

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル
    page.click("text=キャンセル")

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/boostdoc/"))

    assert_equal(page.inner_text("table").find(label_name), -1)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
