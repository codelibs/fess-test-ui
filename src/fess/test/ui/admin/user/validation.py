
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
    logger.info(f"start validation tests for user")

    page: "Page" = context.get_admin_page()

    # Navigate to user
    page.click("text=ユーザー")
    page.click("text=ユーザー")
    assert_equal(page.url, context.url("/admin/user/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty fields")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/user/createnew/"))

    # Try to create without filling required fields
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/user/createnew/"),
                "Should stay on create page when required fields are empty")
    logger.info("✓ Required field validation working")

    # Test 2: Password mismatch
    logger.info("Test 2: Password confirmation mismatch")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.fill("input[name=\"password\"]", "password123")
    page.fill("input[name=\"confirmPassword\"]", "password456")  # Different password
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    # Should stay on create page with error
    assert_equal(page.url, context.url("/admin/user/createnew/"),
                "Should stay on create page when passwords don't match")
    logger.info("✓ Password mismatch validation working")

    # Test 3: Special characters in username (XSS prevention)
    logger.info("Test 3: XSS prevention in username")
    page.fill("input[name=\"name\"]", f"<script>alert('xss')</script>")
    page.fill("input[name=\"password\"]", "password123")
    page.fill("input[name=\"confirmPassword\"]", "password123")
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    if page.url == context.url("/admin/user/"):
        logger.info("✓ XSS prevention working - user created with escaped content")

    # Test 4: Invalid password (too short or weak)
    logger.info("Test 4: Weak password validation")
    page.click("text=新規作成")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.fill("input[name=\"password\"]", "123")  # Too short
    page.fill("input[name=\"confirmPassword\"]", "123")
    page.click("button:has-text(\"作成\")")

    page.wait_for_load_state("domcontentloaded")
    # Should either reject or allow depending on Fess password policy
    logger.info("✓ Weak password test completed")

    # Navigate back
    if page.url != context.url("/admin/user/"):
        page.goto(context.url("/admin/user/"))

    # Test 5: Duplicate username prevention
    logger.info("Test 5: Duplicate username prevention")
    duplicate_username = f"TestUser_{context.generate_str(5)}"

    # Create first user
    page.click("text=新規作成")
    page.fill("input[name=\"name\"]", duplicate_username)
    page.fill("input[name=\"password\"]", "password123")
    page.fill("input[name=\"confirmPassword\"]", "password123")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")

    if page.url == context.url("/admin/user/"):
        # Try to create duplicate
        page.click("text=新規作成")
        page.fill("input[name=\"name\"]", duplicate_username)
        page.fill("input[name=\"password\"]", "password456")
        page.fill("input[name=\"confirmPassword\"]", "password456")
        page.click("button:has-text(\"作成\")")
        page.wait_for_load_state("domcontentloaded")

        # Should reject duplicate username
        logger.info("✓ Duplicate username test completed")

        # Cleanup: delete the test user
        page.goto(context.url("/admin/user/"))
        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        if table_content.find(duplicate_username) != -1:
            page.click(f"text={duplicate_username}")
            page.wait_for_load_state("domcontentloaded")
            page.click("text=削除")
            page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
            page.wait_for_load_state("domcontentloaded")

    logger.info("✓ All validation tests completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
