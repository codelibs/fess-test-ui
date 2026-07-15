
import logging

from fess.test import assert_equal, assert_not_equal, assert_true
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


def _cleanup_by_name(context: FessContext, page: "Page", list_path: str, name: str) -> None:
    """Delete every row matching `name` on an admin list page. Loops rather
    than assuming a single match because Fess never rejects duplicate names
    (see the duplicate-name test below), so a leaked name can appear more
    than once. Swallows and logs its own failures so a cleanup problem never
    masks the real test outcome in the enclosing try/finally."""
    try:
        page.goto(context.url(list_path))
        page.wait_for_load_state("domcontentloaded")
        while page.locator(f'table tr:has-text("{name}")').count() > 0:
            page.locator(f'a:has-text("{name}")').first.click()
            page.wait_for_load_state("domcontentloaded")
            page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
            page.click('div.modal-footer button[name="delete"]')
            page.wait_for_load_state("domcontentloaded")
            page.goto(context.url(list_path))
            page.wait_for_load_state("domcontentloaded")
    except Exception as e:
        logger.warning(f"cleanup failed for name={name!r} at {list_path}: {e}")


def run(context: FessContext) -> None:
    logger.info("Starting user validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to user
    page.click(f"text={t(Labels.MENU_USER)}")
    page.click('a[href*="/admin/user/"]')
    assert_equal(page.url, context.url("/admin/user/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty fields")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url("/admin/user/createnew/"))

    # Try to create without filling required fields
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    # A POST lands on the list URL whether validation passed or failed
    # (LastaFlute re-renders createnew.jsp under /admin/user/ on error and
    # redirects to the same URL on success); ul.has-error is the real
    # discriminator between the two outcomes.
    assert_equal(page.url, context.url("/admin/user/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "empty required fields must be rejected")
    logger.info("Test 1 passed: required field validation working")

    # Test 2: Password mismatch
    logger.info("Test 2: Password confirmation mismatch")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.fill("input[name=\"password\"]", "password123")
    page.fill("input[name=\"confirmPassword\"]", "password456")  # Different password
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/user/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "mismatched password confirmation must be rejected")
    logger.info("Test 2 passed: password mismatch validation working")

    # Test 3: Special characters in username (XSS prevention)
    logger.info("Test 3: XSS prevention in username")
    xss_marker = f"x{context.generate_str(10)}"
    xss_username = f"<script>alert('xss')</script>{xss_marker}"
    try:
        page.fill("input[name=\"name\"]", xss_username)
        page.fill("input[name=\"password\"]", "password123")
        page.fill("input[name=\"confirmPassword\"]", "password123")
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
        logger.info("Test 3 passed: XSS prevention working - payload escaped, not executed")
    finally:
        _cleanup_by_name(context, page, "/admin/user/", xss_marker)

    # Test 4: Invalid password (below password.min.length=8)
    logger.info("Test 4: Weak password validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"name\"]", context.generate_str(10))
    page.fill("input[name=\"password\"]", "123")  # Too short
    page.fill("input[name=\"confirmPassword\"]", "123")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/user/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "password shorter than password.min.length=8 must be rejected")
    logger.info("Test 4 passed: weak password rejected")

    # Test 4 rejected, so the page is still the create form re-rendered
    # under the list URL (no "Create New" link there); get back to the
    # real list page before Test 5 clicks it.
    page.goto(context.url("/admin/user/"))
    page.wait_for_load_state("domcontentloaded")

    # Test 5: Duplicate username prevention
    logger.info("Test 5: Duplicate username prevention")
    duplicate_username = f"TestUser_{context.generate_str(5)}"

    try:
        # Create first user
        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.fill("input[name=\"name\"]", duplicate_username)
        page.fill("input[name=\"password\"]", "password123")
        page.fill("input[name=\"confirmPassword\"]", "password123")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")

        # Try to create a duplicate. Fess has no duplicate check for user
        # names; the id is Base64(name), so this upserts the same row.
        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.fill("input[name=\"name\"]", duplicate_username)
        page.fill("input[name=\"password\"]", "password456")
        page.fill("input[name=\"confirmPassword\"]", "password456")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")

        assert_equal(page.locator("ul.has-error").count(), 0,
                     "Fess does not reject duplicate names")
        assert_equal(page.locator(f'table tr:has-text("{duplicate_username}")').count(), 1,
                     "duplicate user create must upsert onto a single row")
        logger.info("Test 5 passed: duplicate username upserts onto a single row")
    finally:
        _cleanup_by_name(context, page, "/admin/user/", duplicate_username)

    logger.info("User validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
