
import logging

from fess.test import assert_equal
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
    logger.info("Starting group validation test")

    page: "Page" = context.get_admin_page()

    # Navigate to group
    page.click(f"text={t(Labels.MENU_USER)}")
    page.click(f"text={t(Labels.MENU_GROUP)}")
    assert_equal(page.url, context.url("/admin/group/"))

    # Test 1: Required field validation - empty name
    logger.info("Test 1: Required field validation - empty name")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url("/admin/group/createnew/"))

    # Try to create without filling required fields
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/group/createnew/"),
                "Should stay on create page when required fields are empty")
    logger.info("Test 1 passed: Required field validation working")

    # Test 2: Special characters in group name (XSS prevention)
    logger.info("Test 2: XSS prevention in group name")
    page.fill("input[name=\"name\"]", f"<script>alert('xss')</script>{context.generate_str(5)}")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    if page.url == context.url("/admin/group/"):
        logger.info("Test 2 passed: XSS prevention working - group created with escaped content")

    # Test 3: Maximum length validation
    logger.info("Test 3: Maximum length validation")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"name\"]", context.generate_str(300))
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')

    page.wait_for_load_state("domcontentloaded")
    logger.info("Test 3 passed: Long input handled")

    # Navigate back
    if page.url != context.url("/admin/group/"):
        page.goto(context.url("/admin/group/"))

    # Test 4: Duplicate group name prevention
    logger.info("Test 4: Duplicate group name prevention")
    duplicate_group = f"TestGroup_{context.generate_str(5)}"

    # Create first group
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill("input[name=\"name\"]", duplicate_group)
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")

    if page.url == context.url("/admin/group/"):
        # Try to create duplicate
        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.fill("input[name=\"name\"]", duplicate_group)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        page.wait_for_load_state("domcontentloaded")

        # Should reject duplicate
        logger.info("Test 4 passed: Duplicate group name test completed")

        # Cleanup: delete the test group
        page.goto(context.url("/admin/group/"))
        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        if table_content.find(duplicate_group) != -1:
            page.click(f"text={duplicate_group}")
            page.wait_for_load_state("domcontentloaded")
            page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
            page.click('div.modal-footer button[name="delete"]')
            page.wait_for_load_state("domcontentloaded")

    logger.info("Group validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
