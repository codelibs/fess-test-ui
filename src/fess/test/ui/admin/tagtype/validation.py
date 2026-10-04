import logging

from fess.test import assert_equal, assert_true
from fess.test.i18n import t, tm
from fess.test.i18n.keys import Labels
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext
from fess.test.ui.admin.tagtype._names import LIST_PATH, open_list, owner, tag_name
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

# user.tag.name.max.length in the stock fess_config.properties; the {0} of
# errors.tagtype_invalid_name.
NAME_MAX_LENGTH = 50


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _field_errors(page, field: str):
    """The <la:errors property=field/> list rendered next to that input."""
    return page.locator(f'div:has(> #{field}) > ul.has-error')


def _submit_create(context: FessContext, page, name: str, tag_owner: str) -> None:
    page.goto(context.url(LIST_PATH + "createnew/"))
    page.wait_for_load_state("domcontentloaded")
    page.fill("input[name=\"name\"]", name)
    page.fill("input[name=\"owner\"]", tag_owner)
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")


def _assert_rejected_on(page, field: str, other: str, what: str) -> None:
    # A rejected create re-renders the form under the list URL, so the form
    # inputs still being there is what tells it from a successful redirect.
    assert_true(page.locator("input[name=\"owner\"]").count() > 0,
                f"{what}: the create form is gone, so it was accepted")
    assert_true(_field_errors(page, field).count() > 0,
                f"{what}: no error shown on {field}")
    assert_equal(_field_errors(page, other).count(), 0,
                 f"{what}: an error was shown on {other} too")


def run(context: FessContext) -> None:
    logger.info("Starting tag validation test")

    page: "Page" = context.get_admin_page()
    name: str = tag_name(context)
    tag_owner: str = owner(context)
    probe_owner: str = f"val{context.generate_str(12).lower()}"
    invalid_name_msg: str = tm(Messages.ERRORS_TAGTYPE_INVALID_NAME,
                               str(NAME_MAX_LENGTH))

    open_list(context, page)
    assert_equal(page.url, context.url(LIST_PATH))

    # Test 1: blank name (@Required)
    logger.info("Test 1: blank name")
    _submit_create(context, page, "", probe_owner)
    assert_equal(page.url, context.url(LIST_PATH))
    _assert_rejected_on(page, "name", "owner", "blank name")

    # Test 2: blank owner (@Required)
    logger.info("Test 2: blank owner")
    _submit_create(context, page, f"val{context.generate_str(12)}", "")
    _assert_rejected_on(page, "owner", "name", "blank owner")

    # Test 3: a name of ASCII spaces only. @Required trims, so it rejects
    # this before the tag-name check runs.
    logger.info("Test 3: whitespace-only name")
    _submit_create(context, page, "   ", probe_owner)
    _assert_rejected_on(page, "name", "owner", "whitespace-only name")

    # Test 4: a name of ideographic spaces only. String.trim() keeps
    # U+3000, so @Required passes and the tag-name normalization (NFKC folds
    # it to a space, then trims) is what rejects it, with its own message.
    logger.info("Test 4: ideographic-space-only name")
    _submit_create(context, page, "　　", probe_owner)
    _assert_rejected_on(page, "name", "owner", "ideographic-space-only name")
    errors: str = _field_errors(page, "name").inner_text()
    assert_true(invalid_name_msg in errors,
                f"expected '{invalid_name_msg}' on name, got '{errors}'")

    # Test 5: one character over user.tag.name.max.length. @Size(max=1000)
    # lets it through; the tag-name check refuses it.
    logger.info("Test 5: over-long name")
    _submit_create(context, page, context.generate_str(NAME_MAX_LENGTH + 1), probe_owner)
    _assert_rejected_on(page, "name", "owner", "over-long name")
    errors = _field_errors(page, "name").inner_text()
    assert_true(invalid_name_msg in errors,
                f"expected '{invalid_name_msg}' on name, got '{errors}'")

    # Test 6: the same name and owner as add.py's tag. The id is derived from
    # the pair, so this must be refused rather than overwrite that tag.
    logger.info("Test 6: duplicate name and owner")
    _submit_create(context, page, name, tag_owner)
    assert_true(page.locator("input[name=\"owner\"]").count() > 0,
                "duplicate tag was accepted")
    already_exists: str = tm(Messages.ERRORS_TAGTYPE_ALREADY_EXISTS)
    content: str = page.inner_text("section.content")
    assert_true(already_exists in content,
                f"expected '{already_exists}' for a duplicate, got '{content}'")

    # Nothing above was created: the list still holds add.py's tag once,
    # and no tag of the probe owner.
    page.goto(context.url(LIST_PATH))
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.locator(f'table tr:has-text("{name}")').count(), 1,
                 f"{name} is not listed exactly once after the duplicate create")
    listed: str = page.inner_text("section.content")
    assert_true(probe_owner not in listed,
                f"a rejected create left a tag of {probe_owner} behind: {listed}")

    logger.info("Tag validation test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
