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
    logger.info("Starting role delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test role: {label_name}")

    # Step 1: Navigate to role page
    logger.info("Step 1: Navigating to role page")
    page.click(f"text={t(Labels.MENU_USER)}")
    page.click(f"text={t(Labels.MENU_ROLE)}")
    assert_equal(page.url, context.url("/admin/role/"))

    # Step 2: Open role details
    logger.info("Step 2: Opening role details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/role/details/4/"))

    # Step 3: Test delete with cancel
    logger.info("Step 3: Testing delete with cancel")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CANCEL)}")')

    # Step 4: Execute delete
    logger.info("Step 4: Executing delete")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    assert_equal(page.url, context.url("/admin/role/"))

    # Step 5: Verify role was deleted
    logger.info("Step 5: Verifying role was deleted")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} found in {table_content} (should be deleted)")

    logger.info("Role delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
