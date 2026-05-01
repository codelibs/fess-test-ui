import logging

from fess.test import assert_equal
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.webauth._const import WEBCONFIG_NAME
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _delete_row(page, context: FessContext, list_url: str, row_text: str) -> None:
    """Navigate to list_url, click row matching row_text, and confirm delete."""
    page.goto(context.url(list_url))
    page.wait_for_load_state("domcontentloaded")
    if row_text not in page.inner_text("body"):
        logger.info(f"{row_text} not in {list_url}; skipping")
        return
    page.locator(f"tr:has-text('{row_text}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")


def run(context: FessContext) -> None:
    logger.info("Starting webauth delete test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    hostname = f"host-{name[:8]}"

    logger.info("Step 1: Delete webauth row")
    _delete_row(page, context, "/admin/webauth/", hostname)

    logger.info("Step 2: Verify webauth removal")
    page.goto(context.url("/admin/webauth/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("section.content")
    assert_equal(body.find(hostname), -1,
                 f"{hostname} still in list after delete")

    logger.info("Step 3: Delete throwaway webconfig")
    _delete_row(page, context, "/admin/webconfig/", WEBCONFIG_NAME)

    logger.info("Step 4: Verify webconfig removal")
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("section.content")
    assert_equal(body.find(WEBCONFIG_NAME), -1,
                 f"{WEBCONFIG_NAME} still in webconfig list after delete")

    logger.info("webauth delete test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
