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
    logger.info("Starting relatedquery delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=クローラー
    logger.info("Step 1: Navigate to Crawler menu")
    page.click("text=クローラー")

    # Click text=関連クエリー
    logger.info("Step 2: Navigate to Related Query page")
    page.click("text=関連クエリー")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    # Click text=fess
    logger.info("Step 3: Open related query details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/relatedquery/details/4/"))

    # Click text=削除
    logger.info("Step 4: Click delete button")
    page.click("text=削除")

    # Click text=キャンセル
    logger.info("Step 5: Click cancel button to test cancellation")
    page.click("text=キャンセル")

    # Click text=削除
    logger.info("Step 6: Click delete button again")
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    logger.info("Step 7: Confirm deletion")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    logger.info("Step 8: Verify related query was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Relatedquery delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
