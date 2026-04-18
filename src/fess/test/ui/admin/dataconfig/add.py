import logging

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

# handlerName select is empty when no data store plugins are installed.
# We inject an option so the form can be submitted; the server accepts any string.
HANDLER_NAME = "CsvDataStore"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _inject_handler(page, value: str) -> None:
    """Inject a handler option into the empty select and select it."""
    page.evaluate(
        f"""
        (function() {{
            var sel = document.querySelector("select[name=handlerName]");
            var opt = document.createElement("option");
            opt.value = {value!r};
            opt.text = {value!r};
            sel.appendChild(opt);
            sel.value = {value!r};
        }})();
        """
    )


def run(context: FessContext) -> None:
    logger.info("Starting dataconfig add test")
    page = context.get_admin_page()
    name: str = context.create_label_name()

    logger.info("Step 1: Navigate to dataconfig page")
    page.goto(context.url("/admin/dataconfig/"))
    page.wait_for_load_state("domcontentloaded")

    logger.info("Step 2: Open create form")
    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/dataconfig/createnew/"),
                 f"expected createnew URL, got {page.url}")

    logger.info("Step 3: Fill fields")
    page.fill("input[name=\"name\"]", name)
    _inject_handler(page, HANDLER_NAME)
    page.fill("textarea[name=\"handlerScript\"]", "return null;")
    page.fill("input[name=\"boost\"]", "1.0")

    logger.info("Step 4: Submit")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/dataconfig/"),
                 f"expected list URL after create, got {page.url}")

    logger.info("Step 5: Verify row in list")
    body = page.inner_text("section.content")
    assert_contains(body, name, f"{name} not in list after create")

    logger.info("Step 6: Open details page")
    page.locator(f"tr:has-text('{name}')").first.click()
    page.wait_for_load_state("domcontentloaded")
    assert_contains(page.url, "/admin/dataconfig/details/",
                    f"expected details URL, got {page.url}")

    logger.info("dataconfig add test completed")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
