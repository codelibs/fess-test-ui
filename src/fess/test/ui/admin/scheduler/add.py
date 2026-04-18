import logging

from fess.test import assert_equal, assert_contains
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
    logger.info("Starting scheduler add test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    job_name = f"e2e-job-{name[:10]}"
    logger.debug(f"Job name: {job_name}")

    logger.info("Step 1: Navigate")
    page.goto(context.url("/admin/scheduler/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 2: Open create form")
    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/scheduler/createnew/"),
                 f"expected createnew URL, got {page.url}")

    logger.info("Step 3: Fill fields")
    page.fill("input[name=\"name\"]", job_name)
    page.fill("input[name=\"target\"]", "all")
    # Leave cronExpression blank for a manual-trigger job (avoids accidental runs)
    page.fill("input[name=\"scriptType\"]", "groovy")
    page.fill("textarea[name=\"scriptData\"]", "return null;")
    page.fill("input[name=\"sortOrder\"]", "999")

    logger.info("Step 4: Submit")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/scheduler/"),
                 f"expected list URL after create, got {page.url}")

    logger.info("Step 5: Verify row")
    body = page.inner_text("section.content")
    assert_contains(body, job_name, f"{job_name} not in list after create")

    logger.info("Step 6: Open details")
    page.locator(f"tr:has-text('{job_name}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.url, "/admin/scheduler/details/",
                    f"expected details URL, got {page.url}")

    logger.info("scheduler add test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
