
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

    # Click text=システム
    page.click("text=システム")

    # Click text=辞書
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=ja/kuromoji.txt
    page.click("text=ja/kuromoji.txt")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/?dictId=amEva3Vyb21vamkudHh0"))

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/createnew/amEva3Vyb21vamkudHh0"))

    # Fill input[name="token"]
    page.fill("input[name=\"token\"]", "全文検索エンジン")

    # Fill input[name="segmentation"]
    page.fill("input[name=\"segmentation\"]", "全文 検索 エンジン")

    # Fill input[name="reading"]
    page.fill("input[name=\"reading\"]", "ゼンブン ケンサク エンジン")

    # Fill input[name="pos"]
    page.fill("input[name=\"pos\"]", "カスタム名詞")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
