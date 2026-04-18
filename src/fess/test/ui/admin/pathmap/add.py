
import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
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
    logger.info("Starting pathmap add test")

    page = context.get_admin_page()
    name: str = context.create_label_name()
    logger.debug(f"Using test name: {name}")

    # Step 1: Navigate to pathmap page
    logger.info("Step 1: Navigating to pathmap page")
    page.click("text=クローラー")
    page.click("text=パスマッピング")
    assert_equal(page.url, context.url("/admin/pathmap/"))

    # Step 2: Open create form
    logger.info("Step 2: Opening create form")
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/pathmap/createnew/"))

    # Step 3: Fill form fields
    logger.info("Step 3: Filling form fields")
    page.fill("input[name=\"regex\"]", f"/old-{name}/.*")
    page.fill("input[name=\"replacement\"]", f"/new-{name}/")
    page.select_option("select[name=\"processType\"]", "B")
    page.fill("input[name=\"sortOrder\"]", "1")
    page.fill("input[name=\"userAgent\"]", f"TestAgent-{name}")

    # Step 4: Submit form
    logger.info("Step 4: Submitting form")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/pathmap/"))

    # Step 5: Verify pattern in list
    logger.info("Step 5: Verifying pattern in list")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(f"/old-{name}/"), -1,
                     f"/old-{name}/ not in table after create")

    # Step 6: Verify pathmap details
    logger.info("Step 6: Verifying pathmap details")
    page.locator(f"tr:has-text('/old-{name}/')").click()
    assert_startswith(page.url, context.url("/admin/pathmap/details/"))

    regex_value = page.input_value("input[name=\"regex\"]")
    assert_equal(regex_value, f"/old-{name}/.*",
                 f"regex value '{regex_value}' != expected '/old-{name}/.*'")

    replacement_value = page.input_value("input[name=\"replacement\"]")
    assert_equal(replacement_value, f"/new-{name}/",
                 f"replacement value '{replacement_value}' != expected '/new-{name}/'")

    logger.info("Pathmap add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
