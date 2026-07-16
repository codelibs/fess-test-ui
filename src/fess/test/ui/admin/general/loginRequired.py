"""The "login required" checkbox (loginRequired) on /admin/general/ closes the
public search UI to anonymous visitors.

This module runs LAST in the general composer, because leaving loginRequired on
would send every later module to the login screen. Its restore path is the most
important code here: the finally block re-checks the setting and, if the admin
session was somehow lost, logs back in before restoring.

Effect is observed with anonymous HTTP GETs rather than by logging the browser
out. Two reasons: the suite shares one logged-in session across every module,
and the previous version of this test clicked logout before asserting, so any
failure after that point left loginRequired switched on with no way back.

The admin's own session is NOT affected by this setting. isLoginRequired() is
`fessConfig.isLoginRequired() && !getSavedUserBean().isPresent()`, so an
authenticated user short-circuits to false, and /admin/* is gated by @Secured
independently. The re-login in the restore path is therefore a safety net, not
the expected flow.

An anonymous GET / with loginRequired=true redirects twice — to /sso/ and then,
with the default ssoType=none, on to /login/. The assertion is on the final
landing URL so it does not depend on which SSO type is configured.
"""
import logging

import requests

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
TOP_PATH = "/"
FIELD = "#loginRequired"
# Selected by element name, not label: a second submit button (name="sendmail")
# lives on this page and `has-text` matches substrings.
SAVE_BUTTON = 'button[name="update"]'

HTTP_TIMEOUT = 15


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

    A silent failure here locks every later module out of the suite, so the
    restored value is read back and a mismatch is escalated rather than logged
    at debug level.
    """
    _set_login_required(context, page, original)
    _open_general(context, page)
    restored = page.is_checked(FIELD)
    if restored != original:
        logger.error(
            f"loginRequired NOT restored (wanted {original}, got {restored}); "
            f"later modules may be locked out of Fess")
    else:
        logger.info(f"loginRequired restored to {original}")


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
        assert_equal(page.url, context.url(GENERAL_PATH),
                     f"save did not redirect back to {GENERAL_PATH}; landed on {page.url}")

        required = requests.get(context.url(TOP_PATH), timeout=HTTP_TIMEOUT)
        assert_true("/login" in required.url,
                    f"loginRequired=true but an anonymous GET {TOP_PATH} ended at "
                    f"{required.url} instead of the login page")

        _set_login_required(context, page, False)

        public = requests.get(context.url(TOP_PATH), timeout=HTTP_TIMEOUT)
        assert_equal(public.status_code, 200,
                     f"loginRequired=false but an anonymous GET {TOP_PATH} "
                     f"answered HTTP {public.status_code}")
        assert_true("/login" not in public.url,
                    f"loginRequired=false but an anonymous GET {TOP_PATH} was "
                    f"still redirected to {public.url}")
    finally:
        try:
            _restore(context, page, original)
        except Exception as e:
            logger.error(f"loginRequired restore failed: {e}")

    logger.info("loginRequired test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
