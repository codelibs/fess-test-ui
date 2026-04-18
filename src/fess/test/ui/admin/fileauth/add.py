import logging

from fess.test import assert_equal, assert_contains, assert_startswith
from fess.test.ui import FessContext
from fess.test.ui.admin.fileauth._const import FILECONFIG_NAME
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _ensure_fileconfig(page, context: FessContext) -> None:
    """Create FILECONFIG_NAME if not present. Idempotent."""
    page.goto(context.url("/admin/fileconfig/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("body")
    if FILECONFIG_NAME in body:
        logger.info(f"fileconfig {FILECONFIG_NAME} already exists; skipping")
        return
    logger.info(f"Creating fileconfig: {FILECONFIG_NAME}")
    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    page.fill("input[name=\"name\"]", FILECONFIG_NAME)
    page.fill("textarea[name=\"paths\"]", "smb://example.invalid/share/")
    page.fill("input[name=\"maxAccessCount\"]", "10")
    page.fill("input[name=\"numOfThread\"]", "1")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.inner_text("section.content"), FILECONFIG_NAME,
                    "fileconfig not in list after create")


def run(context: FessContext) -> None:
    logger.info("Starting fileauth add test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    hostname = f"host-{name[:8]}"

    _ensure_fileconfig(page, context)

    logger.info("Step 1: Navigate to fileauth")
    page.goto(context.url("/admin/fileauth/"))
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/fileauth/"))

    logger.info("Step 2: Open create form")
    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/fileauth/createnew/"))

    logger.info("Step 3: Fill fields")
    page.fill("input[name=\"hostname\"]", hostname)
    page.fill("input[name=\"port\"]", "445")
    page.select_option("select[name=\"protocolScheme\"]", "SAMBA")
    page.fill("input[name=\"username\"]", f"user-{name[:8]}")
    page.fill("input[name=\"password\"]", "testpass")
    page.select_option("select[name=\"fileConfigId\"]", label=FILECONFIG_NAME)

    logger.info("Step 4: Submit")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/fileauth/"))

    logger.info("Step 5: Verify row")
    body = page.inner_text("section.content")
    assert_contains(body, hostname, f"{hostname} not in list after create")

    logger.info("Step 6: Open details")
    page.locator(f"tr:has-text('{hostname}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url("/admin/fileauth/details/"),
                      f"expected details URL, got {page.url}")

    logger.info("fileauth add test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
