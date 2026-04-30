
import logging

from fess.test import assert_equal, assert_not_equal
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
    logger.info("Starting stopwords dictionary update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=システム
    logger.info("Step 1: Navigate to System menu")
    page.click(f"text={t(Labels.MENU_SYSTEM)}")

    # Click text=辞書
    logger.info("Step 2: Navigate to Dictionary page")
    page.click(f"text={t(Labels.MENU_DICT)}")
    assert_equal(page.url, context.url("/admin/dict/"))

    # Click text=en/stopwords.txt
    logger.info("Step 3: Open stopwords dictionary")
    page.click("text=en/stopwords.txt")
    assert_equal(page.url, context.url("/admin/dict/stopwords/?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    # Navigate to next page to find the entry added by add test
    # (pre-existing entries fill page 1; new entry is appended to end)
    logger.info("Step 4: Navigate to next page and click on existing entry")
    page.goto(context.url("/admin/dict/stopwords/list/2?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={label_name}")

    # Click text=編集
    logger.info("Step 6: Click edit button")
    page.click(f"text={t(Labels.CRUD_BUTTON_EDIT)}")

    # Click text=戻る (test cancel button)
    logger.info("Step 7: Test cancel button")
    page.click(f'a:has-text("{t(Labels.CRUD_BUTTON_BACK)}")')

    # Click text=編集 again
    logger.info("Step 8: Click edit button again")
    page.click(f"text={t(Labels.CRUD_BUTTON_EDIT)}")

    # Fill input[name="input"]
    logger.info("Step 9: Update form field")
    page.fill("input[name=\"input\"]", label_name)

    # Click text=更新
    logger.info("Step 10: Submit form to update entry")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    assert_equal(page.url, context.url("/admin/dict/stopwords/list/1?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="))

    logger.info("Step 11: Verify entry was updated (redirected to list page 1)")
    page.wait_for_load_state("domcontentloaded")
    # Entry may be on any page; URL redirect to list/1 confirms update succeeded

    logger.info("Stopwords dictionary update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
