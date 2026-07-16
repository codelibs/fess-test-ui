"""Verify that a search-result click really travels through GoAction, and pin
where GoAction's two failure paths land.

/go/ is the redirect-and-click-log hop behind every search-result click, and
nothing else in the suite touches it.

The trap this module is built around: js/search.js:111-127 rewrites a result
link's href to /go/?rt=..&docId=..&queryId=..&order=.. on **mousedown**, not
on click. A synthetic dispatch_event("click") never fires mousedown, so it
would follow the un-rewritten href straight to the document and bypass /go/
entirely -- green, and testing nothing.

Worse, no assertion on the landing URL can catch that, because both routes
end at the same place: the raw href goes to the document directly, and /go/
redirects to that same document (GoAction:162). The landing URL is identical
either way. So the click path is pinned two ways that do not share the
failure mode:

  * _assert_mousedown_rewrites_the_href: fire mousedown by hand and pin the
    rewritten href exactly, reproducing search.js:118's own construction.
  * _assert_a_real_click_travels_through_go: watch the network across a real
    click (which does fire mousedown) and require the /go/ request to have
    actually happened. This is the one that would notice if a browser read
    href before the handler ran.

The thumbnail is a second a.link inside the same result (searchResults.jsp:
106-107), so every lookup is scoped to h3.title (searchResults.jsp:99-102).

rt and queryId are read from the hidden inputs the results page renders
(searchResults.jsp:94-95), never fabricated: GoAction:123 calls
Long.parseLong(form.rt) with no guard, so an invented rt would be a 500
rather than the behaviour under test.

No HTTP status is asserted here. web.xml routes errors through
error/redirect.jsp, which sendRedirect()s to a page served as 200, so a
redirect-following client cannot tell a broken endpoint from a working one
by status. The landing URL and the rendered message are the observables.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.i18n import t, tm
from fess.test.i18n.keys import Labels
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

# Matches three sampledata documents that search/seed crawls: docs/ja/
# intro.html, docs/en/intro.html, and index.html itself (which links both
# under "JA Intro"/"EN Intro"). Which one lands at #result0 does not
# matter: every expected value is read off the element itself.
QUERY = "intro"

# h3.title scopes past the thumbnail's a.link (searchResults.jsp:106-107).
TITLE_LINK = "#result0 h3.title a.link"

# One rendered error message on error/error.jsp.
#
# NOT div.alert.alert-warning -- that is index.jsp's box, and it only looks
# that way because index.jsp:126-129 passes prefix="errors.front_prefix"
# explicitly. error.jsp:26 writes <la:errors styleClass="list-unstyled"/>
# with no prefix override, so HtmlErrorsTag falls back to the defaults:
# styleClass replaces the header with <ul class="list-unstyled">
# (HtmlErrorsTag.setupHeader), and each message is wrapped in
# errors.prefix/suffix = <li><i class="fa fa-exclamation-circle"></i> ...
# </li>. Scoped to <main> because header.jsp/footer.jsp are included into
# the same body (neither uses list-unstyled today, but the scope keeps this
# about error.jsp's own markup).
ERROR_MESSAGE = "main ul.list-unstyled li"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _search(page, context: FessContext) -> None:
    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_load_state("domcontentloaded")


def _first_result_link(page):
    link = page.query_selector(TITLE_LINK)
    assert_true(link is not None,
                f"no result link at {TITLE_LINK} for q={QUERY}; "
                f"is the index seeded?")
    return link


def _assert_mousedown_rewrites_the_href(page, context: FessContext) -> None:
    """search.js:111-127 swaps the raw document href for a /go/ URL on
    mousedown. Pin the result exactly, mirroring search.js:118."""
    _search(page, context)
    link = _first_result_link(page)

    doc_url = link.get_attribute("data-uri")
    doc_id = link.get_attribute("data-id")
    order = link.get_attribute("data-order")
    rt = page.input_value("#rt")
    query_id = page.input_value("#queryId")
    context_path = page.input_value("#contextPath")

    # Before mousedown: searchResults.jsp:100-101 renders href and data-uri
    # from the same ${doc.url_link}, so they must still agree. This is what
    # makes the post-mousedown assertion below meaningful rather than
    # vacuous -- it establishes that the href started out as the raw
    # document URL and therefore actually changed.
    before = link.get_attribute("href")
    assert_equal(before, doc_url,
                 f"expected the un-rewritten href to be the document URL "
                 f"{doc_url}, got {before}")

    link.dispatch_event("mousedown")

    # get_attribute returns the literal attribute, not a resolved URL, so
    # this compares against search.js's own string construction.
    expected = (f"{context_path}/go/?rt={rt}&docId={doc_id}"
                f"&queryId={query_id}&order={order}")
    assert_equal(link.get_attribute("href"), expected,
                 f"mousedown did not rewrite the href as search.js:118 "
                 f"builds it; expected {expected}, got "
                 f"{link.get_attribute('href')}")


def _assert_a_real_click_travels_through_go(page, context: FessContext) -> None:
    """A genuine click must reach /go/ before landing on the document.

    The landing URL alone cannot show this -- it is the same document URL
    whether the click went through /go/ or followed the raw href -- so the
    network is the only witness. Deleting the mousedown handler from
    search.js turns this red while leaving the landing assertion green,
    which is exactly the blind spot it exists to cover.

    This click also causes GoAction (:130) to write a ClickLog, but that is
    a deliberate omission here, not a gap: addClickLog (SearchLogHelper:314-
    322) only enqueues to an in-memory ConcurrentLinkedQueue: the queue is
    drained to the persistent store by AggregateLogJob, a scheduled job, not
    by this request. Asserting a ClickLog synchronously after the click
    would be racing that job and would be flaky by construction.
    """
    _search(page, context)
    link = _first_result_link(page)
    doc_url = link.get_attribute("data-uri")
    doc_id = link.get_attribute("data-id")

    requested: list = []

    def _record(request) -> None:
        requested.append(request.url)

    page.on("request", _record)
    try:
        link.click()
        page.wait_for_load_state("domcontentloaded")
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


def _assert_unknown_docid_lands_on_the_error_view(page, context: FessContext) -> None:
    """GoAction:105-107: a docId that resolves to no document saves
    errors.docid_not_found and redirects to /error/, whose error.jsp renders
    it through <la:errors>. This is where GoAction and CacheAction diverge --
    CacheAction sends the same condition to /error/notfound/ instead, and
    that view renders no message at all (see search/cache.py).

    rt and queryId are real values from the results page even though this
    path returns before the click log reads them (GoAction:107 returns while
    Long.parseLong(form.rt) is at :123) -- the point is to vary only the
    docId, so a failure here can only mean the docId lookup.
    """
    _search(page, context)
    rt = page.input_value("#rt")
    query_id = page.input_value("#queryId")
    unknown = context.generate_str(20)

    page.goto(context.url(
        f"/go/?docId={unknown}&rt={rt}&queryId={query_id}"))
    page.wait_for_load_state("domcontentloaded")

    assert_equal(urlparse(page.url).path, "/error/",
                 f"an unknown docId should redirect to /error/, "
                 f"got {page.url}")

    rendered = [el.inner_text().strip()
                for el in page.query_selector_all(ERROR_MESSAGE)]
    assert_contains(rendered, tm(Messages.ERRORS_DOCID_NOT_FOUND, unknown),
                    f"/error/ did not render the docid_not_found message "
                    f"naming {unknown}; messages were {rendered}")


def _assert_missing_required_params_render_the_error_view(
        page, context: FessContext) -> None:
    """GoAction:91 validates the form with an asHtml(error.jsp) fallback,
    which renders in place -- so a request missing the required rt and
    queryId (GoForm:53,:66) stays at /go/ and never reaches the docId
    lookup.

    The URL is what separates this from the unknown-docId case above, which
    redirects to /error/: dropping the validation would send this same
    request on to the lookup, fail it there, and land it on /error/.
    """
    page.goto(context.url("/go/?docId=whatever"))
    page.wait_for_load_state("domcontentloaded")

    assert_equal(urlparse(page.url).path, "/go/",
                 f"a validation failure should render error.jsp in place at "
                 f"/go/, got {page.url}")
    assert_equal(page.inner_text("main h2").strip(), t(Labels.ERROR_TITLE),
                 f"/go/ without rt/queryId did not render error.jsp; "
                 f"main h2 was {page.inner_text('main h2').strip()!r}")


def run(context: FessContext) -> None:
    logger.info("Starting search/go_click")
    page = context.get_wrapped_page() or context.get_admin_page()

    _assert_mousedown_rewrites_the_href(page, context)
    _assert_a_real_click_travels_through_go(page, context)
    _assert_unknown_docid_lands_on_the_error_view(page, context)
    _assert_missing_required_params_render_the_error_view(page, context)

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
