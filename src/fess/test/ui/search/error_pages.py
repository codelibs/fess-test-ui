"""Verify the four error views render, and pin the routing of the paths that
error/redirect.jsp actually sends users to.

Fess maps errors to views in two hops: web.xml points the container's error
pages at error/redirect.jsp, which sendRedirect()s to an /error/* action by
`type`. Two of those redirect targets do not resolve to any action (see
_assert_badrequest_falls_through_to_notfound below); this module encodes
where users land TODAY so that fixing the mismatch is a deliberate, visible
change rather than a silent one.

No HTTP status is asserted anywhere here: web.xml maps 404 to redirect.jsp,
which sendRedirect()s to a page served as 200, so a redirect-following
client never observes the 404. The landing URL is the observable.

The error actions extend FessSearchAction but never call isLoginRequired(),
so all four stay reachable even when the UI is closed to anonymous users.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

NOTFOUND_PATH = "/error/notfound/"

# path -> label whose text only that view renders. Note the action class is
# ErrorBadrequrestAction (sic), so /error/badrequrest/ is the real URL.
ERROR_VIEWS = (
    (NOTFOUND_PATH, Labels.PAGE_NOT_FOUND_TITLE),
    ("/error/systemerror/", Labels.SYSTEM_ERROR_TITLE),
    ("/error/busy/", Labels.BUSY_TITLE),
    ("/error/badrequrest/", Labels.REQUEST_ERROR_TITLE),
)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _goto(page, context: FessContext, path: str) -> None:
    page.goto(context.url(path))
    page.wait_for_load_state("domcontentloaded")


def _assert_view_renders(page, context: FessContext, path: str, key: str) -> None:
    """The view is served at its own path and renders its own text."""
    _goto(page, context, path)

    # Not a tautology: an /error/* path with no action behind it redirects to
    # /error/notfound/ instead, which is exactly what /error/badrequest/ does
    # below. This assertion is what tells the two cases apart.
    assert_equal(urlparse(page.url).path, path,
                 f"{path} did not serve itself; landed on {page.url}")

    marker = t(key)
    _assert_contains_marker(page, marker, path)


def _assert_contains_marker(page, marker: str, path: str) -> None:
    body = page.inner_text("body")
    assert_true(marker in body,
                f"{path} did not render its own text {marker!r}")


def _assert_lands_on_notfound(page, context: FessContext, requested: str) -> None:
    """`requested` resolves to no action, so the 404 handler lands us on the
    Not Found view with the original path echoed in ?url=."""
    _goto(page, context, requested)

    landed = urlparse(page.url)
    assert_equal(landed.path, NOTFOUND_PATH,
                 f"expected {requested} to land on {NOTFOUND_PATH}, got {page.url}")
    # redirect.jsp:31-33 URL-encodes the original request URI into ?url=.
    # parse_qs does the decoding, not Playwright: page.url hands back the
    # percent-encoded form (%2F stays %2F), and parse_qs is what turns it back
    # into the original path. Do not "simplify" this into a substring test on
    # page.url -- that would be testing the encoded form by accident.
    assert_equal(parse_qs(landed.query).get("url"), [requested],
                 f"expected ?url={requested} after landing, got {page.url}")
    _assert_contains_marker(page, t(Labels.PAGE_NOT_FOUND_TITLE), page.url)


def _assert_badrequest_falls_through_to_notfound(page, context: FessContext) -> None:
    """error/redirect.jsp:19 sends the badRequest branch to /error/badrequest/,
    but the action class is ErrorBad*requrest*Action, so the real URL is
    /error/badrequrest/ and /error/badrequest/ resolves to nothing.

    The consequence is a real Fess bug: a genuine HTTP 400 takes the
    badRequest branch and the user is shown the 404 page instead of the 400
    page. This asserts today's behaviour, not the intended behaviour, so that
    correcting the typo shows up here rather than passing unnoticed.
    """
    _assert_lands_on_notfound(page, context, "/error/badrequest/")


def _assert_error_system_falls_through_to_notfound(page, context: FessContext) -> None:
    """error/redirect.jsp:28 sends the badAuth branch to /error/system, but no
    ErrorSystemAction exists (the view is served by /error/systemerror/), so
    that path resolves to nothing either. Same reasoning as above."""
    _goto(page, context, "/error/system?message_key=errors.bad_authentication")
    assert_equal(urlparse(page.url).path, NOTFOUND_PATH,
                 f"expected /error/system to land on {NOTFOUND_PATH}, got {page.url}")


def _assert_unknown_path_lands_on_notfound(page, context: FessContext) -> None:
    """A genuinely unrouted URL exercises the real container 404 -> redirect.jsp
    -> /error/notfound/ chain, rather than a hand-written /error/* path."""
    _assert_lands_on_notfound(page, context,
                              f"/no-such-page-{context.generate_str(12)}")


def run(context: FessContext) -> None:
    logger.info("Starting search/error_pages")
    page = context.get_wrapped_page() or context.get_admin_page()

    for path, key in ERROR_VIEWS:
        _assert_view_renders(page, context, path, key)

    _assert_badrequest_falls_through_to_notfound(page, context)
    _assert_error_system_falls_through_to_notfound(page, context)
    _assert_unknown_path_lands_on_notfound(page, context)

    logger.info("search/error_pages completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        ctx = setup(playwright)
        try:
            run(ctx)
        finally:
            destroy(ctx)
