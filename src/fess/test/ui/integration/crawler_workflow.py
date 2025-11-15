
import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
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

    # Step 1: Create web crawl configuration
    logger.info("Step 1: Creating web crawl configuration")
    page.click("text=クローラー")
    page.click("text=ウェブ")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    page.click("text=新規作成 >> i")
    assert_equal(page.url, context.url("/admin/webconfig/createnew/"))

    page.fill("input[name=\"name\"]", webconfig_name)
    page.fill("textarea[name=\"urls\"]", "https://example.com/")
    page.fill("textarea[name=\"includedUrls\"]", "https://example.com/.*")
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")
    page.fill("input[name=\"maxAccessCount\"]", "10")
    page.fill("input[name=\"numOfThread\"]", "1")
    page.fill("textarea[name=\"description\"]", "Integration test crawler")

    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(webconfig_name), -1,
                     f"{webconfig_name} not created in webconfig")
    logger.info(f"✓ Web crawl configuration '{webconfig_name}' created successfully")

    # Step 2: Create scheduled job for the crawler
    logger.info("Step 2: Creating scheduled job")
    page.click(f"text={webconfig_name}")
    assert_startswith(page.url, context.url("/admin/webconfig/details/4/"))

    # Click on the job tab or scheduler
    page.click("text=ジョブ")
    page.wait_for_load_state("domcontentloaded")

    # Create a new job
    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")

    # Fill job details
    page.fill("input[name=\"name\"]", f"Job_{webconfig_name}")
    page.fill("input[name=\"cronExpression\"]", "0 0 * * *")  # Daily at midnight
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")

    logger.info(f"✓ Scheduled job created for '{webconfig_name}'")

    # Step 3: Verify job exists in scheduler
    logger.info("Step 3: Verifying job in scheduler")
    page.click("text=システム")
    page.click("text=スケジューラー")
    page.wait_for_load_state("domcontentloaded")

    scheduler_content = page.inner_text("table")
    assert_not_equal(scheduler_content.find(webconfig_name), -1,
                     f"Job for {webconfig_name} not found in scheduler")
    logger.info(f"✓ Job verified in scheduler")

    # Step 4: Delete the job
    logger.info("Step 4: Deleting scheduled job")
    page.click(f"text={webconfig_name}")
    page.wait_for_load_state("domcontentloaded")
    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    page.wait_for_load_state("domcontentloaded")

    logger.info(f"✓ Job deleted")

    # Step 5: Delete crawler configuration
    logger.info("Step 5: Deleting web crawl configuration")
    page.click("text=クローラー")
    page.click("text=ウェブ")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    page.click(f"text={webconfig_name}")
    assert_startswith(page.url, context.url("/admin/webconfig/details/4/"))

    page.click("text=削除")
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    page.wait_for_load_state("domcontentloaded")
    table_content = page.inner_text("section.content")
    assert_equal(table_content.find(webconfig_name), -1,
                 f"{webconfig_name} still exists after deletion")
    logger.info(f"✓ Web crawl configuration deleted")

    logger.info("✓ Crawler workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
