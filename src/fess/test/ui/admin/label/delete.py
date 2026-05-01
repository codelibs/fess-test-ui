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
    logger.info("Starting label delete test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Step 1: Navigate to label page
    logger.info("Step 1: Navigating to label page")
    page.click(f"text={t(Labels.MENU_CRAWL)}")
    page.click(f"text={t(Labels.MENU_LABEL_TYPE)}")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 2: Open label details
    logger.info("Step 2: Opening label details")
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/labeltype/details/4/"))

    # Step 3: Test cancel button
    logger.info("Step 3: Testing delete cancel button")
    page.click(f"text={t(Labels.CRUD_BUTTON_DELETE)}")
    page.click(f"text={t(Labels.CRUD_BUTTON_CANCEL)}")

    # Step 4: Perform delete
    logger.info("Step 4: Performing delete")
    page.click(f"text={t(Labels.CRUD_BUTTON_DELETE)}")
    page.click('div.modal-footer button[name="delete"]')
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Step 5: Verify deletion
    logger.info("Step 5: Verifying deletion")
    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("section.content")
    assert_equal(table_content.find(label_name), -1,
                 f"{label_name} found in {table_content} (should be deleted)")

    logger.info("Label delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
