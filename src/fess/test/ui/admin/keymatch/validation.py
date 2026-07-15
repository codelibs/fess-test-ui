
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
    (see the duplicate-name test in sibling modules), so a leaked name can
    appear more than once. Swallows and logs its own failures so a cleanup
    problem never masks the real test outcome in the enclosing try/finally."""
    max_iterations = 10
    try:
        page.goto(context.url(list_path))
        page.wait_for_load_state("domcontentloaded")
        iterations = 0
        while page.locator(f'table tr:has-text("{name}")').count() > 0:
            iterations += 1
            if iterations > max_iterations:
                logger.error(f"CLEANUP FAILED for name={name!r} at {list_path} -- gave up "
                             f"after {max_iterations} iterations without making progress; "
                             f"this record has LEAKED and will pollute later modules on "
                             f"this shared instance")
                break
            page.locator(f'table tr:has-text("{name}")').first.click()
            page.wait_for_load_state("domcontentloaded")
            page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
            page.click('div.modal-footer button[name="delete"]')
            page.wait_for_load_state("domcontentloaded")
            page.goto(context.url(list_path))
            page.wait_for_load_state("domcontentloaded")
    except Exception as e:
        logger.error(f"CLEANUP FAILED for name={name!r} at {list_path} -- this record has "
                     f"LEAKED and will pollute later modules on this shared instance: {e}")


def run(context: FessContext) -> None:
    logger.info("Starting key match validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to keymatch
    page.click(f"text={t(Labels.MENU_CRAWL)}")
    page.click(f"text={t(Labels.MENU_KEY_MATCH)}")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Test 1: Required field validation
    logger.info("Test 1: Required field validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url("/admin/keymatch/createnew/"))

    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    # A POST lands on the list URL whether validation passed or failed
    # (LastaFlute re-renders createnew.jsp under /admin/keymatch/ on error
    # and redirects to the same URL on success); ul.has-error is the real
    # discriminator between the two outcomes.
    assert_equal(page.url, context.url("/admin/keymatch/"))
    assert_true(page.locator("ul.has-error").count() > 0,
                "empty required fields must be rejected")
    logger.info("Test 1 passed: required field validation working")

    # Test 2: XSS prevention. Continues filling the same error-rendered form
    # (does not re-click "Create New") - Tests 2/3 never touch maxSize/boost
    # (both @Required); initialize() already populated them when the create
    # page was first opened above, and LastaFlute preserves submitted values
    # across the error re-render, so they stay valid without being touched.
    logger.info("Test 2: XSS prevention in term field")
    xss_marker = f"x{context.generate_str(10)}"
    xss_term = f"<script>alert('xss')</script>{xss_marker}"
    try:
        page.fill("input[name=\"term\"]", xss_term)
        page.fill("input[name=\"query\"]", "test query")
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
        _cleanup_by_name(context, page, "/admin/keymatch/", xss_marker)

    # Test 3: Maximum length validation
    logger.info("Test 3: Maximum length validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"term\"]", context.generate_str(300))
    page.fill("input[name=\"query\"]", context.generate_str(300))
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_true(page.locator("ul.has-error").count() > 0,
                "over-long term (term has @Size(max=100)) must be rejected")
    logger.info("Test 3 passed: over-long term rejected")

    # Test 3 rejected (nothing was created); leave the browser on the real
    # list page.
    page.goto(context.url("/admin/keymatch/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Key match validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
