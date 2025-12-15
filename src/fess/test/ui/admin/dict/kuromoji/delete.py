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
    logger.info("Starting kuromoji dictionary delete test")

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

    # Click text=全文検索システム
    logger.info("Step 4: Open entry details")
    page.click(f"text={label_name}")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/details/amEva3Vyb21vamkudHh0/4/5"))

    # Click text=削除
    logger.info("Step 5: Click delete button")
    page.click("text=削除")

    # Click text=キャンセル
    logger.info("Step 6: Test cancel button")
    page.click("text=キャンセル")

    # Click text=削除
    logger.info("Step 7: Click delete button again")
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    logger.info("Step 8: Confirm deletion")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))

    logger.info("Step 9: Verify entry was deleted successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Kuromoji dictionary delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
