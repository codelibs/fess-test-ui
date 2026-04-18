import logging

from fess.test import assert_equal
from fess.test.ui import FessContext
from fess.test.ui.admin.fileauth._const import FILECONFIG_NAME
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
    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    page.wait_for_load_state("domcontentloaded")


def run(context: FessContext) -> None:
    logger.info("Starting fileauth delete test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    hostname = f"host-{name[:8]}"

    logger.info("Step 1: Delete fileauth row")
    _delete_row(page, context, "/admin/fileauth/", hostname)

    logger.info("Step 2: Verify fileauth removal")
    page.goto(context.url("/admin/fileauth/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("section.content")
    assert_equal(body.find(hostname), -1,
                 f"{hostname} still in list after delete")

    logger.info("Step 3: Delete throwaway fileconfig")
    _delete_row(page, context, "/admin/fileconfig/", FILECONFIG_NAME)

    logger.info("Step 4: Verify fileconfig removal")
    page.goto(context.url("/admin/fileconfig/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("section.content")
    assert_equal(body.find(FILECONFIG_NAME), -1,
                 f"{FILECONFIG_NAME} still in fileconfig list after delete")

    logger.info("fileauth delete test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
