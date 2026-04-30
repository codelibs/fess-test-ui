import logging

from fess.test import assert_equal, assert_startswith
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
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
    logger.info("Starting fileconfig delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    logger.info("Step 1: Navigate to file system configuration page")
    # Click text=クローラー
    page.click(f"text={t(Labels.MENU_CRAWL)}")

    # Click text=ファイルシステム
    page.click(f"text={t(Labels.MENU_FILE_SYSTEM)}")
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    logger.info("Step 2: Open configuration details")
    # Click text=Fess
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/fileconfig/details/4/"))

    logger.info("Step 3: Test delete button and cancel functionality")
    # Click text=削除
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')

    # Click text=キャンセル
    page.click(f"text={t(Labels.CRUD_BUTTON_CANCEL)}")

    logger.info("Step 4: Confirm configuration deletion")
    # Click text=削除
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')

    # Click modal confirm delete button
    page.click('div.modal-footer button[name="delete"]')
    assert_equal(page.url, context.url("/admin/fileconfig/"))

    logger.info("Step 5: Verify configuration is removed from list")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Fileconfig delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
