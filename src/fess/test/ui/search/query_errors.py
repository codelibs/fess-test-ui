"""Verify the search query errors reach the user on the results page.

Since fess#3460, /search is the bootstrap static-theme SPA. It asks
/api/v2/search, and the two query errors this module covers come back from
that API as HTTP 400 with the localized server message in
response.error.message. search.js shows that message in
#search-error (alert-danger) and stays at the requested /search/ URL --
there is no redirect to the root any more. Neither case needs crawled data.

The message text is still fess_message text (the server localizes it for the
request's locale), so it is compared with tm(), not with the theme bundle.

Note on the InvalidQueryException case: an unparseable query string such as
`q=test(` does NOT produce an error. SearchHelper.search catches
InvalidQueryException from searchInternal and retries the query with
escape(true), which turns `test(` into a literal term and succeeds. The sort
variant is used instead: escaping the query text cannot fix an unsupported
sort field, so the retry throws again and the API reports it.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import tm
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

ERROR_BOX = "#search-error"

# query.max.search.result.offset (fess_config.properties). The guard is a
# strict >, so MAX_OFFSET itself must not trip it and MAX_OFFSET + 1 must.
MAX_OFFSET = 100000

UNSUPPORTED_SORT = "nosuchfield"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _search(page, context: FessContext, query: str):
    """Open /search/<query> and return the /api/v2/search response it made."""
    with page.expect_response(lambda r: "/api/v2/search?" in r.url) as info:
        page.goto(context.url(f"/search/{query}"))
    return info.value


def _assert_error_is_shown(page, response, what: str, expected: str) -> None:
    assert_equal(response.status, 400,
                 f"{what}: /api/v2/search should answer 400, got "
                 f"HTTP {response.status}")
    box = page.wait_for_selector(f"{ERROR_BOX}:not(.d-none)")
    assert_equal(box.inner_text().strip(), expected,
                 f"{what}: expected {expected!r} in {ERROR_BOX}, got "
                 f"{box.inner_text().strip()!r}")
    assert_equal(urlparse(page.url).path, "/search/",
                 f"{what}: the page should stay at /search/, got {page.url}")


def _assert_unsupported_sort_is_reported(page, context: FessContext) -> None:
    """An unsupported sort field raises InvalidQueryException, whose own
    message code carries the offending field as {0}."""
    response = _search(page, context, f"?q=alpha&sort={UNSUPPORTED_SORT}")
    _assert_error_is_shown(
        page, response, f"sort={UNSUPPORTED_SORT}",
        tm(Messages.ERRORS_INVALID_QUERY_UNSUPPORTED_SORT_FIELD,
           UNSUPPORTED_SORT))


def _assert_offset_over_max_is_reported(page, context: FessContext) -> None:
    """start beyond query.max.search.result.offset raises
    ResultOffsetExceededException."""
    response = _search(page, context, f"?q=alpha&start={MAX_OFFSET + 1}")
    _assert_error_is_shown(page, response, f"start={MAX_OFFSET + 1}",
                           tm(Messages.ERRORS_RESULT_SIZE_EXCEEDED))


def _assert_offset_at_max_does_not_trip_the_guard(page, context: FessContext) -> None:
    """The boundary: at exactly the max offset the guard must stay silent.

    Fess checks `start > max` against query.max.search.result.offset=100000,
    so relaxing it to `>=` would report the result-size error one document
    early and turn this red.

    Clearing the offset guard does hand the request to the search engine, and
    from+size at this depth exceeds max_result_window (10000 by default, which
    Fess does not raise), so the engine refuses it. That refusal is HANDLED,
    not fatal: SearchEngineClient catches the OpenSearchException and rethrows
    InvalidQueryException(invalid_query_cannot_process), which the API answers
    as 400 "Could not process the specified query." -- no 500, and no stack
    trace, because that catch logs at DEBUG only. A 500 or an ERROR-level
    trace from this check is therefore NOT expected and IS worth chasing.

    Only the ABSENCE of the result-size message is asserted, after the search
    has answered. Do not "improve" this by also pinning the engine's refusal:
    raising max_result_window past 100000 would let the search succeed. That
    is the engine's behaviour, not this guard's, and not this suite's to pin.
    """
    response = _search(page, context, f"?q=alpha&start={MAX_OFFSET}")
    assert_true(response.status < 500,
                f"start={MAX_OFFSET} made /api/v2/search fail with "
                f"HTTP {response.status}")

    # Parsed, not a substring of response.text(): the JSON body may escape
    # non-ASCII text, which would make a raw `not in` pass in most locales.
    error = (response.json().get("response", {}).get("error") or {})
    result_size_error = tm(Messages.ERRORS_RESULT_SIZE_EXCEEDED)
    assert_true(error.get("message") != result_size_error,
                f"start={MAX_OFFSET} tripped the offset guard, but the guard "
                f"is a strict > and {MAX_OFFSET} is the configured maximum")


def run(context: FessContext) -> None:
    logger.info("Starting search/query_errors")
    page = context.get_wrapped_page() or context.get_admin_page()

    _assert_unsupported_sort_is_reported(page, context)
    _assert_offset_over_max_is_reported(page, context)
    _assert_offset_at_max_does_not_trip_the_guard(page, context)

    logger.info("search/query_errors completed")


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
