
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
    logger.info("Starting stopwords dictionary update test")

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

    # Click text=en/stopwords.txt
    logger.info("Step 3: Open stopwords dictionary")
    page.click("text=en/stopwords.txt")
    assert_equal(page.url, context.url("/admin/dict/stopwords/?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    # Click on page 2 to find the entry created by add test
    logger.info("Step 4: Navigate to page 2")
    page.click("a:has-text(\"2\")")
    assert_equal(page.url, context.url("/admin/dict/stopwords/list/2?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    # Click on the first entry on page 2
    logger.info("Step 5: Click on existing entry to view details")
    page.click("table tbody tr:first-child td:first-child a")

    # Click text=編集
    logger.info("Step 6: Click edit button")
    page.click("text=編集")

    # Click text=戻る (test cancel button)
    logger.info("Step 7: Test cancel button")
    page.click("text=戻る")

    # Click text=編集 again
    logger.info("Step 8: Click edit button again")
    page.click("text=編集")

    # Fill input[name="input"]
    logger.info("Step 9: Update form field")
    page.fill("input[name=\"input\"]", label_name)

    # Click text=更新
    logger.info("Step 10: Submit form to update entry")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/dict/stopwords/list/1?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    logger.info("Step 11: Verify entry was updated successfully")
    page.wait_for_load_state("domcontentloaded")
    # Navigate back to page 2 to verify the updated entry
    page.click("a:has-text(\"2\")")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Stopwords dictionary update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
