
import logging

from fess.test import assert_equal, assert_not_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup, delete_by_name
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()



def run(context: FessContext) -> None:
    logger.info("Starting access token validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to accesstoken
    page.click(f"text={t(Labels.MENU_SYSTEM)}")
    page.click(f"text={t(Labels.MENU_ACCESS_TOKEN)}")
    assert_equal(page.url, context.url("/admin/accesstoken/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty name")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url("/admin/accesstoken/createnew/"))

    # Try to create without filling required fields
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    # A POST lands on the list URL whether validation passed or failed
    # (LastaFlute re-renders createnew.jsp under /admin/accesstoken/ on error
    # and redirects to the same URL on success); ul.has-error is the real
    # discriminator between the two outcomes.
    assert_equal(page.url, context.url("/admin/accesstoken/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "empty required fields must be rejected")
    logger.info("Test 1 passed: required field validation working")

    # Test 2: XSS prevention in name field
    logger.info("Test 2: XSS prevention in name field")
    xss_marker = f"x{context.generate_str(10)}"
    xss_name = f"<script>alert('xss')</script>{xss_marker}"
    try:
        page.fill("input[name=\"name\"]", xss_name)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.locator("ul.has-error").count(), 0,
                     f"XSS-named record should have been created; url={page.url}")
        # The payload must render as escaped TEXT, never as live markup.
        payload_is_live = page.evaluate(
            "() => Array.from(document.querySelectorAll('script'))"
            ".some(s => (s.textContent || '').includes(\"alert('xss')\"))")
        assert_true(not payload_is_live,
                    "XSS payload was parsed into a live script element")
        assert_not_equal(page.inner_text("table").find("script"), -1,
                         "XSS attempt should be visible as text, not executed")
        logger.info("Test 2 passed: XSS prevention working - payload escaped, not executed")
    finally:
        cleanup = Cleanup()
        with cleanup.guard(f"access token '{xss_marker}'"):
            delete_by_name(context, page, "/admin/accesstoken/", xss_marker)
        cleanup.escalate()

    # Test 3: Maximum length validation
    # name has @Size(max=1000); 300 chars would be accepted (and leak a
    # record with no cleanup path), so use 1001 chars to actually exercise
    # the reject path.
    logger.info("Test 3: Maximum length validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"name\"]", context.generate_str(1001))
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_true(page.locator("ul.has-error").count() > 0,
                "name over 1000 chars must be rejected")
    logger.info("Test 3 passed: over-long name rejected")

    # Test 3 rejected (nothing was created); leave the browser on the real
    # list page.
    page.goto(context.url("/admin/accesstoken/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Access token validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
