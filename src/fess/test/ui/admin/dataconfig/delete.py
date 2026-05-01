import logging

from fess.test import assert_equal
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
    logger.info("Starting dataconfig delete test")
    page = context.get_admin_page()
    name: str = context.create_label_name()

    logger.info("Step 1: Open dataconfig list")
    page.goto(context.url("/admin/dataconfig/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 2: Open details row")
    page.locator(f"tr:has-text('{name}')").first.click()
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 3: Delete with modal confirmation")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/dataconfig/"),
                 f"expected list URL after delete, got {page.url}")

    logger.info("Step 4: Verify removal")
    body = page.inner_text("section.content")
    assert_equal(body.find(name), -1, f"{name} still present after delete")

    logger.info("dataconfig delete test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
