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
    logger.info("Starting relatedquery update test")

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

    # Click text=編集
    logger.info("Step 4: Click edit button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    # Click text=戻る
    logger.info("Step 5: Click back button to test navigation")
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    # Click text=編集
    logger.info("Step 6: Click edit button again")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    # Fill text=n2sm
    logger.info("Step 7: Update query field")
    page.fill("text=n2sm", "elasticsearch")

    # Click text=更新
    logger.info("Step 8: Submit form to update related query")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    logger.info("Relatedquery update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
