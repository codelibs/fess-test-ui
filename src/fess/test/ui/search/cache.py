"""Verify the cached-copy view: the per-result link, the snapshot it serves,
and what a bad docId shows.

/cache/ serves the crawler's stored copy of a document. The link only exists
for documents whose has_cache field is 'true', which FessXpathTransformer
sets when crawler.document.cache.enabled is on (default) and the mimetype is
one of crawler.document.cache.supported.mimetypes (default text/html) -- so
sampledata's HTML pages qualify and its files/sample.txt does not. The query
below is chosen to hit HTML.

Since fess#3460, /cache is the bootstrap static-theme SPA. The results view
renders the link as `a.cache href="cache/?docId=...&hq=..." target=_blank`
(relative to the <base href> Fess injects), so this module opens that URL in
the same tab instead of following the new tab. cache.js asks
/api/v2/cache/<docId> for the stored copy -- still rendered through cache.hbs,
so it keeps its <base href> to the original document, its banner
(labels.search_cache_msg) and the <strong> highlighting -- and shows it in a
sandboxed iframe.cache-frame, where frame_locator reads it.

A docId that is missing or resolves to nothing never reaches an error page:
the view stays at /cache/ and says labels.cache_not_found in an
alert-warning.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt
from fess.test.ui.search import cache_jsp
from fess.test.ui.version import run_jsp_variant

logger = logging.getLogger(__name__)

# Matches three sampledata documents, not two: docs/ja/intro.html,
# docs/en/intro.html, and index.html itself (which links both under "JA
# Intro"/"EN Intro"). Harmless -- every expected value below is read off
# whichever document ranks #result0 rather than assumed, and all three are
# text/html with the term in lower case in their body text, which the
# highlight assertion depends on.
QUERY = "intro"

TITLE_LINK = "#result0 h3.title a.link"
CACHE_LINK = "#result0 a.cache"
CACHE_FRAME = "#cache-view iframe.cache-frame"
NOT_FOUND_ALERT = "#cache-view .alert.alert-warning"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _normalize_ws(text: str) -> str:
    """Collapse whitespace so a properties-file string can be compared with
    rendered text, where the HTML parser has folded runs of space."""
    return " ".join(text.split())


def _search(page, context: FessContext):
    """Search and return the top result's title link. Waiting on it also
    waits for the SPA to render the results."""
    page.goto(context.url(f"/search/?q={QUERY}"))
    return page.wait_for_selector(TITLE_LINK)


def _cache_link(page):
    """The top result's cache link. Absent rather than empty when the
    document has no stored copy (search.js renders it only for
    has_cache == 'true'), so this is the one place that turns 'no cache at
    all' into a message that says so."""
    link = page.query_selector(CACHE_LINK)
    assert_true(link is not None,
                f"no {CACHE_LINK} for q={QUERY}; the top result has no "
                f"cached copy (has_cache != 'true'), so crawler document "
                f"caching may be off")
    return link


def _assert_cache_link_is_rendered(page, context: FessContext) -> None:
    """The cache link carries its localized text and points at cache/ with
    the result's docId plus the highlight terms."""
    title_link = _search(page, context)
    doc_id = title_link.get_attribute("data-id")

    cache_link = _cache_link(page)
    expected_text = tt(context, ThemeKeys.RESULT_CACHE)
    assert_equal(cache_link.inner_text().strip(), expected_text,
                 f"the cache link is not labelled {expected_text!r}, got "
                 f"{cache_link.inner_text().strip()!r}")

    href = cache_link.get_attribute("href")
    params = parse_qs(urlparse(href).query)
    assert_equal(urlparse(href).path, "cache/",
                 f"the cache link should address cache/, got {href}")
    assert_equal(params.get("docId"), [doc_id],
                 f"the cache link should address the result's own "
                 f"docId={doc_id}; got {href}")
    # The highlight terms are what carries the query over to the snapshot;
    # without them the highlight below cannot work.
    assert_equal(params.get("hq"), [QUERY],
                 f"the cache link dropped the highlight term hq={QUERY}; "
                 f"got {href}")
    assert_equal(cache_link.get_attribute("target"), "_blank",
                 "the cache link should open a new tab")


def _assert_snapshot_renders(page, context: FessContext) -> None:
    """Opening the link serves the snapshot: cache.hbs points <base> at the
    original document, banners it with the localized labels.search_cache_msg,
    and emits the stored copy with the hq terms wrapped in
    query.highlight.tag.pre (default <strong>)."""
    title_link = _search(page, context)
    doc_url = title_link.get_attribute("data-uri")
    href = _cache_link(page).get_attribute("href")

    # target=_blank would open a second tab; the same URL in this tab is
    # the same request, and keeps the module on the page main.py tracks.
    page.goto(context.url("/" + href))
    assert_equal(urlparse(page.url).path, "/cache/",
                 f"the cache link did not serve /cache/, landed on {page.url}")
    page.wait_for_selector(CACHE_FRAME)
    frame = page.frame_locator(CACHE_FRAME)

    base = frame.locator("base").first
    assert_equal(base.get_attribute("href"), doc_url,
                 f"cache.hbs should <base href> the original document "
                 f"{doc_url}, got {base.get_attribute('href')}")

    # ViewHelper fills {0} with the document URL and {1} with the crawl
    # timestamp. Only the {0} half is predictable, so assert up to {1}.
    banner = t(Labels.SEARCH_CACHE_MSG).split("{1}")[0].replace("{0}", doc_url)
    assert_contains(_normalize_ws(frame.locator("body").inner_text()),
                    _normalize_ws(banner),
                    f"the snapshot is missing its cache banner for "
                    f"{doc_url}; expected {_normalize_ws(banner)!r}")

    # ViewHelper.replaceHighlightQueries wraps each hq term found in the
    # stored copy's text (never inside a tag). sampledata's pages contain no
    # <strong> of their own, so any hit here came from the highlighter.
    highlighted = frame.locator("strong").all_inner_texts()
    assert_contains(highlighted, QUERY,
                    f"the snapshot did not highlight {QUERY!r}; "
                    f"<strong> texts were {highlighted}")


def _assert_not_found(page, context: FessContext, path: str) -> None:
    page.goto(context.url(path))
    alert = page.wait_for_selector(NOT_FOUND_ALERT)
    expected = tt(context, ThemeKeys.CACHE_NOT_FOUND)
    assert_equal(alert.inner_text().strip(), expected,
                 f"{path} should say {expected!r}, got "
                 f"{alert.inner_text().strip()!r}")
    assert_equal(urlparse(page.url).path, "/cache/",
                 f"{path} should stay at /cache/, got {page.url}")
    assert_true(page.query_selector(CACHE_FRAME) is None,
                f"{path} rendered a snapshot frame")


def _assert_unknown_docid_is_not_found(page, context: FessContext) -> None:
    """A docId that resolves to no stored copy."""
    _assert_not_found(page, context,
                      f"/cache/?docId={context.generate_str(20)}")


def _assert_missing_docid_is_not_found(page, context: FessContext) -> None:
    """No docId at all: cache.js does not even ask the API."""
    _assert_not_found(page, context, "/cache/")


def run(context: FessContext) -> None:
    if run_jsp_variant(context, cache_jsp):
        return
    logger.info("Starting search/cache")
    page = context.get_wrapped_page() or context.get_admin_page()

    _assert_cache_link_is_rendered(page, context)
    _assert_snapshot_renders(page, context)
    _assert_unknown_docid_is_not_found(page, context)
    _assert_missing_docid_is_not_found(page, context)

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
