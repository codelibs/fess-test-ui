import logging

from fess.test import assert_contains, assert_equal, assert_startswith
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
    logger.info("Starting fileauth update test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    hostname = f"host-{name[:8]}"

    logger.info("Step 1: Navigate and open row")
    page.goto(context.url("/admin/fileauth/"))
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/fileauth/"))
    page.locator(f"tr:has-text('{hostname}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url("/admin/fileauth/details/"),
                      f"expected details URL, got {page.url}")

    logger.info("Step 2: Enter edit mode")
    page.click("text=編集")
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 3: Modify username")
    page.fill("input[name=\"username\"]", f"upd-{name[:8]}")

    logger.info("Step 4: Submit update")
    page.click("button:has-text(\"更新\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/fileauth/"))

    logger.info("Step 5: Verify row still present")
    body = page.inner_text("section.content")
    assert_contains(body, hostname, f"{hostname} not in list after update")

    logger.info("fileauth update test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
