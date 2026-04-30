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
    logger.info("Starting keymatch delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=クローラー
    logger.info("Step 1: Navigate to Suggest menu")
    page.click(f"text={t(Labels.MENU_CRAWL)}")

    # Click text=キーマッチ
    logger.info("Step 2: Navigate to Key Match page")
    page.click(f"text={t(Labels.MENU_KEY_MATCH)}")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Click text=n2sm
    logger.info("Step 3: Click on key match to delete")
    page.click(f"text={label_name}")
    assert_startswith(page.url, context.url("/admin/keymatch/details/4/"))

    # Click text=削除
    logger.info("Step 4: Click delete button")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')

    # Click text=キャンセル
    logger.info("Step 5: Test cancel button")
    page.click(f"text={t(Labels.CRUD_BUTTON_CANCEL)}")

    # Click text=削除
    logger.info("Step 6: Click delete button again")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')

    # Click text=キャンセル 削除 >> button[name="delete"]
    logger.info("Step 7: Confirm deletion")
    page.click('div.modal-footer button[name="delete"]')
    assert_equal(page.url, context.url("/admin/keymatch/"))

    logger.info("Step 8: Verify key match was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Keymatch delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
