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

    # Click text=ja/kuromoji.txt
    page.click("text=ja/kuromoji.txt")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/?dictId=amEva3Vyb21vamkudHh0"))

    # Click text=全文検索エンジン
    page.click("text=全文検索エンジン")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/details/amEva3Vyb21vamkudHh0/4/5"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Fill input[name="token"]
    page.fill("input[name=\"token\"]", "全文検索システム")

    # Fill input[name="segmentation"]
    page.fill("input[name=\"segmentation\"]", "全文 検索 システム")

    # Fill input[name="reading"]
    page.fill("input[name=\"reading\"]", "ゼンブン ケンサク システム")

    # Fill input[name="pos"]
    page.fill("input[name=\"pos\"]", "カスタム")

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
