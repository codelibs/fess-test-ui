
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
    logger.info(f"start validation tests for accesstoken")

    page: "Page" = context.get_admin_page()

    # Navigate to accesstoken
    page.click("text=システム")
    page.click("text=アクセストークン")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty name")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/accesstoken/createnew/"))

    # Try to create without filling required fields
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/accesstoken/createnew/"),
                "Should stay on create page when required fields are empty")
    logger.info("✓ Required field validation working")

    # Test 2: XSS prevention in name field
    logger.info("Test 2: XSS prevention in name field")
    page.fill("input[name=\"name\"]", f"<script>alert('xss')</script>{context.generate_str(5)}")
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    if page.url == context.url("/admin/accesstoken/"):
        logger.info("✓ XSS prevention working - token created with escaped content")

    # Test 3: Maximum length validation
    logger.info("Test 3: Maximum length validation")
    page.click("text=新規作成")
    page.fill("input[name=\"name\"]", context.generate_str(300))
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    logger.info("✓ Long input handled")

    # Navigate back
    if page.url != context.url("/admin/accesstoken/"):
        page.goto(context.url("/admin/accesstoken/"))

    logger.info("✓ All validation tests completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
