
import logging

from fess.test import assert_equal, assert_not_equal
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
    label_name: str = context.create_label_name()

    # Navigate to scheduler list
    page.click("text=システム")
    page.click("text=スケジューラ")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    # Click new creation button
    page.click("text=新規作成 >> em")
    assert_equal(page.url, context.url("/admin/scheduler/createnew/"))

    # Fill name
    page.fill("input[name=\"name\"]", label_name)

    # Fill target
    page.fill("input[name=\"target\"]", "org.codelibs.fess.app.job.ScriptExecutorJob")

    # Fill cron expression (every day at midnight)
    page.fill("input[name=\"cronExpression\"]", "0 0 0 * * ?")

    # Select script type
    page.select_option("select[name=\"scriptType\"]", "groovy")

    # Fill script data
    page.fill("textarea[name=\"scriptData\"]", "logger.info('Test scheduled job')")

    # Set available to true
    page.select_option("select[name=\"available\"]", "true")

    # Set crawler to false
    page.select_option("select[name=\"crawler\"]", "false")

    # Set job logging to true
    page.select_option("select[name=\"jobLogging\"]", "true")

    # Fill sort order
    page.fill("input[name=\"sortOrder\"]", "100")

    # Click create button
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/scheduler/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not found in table")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
