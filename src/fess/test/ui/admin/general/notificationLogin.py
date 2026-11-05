"""The "login page notification" textarea (notificationLogin) on
/admin/general/ sets a message shown on the login screen.

Since fess#3728 (15.10) the JSP login page (/login/) no longer renders it: the
theme fills it into the login modal from /api/v2/ui/config
(notifications.login). The config endpoint is therefore what is asserted here;
the 15.9 and earlier behaviour (a <div class="notification"> on /login/) lives
in notificationLogin_jsp.py and runs on those versions.

The config is fetched with an anonymous HTTP GET: the suite shares one
logged-in session across every module, and logging out to look at the login
screen is what made the previous version of this test leave settings behind
when it failed.

The test value is deliberately plain alphanumeric text so it round-trips
unchanged.
"""
import logging

import requests

from fess.test import assert_equal
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup
from fess.test.ui.version import (LOGIN_NOTIFICATION_IN_THEME_SINCE,
                                  run_jsp_variant)

from . import notificationLogin_jsp
from ._saved import assert_saved
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
CONFIG_PATH = "/api/v2/ui/config"
FIELD = "#notificationLogin"
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


def _notification_in_ui_config(context: FessContext) -> str:
    """Return notifications.login from the anonymous /api/v2/ui/config."""
    response = requests.get(context.url(CONFIG_PATH), timeout=HTTP_TIMEOUT)
    assert_equal(response.status_code, 200,
                 f"{CONFIG_PATH} answered HTTP {response.status_code}")
    return response.json()["response"]["notifications"]["login"].strip()


def run(context: FessContext) -> None:
    if run_jsp_variant(context, notificationLogin_jsp,
                       since=LOGIN_NOTIFICATION_IN_THEME_SINCE):
        return
    logger.info("Starting notificationLogin test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    original = page.input_value(FIELD)
    logger.debug(f"original notificationLogin length: {len(original)}")
    test_value = f"e2e-notification-login-{context.generate_str(12)}"

    try:
        _save(context, page, test_value)
        assert_saved(page)

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        persisted = page.input_value(FIELD)
        assert_equal(persisted, test_value,
                     f"notificationLogin textarea lost the saved value; got {persisted!r}")

        assert_equal(_notification_in_ui_config(context), test_value,
                     "saved notificationLogin text is not what notifications.login carries")
    finally:
        # assert_saved, not just the click: a rejected save raises nothing --
        # the page simply re-renders with ul.has-error -- so without it the
        # log below would claim a restore that never happened.
        cleanup = Cleanup()
        with cleanup.guard(f"notificationLogin not restored (left showing the "
                           f"test banner {test_value!r} on the login screen)"):
            _save(context, page, original)
            assert_saved(page)
            logger.info("notificationLogin restored")
        cleanup.escalate()

    logger.info("notificationLogin test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
