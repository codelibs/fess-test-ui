
import logging
import re

from fess.test import assert_equal, assert_not_equal
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup, assert_absent
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def _last_page(page: "Page") -> int:
    """Last page number of an admin dictionary list, read from the "n/m" pager.

    New entries are appended at the end of the list, so a dictionary that
    ships with more rows than fit on one page puts a freshly created entry on
    the last page rather than the first. Falls back to 1 when the pager cannot
    be read, and says so: a silent fall back to page 1 looks exactly like a
    record that was never created.
    """
    page_info: str = page.inner_text("div.col-sm-2")
    match = re.search(r'(\d+)/(\d+)', page_info)
    if not match:
        logger.warning(f"could not read the pager from {page_info!r}; assuming a "
                       f"single page. If the entry is not found below, suspect this "
                       f"first -- the div.col-sm-2 markup may have changed.")
        return 1
    return int(match.group(2))


def _assert_entry_deleted(page: "Page", word: str, where: str) -> None:
    """Assert `word` is gone, looking on the page a survivor would be on.

    Every dict delete ends in redirectWith(..., moreUrl("list/1")), but new
    entries are appended, so an entry that survived deletion sits on the LAST
    page (see _last_page). Checking whichever page the redirect lands on would
    therefore pass while the row sat pages away -- an assertion that cannot
    fail, which is exactly what this replaces.

    _last_page is read before the goto, off the list/1 pager we land on.
    """
    page.goto(page.url.replace("/list/1", f"/list/{_last_page(page)}"))
    page.wait_for_load_state("domcontentloaded")
    assert_absent(page, word, where)


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
        # Register for cleanup before verifying. If an assertion below fails
        # after the record landed, finally must still delete it -- gating
        # cleanup on the verification would leak the record silently, with no
        # LEAKED log, onto an instance every later module shares.
        created.append("kuromoji")
        assert_equal(page.url, context.url("/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"))
        page.wait_for_load_state("domcontentloaded")

        table_content: str = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

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
        created.append("protwords")
        assert_equal(page.url, context.url("/admin/dict/protwords/list/1?dictId=ZW4vcHJvdHdvcmRzLnR4dA=="))
        page.wait_for_load_state("domcontentloaded")

        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

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
        created.append("mapping")
        assert_equal(page.url, context.url("/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="))
        page.wait_for_load_state("domcontentloaded")

        # mapping.txt ships with over a thousand entries, so the new one is not
        # on page 1 -- see _last_page.
        page.goto(page.url.replace("/list/1", f"/list/{_last_page(page)}"))
        page.wait_for_load_state("domcontentloaded")

        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(test_word), -1,
                         f"{test_word} not in {table_content}")

        logger.info(f"✓ Mapping entry '{test_word}' created")
    finally:
        # These entries are GLOBAL analyzer config: a survivor changes
        # tokenisation for every later run on this shared instance, so a leak
        # here is escalated rather than merely logged.
        cleanup = Cleanup()

        # Step 5: Cleanup - Delete mapping entry
        if "mapping" in created:
            with cleanup.guard(f"mapping dictionary entry '{test_word}' (global analyzer config)"):
                logger.info("Step 5: Cleanup - deleting mapping entry")
                page.goto(context.url("/admin/dict/"))
                page.click(":nth-match(:text(\"mapping.txt\"), 3)")
                page.wait_for_load_state("domcontentloaded")

                page.goto(page.url.replace(
                    "/admin/dict/mapping/?dictId=",
                    f"/admin/dict/mapping/list/{_last_page(page)}?dictId="))
                page.wait_for_load_state("domcontentloaded")

                # The list cell renders data.inputs (a List) via
                # List.toString(), so a single input shows as [test_word].
                page.click(f"text=[{test_word}]")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                _assert_entry_deleted(page, test_word, "mapping.txt")
                logger.info("✓ Mapping entry deleted")

        # Step 6: Delete protwords entry
        if "protwords" in created:
            with cleanup.guard(f"protwords dictionary entry '{test_word}' (global analyzer config)"):
                logger.info("Step 6: Deleting protwords entry")
                page.goto(context.url("/admin/dict/"))
                page.click("text=en/protwords.txt")
                page.wait_for_load_state("domcontentloaded")

                page.click(f"text={test_word}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                _assert_entry_deleted(page, test_word, "en/protwords.txt")
                logger.info("✓ Protwords entry deleted")

        # Step 7: Delete kuromoji entry
        if "kuromoji" in created:
            with cleanup.guard(f"kuromoji dictionary entry '{test_word}' (global analyzer config)"):
                logger.info("Step 7: Deleting kuromoji entry")
                page.goto(context.url("/admin/dict/"))
                page.click("text=ja/kuromoji.txt")
                page.wait_for_load_state("domcontentloaded")

                page.click(f"text={test_word}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                page.wait_for_load_state("domcontentloaded")
                _assert_entry_deleted(page, test_word, "ja/kuromoji.txt")
                logger.info("✓ Kuromoji entry deleted")

        cleanup.escalate()

    logger.info("✓ Dictionary workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
