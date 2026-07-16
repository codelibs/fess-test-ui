"""Verify SearchAction's two query-error handlers surface a message on the root.

Both handlers (SearchAction.java:222-236) end the same way -- saveError(...)
then redirectToRoot() -- so both cases assert the same shape: the browser
lands on /, and index.jsp's <la:errors> block (index.jsp:126-129) renders the
specific message. Neither needs crawled data.

<la:errors> wraps each message in errors.front_prefix, which is
'<div class="alert alert-warning">'. That is a different class from
<la:info>'s alert-info, so the selector cannot pick up an informational
message by accident.

Note on the InvalidQueryException case: an unparseable query string such as
`q=test(` does NOT reach the handler. SearchHelper.search (:153-163) catches
InvalidQueryException from searchInternal and retries the query with
escape(true), which turns `test(` into a literal term and succeeds -- so the
UI renders results and no error is ever shown. The sort variant is used
instead: escaping the query text cannot fix an unsupported sort field, so the
retry throws again and the exception propagates to SearchAction.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import tm
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

ERROR_BOX = "div.alert.alert-warning"

# query.max.search.result.offset (fess_config.properties:783). The guard is a
# strict >, so MAX_OFFSET itself must not trip it and MAX_OFFSET + 1 must.
MAX_OFFSET = 100000

UNSUPPORTED_SORT = "nosuchfield"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _search(page, context: FessContext, query: str) -> None:
    page.goto(context.url(f"/search/{query}"))
    page.wait_for_load_state("domcontentloaded")


def _assert_redirected_to_root(page, what: str) -> None:
    landed = urlparse(page.url)
    assert_equal(landed.path, "/",
                 f"{what} should redirect to the root, got {page.url}")


def _error_text(page) -> str:
    box = page.query_selector(ERROR_BOX)
    return box.inner_text().strip() if box is not None else ""


def _assert_unsupported_sort_is_reported(page, context: FessContext) -> None:
    """An unsupported sort field raises InvalidQueryException, whose own
    message code carries the offending field as {0}."""
    _search(page, context, f"?q=alpha&sort={UNSUPPORTED_SORT}")
    _assert_redirected_to_root(page, f"sort={UNSUPPORTED_SORT}")

    expected = tm(Messages.ERRORS_INVALID_QUERY_UNSUPPORTED_SORT_FIELD,
                  UNSUPPORTED_SORT)
    assert_equal(_error_text(page), expected,
                 f"expected the unsupported-sort error on the root page, "
                 f"got {_error_text(page)!r}")


def _assert_offset_over_max_is_reported(page, context: FessContext) -> None:
    """start beyond query.max.search.result.offset raises
    ResultOffsetExceededException."""
    _search(page, context, f"?q=alpha&start={MAX_OFFSET + 1}")
    _assert_redirected_to_root(page, f"start={MAX_OFFSET + 1}")

    expected = tm(Messages.ERRORS_RESULT_SIZE_EXCEEDED)
    assert_equal(_error_text(page), expected,
                 f"expected the result-size error on the root page, "
                 f"got {_error_text(page)!r}")


def _assert_offset_at_max_does_not_trip_the_guard(page, context: FessContext) -> None:
    """The boundary: at exactly the max offset the guard must stay silent.

    Fess checks `start > max`, so relaxing that to `>=` would report the
    result-size error one document early and turn this red. Only the absence
    of THAT message is asserted: the search engine still rejects an offset
    this deep for its own reasons (max_result_window), which is not this
    guard's behaviour and not this suite's to pin.
    """
    _search(page, context, f"?q=alpha&start={MAX_OFFSET}")

    result_size_error = tm(Messages.ERRORS_RESULT_SIZE_EXCEEDED)
    assert_true(result_size_error not in page.inner_text("body"),
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
