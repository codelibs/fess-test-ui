"""Verify the cached-copy view: the per-result link, the snapshot it serves,
and where a bad docId lands.

/cache/ serves the crawler's stored copy of a document. The link only exists
for documents whose has_cache field is 'true' (searchResults.jsp:141), which
FessXpathTransformer:521-533 sets when crawler.document.cache.enabled is on
(default) and the mimetype is one of crawler.document.cache.supported.mimetypes
(default text/html) -- so sampledata's HTML pages qualify and its files/
sample.txt does not. The query below is chosen to hit HTML.

Unlike a result's title link, the cache link is not touched by search.js's
mousedown rewrite: that handler is delegated on "a.link" (search.js:110) and
this link's class is "cache d-print-none", so a plain click is the real user
path and there is no /go/ hop to account for.

CacheAction responds with text/html inline rather than an attachment
(CacheAction:88 headerContentDispositionInline), so the browser renders the
snapshot and its DOM is readable here.

  *** The not-found path differs from GoAction's. Do not copy one to the
      other: ***
    GoAction:87    -> redirect(ErrorAction.class)          -> /error/
    CacheAction:95 -> redirect2ErrorWithMessageKey(...)    ->
                      /error/notfound/?message_key=errors.docid_not_found

  and the message itself is assertable on the Go path only. error/error.jsp
  renders <la:errors>, so /error/ shows the docid_not_found text;
  error/notFound.jsp renders neither <la:errors> nor the message_key
  parameter (it only prints labels.page_not_found_title, labels.check_url
  and ${url}). message_key is there for StaticThemeResponder's SPA themes,
  not for the JSP theme this suite drives -- so here the landing URL and its
  query string are the observables.

No HTTP status is asserted: web.xml routes errors through error/redirect.jsp,
which sendRedirect()s to a page served as 200, so status cannot distinguish a
working endpoint from a missing one.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_startswith, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

# Matches sampledata's docs/ja/intro.html and docs/en/intro.html. Both are
# text/html, so both carry a cache; both contain the term in lower case in
# their body text, which the highlight assertion below depends on.
QUERY = "intro"

TITLE_LINK = "#result0 h3.title a.link"
CACHE_LINK = "#result0 a.cache"

NOTFOUND_PATH = "/error/notfound/"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _normalize_ws(text: str) -> str:
    """Collapse whitespace so a properties-file string can be compared with
    rendered text, where the HTML parser has folded runs of space."""
    return " ".join(text.split())


def _search(page, context: FessContext) -> None:
    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_load_state("domcontentloaded")


def _cache_link(page):
    """The top result's cache link. Absent rather than empty when the
    document has no stored copy (searchResults.jsp:141 wraps it in
    <c:if test="${doc.has_cache=='true'}">), so this is the one place that
    turns 'no cache at all' into a message that says so."""
    link = page.query_selector(CACHE_LINK)
    assert_true(link is not None,
                f"no {CACHE_LINK} for q={QUERY}; the top result has no "
                f"cached copy (has_cache != 'true'), so crawler document "
                f"caching may be off")
    return link


def _first_result_doc_url(page) -> str:
    """The document URL of the top result, read off the element rather than
    assumed: which of the two 'intro' pages ranks first does not matter, but
    every later assertion must be about the same one."""
    title_link = page.query_selector(TITLE_LINK)
    assert_true(title_link is not None,
                f"no result at {TITLE_LINK} for q={QUERY}; is the index "
                f"seeded?")
    return title_link.get_attribute("data-uri")


def _assert_cache_link_is_rendered(page, context: FessContext) -> None:
    """The cache link carries its localized text and points at /cache/ with
    the result's docId plus the highlight terms SearchHelper:176 appends."""
    _search(page, context)

    title_link = page.query_selector(TITLE_LINK)
    assert_true(title_link is not None,
                f"no result at {TITLE_LINK} for q={QUERY}; is the index "
                f"seeded?")
    doc_id = title_link.get_attribute("data-id")

    cache_link = _cache_link(page)
    assert_equal(cache_link.inner_text().strip(),
                 t(Labels.SEARCH_RESULT_CACHE),
                 f"the cache link is not labelled "
                 f"{t(Labels.SEARCH_RESULT_CACHE)!r}, got "
                 f"{cache_link.inner_text().strip()!r}")

    context_path = page.input_value("#contextPath")
    href = cache_link.get_attribute("href")
    assert_startswith(href, f"{context_path}/cache/?docId={doc_id}",
                      f"the cache link should address the result's own "
                      f"docId={doc_id}; got {href}")
    # appendHighlightParams (SearchHelper:170-178) is what carries the query
    # terms over to the snapshot; without it the highlight below cannot work.
    assert_contains(href, f"&hq={QUERY}",
                    f"the cache link dropped the highlight term "
                    f"hq={QUERY}; got {href}")


