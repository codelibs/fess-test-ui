
import logging
import re

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
    """
    Integration test for dictionary management workflow:
    1. Create multiple dictionary entries (kuromoji, mapping, protwords)
    2. Verify all entries are created
    3. Delete all entries (cleanup)
    """
    logger.info("start dictionary workflow integration test")

    page: "Page" = context.get_admin_page()
    test_word = f"TestWord_{context.generate_str(5)}"

    created: list = []
    try:
        # Step 1: Navigate to dictionary management
        logger.info("Step 1: Navigating to dictionary management")
        page.click(f"text={t(Labels.MENU_SYSTEM)}")
        page.click(f"text={t(Labels.MENU_DICT)}")
        assert_equal(page.url, context.url("/admin/dict/"))

        # Step 2: Add kuromoji entry
        logger.info("Step 2: Adding kuromoji dictionary entry")
        page.click("text=ja/kuromoji.txt")
        page.wait_for_load_state("domcontentloaded")

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.wait_for_load_state("domcontentloaded")

        page.fill("input[name=\"token\"]", test_word)
        page.fill("input[name=\"segmentation\"]", "全文 検索 エンジン")
        page.fill("input[name=\"reading\"]", "ゼンブン ケンサク エンジン")
        page.fill("input[name=\"pos\"]", "名詞")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))
        page.wait_for_load_state("domcontentloaded")

        table_content: str = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

        created.append("kuromoji")
        logger.info(f"✓ Kuromoji entry '{test_word}' created")

        # Step 3: Add protwords entry
        logger.info("Step 3: Adding protwords dictionary entry")
        page.goto(context.url("/admin/dict/"))
        page.click("text=en/protwords.txt")
        page.wait_for_load_state("domcontentloaded")

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.wait_for_load_state("domcontentloaded")

        page.fill("input[name=\"input\"]", test_word)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/dict/protwords/list/1?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))
        page.wait_for_load_state("domcontentloaded")

        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

        created.append("protwords")
        logger.info(f"✓ Protwords entry '{test_word}' created")

        # Step 4: Add mapping entry
        logger.info("Step 4: Adding mapping dictionary entry")
        page.goto(context.url("/admin/dict/"))
        page.click(":nth-match(:text(\"mapping.txt\"), 3)")
        page.wait_for_load_state("domcontentloaded")

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        page.wait_for_load_state("domcontentloaded")

        page.fill("textarea[name=\"inputs\"]", test_word)
        page.fill("input[name=\"output\"]", "mapped_value")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="))
        page.wait_for_load_state("domcontentloaded")

        # New entries are appended at the end of the list; jump to
        # the last page to find the one just created.
        page_info: str = page.inner_text("div.col-sm-2")
        match = re.search(r'(\d+)/(\d+)', page_info)
        last_page = int(match.group(2)) if match else 1
        page.goto(page.url.replace("/list/1", f"/list/{last_page}"))
        page.wait_for_load_state("domcontentloaded")

        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

        created.append("mapping")
        logger.info(f"✓ Mapping entry '{test_word}' created")
    finally:
        # Step 5: Cleanup - Delete mapping entry
        if "mapping" in created:
            try:
                logger.info("Step 5: Cleanup - deleting mapping entry")
                page.goto(context.url("/admin/dict/"))
                page.click(":nth-match(:text(\"mapping.txt\"), 3)")
                page.wait_for_load_state("domcontentloaded")

                # New entries are appended at the end of the list; jump to
                # the last page to find the one just created.
                page_info: str = page.inner_text("div.col-sm-2")
                match = re.search(r'(\d+)/(\d+)', page_info)
                last_page = int(match.group(2)) if match else 1
                page.goto(page.url.replace("/admin/dict/mapping/?dictId=",
                                            f"/admin/dict/mapping/list/{last_page}?dictId="))
                page.wait_for_load_state("domcontentloaded")

                # The list cell renders data.inputs (a List) via
                # List.toString(), so a single input shows as [test_word].
                page.click(f"text=[{test_word}]")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                logger.info("✓ Mapping entry deleted")
            except Exception as e:
                logger.error(f"LEAKED mapping dictionary entry '{test_word}' (global analyzer config) — will pollute later modules: {e}")

        # Step 6: Delete protwords entry
        if "protwords" in created:
            try:
                logger.info("Step 6: Deleting protwords entry")
                page.goto(context.url("/admin/dict/"))
                page.click("text=en/protwords.txt")
                page.wait_for_load_state("domcontentloaded")

                page.click(f"text={test_word}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                logger.info("✓ Protwords entry deleted")
            except Exception as e:
                logger.error(f"LEAKED protwords dictionary entry '{test_word}' (global analyzer config) — will pollute later modules: {e}")

        # Step 7: Delete kuromoji entry
        if "kuromoji" in created:
            try:
                logger.info("Step 7: Deleting kuromoji entry")
                page.goto(context.url("/admin/dict/"))
                page.click("text=ja/kuromoji.txt")
                page.wait_for_load_state("domcontentloaded")

                page.click(f"text={test_word}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                logger.info("✓ Kuromoji entry deleted")
            except Exception as e:
                logger.error(f"LEAKED kuromoji dictionary entry '{test_word}' (global analyzer config) — will pollute later modules: {e}")

    logger.info("✓ Dictionary workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
