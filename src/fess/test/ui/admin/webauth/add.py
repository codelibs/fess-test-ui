
import logging

from fess.test import assert_equal, assert_not_equal
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
    logger.info(f"start")

    page: "Page" = context.get_admin_page()

    # Navigate to web authentication list
    page.wait_for_selector("text=クローラー", state="visible", timeout=60000)
    page.click("text=クローラー")
    page.wait_for_selector("text=ウェブ認証", state="visible", timeout=60000)
    page.click("text=ウェブ認証")
    assert_equal(page.url, context.url("/admin/webauth/"))

    # Click new creation button
    page.wait_for_selector("text=新規作成 >> em", state="visible", timeout=60000)
    page.click("text=新規作成 >> em")
    assert_equal(page.url, context.url("/admin/webauth/createnew/"))

    # Wait for form to load completely
    page.wait_for_load_state("networkidle", timeout=60000)

    # Fill hostname
    page.fill("input[name=\"hostname\"]", "test.example.com")

    # Fill port
    page.fill("input[name=\"port\"]", "80")

    # Fill username
    page.fill("input[name=\"username\"]", "testuser")

    # Fill password
    page.fill("input[name=\"password\"]", "testpass123")

    # Select protocol scheme
    page.wait_for_selector("select[name=\"protocolScheme\"]", state="visible", timeout=60000)
    page.select_option("select[name=\"protocolScheme\"]", "http")

    # Select web config if available
    try:
        page.wait_for_selector("select[name=\"webConfigId\"]", state="visible", timeout=5000)
        page.select_option("select[name=\"webConfigId\"]", index=0)
    except Exception:
        logger.warning("No web config available, test may fail")

    # Click create button
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/webauth/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find("test.example.com"), -1,
                     f"Web authentication not found in table")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