def _assert_snapshot_renders(page, context: FessContext) -> None:
    """Clicking the link serves the snapshot: cache.hbs points <base> at the
    original document, banners it with the localized labels.search_cache_msg,
    and emits the stored copy with the hq terms wrapped in
    query.highlight.tag.pre (default <strong>)."""
    _search(page, context)
    doc_url = _first_result_doc_url(page)

    _cache_link(page).click()
    page.wait_for_load_state("domcontentloaded")

    assert_equal(urlparse(page.url).path, "/cache/",
                 f"the cache link did not serve /cache/, landed on "
                 f"{page.url}")

    base = page.query_selector("base")
    assert_true(base is not None,
                "the snapshot has no <base>, so cache.hbs did not render")
    assert_equal(base.get_attribute("href"), doc_url,
                 f"cache.hbs should <base href> the original document "
                 f"{doc_url}, got {base.get_attribute('href')}")

    # ViewHelper:742 fills {0} with the document URL and {1} with the crawl
    # timestamp. Only the {0} half is predictable, so assert up to {1}.
    banner = t(Labels.SEARCH_CACHE_MSG).split("{1}")[0].replace("{0}", doc_url)
    assert_contains(_normalize_ws(page.inner_text("body")),
                    _normalize_ws(banner),
                    f"the snapshot is missing its cache banner for "
                    f"{doc_url}; expected {_normalize_ws(banner)!r}")

    # ViewHelper.replaceHighlightQueries wraps each hq term found in the
    # stored copy's text (never inside a tag). sampledata's pages contain no
    # <strong> of their own, so any hit here came from the highlighter.
    highlighted = [el.inner_text() for el in page.query_selector_all("strong")]
    assert_contains(highlighted, QUERY,
                    f"the snapshot did not highlight {QUERY!r}; "
                    f"<strong> texts were {highlighted}")


def _assert_unknown_docid_lands_on_notfound(page, context: FessContext) -> None:
    """CacheAction:95-97 sends an unresolvable docId to
    /error/notfound/?message_key=errors.docid_not_found -- a different target
    from GoAction's /error/ (see the module docstring).

    Only the URL is assertable: error/notFound.jsp ignores message_key, so
    the message text never reaches this page.
    """
    unknown = context.generate_str(20)
    page.goto(context.url(f"/cache/?docId={unknown}"))
    page.wait_for_load_state("domcontentloaded")

    landed = urlparse(page.url)
    assert_equal(landed.path, NOTFOUND_PATH,
                 f"an unknown docId should land on {NOTFOUND_PATH}, "
                 f"got {page.url}")
    assert_equal(parse_qs(landed.query).get("message_key"),
                 [Messages.ERRORS_DOCID_NOT_FOUND],
                 f"expected ?message_key={Messages.ERRORS_DOCID_NOT_FOUND} "
                 f"after landing, got {page.url}")
    assert_contains(page.inner_text("body"), t(Labels.PAGE_NOT_FOUND_TITLE),
                    f"{NOTFOUND_PATH} did not render its own text "
                    f"{t(Labels.PAGE_NOT_FOUND_TITLE)!r}")


def _assert_missing_docid_renders_the_error_view(page, context: FessContext) -> None:
    """CacheAction:70 validates the form with an asHtml(error.jsp) fallback,
    which renders in place -- so a request with no docId (CacheForm:29
    @Required) stays at /cache/ and never reaches the lookup.

    The URL is what separates this from the unknown-docId case above:
    dropping the validation would send this request on to the lookup, fail it
    there, and land it on /error/notfound/ instead.
    """
    page.goto(context.url("/cache/"))
    page.wait_for_load_state("domcontentloaded")

    assert_equal(urlparse(page.url).path, "/cache/",
                 f"a validation failure should render error.jsp in place at "
                 f"/cache/, got {page.url}")
    assert_contains(page.inner_text("body"), t(Labels.ERROR_TITLE),
                    f"/cache/ without a docId did not render error.jsp "
                    f"(no {t(Labels.ERROR_TITLE)!r} in the body)")


def run(context: FessContext) -> None:
    logger.info("Starting search/cache")
    page = context.get_wrapped_page() or context.get_admin_page()

    _assert_cache_link_is_rendered(page, context)
    _assert_snapshot_renders(page, context)
    _assert_unknown_docid_lands_on_notfound(page, context)
    _assert_missing_docid_renders_the_error_view(page, context)

    logger.info("search/cache completed")


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
