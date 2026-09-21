"""Verify the error views render in place with their real HTTP status.

Since fess#3460 there is no error/redirect.jsp hop: ErrorPageServlet answers
the failing URL itself with the real status, an X-Fess-Error-Code header, and
the bootstrap static theme's error view, into which it injects
<meta name="x-fess-error-code"> (and, when a reason is known,
<meta name="x-fess-error-detail-key">). error.js renders the view from those:
h2.error-title from the theme bundle's error.title_<code>, and the requested
path in .error-detail dd. So status, URL and title are all observable, and
this module asserts all three.

The /error/<kind>/ paths keep answering, through the same theme page:
StaticThemeResponder.computeErrorStatus maps the segment after /error/ to a
status (notfound -> 404, badrequest -> 400, busy -> 429, system -> 500) and
anything it does not recognise -- systemerror, and the old
/error/badrequrest/ misspelling, included -- to 500.

The error views never call isLoginRequired(), so they stay reachable even
when the UI is closed to anonymous users.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt

logger = logging.getLogger(__name__)

ERROR_TITLE = "#error-view h2.error-title"
ERROR_DETAIL = "#error-view .error-detail-additional"
REQUESTED_URL = "#error-view .error-detail dd"

# path -> (status, theme key of the title only that status renders).
ERROR_VIEWS = (
    ("/error/notfound/", 404, ThemeKeys.ERROR_TITLE_404),
    ("/error/systemerror/", 500, ThemeKeys.ERROR_TITLE_500),
    ("/error/busy/", 429, ThemeKeys.ERROR_TITLE_429),
    ("/error/badrequest/", 400, ThemeKeys.ERROR_TITLE_400),
    # The misspelling Fess <= 15.7 routed. Unrecognised now, so it falls into
    # the catch-all 500 like any other unknown /error/<name>/.
    ("/error/badrequrest/", 500, ThemeKeys.ERROR_TITLE_500),
)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _assert_error_view(page, context: FessContext, path: str, status: int,
                       title_key: str) -> None:
    """`path` is answered in place with `status` and the view titled by
    `title_key`."""
    response = page.goto(context.url(path))
    assert_equal(response.status, status,
                 f"{path} should answer HTTP {status}, got {response.status}")
    assert_equal(response.headers.get("x-fess-error-code"), str(status),
                 f"{path} should carry X-Fess-Error-Code: {status}")
    requested_path = path.split("?")[0]
    assert_equal(urlparse(page.url).path, requested_path,
                 f"{path} should be rendered in place, landed on {page.url}")

    title = page.wait_for_selector(ERROR_TITLE).inner_text().strip()
    expected = tt(context, title_key)
    assert_equal(title, expected,
                 f"{path} should render {expected!r}, got {title!r}")
    assert_equal(page.inner_text(REQUESTED_URL).strip(), requested_path,
                 f"{path} should name the requested path in the view")


def _assert_error_system_shows_its_detail(page, context: FessContext) -> None:
    """/error/system?message_key=... is a 500 whose view also shows the reason
    the key names: the servlet passes it on as x-fess-error-detail-key, and
    error.js maps errors.<x> to the bundle's error.detail_<x>."""
    path = "/error/system?message_key=errors.bad_authentication"
    _assert_error_view(page, context, path, 500, ThemeKeys.ERROR_TITLE_500)
    detail_key = page.get_attribute('meta[name="x-fess-error-detail-key"]',
                                    "content")
    assert_equal(detail_key, "errors.bad_authentication",
                 f"{path} should pass message_key on as "
                 f"x-fess-error-detail-key, got {detail_key!r}")
    assert_equal(page.inner_text(ERROR_DETAIL).strip(),
                 tt(context, ThemeKeys.ERROR_DETAIL_BAD_AUTHENTICATION),
                 f"{path} did not render the bad-authentication detail")


def _assert_unknown_path_is_not_found(page, context: FessContext) -> None:
    """A genuinely unrouted URL exercises the real container 404, rather than
    a hand-written /error/* path: it is a 404 at the URL the visitor asked
    for."""
    path = f"/no-such-page-{context.generate_str(12)}"
    _assert_error_view(page, context, path, 404, ThemeKeys.ERROR_TITLE_404)
    code = page.get_attribute('meta[name="x-fess-error-code"]', "content")
    assert_equal(code, "404",
                 f"{path} should mark the page with x-fess-error-code=404, "
                 f"got {code!r}")


def run(context: FessContext) -> None:
    logger.info("Starting search/error_pages")
    page = context.get_wrapped_page() or context.get_admin_page()

    for path, status, title_key in ERROR_VIEWS:
        _assert_error_view(page, context, path, status, title_key)

    _assert_error_system_shows_its_detail(page, context)
    _assert_unknown_path_is_not_found(page, context)

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
