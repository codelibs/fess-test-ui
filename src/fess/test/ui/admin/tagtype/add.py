import logging

from fess.test import assert_equal, assert_true, assert_startswith
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.admin.tagtype._names import (DETAILS_PATH, LIST_PATH,
                                               open_list, owner, tag_name)
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

PATHS = ["https://example.com/tag/a.html", "https://example.com/tag/b.html"]
VIRTUAL_HOST = "tag.example.com"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting tag add test")

    page: "Page" = context.get_admin_page()
    name: str = tag_name(context)
    tag_owner: str = owner(context)
    logger.debug(f"Generated test tag: {name} owned by {tag_owner}")

    # Step 1: Navigate to the tag page
    logger.info("Step 1: Navigating to tag page")
    open_list(context, page)
    assert_equal(page.url, context.url(LIST_PATH))

    # Step 2: Open create form
    logger.info("Step 2: Opening create form")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    assert_equal(page.url, context.url(LIST_PATH + "createnew/"))

    # Step 3: Fill form fields. permissions is left blank on purpose: the
    # action then grants the tag to its owner only.
    logger.info("Step 3: Filling form fields")
    page.fill("input[name=\"name\"]", name)
    page.fill("input[name=\"owner\"]", tag_owner)
    page.fill("textarea[name=\"paths\"]", "\n".join(PATHS))
    page.fill("input[name=\"virtualHost\"]", VIRTUAL_HOST)
    page.fill("input[name=\"sortOrder\"]", "1")

    # Step 4: Submit form
    logger.info("Step 4: Submitting form")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url(LIST_PATH))
    # The list URL is also where a rejected create re-renders the form.
    assert_equal(page.locator("ul.has-error").count(), 0,
                 "create was rejected by validation")

    # Step 5: Verify the tag in the list, with its owner in the same row
    logger.info("Step 5: Verifying tag in list")
    row = page.locator(f'table tr:has-text("{name}")')
    assert_equal(row.count(), 1, f"{name} is not listed exactly once")
    row_text: str = row.inner_text()
    assert_true(tag_owner in row_text,
                f"owner {tag_owner} not in the row of {name}: {row_text}")

    # Step 6: Verify the details page
    logger.info("Step 6: Verifying tag details")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    assert_startswith(page.url, context.url(DETAILS_PATH))

    assert_equal(page.input_value("input[name=\"name\"]"), name)
    assert_equal(page.input_value("input[name=\"owner\"]"), tag_owner)
    assert_equal(page.input_value("input[name=\"virtualHost\"]"), VIRTUAL_HOST)
    assert_equal(page.input_value("input[name=\"sortOrder\"]"), "1")

    details: str = page.inner_text("section.content table")
    for path in PATHS:
        assert_true(path in details, f"path {path} not shown in details: {details}")
    # Once in the owner row and once more in the defaulted permission.
    assert_true(details.count(tag_owner) >= 2,
                f"blank permissions should default to the owner {tag_owner}: {details}")

    logger.info("Tag add test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
