"""The "login link" checkbox (loginLink) on /admin/general/ controls whether the
search top page offers a link to the login page.

FessSearchAction registers pageLoginLink unconditionally; index.jsp does the
real gating in a <c:choose>, where the logged-in user dropdown is an earlier
<c:when>. The link is therefore only reachable when nobody is logged in, which
is why the effect is observed with an anonymous HTTP GET rather than in the
browser: the suite shares one logged-in session across every module, and
logging out to look at the top page is what made the previous version of this
test leave settings behind when it failed.

The anchor is emitted by <la:link href="/login">, and LastaFlute's link tag
appends a trailing slash to a resolved action path, so the rendered href is
"/login/" — a matcher for "/login" without the slash would never fire.
"""
import logging
import re

import requests

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

HTTP_TIMEOUT = 15

# <a ... href="/login/" ...> — tolerant of a servlet context path prefix.
LOGIN_ANCHOR = re.compile(r'<a[^>]*\shref="[^"]*/login/"', re.IGNORECASE)


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


def _anonymous_top(context: FessContext) -> str:
    """Fetch the search top page with no session cookie, and return its HTML."""
    response = requests.get(context.url(TOP_PATH), timeout=HTTP_TIMEOUT)
    assert_equal(response.status_code, 200,
                 f"anonymous GET {TOP_PATH} should render the top page, "
                 f"got HTTP {response.status_code}")
    # loginRequired would bounce an anonymous caller to the login page, and the
    # login page has no login link either way — that would make the assertions
    # below meaningless rather than failing honestly.
    assert_true("/login" not in response.url,
                f"anonymous GET {TOP_PATH} was redirected to {response.url}; "
                f"loginRequired must be off for this test to observe anything")
    return response.text


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
        enabled_body = _anonymous_top(context)
        assert_true(LOGIN_ANCHOR.search(enabled_body),
                    "loginLink=true but the anonymous top page carries no anchor to /login/")

        _set_login_link(context, page, False)
        disabled_body = _anonymous_top(context)
        assert_equal(len(LOGIN_ANCHOR.findall(disabled_body)), 0,
                     "loginLink=false but the anonymous top page still carries an anchor to /login/")
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
