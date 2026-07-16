"""The "JSON response" checkbox (webApiJson) on /admin/general/ gates the JSON
web API.

It no longer has anything to do with /json: JsonApiManager is gone from Fess.
The only consumer left is SearchApiV2Manager, which registers the /api/v2
prefix and returns false from matches() when isWebApiJson() is false. With no
manager matching and no LastaFlute action mapped under /api/v2, the request
falls through to a 404. So the observable effect of this checkbox today is
exactly: /api/v2/* answers, or it 404s.

The request goes through page.request so it carries the logged-in session
cookie. That keeps the checkbox as the only variable under test — an anonymous
call could differ for authentication reasons that have nothing to do with
webApiJson.
"""
import logging

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext

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
        # The unrouted path does 404 internally, but web.xml maps 404 to
        # error/redirect.jsp, which sendRedirect()s to /error/notfound/ — an
        # HTML page served as 200. So the wire never shows a 404 status to a
        # redirect-following client; landing on the not-found page is the
        # observable signal that the API is gated off.
        assert_contains(disabled_response.url, "/error/notfound/",
                        f"webApiJson=false should leave {API_PATH} unrouted and land on "
                        f"the not-found page, but the request ended at "
                        f"{disabled_response.url} (HTTP {disabled_response.status})")

        _set_web_api_json(context, page, True)

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.is_checked(FIELD), True,
                     "webApiJson checkbox did not stay checked after save")

        enabled_response = page.request.get(context.url(API_PATH))
        # Assert the landing URL, not the status: the not-found page is itself
        # served as 200 (see the disabled case above), so a status check would
        # pass even if the API were still gated off. Staying on the API path is
        # what distinguishes "answered" from "laundered into /error/notfound/".
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
        try:
            _set_web_api_json(context, page, original)
            logger.info(f"webApiJson restored to {original}")
        except Exception as e:
            logger.warning(f"webApiJson restore failed (continuing): {e}")

    logger.info("jsonResponse (webApiJson) test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
