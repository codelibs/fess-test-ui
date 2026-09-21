"""Verify that a search-result click really travels through GoAction, and pin
how GoAction's two failure paths are answered.

/go/ is the redirect-and-click-log hop behind every search-result click, and
nothing else in the suite touches it.

Since fess#3460, /search is the bootstrap static-theme SPA. It renders the
title link's href as the /go/ URL up front --
go/?rt=<#rt>&docId=<data-id>&queryId=<#queryId>&order=<n>, relative to the
<base href> Fess injects -- with the document URL kept in data-uri. There is
no mousedown rewrite any more, so the href is pinned as rendered, and a real
click is watched on the network: the landing URL alone cannot show that the
click went through /go/, because /go/ redirects to the same document the
raw URL would have opened.

The thumbnail is a second a.link inside the same result, so every lookup is
scoped to h3.title.

rt and queryId are read from the hidden inputs the results view fills,
never fabricated: GoAction calls Long.parseLong(form.rt) with no guard, so
an invented rt would be a 500 rather than the behaviour under test.

Errors are rendered in place: ErrorPageServlet answers the failing /go/ URL
itself with the real HTTP status and the static theme's error view, and
names the reason in <meta name="x-fess-error-detail-key">, which the view
turns into its .error-detail-additional line. So status, URL and the
rendered title/detail are all observable.

The last check -- that the href's order equals the result's 0-based
data-order, as the JSP pages sent it -- pins codelibs/fess#3463: before it,
the SPA sent order=<n+1>. It runs last so the checks before it still report
on a Fess without that fix.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt

logger = logging.getLogger(__name__)

# Matches three sampledata documents that search/seed crawls: docs/ja/
# intro.html, docs/en/intro.html, and index.html itself (which links both
# under "JA Intro"/"EN Intro"). Which one lands at #result0 does not
# matter: every expected value is read off the element itself.
QUERY = "intro"

# h3.title scopes past the thumbnail's a.link.
TITLE_LINK = "#result0 h3.title a.link"

ERROR_TITLE = "#error-view h2.error-title"
ERROR_DETAIL = "#error-view .error-detail-additional"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _search(page, context: FessContext):
    page.goto(context.url(f"/search/?q={QUERY}"))
    # Times out, rather than returning None, when the index is not seeded.
    return page.wait_for_selector(TITLE_LINK)


def _go_params(link) -> dict:
    href = link.get_attribute("href")
    assert_true(href.startswith("go/?"),
                f"the result link should point at go/?..., got {href}")
    return parse_qs(urlparse(href).query)


def _assert_href_is_the_go_url(page, context: FessContext) -> None:
    """The href carries the click-log parameters of this very result."""
    link = _search(page, context)
    params = _go_params(link)

    expected = {
        "rt": [page.input_value("#rt")],
        "docId": [link.get_attribute("data-id")],
        "queryId": [page.input_value("#queryId")],
    }
    for name, value in expected.items():
        assert_true(value[0], f"the results view left {name} empty")
        assert_equal(params.get(name), value,
                     f"the /go/ href carries {name}={params.get(name)}, "
                     f"expected {value}; href={link.get_attribute('href')}")


def _assert_a_real_click_travels_through_go(page, context: FessContext) -> None:
    """A genuine click must reach /go/ before landing on the document.

    The landing URL alone cannot show this -- it is the same document URL
    whether the click went through /go/ or opened the document directly --
    so the network is the only witness.

    This click also causes GoAction to write a ClickLog, but that is a
    deliberate omission here, not a gap: addClickLog only enqueues to an
    in-memory queue that AggregateLogJob, a scheduled job, drains to the
    persistent store. Asserting a ClickLog synchronously after the click
    would be racing that job and would be flaky by construction.
    """
    link = _search(page, context)
    doc_url = link.get_attribute("data-uri")
    doc_id = link.get_attribute("data-id")

    requested: list = []

    def _record(request) -> None:
        requested.append(request.url)

    page.on("request", _record)
    try:
        with page.expect_navigation(url=doc_url):
            link.click()
    finally:
        # The page outlives this module (main.py reuses one FessContext), so
        # a listener left attached would keep appending for every later test.
        page.remove_listener("request", _record)

    go_requests = [url for url in requested if "/go/?" in url]
    assert_true(go_requests,
                f"a real click on the result link never requested /go/, so "
                f"the click bypassed GoAction; requested={requested}")
    assert_contains(go_requests[0], f"docId={doc_id}",
                    f"the /go/ request did not carry the clicked document's "
                    f"docId={doc_id}; got {go_requests[0]}")
    assert_equal(page.url, doc_url,
                 f"after /go/ the browser should land on the document "
                 f"{doc_url}, got {page.url}")


def _goto_error(page, context: FessContext, path: str, status: int) -> None:
    """Open `path`, which must be answered in place with `status`."""
    response = page.goto(context.url(path))
    assert_equal(response.status, status,
                 f"{path} should answer HTTP {status}, got {response.status}")
    assert_equal(response.headers.get("x-fess-error-code"), str(status),
                 f"{path} should carry X-Fess-Error-Code: {status}")
    assert_equal(urlparse(page.url).path, "/go/",
                 f"the error should be rendered in place at /go/, got {page.url}")
    page.wait_for_selector(ERROR_TITLE)


def _assert_unknown_docid_is_not_found(page, context: FessContext) -> None:
    """A docId that resolves to no document is a 404 at /go/ whose view says
    the document was not found (x-fess-error-detail-key =
    errors.docid_not_found).

    rt and queryId are real values from the results view even though this
    path returns before the click log reads them -- the point is to vary
    only the docId, so a failure here can only mean the docId lookup.
    """
    _search(page, context)
    rt = page.input_value("#rt")
    query_id = page.input_value("#queryId")
    unknown = context.generate_str(20)

    _goto_error(page, context,
                f"/go/?docId={unknown}&rt={rt}&queryId={query_id}", 404)
    assert_equal(page.inner_text(ERROR_TITLE).strip(),
                 tt(context, ThemeKeys.ERROR_TITLE_404),
                 "an unknown docId did not render the Not Found view")
    assert_equal(page.inner_text(ERROR_DETAIL).strip(),
                 tt(context, ThemeKeys.ERROR_DETAIL_DOCID_NOT_FOUND),
                 "an unknown docId did not say the document was not found")


def _assert_missing_required_params_are_a_bad_request(
        page, context: FessContext) -> None:
    """GoAction validates the form first, so a request missing the required
    rt and queryId is a 400 and never reaches the docId lookup.

    The status is what separates this from the unknown-docId case above:
    dropping the validation would send this same request on to the lookup,
    fail it there, and answer 404 instead.
    """
    _goto_error(page, context, "/go/?docId=whatever", 400)
    assert_equal(page.inner_text(ERROR_TITLE).strip(),
                 tt(context, ThemeKeys.ERROR_TITLE_400),
                 "/go/ without rt/queryId did not render the Bad Request view")


def _assert_order_is_the_zero_based_position(page, context: FessContext) -> None:
    """order in the /go/ href is the result's 0-based data-order, as the JSP
    pages sent it (codelibs/fess#3463)."""
    link = _search(page, context)
    order = _go_params(link).get("order")
    data_order = link.get_attribute("data-order")
    assert_equal(order, [data_order],
                 f"the /go/ href sends order={order}, but the result's "
                 f"data-order is {data_order}; "
                 f"href={link.get_attribute('href')}")


def run(context: FessContext) -> None:
    logger.info("Starting search/go_click")
    page = context.get_wrapped_page() or context.get_admin_page()

    _assert_href_is_the_go_url(page, context)
    _assert_a_real_click_travels_through_go(page, context)
    _assert_unknown_docid_is_not_found(page, context)
    _assert_missing_required_params_are_a_bad_request(page, context)
    _assert_order_is_the_zero_based_position(page, context)

    logger.info("search/go_click completed")


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
