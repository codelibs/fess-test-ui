"""The "login required" checkbox (loginRequired) on /admin/general/ closes the
public search UI to anonymous visitors.

This module runs LAST in the general composer, because leaving loginRequired on
would send every later module to the login screen. Its restore path is the most
important code here: the finally block re-checks the setting and, if the admin
session was somehow lost, logs back in before restoring.

Effect is observed in a guest page -- a separate browser context with none of
the suite's cookies (FessContext.guest_page) -- rather than by logging the
browser out. Two reasons: the suite shares one logged-in session across every
module, and an older version of this test clicked logout before asserting, so
any failure after that point left loginRequired switched on with no way back.

The admin's own session is NOT affected by this setting. isLoginRequired() is
`fessConfig.isLoginRequired() && !getSavedUserBean().isPresent()`, so an
authenticated user short-circuits to false, and /admin/* is gated by @Secured
independently. The re-login in the restore path is therefore a safety net, not
the expected flow.

Since fess#3460 (and #3459) the top page is the bootstrap static-theme SPA and
the server no longer redirects a guest: / answers the SPA, /api/v2/ui/config
reports login_required, and app.js keeps the page behind a login modal that
cannot be closed (its close controls are hidden and hide.bs.modal is
prevented), or goes to sso/ when SSO is served. The suite runs without SSO,
so the modal is what is asserted.
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
FIELD = "#loginRequired"
# Selected by element name, not label: a second submit button (name="sendmail")
# lives on this page and `has-text` matches substrings.
SAVE_BUTTON = 'button[name="update"]'

LOGIN_MODAL = "#login-modal.show"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _open_general(context: FessContext, page) -> None:
    """Open /admin/general/, logging back in first if the session is gone."""
    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")
    if GENERAL_PATH not in page.url:
        logger.warning(f"admin session lost (landed on {page.url}); logging in again")
        context.login()
        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")


def _set_login_required(context: FessContext, page, enabled: bool) -> None:
    """Set the checkbox and save via a real page load + button click.

    updateConfig() rebuilds ~60 settings from the submitted form, so the page
    must be re-rendered first or every untouched field would be blanked; a
    hand-built POST would also be rejected by verifyToken().
    """
    _open_general(context, page)
    page.set_checked(FIELD, enabled)
    page.click(SAVE_BUTTON)
    page.wait_for_load_state("domcontentloaded")


def _restore(context: FessContext, page, original: bool) -> None:
    """Put loginRequired back and confirm it actually went back.

    A failure here locks every later module out of the suite, so the restored
    value is read back and a mismatch is raised, not logged: this is the leak
    with the largest blast radius in the suite, and a log alone would surface
    it as a wall of unrelated login-screen failures in other modules.
    """
    _set_login_required(context, page, original)
    _open_general(context, page)
    restored = page.is_checked(FIELD)
    assert_equal(restored, original,
                 f"loginRequired NOT restored (wanted {original}, got "
                 f"{restored}); every later module would be locked out of Fess")
    logger.info(f"loginRequired restored to {original}")


def _guest_view(context: FessContext, required: bool) -> None:
    """Open the top page as a guest and check it is gated iff `required`."""
    with context.guest_page() as guest:
        with guest.expect_response(lambda r: "/api/v2/ui/config" in r.url) as info:
            guest.goto(context.url(TOP_PATH))
        reported = info.value.json()["response"]["login_required"]
        assert_equal(reported, required,
                     f"loginRequired={required} but /api/v2/ui/config reports "
                     f"login_required={reported!r}")

        if not required:
            # Public access restored: the home view renders and no login
            # prompt stands in front of it.
            guest.wait_for_selector("#home-view:not([hidden])")
            assert_true(guest.query_selector(LOGIN_MODAL) is None,
                        "loginRequired=false but the guest is still asked to log in")
            return

        guest.wait_for_selector(f"{LOGIN_MODAL} #login-form")
        assert_equal(urlparse(guest.url).path, TOP_PATH,
                     f"the guest should be asked to log in at {TOP_PATH}, not "
                     f"sent to {guest.url}")
        closers = guest.query_selector_all('#login-modal [data-bs-dismiss="modal"]')
        assert_true(closers and all(not c.is_visible() for c in closers),
                    "loginRequired=true but the login modal can be closed")
        # Escape (and a backdrop click) would close an ordinary modal.
        guest.keyboard.press("Escape")
        guest.wait_for_timeout(500)
        assert_true(guest.is_visible(LOGIN_MODAL),
                    "the required login modal closed on Escape")
        assert_true(guest.is_hidden("#home-view"),
                    "loginRequired=true but the guest can see the home view")


def run(context: FessContext) -> None:
    logger.info("Starting loginRequired test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    # Checkboxes have no hidden companion input, so is_checked() (not
    # input_value()) is how the original state is read.
    original = page.is_checked(FIELD)
    logger.debug(f"original loginRequired: {original}")

    try:
        _set_login_required(context, page, True)
        assert_saved(page)

        _guest_view(context, True)

        _set_login_required(context, page, False)
        assert_saved(page)
        _guest_view(context, False)
    finally:
        cleanup = Cleanup()
        with cleanup.guard("loginRequired possibly left ON — every later module "
                           "would be sent to the login screen"):
            _restore(context, page, original)
        cleanup.escalate()

    logger.info("loginRequired test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
