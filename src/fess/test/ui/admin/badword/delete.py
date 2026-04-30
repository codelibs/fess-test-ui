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
    logger.info("Starting badword delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Step 1: Navigate to badword page
    logger.info("Step 1: Navigating to badword page")
    page.click(f"text={t(Labels.MENU_SUGGEST)}")
    page.click(f"text={t(Labels.MENU_BAD_WORD)}")
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 2: Open badword details
    logger.info("Step 2: Opening badword details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/badword/details/4/"))

    # Step 3: Test delete button and cancel
    logger.info("Step 3: Testing delete button and cancel")
    page.click(f"text={t(Labels.CRUD_LINK_DELETE)}")
    page.click(f"text={t(Labels.CRUD_BUTTON_CANCEL)}")

    # Step 4: Delete badword
    logger.info("Step 4: Deleting badword")
    page.click(f"text={t(Labels.CRUD_LINK_DELETE)}")
    page.click('div.modal-footer button[name="delete"]')
    assert_equal(page.url, context.url("/admin/badword/"))

    # Step 5: Verify badword was deleted
    logger.info("Step 5: Verifying badword was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} in {table_content}")

    logger.info("Badword delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
