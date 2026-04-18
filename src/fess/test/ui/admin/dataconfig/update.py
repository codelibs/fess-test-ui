import logging

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext
from fess.test.ui.admin.dataconfig.add import HANDLER_NAME, _inject_handler
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting dataconfig update test")
    page = context.get_admin_page()
    name: str = context.create_label_name()

    logger.info("Step 1: Open dataconfig list")
    page.goto(context.url("/admin/dataconfig/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 2: Open details row")
    page.locator(f"tr:has-text('{name}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.url, "/admin/dataconfig/details/",
                    f"expected details URL, got {page.url}")

    logger.info("Step 3: Enter edit mode")
    page.click("text=編集")
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 4: Re-inject handler and modify boost")
    _inject_handler(page, HANDLER_NAME)
    page.fill("input[name=\"boost\"]", "2.5")

    logger.info("Step 5: Submit update")
    page.click("button:has-text(\"更新\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/dataconfig/"),
                 f"expected list URL after update, got {page.url}")

    logger.info("Step 6: Verify row still present")
    body = page.inner_text("section.content")
    assert_contains(body, name, f"{name} not in list after update")

    logger.info("dataconfig update test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
