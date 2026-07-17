"""Verify the four error views render, and pin the routing of the paths that
error/redirect.jsp actually sends users to.

Fess maps errors to views in two hops: web.xml points the container's error
pages at error/redirect.jsp, which sendRedirect()s to an /error/* action by
`type`. Not every redirect target resolves to an action, and where a target
does not, the user silently lands on the Not Found view instead of the view
the branch names; this module pins where users actually land so that closing
one of those gaps is a deliberate, visible change rather than a silent one.

The suite runs against several Fess builds (README: 15.7.0 and snapshot), and
the request error view is served at a different path depending on the build --
/error/badrequrest/ on 15.7.0 and below, /error/badrequest/ on builds that
have renamed the action. No version flag is plumbed to the runner, so which
spelling is routed is detected at runtime and the assertion is the invariant
that holds on either build; see _assert_exactly_one_request_error_path_renders.

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

# path -> label whose text only that view renders. The request error view is
# not listed: its path is build-dependent, so it is resolved at runtime by
# _assert_exactly_one_request_error_path_renders rather than named here.
ERROR_VIEWS = (
    (NOTFOUND_PATH, Labels.PAGE_NOT_FOUND_TITLE),
    ("/error/systemerror/", Labels.SYSTEM_ERROR_TITLE),
    ("/error/busy/", Labels.BUSY_TITLE),
)

# The two spellings of the request error path, exactly one of which is routed.
# Order is irrelevant: the routed one is detected, never assumed.
REQUEST_ERROR_PATHS = ("/error/badrequest/", "/error/badrequrest/")


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
    # /error/notfound/ instead, which is exactly what the unrouted spelling of
    # the request error path does below. This assertion tells the cases apart.
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
    # redirect.jsp's fall-through branch URL-encodes the original request URI
    # into ?url=. parse_qs does the decoding, not Playwright: page.url returns the
    # percent-encoded form (%2F stays %2F), and parse_qs is what turns it back
    # into the original path. Do not "simplify" this into a substring test on
    # page.url -- that would be testing the encoded form by accident.
    assert_equal(parse_qs(landed.query).get("url"), [requested],
                 f"expected ?url={requested} after landing, got {page.url}")
    _assert_contains_marker(page, t(Labels.PAGE_NOT_FOUND_TITLE), page.url)


def _serves_itself(page, context: FessContext, path: str) -> bool:
    """True when an action is routed at `path`: a routed /error/* path stays put,
    while an unrouted one is redirected away to the Not Found view."""
    _goto(page, context, path)
    return urlparse(page.url).path == path


def _assert_exactly_one_request_error_path_renders(page, context: FessContext) -> None:
    """The request error view answers exactly one of REQUEST_ERROR_PATHS, and the
    other spelling falls through to Not Found.

    Which spelling is routed depends on the build, so it is detected rather than
    pinned -- the same reason FessContext.api_search probes for /api/v2 instead
    of reading a version flag:

      * Fess <= 15.7.0 names the action ErrorBad*requrest*Action (sic), so the
        view answers /error/badrequrest/ while error/redirect.jsp sends the
        badRequest branch to the correctly spelled /error/badrequest/, which
        resolves to nothing. That mismatch is a real Fess bug: a genuine HTTP
        400 shows the user the 404 page rather than the request error page.
      * Later builds rename the action to ErrorBadrequestAction, so the JSP and
        the action agree and the misspelling is what resolves to nothing.

    Asserting the exclusive-or covers both spellings on either build without
    pinning a version, and still fails loudly if neither answers (the view went
    unreachable) or if both appear to (the 404 fall-through itself broke).
    """
    routed = [path for path in REQUEST_ERROR_PATHS
              if _serves_itself(page, context, path)]
    assert_equal(len(routed), 1,
                 f"expected exactly one of {REQUEST_ERROR_PATHS} to serve the "
                 f"request error view, got {routed}")

    _assert_view_renders(page, context, routed[0], Labels.REQUEST_ERROR_TITLE)
    unrouted = next(p for p in REQUEST_ERROR_PATHS if p != routed[0])
    _assert_lands_on_notfound(page, context, unrouted)


def _assert_error_system_falls_through_to_notfound(page, context: FessContext) -> None:
    """No ErrorSystemAction exists in the default JSP mode -- the view is served
    by /error/systemerror/ -- so /error/system resolves to nothing and lands on
    Not Found.

    This navigates to the path directly, so it holds on every build. What it is
    worth varies: on builds whose error/redirect.jsp sends the badAuth branch to
    /error/system it pins a real fall-through (a bad authentication shows the 404
    page), while on builds that point that branch elsewhere nothing reaches this
    path from redirect.jsp any more and the check is only a guard that no
    ErrorSystemAction has appeared. Kept for the older builds in the matrix."""
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

    _assert_exactly_one_request_error_path_renders(page, context)
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
