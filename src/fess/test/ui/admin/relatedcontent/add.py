
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
    logger.info("Starting relatedcontent add test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=クローラー
    logger.info("Step 1: Navigate to Crawler menu")
    page.click("text=クローラー")

    # Click text=関連コンテンツ
    logger.info("Step 2: Navigate to Related Content page")
    page.click("text=関連コンテンツ")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    # Click text=新規作成
    logger.info("Step 3: Click create new button")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/relatedcontent/createnew/"))

    # Fill input[name="name"]
    logger.info("Step 4: Fill in related content form")
    page.fill("input[name=\"term\"]", label_name)

    # Fill textarea[name="content"]
    page.fill("textarea[name=\"content\"]", "<a href=\"https://www.n2sm.net/\">N2SM,Inc.</a>はこちら。")

    # Fill input[name="sortOrder"]
    page.fill("input[name=\"sortOrder\"]", "1")

    # Click button:has-text("作成")
    logger.info("Step 5: Submit form to create related content")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/relatedcontent/"))

    logger.info("Step 6: Verify related content was created")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Relatedcontent add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
