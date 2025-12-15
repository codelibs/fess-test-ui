
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
    logger.info("Starting synonym dictionary update test")

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

    # Click text=synonym.txt
    logger.info("Step 3: Open synonym dictionary")
    page.click("text=synonym.txt")
    assert_equal(page.url, context.url("/admin/dict/synonym/?dictId=c3lub255bS50eHQ="))

    # Click on the first entry (assuming it was created by add test)
    logger.info("Step 4: Click on existing entry to view details")
    page.click("table tbody tr:first-child td:first-child a")

    # Click text=編集
    logger.info("Step 5: Click edit button")
    page.click("text=編集")

    # Click text=戻る (test cancel button)
    logger.info("Step 6: Test cancel button")
    page.click("text=戻る")

    # Click text=編集 again
    logger.info("Step 7: Click edit button again")
    page.click("text=編集")

    # Fill textarea[name="inputs"]
    logger.info("Step 8: Update form fields")
    page.fill("textarea[name=\"inputs\"]", label_name)

    # Fill textarea[name="outputs"]
    page.fill("textarea[name=\"outputs\"]", f"{label_name}\n更新テスト")

    # Click text=更新
    logger.info("Step 9: Submit form to update entry")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/dict/synonym/list/1?dictId=c3lub255bS50eHQ="))

    logger.info("Step 10: Verify entry was updated successfully")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    logger.info("Synonym dictionary update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
