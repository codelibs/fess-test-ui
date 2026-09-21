"""The "search top notification" textarea (notificationSearchTop) on
/admin/general/ sets a message rendered on the search top page.

Since fess#3460 the top page is the bootstrap static-theme SPA: the server's
HTML carries an empty <div class="notification" id="home-notification">, and
app.js fills it from /api/v2/ui/config (notifications.search_top) through
the theme's HTML sanitizer, hiding it with d-none when the setting is empty.
So both the config field and the rendered banner are asserted, in a guest
page (a separate browser context with none of the suite's cookies) so the
check observes what an ordinary visitor sees.

The test value is deliberately plain alphanumeric text so it round-trips
through the sanitizer unchanged.
"""
import logging

from fess.test import assert_equal
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup

from ._saved import assert_saved
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
TOP_PATH = "/"
FIELD = "#notificationSearchTop"
# Selected by element name, not label: a second submit button (name="sendmail")
# lives on this page and `has-text` matches substrings.
SAVE_BUTTON = 'button[name="update"]'

BANNER = "#home-view #home-notification"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _save(context: FessContext, page, value: str) -> None:
    """Fill the textarea and save via a real page load + button click.

    updateConfig() rebuilds ~60 settings from the submitted form, so the page
    must be re-rendered first or every untouched field would be blanked; a
    hand-built POST would also be rejected by verifyToken().
    """
    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")
    page.fill(FIELD, value)
    page.click(SAVE_BUTTON)
    page.wait_for_load_state("domcontentloaded")


def _notification_on_top_page(context: FessContext) -> str:
    """Return the banner text a guest sees on the top page, after checking
    that /api/v2/ui/config carries the same text."""
    with context.guest_page() as guest:
        with guest.expect_response(lambda r: "/api/v2/ui/config" in r.url) as info:
            guest.goto(context.url(TOP_PATH))
        configured = info.value.json()["response"]["notifications"]["search_top"]
        # Visible only when app.js filled it; loginRequired would keep the
        # home view hidden behind the login modal and time out here.
        banner = guest.wait_for_selector(f"{BANNER}:not(.d-none)")
        shown = banner.inner_text().strip()
    assert_equal(shown, configured.strip(),
                 "the top page banner differs from notifications.search_top "
                 "in /api/v2/ui/config")
    return shown


def run(context: FessContext) -> None:
    logger.info("Starting notificationSearchTop test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    original = page.input_value(FIELD)
    logger.debug(f"original notificationSearchTop length: {len(original)}")
    test_value = f"e2e-notification-searchtop-{context.generate_str(12)}"

    try:
        _save(context, page, test_value)
        assert_saved(page)

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        persisted = page.input_value(FIELD)
        assert_equal(persisted, test_value,
                     f"notificationSearchTop textarea lost the saved value; got {persisted!r}")

        assert_equal(_notification_on_top_page(context), test_value,
                     "saved notificationSearchTop text is not what the top page shows")
    finally:
        # assert_saved, not just the click: a rejected save raises nothing --
        # the page simply re-renders with ul.has-error -- so without it the
        # log below would claim a restore that never happened.
        cleanup = Cleanup()
        with cleanup.guard(f"notificationSearchTop not restored (left showing "
                           f"the test banner {test_value!r} on the top page)"):
            _save(context, page, original)
            assert_saved(page)
            logger.info("notificationSearchTop restored")
        cleanup.escalate()

    logger.info("notificationSearchTop test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
