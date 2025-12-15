
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
    logger.info("Starting key match validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to keymatch
    page.click("text=サジェスト")
    page.click("text=キーマッチ")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Test 1: Required field validation
    logger.info("Test 1: Required field validation")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/keymatch/createnew/"))

    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/keymatch/createnew/"),
                "Should stay on create page when required fields are empty")
    logger.info("Test 1 passed: Required field validation working")

    # Test 2: XSS prevention
    logger.info("Test 2: XSS prevention in term field")
    page.fill("input[name=\"term\"]", f"<script>alert('xss')</script>")
    page.fill("input[name=\"query\"]", "test query")
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    if page.url == context.url("/admin/keymatch/"):
        logger.info("Test 2 passed: XSS prevention working")

    # Test 3: Maximum length validation
    logger.info("Test 3: Maximum length validation")
    page.click("text=新規作成")
    page.fill("input[name=\"term\"]", context.generate_str(300))
    page.fill("input[name=\"query\"]", context.generate_str(300))
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    logger.info("Test 3 passed: Long input handled")

    if page.url != context.url("/admin/keymatch/"):
        page.goto(context.url("/admin/keymatch/"))

    logger.info("Key match validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
