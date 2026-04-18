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
    logger.info("Starting scheduler delete test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    job_name = f"e2e-job-{name[:10]}"

    logger.info("Step 1: Open row")
    page.goto(context.url("/admin/scheduler/"))
    page.wait_for_load_state("domcontentloaded")
    page.locator(f"tr:has-text('{job_name}')").first.click()
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 2: Delete")
    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/scheduler/"),
                 f"expected list URL after delete, got {page.url}")

    logger.info("Step 3: Verify removal")
    body = page.inner_text("section.content")
    assert_equal(body.find(job_name), -1, f"{job_name} still present after delete")

    logger.info("scheduler delete test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
