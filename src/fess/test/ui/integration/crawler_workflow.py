
import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
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
    """
    Integration test for crawler workflow:
    1. Create web crawl configuration
    2. Create scheduled job for the crawler
    3. Verify job is created
    4. Delete job
    5. Delete crawler configuration
    """
    logger.info("start crawler workflow integration test")

    page: "Page" = context.get_admin_page()
    webconfig_name: str = f"IntegTest_{context.create_label_name()}"
    job_name: str = f"Job_{webconfig_name}"

    created: list = []
    try:
        # Step 1: Create web crawl configuration
        logger.info("Step 1: Creating web crawl configuration")
        page.click(f"text={t(Labels.MENU_CRAWL)}")
        page.click(f"text={t(Labels.MENU_WEB)}")
        assert_equal(page.url, context.url("/admin/webconfig/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/webconfig/createnew/"))

        page.fill("input[name=\"name\"]", webconfig_name)
        page.fill("textarea[name=\"urls\"]", "https://example.com/")
        page.fill("textarea[name=\"includedUrls\"]", "https://example.com/.*")
        page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")
        page.fill("input[name=\"maxAccessCount\"]", "10")
        page.fill("input[name=\"numOfThread\"]", "1")
        page.fill("textarea[name=\"description\"]", "Integration test crawler")

        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/webconfig/"))

        page.wait_for_load_state("domcontentloaded")
        table_content: str = page.inner_text("table")
        assert_not_equal(table_content.find(webconfig_name), -1,
                         f"{webconfig_name} not created in webconfig")
        created.append("webconfig")
        logger.info(f"✓ Web crawl configuration '{webconfig_name}' created successfully")

        # Step 2: Create scheduled job for the crawler
        logger.info("Step 2: Creating scheduled job")
        page.click(f"text={webconfig_name}")
        assert_startswith(page.url, context.url("/admin/webconfig/details/4/"))

        # Click the "create new job" button; it navigates straight to the
        # web-crawling job creation form (there is no further create-new link).
        page.click(f"text={t(Labels.WEB_CRAWLING_BUTTON_CREATE_JOB)}")
        page.wait_for_load_state("domcontentloaded")
        assert_startswith(page.url, context.url("/admin/scheduler/createnewjob/web_crawling/"))

        # Fill job details
        page.fill("input[name=\"name\"]", job_name)
        # Leave cronExpression blank for a manual-trigger job (avoids accidental runs)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.url, context.url("/admin/scheduler/"))

        created.append("job")
        logger.info(f"✓ Scheduled job created for '{webconfig_name}'")

        # Step 3: Verify job exists in scheduler
        logger.info("Step 3: Verifying job in scheduler")
        page.goto(context.url("/admin/scheduler/"))
        page.wait_for_load_state("domcontentloaded")

        scheduler_content = page.inner_text("table")
        assert_not_equal(scheduler_content.find(job_name), -1,
                         f"Job for {webconfig_name} not found in scheduler")
        logger.info(f"✓ Job verified in scheduler")
    finally:
        # Step 4: Delete the job (cleanup)
        if "job" in created:
            try:
                logger.info("Step 4: Deleting scheduled job")
                page.goto(context.url("/admin/scheduler/"))
                page.wait_for_load_state("domcontentloaded")
                page.locator(f"tr:has-text('{job_name}')").first.click()
                page.wait_for_load_state("domcontentloaded")
                page.click(f"text={t(Labels.CRUD_BUTTON_DELETE)}")
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                logger.info("✓ Job deleted")
            except Exception as e:
                logger.error(f"LEAKED scheduled job '{job_name}' — will pollute later modules: {e}")

        # Step 5: Delete crawler configuration (cleanup)
        if "webconfig" in created:
            try:
                logger.info("Step 5: Deleting web crawl configuration")
                page.click(f"text={t(Labels.MENU_CRAWL)}")
                page.click(f"text={t(Labels.MENU_WEB)}")
                assert_equal(page.url, context.url("/admin/webconfig/"))

                page.click(f"text={webconfig_name}")
                assert_startswith(page.url, context.url("/admin/webconfig/details/4/"))

                page.click(f"text={t(Labels.CRUD_BUTTON_DELETE)}")
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/webconfig/"))

                page.wait_for_load_state("domcontentloaded")
                table_content = page.inner_text("section.content")
                assert_equal(table_content.find(webconfig_name), -1,
                             f"{webconfig_name} still exists after deletion")
                logger.info(f"✓ Web crawl configuration deleted")
            except Exception as e:
                logger.error(f"LEAKED webconfig '{webconfig_name}' — will pollute later modules: {e}")

    logger.info("✓ Crawler workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
