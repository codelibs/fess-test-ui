
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
    logger.info("Starting web config validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to webconfig
    page.click(f"text={t(Labels.MENU_CRAWL)}")
    page.click(f"text={t(Labels.MENU_WEB)}")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty name")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url("/admin/webconfig/createnew/"))

    # Try to create without filling required fields
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    # A POST lands on the list URL whether validation passed or failed
    # (LastaFlute re-renders createnew.jsp under /admin/webconfig/ on error
    # and redirects to the same URL on success); ul.has-error is the real
    # discriminator between the two outcomes.
    assert_equal(page.url, context.url("/admin/webconfig/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "empty required fields must be rejected")
    logger.info("Test 1 passed: required field validation working")

    # Test 2: Required field validation - name only, missing urls
    # (continues filling the same error-rendered form, not a fresh page -
    # resubmitting here is safe because verifyToken() runs after validate(),
    # so a validation failure never consumes the double-submit token)
    logger.info("Test 2: Required field validation - name only, missing URLs")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/webconfig/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "urls is @Required; missing it must be rejected")
    logger.info("Test 2 passed: name-only submission rejected")

    # Navigate back to the real list page
    page.click(f"text={t(Labels.CRUD_BUTTON_BACK)}")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    # Test 3: Special characters in name (XSS prevention)
    logger.info("Test 3: Special characters in name")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    special_char_marker = f"x{context.generate_str(10)}"
    special_char_name = f"Test<script>alert('xss')</script>{special_char_marker}"
    try:
        page.fill("input[name=\"name\"]", special_char_name)
        page.fill("textarea[name=\"urls\"]", "https://example.com/")
        page.fill("textarea[name=\"includedUrls\"]", "https://example.com/.*")
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
        logger.info("Test 3 passed: XSS prevention working - script tag displayed as text")
    finally:
        cleanup = Cleanup()
        with cleanup.guard(f"web config '{special_char_marker}'"):
            delete_by_name(context, page, "/admin/webconfig/", special_char_marker)
        cleanup.escalate()

    # Test 4: Maximum length validation for name
    logger.info("Test 4: Maximum length validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    very_long_name = context.generate_str(300)  # name has @Size(max=200)
    page.fill("input[name=\"name\"]", very_long_name)
    page.fill("textarea[name=\"urls\"]", "https://example.com/")
    page.fill("textarea[name=\"includedUrls\"]", "https://example.com/.*")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_true(page.locator("ul.has-error").count() > 0,
                "over-long name must be rejected")
    logger.info("Test 4 passed: over-long name rejected")

    # Test 4 rejected, so the page is still the create form re-rendered
    # under the list URL (no "Create New" link there); get back to the
    # real list page before Test 5 clicks it.
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")

    # Test 5: Invalid URL format
    logger.info("Test 5: Invalid URL format")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.fill("textarea[name=\"urls\"]", "not-a-valid-url")
    page.fill("textarea[name=\"includedUrls\"]", "also-not-valid")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    # urls has @UriType(protocolType = WEB): every non-blank line must start
    # with an allowed web protocol (http/https). "not-a-valid-url" does not,
    # so this must be rejected. includedUrls has no such format check (it is
    # a regex pattern, not a URL), so it is not what triggers the rejection.
    assert_true(page.locator("ul.has-error").count() > 0,
                "urls not matching an allowed protocol (http/https) must be rejected")
    logger.info("Test 5 passed: non-URL value in urls field rejected")

    # Test 5 rejected, so the page is still the create form re-rendered
    # under the list URL (no "Create New" link there); get back to the
    # real list page before Test 6 clicks it.
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")

    # Test 6: Duplicate name prevention
    logger.info("Test 6: Duplicate name prevention")
    duplicate_test_name = f"DuplicateTest_{context.generate_str(5)}"

    try:
        # Create first entry
        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.fill("input[name=\"name\"]", duplicate_test_name)
        page.fill("textarea[name=\"urls\"]", "https://example1.com/")
        page.fill("textarea[name=\"includedUrls\"]", "https://example1.com/.*")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")

        # Try to create a duplicate. Fess has no duplicate check for
        # webconfig names; the id is auto-generated (not derived from the
        # name), so this creates a second, independent row.
        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.fill("input[name=\"name\"]", duplicate_test_name)
        page.fill("textarea[name=\"urls\"]", "https://example2.com/")
        page.fill("textarea[name=\"includedUrls\"]", "https://example2.com/.*")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")

        assert_equal(page.locator("ul.has-error").count(), 0,
                     "Fess does not reject duplicate names")
        assert_equal(page.locator(f'table tr:has-text("{duplicate_test_name}")').count(), 2,
                     "duplicate webconfig create gets an auto-generated id -> two independent rows")
        logger.info("Test 6 passed: duplicate name creates two independent rows")
    finally:
        cleanup = Cleanup()
        with cleanup.guard(f"web config '{duplicate_test_name}'"):
            delete_by_name(context, page, "/admin/webconfig/", duplicate_test_name)
        cleanup.escalate()

    logger.info("Web config validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
