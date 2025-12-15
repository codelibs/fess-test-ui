
import logging

from fess.test import assert_equal
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
    logger.info("Starting synonym dictionary delete test")

    page: "Page" = context.get_admin_page()

    # Click text=システム
    logger.info("Step 1: Navigate to System menu")
    page.click("text=システム")

    # Click text=辞書
    logger.info("Step 2: Navigate to Dictionary page")
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=synonym.txt
    logger.info("Step 3: Open synonym dictionary")
    page.click("text=synonym.txt")
    assert_equal(page.url, context.url("/admin/dict/synonym/?dictId=c3lub255bS50eHQ="))

    # Click on the first entry (assuming it was created/updated by previous tests)
    logger.info("Step 4: Click on existing entry to view details")
    page.click("table tbody tr:first-child td:first-child a")

    # Click text=削除
    logger.info("Step 5: Click delete button")
    page.click("text=削除")

    # Click text=キャンセル (test cancel button)
    logger.info("Step 6: Test cancel button in confirmation dialog")
    page.click("text=キャンセル")

    # Click text=削除 again
    logger.info("Step 7: Click delete button again")
    page.click("text=削除")

    # Click button[name="delete"] to confirm deletion
    logger.info("Step 8: Confirm deletion")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/dict/synonym/list/1?dictId=c3lub255bS50eHQ="))

    logger.info("Synonym dictionary delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
