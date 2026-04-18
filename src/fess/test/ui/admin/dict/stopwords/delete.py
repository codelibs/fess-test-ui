
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
    logger.info("Starting stopwords dictionary delete test")

    page: "Page" = context.get_admin_page()

    # Click text=システム
    logger.info("Step 1: Navigate to System menu")
    page.click("text=システム")

    # Click text=辞書
    logger.info("Step 2: Navigate to Dictionary page")
    page.click("text=辞書")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=en/stopwords.txt
    logger.info("Step 3: Open stopwords dictionary")
    page.click("text=en/stopwords.txt")
    assert_equal(page.url, context.url("/admin/dict/stopwords/?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    # Navigate to next page to find the entry created/updated by previous tests
    # (pre-existing entries fill page 1; our entry is appended to end)
    logger.info("Step 4: Navigate to next page and click on existing entry")
    label_name: str = context.create_label_name()
    page.goto(context.url("/admin/dict/stopwords/list/2?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={label_name}")

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
    assert_equal(page.url, context.url("/admin/dict/stopwords/list/1?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    logger.info("Stopwords dictionary delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
