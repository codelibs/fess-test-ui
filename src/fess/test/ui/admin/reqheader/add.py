import logging

from fess.test import assert_equal, assert_contains, assert_startswith
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.reqheader._const import WEBCONFIG_NAME
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _ensure_webconfig(page, context: FessContext) -> None:
    """Create WEBCONFIG_NAME if not present. Idempotent."""
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("body")
    if WEBCONFIG_NAME in body:
        logger.info(f"webconfig {WEBCONFIG_NAME} already exists; skipping")
        return
    logger.info(f"Creating webconfig: {WEBCONFIG_NAME}")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.wait_for_load_state("domcontentloaded")
    page.fill("input[name=\"name\"]", WEBCONFIG_NAME)
    page.fill("textarea[name=\"urls\"]", "http://sampledata01/")
    page.fill("textarea[name=\"includedUrls\"]", "http://sampledata01/.*")
    page.fill("input[name=\"maxAccessCount\"]", "10")
    page.fill("input[name=\"numOfThread\"]", "1")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.inner_text("section.content"), WEBCONFIG_NAME,
                    "webconfig not in list after create")


def run(context: FessContext) -> None:
    logger.info("Starting reqheader add test")
    page = context.get_admin_page()
    name: str = context.create_label_name()
    header_name = f"X-E2E-{name[:10]}"
    logger.debug(f"Using header name: {header_name}")

    _ensure_webconfig(page, context)

    logger.info("Step 1: Navigate to reqheader")
    page.goto(context.url("/admin/reqheader/"))
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/reqheader/"))

    logger.info("Step 2: Open create form")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/reqheader/createnew/"))

    logger.info("Step 3: Fill fields")
    page.fill("input[name=\"name\"]", header_name)
    page.fill("input[name=\"value\"]", f"value-{name}")
    page.select_option("select[name=\"webConfigId\"]", label=WEBCONFIG_NAME)

    logger.info("Step 4: Submit")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/reqheader/"))

    logger.info("Step 5: Verify row")
    body = page.inner_text("section.content")
    assert_contains(body, header_name, f"{header_name} not in list after create")

    logger.info("Step 6: Open details")
    page.locator(f"tr:has-text('{header_name}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url("/admin/reqheader/details/"),
                      f"expected details URL, got {page.url}")

    logger.info("reqheader add test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
