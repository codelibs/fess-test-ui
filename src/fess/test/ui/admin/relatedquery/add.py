
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
    logger.info("Starting relatedquery add test")

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

    # Click text=新規作成
    logger.info("Step 3: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/relatedquery/createnew/"))

    # Fill input[name="term"]
    logger.info("Step 4: Fill in related query form")
    page.fill("input[name=\"term\"]", label_name)

    # Fill textarea[name="queries"]
    page.fill("textarea[name=\"queries\"]", "n2sm")

    # Click button:has-text("作成")
    logger.info("Step 5: Submit form to create related query")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/relatedquery/"))

    logger.info("Step 6: Verify related query was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Relatedquery add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
