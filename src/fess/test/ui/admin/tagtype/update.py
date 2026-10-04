import logging

from fess.test import assert_equal, assert_startswith, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.tagtype._names import (DETAILS_PATH, LIST_PATH, new_owner,
                                               open_list, owner, tag_name)
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

UPDATED_PATH = "https://example.com/tag/updated.html"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting tag update test")

    page: "Page" = context.get_admin_page()
    name: str = tag_name(context)
    old_owner: str = owner(context)
    moved_owner: str = new_owner(context)

    # Step 1: Navigate to the tag page
    logger.info("Step 1: Navigating to tag page")
    open_list(context, page)
    assert_equal(page.url, context.url(LIST_PATH))

    # Step 2: Open tag details
    logger.info("Step 2: Opening tag details")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url(DETAILS_PATH))
    old_details_url: str = page.url

    # Step 3: Edit, then Back returns to the details without saving
    logger.info("Step 3: Testing edit and back button")
    page.click(f"text={t(Labels.CRUD_BUTTON_EDIT)}")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.input_value("input[name=\"owner\"]"), old_owner)
    page.click(f"text={t(Labels.CRUD_BUTTON_BACK)}")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.input_value("input[name=\"owner\"]"), old_owner)
    assert_equal(page.locator("textarea[name=\"paths\"]").count(), 0,
                 "Back should land on the read-only details, not the edit form")

    # Step 4: Open edit form; it is pre-filled with the stored values
    logger.info("Step 4: Opening edit form")
    page.click(f"text={t(Labels.CRUD_BUTTON_EDIT)}")
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url(LIST_PATH))
    assert_equal(page.input_value("input[name=\"name\"]"), name)
    assert_true("https://example.com/tag/a.html"
                in page.input_value("textarea[name=\"paths\"]"),
                "edit form lost the stored paths")
    permissions: str = page.input_value("textarea[name=\"permissions\"]")
    assert_true(old_owner in permissions,
                f"edit form permissions should hold the owner {old_owner}: {permissions}")

    # Step 5: Change the owner, the paths and the sort order. The
    # permissions textarea is left as loaded: the owner's permission must
    # move to the new owner with it.
    logger.info("Step 5: Updating form fields")
    page.fill("input[name=\"owner\"]", moved_owner)
    page.fill("textarea[name=\"paths\"]", UPDATED_PATH)
    page.fill("input[name=\"sortOrder\"]", "10")

    # Step 6: Submit update
    logger.info("Step 6: Submitting update")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url(LIST_PATH))
    assert_equal(page.locator("ul.has-error").count(), 0,
                 "update was rejected by validation")

    # Step 7: The list shows the tag once, under the new owner only
    logger.info("Step 7: Verifying update in list")
    row = page.locator(f'table tr:has-text("{name}")')
    assert_equal(row.count(), 1, f"{name} is not listed exactly once after update")
    row_text: str = row.inner_text()
    assert_true(moved_owner in row_text,
                f"new owner {moved_owner} not in the row of {name}: {row_text}")
    assert_true(old_owner not in page.inner_text("section.content"),
                f"old owner {old_owner} is still listed after the owner change")

    # Step 8: The details carry the new values; the id follows the owner
    logger.info("Step 8: Verifying updated details")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url(DETAILS_PATH))
    assert_true(page.url != old_details_url,
                f"the id should change with the owner, still {page.url}")
    assert_equal(page.input_value("input[name=\"owner\"]"), moved_owner)
    assert_equal(page.input_value("input[name=\"sortOrder\"]"), "10")
    details: str = page.inner_text("section.content table")
    assert_true(UPDATED_PATH in details, f"updated path not shown: {details}")
    assert_true("https://example.com/tag/a.html" not in details,
                f"replaced path still shown: {details}")
    assert_true(details.count(moved_owner) >= 2,
                f"the owner permission should move to {moved_owner}: {details}")
    assert_true(old_owner not in details,
                f"the old owner {old_owner} is still in the details: {details}")

    logger.info("Tag update test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
