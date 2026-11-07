"""Archives the theme upload must refuse, and that refusing leaves nothing
behind.

A refused upload re-renders the upload page with the reason; the theme list
must be exactly what it was. The built-in theme in particular cannot be
replaced by an upload that reuses its name.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal
from fess.test.i18n import tm
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext
from fess.test.ui.admin.theme import _ui
from fess.test.ui.admin.theme._zip import theme_zip

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting theme/rejection")
    page = context.get_admin_page()
    before = _ui.installed_names(page, context)
    assert_contains(before, _ui.BUILT_IN, "the built-in theme is listed")

    name = "e2e" + context.generate_str(8).lower()
    marker = f"marker-{name}"

    # 1. Not a ZIP by its name. The reason names the file.
    _ui.upload(page, context, f"{name}.txt", theme_zip(name, marker))
    _ui.assert_on_upload_page(page, "a file that is not a .zip")
    assert_contains(page.inner_text("body"), f"{name}.txt",
                    "the refusal names the file")

    # 2. A ZIP without theme.yml.
    _ui.upload(page, context, f"{name}.zip", theme_zip(name, marker, with_manifest=False))
    _ui.assert_on_upload_page(page, "a ZIP without theme.yml")

    # 3. A manifest whose name is not a valid theme name.
    bad_name = "Not A Valid Name"
    _ui.upload(page, context, f"{name}.zip", theme_zip(bad_name, marker))
    _ui.assert_on_upload_page(page, "a manifest with an invalid name")
    assert_contains(page.inner_text("body"), tm(Messages.ERRORS_THEME_MANIFEST_INVALID_NAME),
                    "the invalid name is reported")

    # 4. A manifest that takes the built-in theme's name.
    _ui.upload(page, context, f"{name}.zip", theme_zip(_ui.BUILT_IN, marker))
    _ui.assert_on_upload_page(page, "a ZIP that reuses the built-in theme's name")
    assert_contains(page.inner_text("body"),
                    tm(Messages.ERRORS_THEME_IS_BUILTIN, _ui.BUILT_IN),
                    "replacing the built-in theme is refused by name")

    # None of the four installed anything.
    assert_equal(_ui.installed_names(page, context), before,
                 "the theme list after four refused uploads")
    logger.info("theme/rejection completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
