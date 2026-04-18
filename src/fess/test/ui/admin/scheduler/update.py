import logging

from fess.test import assert_contains, assert_equal
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
    logger.info("Starting scheduler update test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    job_name = f"e2e-job-{name[:10]}"

    logger.info("Step 1: Open row")
    page.goto(context.url("/admin/scheduler/"))
    page.wait_for_load_state("domcontentloaded")
    page.locator(f"tr:has-text('{job_name}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.url, "/admin/scheduler/details/",
                    f"expected details URL, got {page.url}")

    logger.info("Step 2: Enter edit mode")
    page.click("text=編集")
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 3: Modify sortOrder")
    page.fill("input[name=\"sortOrder\"]", "998")

    logger.info("Step 4: Submit")
    page.click("button:has-text(\"更新\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/scheduler/"),
                 f"expected list URL after update, got {page.url}")

    logger.info("Step 5: Verify row still present")
    body = page.inner_text("section.content")
    assert_contains(body, job_name, f"{job_name} not in list after update")

    logger.info("scheduler update test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
