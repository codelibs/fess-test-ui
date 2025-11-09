
import logging

from fess.test import assert_equal
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
    logger.info(f"start")

    page: "Page" = context.get_admin_page()

    # Navigate to scheduler list
    page.click("text=システム")
    page.click("text=スケジューラ")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    page.wait_for_load_state("domcontentloaded")

    # Click first edit button
    page.click("tbody tr:first-child a[href*='edit']")
    page.wait_for_load_state("domcontentloaded")

    # Update cron expression (every day at 1 AM)
    page.fill("input[name=\"cronExpression\"]", "0 0 1 * * ?")

    # Click update button
    page.click("button:has-text(\"更新\")")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert "0 0 1 * * ?" in table_content, \
        f"Updated cron expression not found in table"


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
