
import logging

from fess.test import assert_equal
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

    # Navigate to path mapping list
    page.click("text=システム")
    page.click("text=パスマッピング")
    assert_equal(page.url, context.url("/admin/pathmap/"))

    page.wait_for_load_state("domcontentloaded")

    # Get the regex from the first row before deletion
    first_row_content = page.inner_text("tbody tr:first-child")

    # Click first delete button
    page.click("tbody tr:first-child button[data-toggle='modal']")

    # Wait for modal to appear
    page.wait_for_selector(".modal.show")

    # Click confirm delete button in modal
    page.click(".modal.show button:has-text(\"削除\")")
    page.wait_for_load_state("domcontentloaded")

    assert_equal(page.url, context.url("/admin/pathmap/"))

    # Verify item is deleted
    page.wait_for_load_state("domcontentloaded")
    try:
        table_content: str = page.inner_text("table")
        assert first_row_content not in table_content or "該当するデータがありません" in page.inner_text("body"), \
            f"Item was not deleted"
    except Exception:
        # Table might not exist if all items are deleted
        assert "該当するデータがありません" in page.inner_text("body"), \
            f"Expected empty data message"


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
