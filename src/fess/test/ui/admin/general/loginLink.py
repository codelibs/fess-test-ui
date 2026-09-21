"""The "login link" checkbox (loginLink) on /admin/general/ controls whether the
search top page offers a link to the login page.

Since fess#3460 the top page is the bootstrap static-theme SPA. It learns the
setting from /api/v2/ui/config (features.login_link: true/false, or "sso/"
when SSO is served), and auth.js renders a#login-btn into #auth-controls only
for a guest and only when the flag is on. Nothing of that is in the HTML the
server sends, so the effect is observed in a real guest page -- a separate
browser context with none of the suite's cookies (FessContext.guest_page) --
rather than by logging the shared admin session out, which is what made an
older version of this test leave settings behind when it failed.

app.js shows #home-view only after auth.js has rendered the header, so once
the home view is visible the link's absence is a result, not a race.
"""
import logging
from urllib.parse import urlparse

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup

from ._saved import assert_saved
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
TOP_PATH = "/"
FIELD = "#loginLink"
# Selected by element name, not label: a second submit button (name="sendmail")
# lives on this page and `has-text` matches substrings.
SAVE_BUTTON = 'button[name="update"]'

LOGIN_LINK = "#auth-controls a#login-btn"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _set_login_link(context: FessContext, page, enabled: bool) -> None:
    """Set the checkbox and save via a real page load + button click.

    updateConfig() rebuilds ~60 settings from the submitted form, so the page
    must be re-rendered first or every untouched field would be blanked; a
    hand-built POST would also be rejected by verifyToken().
    """
    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")
    page.set_checked(FIELD, enabled)
    page.click(SAVE_BUTTON)
    page.wait_for_load_state("domcontentloaded")


def _guest_view(context: FessContext, enabled: bool) -> None:
    """Open the top page as a guest and check the login link matches `enabled`."""
    with context.guest_page() as guest:
        with guest.expect_response(lambda r: "/api/v2/ui/config" in r.url) as info:
            guest.goto(context.url(TOP_PATH))
        flag = info.value.json()["response"]["features"]["login_link"]
        assert_equal(flag, enabled,
                     f"loginLink={enabled} but /api/v2/ui/config reports "
                     f"features.login_link={flag!r}")
        # Visible only once auth.js has rendered the header (see docstring);
        # with loginRequired on it would stay hidden behind the login modal.
        guest.wait_for_selector("#home-view:not([hidden])")

        link = guest.query_selector(LOGIN_LINK)
        if not enabled:
            assert_true(link is None,
                        "loginLink=false but the guest top page still shows "
                        f"{LOGIN_LINK}")
            return
        assert_true(link is not None and link.is_visible(),
                    f"loginLink=true but the guest top page shows no {LOGIN_LINK}")
        path = urlparse(link.evaluate("a => a.href")).path
        assert_equal(path, "/login",
                     f"the login link resolves to {path}, expected /login")
        # Without SSO the link opens the SPA's login modal.
        link.click()
        guest.wait_for_selector("#login-modal.show #login-form")


def run(context: FessContext) -> None:
    logger.info("Starting loginLink test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    # Checkboxes have no hidden companion input, so is_checked() (not
    # input_value()) is how the original state is read.
    original = page.is_checked(FIELD)
    logger.debug(f"original loginLink: {original}")

    try:
        _set_login_link(context, page, True)
        assert_saved(page)
        _guest_view(context, True)

        _set_login_link(context, page, False)
        assert_saved(page)
        _guest_view(context, False)
    finally:
        # assert_saved, not just the click: a rejected save raises nothing --
        # the page simply re-renders with ul.has-error -- so without it the
        # log below would claim a restore that never happened.
        cleanup = Cleanup()
        with cleanup.guard(f"loginLink not restored to {original}"):
            _set_login_link(context, page, original)
            assert_saved(page)
            logger.info(f"loginLink restored to {original}")
        cleanup.escalate()

    logger.info("loginLink test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
