"""Install a theme by upload, make it the default, and take it away again.

The part nothing else checks is the effect on visitors: once a theme is the
default, an anonymous visitor's / is that theme's index.html, and once the
default is cleared it is the built-in theme again. The sequence:

1. Upload a minimal theme ZIP; it is listed and has a details page.
2. Make it the default; an anonymous visitor's / carries the theme's marker.
3. While it is the default its row offers no Delete (as the built-in theme's never does).
4. Clear the default; / no longer carries the marker.
5. Delete it; it is gone from the list.

The default theme the instance had before is put back, and the uploaded
theme deleted, even when an assertion fails half-way.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.i18n import tm
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext
from fess.test.ui.admin.theme import _ui
from fess.test.ui.admin.theme._zip import theme_zip
from fess.test.ui.cleanup import Cleanup

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _home_html(context: FessContext) -> str:
    """The body an anonymous visitor gets for /."""
    with context.guest_page() as visitor:
        response = visitor.goto(context.url("/"))
        assert_true(response is not None and response.ok,
                    f"/ answered {response.status if response else 'nothing'}")
        return response.text()


def run(context: FessContext) -> None:
    logger.info("Starting theme/lifecycle")
    page = context.get_admin_page()
    name = "e2e" + context.generate_str(8).lower()
    marker = f"marker-{name}"
    original_default = _ui.default_theme(page, context)
    installed = False

    try:
        logger.info("Step 1: upload")
        _ui.upload(page, context, f"{name}.zip", theme_zip(name, marker))
        installed = True
        assert_equal(page.url, context.url(_ui.LIST_PATH), "after a successful upload")
        assert_contains(page.inner_text("body"), tm(Messages.SUCCESS_UPLOAD_THEME, f"{name}.zip"),
                        "the upload is confirmed")
        assert_contains(_ui.installed_names(page, context), name, "the uploaded theme is listed")
        page.click(f'a[href*="details"]:text-is("{name}")')
        page.wait_for_load_state("domcontentloaded")
        assert_contains(page.inner_text("body"), "E2E Theme", "the details page shows the manifest")

        logger.info("Step 2: make it the default")
        assert_true(marker not in _home_html(context), "the marker is not served before the theme is the default")
        _ui.set_default(page, context, name)
        assert_contains(page.inner_text("body"), tm(Messages.SUCCESS_CHANGE_DEFAULT_THEME, name),
                        "the change is confirmed")
        assert_equal(_ui.default_theme(page, context), name, "the Default Theme select after Set")
        assert_contains(_home_html(context), marker, "an anonymous visitor's / is the new default theme")

        logger.info("Step 3: the default theme offers no Delete")
        assert_true(not _ui.can_delete(page, context, name),
                    "the default theme's row has a Delete button")
        assert_contains(_ui.installed_names(page, context), name, "the default theme stays installed")

        logger.info("Step 4: clear the default")
        _ui.set_default(page, context, "")
        assert_contains(page.inner_text("body"), tm(Messages.SUCCESS_CLEAR_DEFAULT_THEME),
                        "clearing the default is confirmed")
        assert_true(marker not in _home_html(context), "the marker is gone once the default is cleared")

        logger.info("Step 5: delete")
        assert_true(_ui.can_delete(page, context, name), "the theme has a Delete button once it is no longer the default")
        _ui.delete(page, context, name)
        assert_contains(page.inner_text("body"), tm(Messages.SUCCESS_DELETE_THEME, name),
                        "the delete is confirmed")
        installed = False
        assert_true(name not in _ui.installed_names(page, context), "the deleted theme is gone from the list")
    finally:
        cleanup = Cleanup()
        with cleanup.guard(f"default theme (was {original_default!r})"):
            if _ui.default_theme(page, context) != original_default:
                _ui.set_default(page, context, original_default)
            assert_equal(_ui.default_theme(page, context), original_default, "the default theme restored")
        if installed:
            with cleanup.guard(f"theme '{name}'"):
                _ui.delete(page, context, name)
                assert_true(name not in _ui.installed_names(page, context), "the uploaded theme deleted")
        cleanup.escalate()

    logger.info("theme/lifecycle completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
