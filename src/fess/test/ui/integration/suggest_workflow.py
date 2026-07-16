
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
    """
    Integration test for suggest features workflow:
    1. Create keymatch entry
    2. Create related content entry
    3. Create related query entry
    4. Verify all entries are created
    5. Delete all entries (cleanup)
    """
    logger.info("start suggest workflow integration test")

    page: "Page" = context.get_admin_page()
    label_base = context.create_label_name()
    search_term = f"term_{label_base}"

    created: list = []
    try:
        # Step 1: Create KeyMatch entry
        logger.info("Step 1: Creating KeyMatch entry")
        page.click(f"text={t(Labels.MENU_CRAWL)}")
        page.click(f"text={t(Labels.MENU_KEY_MATCH)}")
        assert_equal(page.url, context.url("/admin/keymatch/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/keymatch/createnew/"))

        page.fill("input[name=\"term\"]", search_term)
        page.fill("input[name=\"query\"]", f"{search_term} AND test")
        page.fill("input[name=\"maxSize\"]", "10")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/keymatch/"))

        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(search_term), -1,
                         f"KeyMatch {search_term} not created")
        created.append("keymatch")
        logger.info(f"✓ KeyMatch entry '{search_term}' created")

        # Step 2: Create RelatedContent entry
        logger.info("Step 2: Creating RelatedContent entry")
        page.goto(context.url("/admin/relatedcontent/"))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.url, context.url("/admin/relatedcontent/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/relatedcontent/createnew/"))

        page.fill("input[name=\"term\"]", search_term)
        page.fill("textarea[name=\"content\"]", f"<p>Related content for {search_term}</p>")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/relatedcontent/"))

        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(search_term), -1,
                         f"RelatedContent {search_term} not created")
        created.append("relatedcontent")
        logger.info(f"✓ RelatedContent entry '{search_term}' created")

        # Step 3: Create RelatedQuery entry
        logger.info("Step 3: Creating RelatedQuery entry")
        page.goto(context.url("/admin/relatedquery/"))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.url, context.url("/admin/relatedquery/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/relatedquery/createnew/"))

        page.fill("input[name=\"term\"]", search_term)
        page.fill("textarea[name=\"queries\"]", f"{search_term} related\n{search_term} similar")
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/relatedquery/"))

        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(search_term), -1,
                         f"RelatedQuery {search_term} not created")
        created.append("relatedquery")
        logger.info(f"✓ RelatedQuery entry '{search_term}' created")
    finally:
        # Step 4: Cleanup - Delete RelatedQuery
        if "relatedquery" in created:
            try:
                logger.info("Step 4: Cleanup - deleting RelatedQuery")
                page.goto(context.url("/admin/relatedquery/"))
                page.wait_for_load_state("domcontentloaded")
                page.click(f"text={search_term}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/relatedquery/"))
                logger.info("✓ RelatedQuery entry deleted")
            except Exception as e:
                logger.error(f"LEAKED RelatedQuery entry '{search_term}' — will pollute later modules: {e}")

        # Step 5: Delete RelatedContent
        if "relatedcontent" in created:
            try:
                logger.info("Step 5: Deleting RelatedContent")
                page.goto(context.url("/admin/relatedcontent/"))
                page.wait_for_load_state("domcontentloaded")
                assert_equal(page.url, context.url("/admin/relatedcontent/"))

                page.click(f"text={search_term}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/relatedcontent/"))
                logger.info("✓ RelatedContent entry deleted")
            except Exception as e:
                logger.error(f"LEAKED RelatedContent entry '{search_term}' — will pollute later modules: {e}")

        # Step 6: Delete KeyMatch
        if "keymatch" in created:
            try:
                logger.info("Step 6: Deleting KeyMatch")
                page.goto(context.url("/admin/keymatch/"))
                page.wait_for_load_state("domcontentloaded")
                assert_equal(page.url, context.url("/admin/keymatch/"))

                page.click(f"text={search_term}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/keymatch/"))
                logger.info("✓ KeyMatch entry deleted")
            except Exception as e:
                logger.error(f"LEAKED KeyMatch entry '{search_term}' — will pollute later modules: {e}")

    logger.info("✓ Suggest workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
