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
    logger.info("Starting kuromoji dictionary update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=システム
    logger.info("Step 1: Navigate to System menu")
    page.click("text=システム")

    # Click text=辞書
    logger.info("Step 2: Navigate to Dictionary page")
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=ja/kuromoji.txt
    logger.info("Step 3: Open kuromoji dictionary")
    page.click("text=ja/kuromoji.txt")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/?dictId=amEva3Vyb21vamkudHh0"))

    # Click text=全文検索エンジン
    logger.info("Step 4: Open entry details")
    page.click(f"text={label_name}")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/details/amEva3Vyb21vamkudHh0/4/5"))

    # Click text=編集
    logger.info("Step 5: Click edit button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Click text=戻る
    logger.info("Step 6: Test cancel button")
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Click text=編集
    logger.info("Step 7: Click edit button again")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/"))

    # Fill input[name="segmentation"]
    logger.info("Step 8: Update form fields")
    page.fill("input[name=\"segmentation\"]", "全文検索 システム")

    # Fill input[name="reading"]
    page.fill("input[name=\"reading\"]", "ゼンブンケンサク システム")

    # Fill input[name="pos"]
    page.fill("input[name=\"pos\"]", "カスタム")

    # Click text=更新
    logger.info("Step 9: Submit form to update entry")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))

    logger.info("Kuromoji dictionary update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
