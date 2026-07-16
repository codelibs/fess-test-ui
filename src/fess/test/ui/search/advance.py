"""Exercise /search/advance: fill the advanced-search fields, submit, and assert
the query Fess assembled from them.

The advance form GETs /search/ (advance.jsp:18), not /search/advance. On the
results page SearchAction writes the assembled query back into the form
(SearchAction.java:207-210: `if (form.hasConditionQuery()) form.q =
renderData.getSearchQuery()`), and getSearchQuery() is the string
QueryStringBuilder built from the as.* fields (SearchHelper.java:153,207).
So input#query on the results page is the assembly's observable output.

Asserts only on that query round-trip, never on hit counts, so it needs no
crawled data. The expected values below are exact: they were captured from a
live Fess and match QueryStringBuilder.appendConditions (QueryStringBuilder
.java:207-245) term for term, including the quoting of as.epq, the NOT
prefixing of as.nq, and the leading space being trimmed.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

ALL_WORDS = "alpha"
EXACT_PHRASE = "beta gamma"
NONE_WORDS = "delta"
SITE = "example.com"

# Every field the form is expected to expose. Renaming or dropping one in
# advance.jsp turns the corresponding assertion red.
TEXT_FIELDS = ("as.q", "as.epq", "as.oq", "as.nq", "as.sitesearch")
SELECT_FIELDS = ("as.filetype", "as.occt", "as.timestamp", "num", "sort", "lang")


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _open_advance(page, context: FessContext) -> None:
    page.goto(context.url("/search/advance"))
    page.wait_for_load_state("domcontentloaded")
    # SearchAction.advance() redirects to /login/ when isLoginRequired();
    # landing anywhere else means the page under test never rendered.
    #
    # Compare the parsed path, not a substring of the whole URL. If the route
    # disappeared, the 404 handler redirects to /error/notfound/?url=%2Fsearch%2Fadvance
    # -- which contains "/search/advance" only in percent-encoded form, so a
    # substring test happens to still work. Relying on that is fragile: it turns
    # on how the browser normalises %2F, and it would silently stop failing if
    # that ever changed.
    assert_equal(urlparse(page.url).path.rstrip("/"), "/search/advance",
                 f"expected /search/advance, got {page.url}")


def _submit(page) -> None:
    # advance.jsp:309 -- the form GETs /search/, so this leaves /search/advance.
    page.click('button[name="search"]')
    page.wait_for_load_state("domcontentloaded")


def _assert_form_contract(page) -> None:
    for field in TEXT_FIELDS:
        assert_true(page.query_selector(f'input[name="{field}"]') is not None,
                    f"advance form is missing input[name={field}]")
    for field in SELECT_FIELDS:
        assert_true(page.query_selector(f'select[name="{field}"]') is not None,
                    f"advance form is missing select[name={field}]")


def _assert_words_are_assembled(page, context: FessContext) -> None:
    """as.q + as.epq + as.nq -> `alpha "beta gamma" NOT delta`."""
    _open_advance(page, context)
    page.fill('input[name="as.q"]', ALL_WORDS)
    page.fill('input[name="as.epq"]', EXACT_PHRASE)
    page.fill('input[name="as.nq"]', NONE_WORDS)
    _submit(page)

    assert_true("/search/" in page.url,
                f"expected /search/ after submit, got {page.url}")
    # Exact, not a substring check: this pins the quoting of as.epq and the
    # NOT prefixing of as.nq, either of which could regress independently
    # while every loose `in` assertion stayed green.
    assert_equal(page.input_value("#query"),
                 f'{ALL_WORDS} "{EXACT_PHRASE}" NOT {NONE_WORDS}',
                 f"assembled query mismatch at {page.url}")


def _assert_operators_are_assembled(page, context: FessContext) -> None:
    """as.q + as.occt + as.filetype + as.sitesearch ->
    `allintitle: alpha filetype:"pdf" site:example.com`."""
    _open_advance(page, context)
    page.fill('input[name="as.q"]', ALL_WORDS)
    page.fill('input[name="as.sitesearch"]', SITE)
    page.select_option('select[name="as.filetype"]', "pdf")
    page.select_option('select[name="as.occt"]', "allintitle")
    _submit(page)

    # as.occt is inserted at position 0 while the rest append, so the space
    # after the colon is the trimmed-away leading space of " alpha".
    assert_equal(page.input_value("#query"),
                 f'allintitle: {ALL_WORDS} filetype:"pdf" site:{SITE}',
                 f"assembled query mismatch at {page.url}")


def _assert_occurrence_alone_is_a_noop(page, context: FessContext) -> None:
    """as.occt on its own must not run a search.

    SearchRequestParams.hasConditionQuery() (:200-209) deliberately omits
    AS_OCCURRENCE, so with every other field blank the form submit leaves q
    blank and SearchAction redirects to the root rather than searching.
    Adding AS_OCCURRENCE to hasConditionQuery() would turn this red.
    """
    _open_advance(page, context)
    page.select_option('select[name="as.occt"]', "allintitle")
    _submit(page)

    landed = urlparse(page.url)
    assert_equal(landed.path, "/",
                 f"as.occt alone should redirect to the root, got {page.url}")
    assert_equal(landed.query, "",
                 f"root redirect should carry no query, got {page.url}")


def run(context: FessContext) -> None:
    logger.info("Starting search/advance")
    page = context.get_wrapped_page() or context.get_admin_page()

    _open_advance(page, context)
    _assert_form_contract(page)

    _assert_words_are_assembled(page, context)
    _assert_operators_are_assembled(page, context)
    _assert_occurrence_alone_is_a_noop(page, context)

    logger.info("search/advance completed")


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
