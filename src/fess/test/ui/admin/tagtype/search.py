import logging

from fess.test import assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.tagtype._names import LIST_PATH, open_list, owner, tag_name
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _search(page, name: str = "", tag_owner: str = "") -> None:
    """Fill the collapsed list search form and submit it."""
    form = page.locator("#listSearchForm")
    if not form.locator("#name").is_visible():
        page.click('a[href="#listSearchForm"]')
        form.locator("#name").wait_for(state="visible")
    form.locator("#name").fill(name)
    form.locator("#owner").fill(tag_owner)
    form.locator(f'button[name="search"]:has-text("{t(Labels.CRUD_BUTTON_SEARCH)}")').click()
    page.wait_for_load_state("domcontentloaded")


def _reset(page) -> None:
    """Clear the search conditions the pager keeps in the session."""
    form = page.locator("#listSearchForm")
    if not form.locator("#name").is_visible():
        page.click('a[href="#listSearchForm"]')
        form.locator("#name").wait_for(state="visible")
    form.locator(f'button[name="reset"]:has-text("{t(Labels.CRUD_BUTTON_RESET)}")').click()
    page.wait_for_load_state("domcontentloaded")


def _listed(page) -> str:
    return page.inner_text("section.content")


def run(context: FessContext) -> None:
    logger.info("Starting tag list/search test")

    page: "Page" = context.get_admin_page()
    name: str = tag_name(context)
    tag_owner: str = owner(context)
    no_match: str = f"none{context.generate_str(16)}"

    # Step 1: The unfiltered list shows the tag and both column headers
    logger.info("Step 1: Checking the list page")
    open_list(context, page)
    assert_equal(page.url, context.url(LIST_PATH))
    headers: str = page.inner_text("table thead")
    assert_true(t(Labels.TAGTYPE_NAME) in headers and t(Labels.TAGTYPE_OWNER) in headers,
                f"name/owner column headers missing: {headers}")
    assert_true(name in _listed(page), f"{name} not in the unfiltered list")

    try:
        # Step 2: Search by name finds the tag
        logger.info("Step 2: Searching by name")
        _search(page, name=name)
        assert_equal(page.locator(f'table tr:has-text("{name}")').count(), 1,
                     f"search by name did not list {name}")

        # Step 3: Search by owner finds the tag
        logger.info("Step 3: Searching by owner")
        _search(page, tag_owner=tag_owner)
        assert_equal(page.locator(f'table tr:has-text("{name}")').count(), 1,
                     f"search by owner {tag_owner} did not list {name}")

        # Step 4: A name that matches nothing empties the list
        logger.info("Step 4: Searching for a name that matches nothing")
        _search(page, name=no_match)
        listed: str = _listed(page)
        assert_true(name not in listed, f"{name} listed for search {no_match}")
        assert_true(t(Labels.LIST_COULD_NOT_FIND_CRUD_TABLE) in listed,
                    f"empty-list placeholder missing for search {no_match}: {listed}")

        # Step 5: The right name with the wrong owner matches nothing too:
        # the conditions are ANDed, not ORed.
        logger.info("Step 5: Searching by name with another owner")
        _search(page, name=name, tag_owner=no_match)
        assert_true(name not in _listed(page),
                    f"{name} listed although its owner is not {no_match}")
    finally:
        # Step 6: Reset brings the tag back and leaves no condition behind
        # for the leaves that follow.
        logger.info("Step 6: Resetting the search")
        _reset(page)

    assert_true(name in _listed(page), f"{name} not listed after reset")
    assert_equal(page.locator("#listSearchForm #name").input_value(), "",
                 "reset left the name condition in the form")

    logger.info("Tag list/search test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
