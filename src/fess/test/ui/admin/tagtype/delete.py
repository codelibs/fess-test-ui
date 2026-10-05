import logging
import time

from fess.test import assert_equal, assert_startswith, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.tagtype._names import DETAILS_PATH, LIST_PATH, open_list, tag_name
from fess.test.ui.cleanup import assert_absent
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

# The delete is written with refresh=true, but give the list a margin
# before calling the row leaked.
CONVERGE_SECONDS = 30


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting tag delete test")

    page: "Page" = context.get_admin_page()
    name: str = tag_name(context)

    # Step 1: Navigate to the tag page
    logger.info("Step 1: Navigating to tag page")
    open_list(context, page)
    assert_equal(page.url, context.url(LIST_PATH))

    # Step 2: Open tag details
    logger.info("Step 2: Opening tag details")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url(DETAILS_PATH))

    # Step 3: Cancel in the confirmation dialog keeps the tag
    logger.info("Step 3: Testing delete cancel button")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click(f"text={t(Labels.CRUD_BUTTON_CANCEL)}")
    assert_equal(page.input_value("input[name=\"name\"]"), name,
                 "cancel should leave the details page as it was")

    # Step 4: Perform delete
    logger.info("Step 4: Performing delete")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url(LIST_PATH))
    assert_equal(page.locator("ul.has-error").count(), 0,
                 "delete was rejected")
    assert_true(page.locator("div.alert-success").count() > 0,
                "no success message after delete")

    # Step 5: Verify deletion, reloading until the list converges
    logger.info("Step 5: Verifying deletion")
    deadline = time.monotonic() + CONVERGE_SECONDS
    while name in page.inner_text("section.content") and time.monotonic() < deadline:
        time.sleep(1)
        page.goto(context.url(LIST_PATH))
        page.wait_for_load_state("domcontentloaded")
    assert_absent(page, name, LIST_PATH)

    logger.info("Tag delete test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
