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

    # Click text=サジェスト
    page.click("text=サジェスト")

    # Click text=追加ワード
    page.click("text=追加ワード")
    assert_equal(page.url, context.url("/admin/elevateword/"))

    # Click text=application
    page.click(f"text={label_name}")
    assert_startswith(page.url, context.url("/admin/elevateword/details/4/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/elevateword/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/elevateword/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/elevateword/"))

    # Fill input[name="suggestWord"]
    page.fill("input[name=\"suggestWord\"]", f"{label_name}X")

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/elevateword/"))

    # TODO check content


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
