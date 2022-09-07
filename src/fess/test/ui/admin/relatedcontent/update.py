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

    # Click text=関連コンテンツ
    page.click("text=関連コンテンツ")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    # Click text=fess
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/relatedcontent/details/4/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    # Fill input[name="sortOrder"]
    page.fill("input[name=\"sortOrder\"]", "99")

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
