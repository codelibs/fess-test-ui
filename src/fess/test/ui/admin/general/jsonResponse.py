"""The "JSON response" checkbox (webApiJson) on /admin/general/ gates the JSON
web API.

It no longer has anything to do with /json: JsonApiManager is gone from Fess.
The only consumer left is SearchApiV2Manager, which registers the /api/v2
prefix and returns false from matches() when isWebApiJson() is false. With no
manager matching and no LastaFlute action mapped under /api/v2, the request
falls through to a 404. So the observable effect of this checkbox today is
exactly: /api/v2/* answers, or it 404s.

Since fess#3460 that 404 is answered in place, at the requested URL, with the
real status: there is no error/redirect.jsp hop to an /error/notfound/ page
served as 200 any more. An /api/ path gets a plain-text "Not Found." rather
than the theme's HTML error view, so status, content type and body are all
asserted.

The request goes through page.request so it carries the logged-in session
cookie. That keeps the checkbox as the only variable under test — an anonymous
call could differ for authentication reasons that have nothing to do with
webApiJson.
"""
import logging

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup

from ._saved import assert_saved
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
FIELD = "#webApiJson"
# Selected by element name, not label: a second submit button (name="sendmail")
# lives on this page and `has-text` matches substrings.
SAVE_BUTTON = 'button[name="update"]'

API_PATH = "/api/v2/search?q=fess"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _save(page) -> None:
    page.click(SAVE_BUTTON)
    page.wait_for_load_state("domcontentloaded")


def _set_web_api_json(context: FessContext, page, enabled: bool) -> None:
    """Set the checkbox and save, always via a real page load + button click.

    updateConfig() rebuilds ~60 settings from whatever the submitted form
    carries, so a hand-built POST would blank every field not included (and
    verifyToken() would reject it anyway). Re-rendering the page first keeps
    every other setting at its current value.
    """
    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")
    page.set_checked(FIELD, enabled)
    _save(page)


def run(context: FessContext) -> None:
    logger.info("Starting jsonResponse (webApiJson) test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    # Checkboxes carry no hidden companion input: unchecked simply means the
    # parameter is absent, which isCheckboxEnabled() reads as false. input_value
    # is meaningless here, so the original state is read with is_checked().
    original = page.is_checked(FIELD)
    logger.debug(f"original webApiJson: {original}")

    try:
        _set_web_api_json(context, page, False)
        assert_saved(page)

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.is_checked(FIELD), False,
                     "webApiJson checkbox did not stay unchecked after save")

        disabled_response = page.request.get(context.url(API_PATH))
        # Status, URL, type and body together: the status alone would also
        # match an HTML error page, and the URL alone a 200 that answered.
        assert_equal(disabled_response.status, 404,
                     f"webApiJson=false should leave {API_PATH} unrouted (404), "
                     f"got HTTP {disabled_response.status}")
        assert_contains(disabled_response.url, API_PATH,
                        f"the 404 should be answered in place at {API_PATH}, but "
                        f"the request ended at {disabled_response.url}")
        disabled_type = disabled_response.headers.get("content-type", "")
        assert_contains(disabled_type, "text/plain",
                        f"the {API_PATH} 404 should be plain text; content-type "
                        f"was {disabled_type!r}")
        assert_equal(disabled_response.text().strip(), "Not Found.",
                     f"unexpected body for the {API_PATH} 404")

        _set_web_api_json(context, page, True)

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.is_checked(FIELD), True,
                     "webApiJson checkbox did not stay checked after save")

        enabled_response = page.request.get(context.url(API_PATH))
        assert_equal(enabled_response.status, 200,
                     f"webApiJson=true should let {API_PATH} answer, got "
                     f"HTTP {enabled_response.status}")
        assert_contains(enabled_response.url, "/api/v2/search",
                        f"webApiJson=true should leave {API_PATH} routed, but the "
                        f"request ended at {enabled_response.url} "
                        f"(HTTP {enabled_response.status})")
        content_type = enabled_response.headers.get("content-type", "")
        assert_contains(content_type, "application/json",
                        f"{API_PATH} should answer JSON; content-type was {content_type!r}")
        # The v2 envelope nests the payload under a top-level "response" key.
        assert_contains(enabled_response.json(), "response",
                        "v2 search response is missing its top-level 'response' key")
    finally:
        # assert_saved, not just the click: a rejected save raises nothing --
        # the page simply re-renders with ul.has-error -- so without it the
        # log below would claim a restore that never happened.
        cleanup = Cleanup()
        with cleanup.guard(f"webApiJson not restored to {original}"):
            _set_web_api_json(context, page, original)
            assert_saved(page)
            logger.info(f"webApiJson restored to {original}")
        cleanup.escalate()

    logger.info("jsonResponse (webApiJson) test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
