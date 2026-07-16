"""The "search top notification" textarea (notificationSearchTop) on
/admin/general/ sets a message rendered on the search top page.

RootAction registers it as "notification" and index.jsp emits
<div class="notification">${notification}</div>. That div is not wrapped in a
<c:if>, so it exists even when the setting is empty — the assertion has to be
about the text inside it, not about the element being present.

The top page is fetched with an anonymous HTTP GET so the check does not depend
on the shared logged-in session, and so it observes what an ordinary visitor
sees.

${notification} is written unescaped (it is not ${f:h(...)}), which is Fess's
documented behaviour and lets an administrator put markup in the banner. The
test value is deliberately plain alphanumeric text so it round-trips through
the JSP byte-for-byte.
"""
import logging
import re

import requests

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

from ._saved import assert_saved
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
TOP_PATH = "/"
FIELD = "#notificationSearchTop"
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


def _notification_on_top_page(context: FessContext) -> str:
    """Return the contents of div.notification on the anonymous top page."""
    response = requests.get(context.url(TOP_PATH), timeout=HTTP_TIMEOUT)
    assert_equal(response.status_code, 200,
                 f"anonymous GET {TOP_PATH} should render the top page, "
                 f"got HTTP {response.status_code}")
    # loginRequired would bounce an anonymous caller to the login page, whose
    # notification comes from a different setting entirely.
    assert_true("/login" not in response.url,
                f"anonymous GET {TOP_PATH} was redirected to {response.url}; "
                f"loginRequired must be off for this test to observe anything")
    match = re.search(r'<div class="notification">(.*?)</div>', response.text,
                      re.DOTALL)
    assert_true(match,
                "top page has no div.notification; index.jsp should always "
                "render it, empty or not")
    return match.group(1).strip()


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
        try:
            _save(context, page, original)
            logger.info("notificationSearchTop restored")
        except Exception as e:
            logger.warning(f"notificationSearchTop restore failed (continuing): {e}")

    logger.info("notificationSearchTop test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
