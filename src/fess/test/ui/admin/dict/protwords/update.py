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

    # Click text=システム
    page.click("text=システム")

    # Click text=辞書
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=en/protwords.txt
    page.click("text=en/protwords.txt")
    assert_equal(page.url, context.url("/admin/dict/protwords/?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))

    # Click text=Maine
    page.click(f"text={label_name}")
    assert_equal(page.url, context.url("/admin/dict/protwords/details/ZW4vcHJvdHdvcmRzLnR4dA%3D%3D/4/2"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/protwords/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/dict/protwords/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/protwords/"))

    # Fill input[name="input"]
    page.fill("input[name=\"input\"]", label_name)

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/dict/protwords/list/1?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))

    # TODO check content


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
