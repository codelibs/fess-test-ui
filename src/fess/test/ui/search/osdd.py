"""Verify the OpenSearch description document is advertised and served.

Two halves that can regress independently: index.jsp:8-12 only emits the
<link rel="search"> when ${osddLink} is set (osdd.link.enabled=auto plus
sso.type=none makes isOsddLinkEnabled() true by default), and OsddAction
must actually serve the document at the advertised href.

/osdd is behind the loginRequired gate (OsddAction.java:57), so this must not
run while a test has the UI closed to anonymous users. In the default order
that test (general/loginRequired) runs last, after every search module.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

OSDD_LINK = 'link[rel="search"][type="application/opensearchdescription+xml"]'
OSDD_HREF = "/osdd"
# /osdd 301s to /osdd/, so this is where the fetch actually lands.
OSDD_SERVED_PATH = "/osdd/"
# The OpenSearch 1.1 spec namespace: what makes the document an OSDD at all.
OSDD_NAMESPACE = "http://a9.com/-/spec/opensearch/1.1/"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _assert_top_page_advertises_osdd(page, context: FessContext) -> str:
    """The search top page must carry the <link rel="search"> discovery tag."""
    page.goto(context.url("/"))
    page.wait_for_load_state("domcontentloaded")

    link = page.query_selector(OSDD_LINK)
    assert_true(link is not None,
                "top page is missing the OSDD <link rel=\"search\"> tag")

    href = link.get_attribute("href")
    assert_equal(href, OSDD_HREF,
                 f"OSDD link points somewhere unexpected: {href!r}")
    # The tag's title is localized (labels.index_osdd_title), so it is also a
    # check that the head renders in the session locale, not a fixed language.
    assert_equal(link.get_attribute("title"), t(Labels.INDEX_OSDD_TITLE),
                 "OSDD link title is not the localized label")
    return href


def _assert_osdd_document_is_served(page, context: FessContext, href: str) -> None:
    """Following the advertised href must yield the XML document itself.

    Fetched rather than navigated to: OsddHelper.asStream() sends
    `Content-Disposition: attachment`, so page.goto() would start a download
    instead of a navigation and raise. page.request reuses this browser
    context's cookies, so the loginRequired gate is exercised as the UI sees
    it. /osdd 301s to /osdd/; the request follows that redirect.
    """
    response = page.request.get(context.url(href))

    # Deliberately not an HTTP status assertion. An /osdd that resolved to
    # nothing would redirect to /error/notfound/, which Fess answers with 200,
    # and page.request follows redirects -- so `status == 200` would still pass
    # with the endpoint gone. The landing URL is what tells the two apart.
    assert_equal(urlparse(response.url).path, OSDD_SERVED_PATH,
                 f"{href} did not serve the OSDD; landed on {response.url}")

    headers = response.headers
    content_type = headers.get("content-type", "")
    assert_contains(content_type, "text/xml",
                    f"OSDD served as {content_type!r}, expected text/xml")
    assert_contains(headers.get("content-disposition", ""), "osdd.xml",
                    "OSDD is not offered under its osdd.xml filename")

    body = response.text()
    assert_contains(body, OSDD_NAMESPACE,
                    "OSDD body is not an OpenSearch 1.1 description document")
    assert_contains(body, "<ShortName>",
                    "OSDD body has no <ShortName> element")


def run(context: FessContext) -> None:
    logger.info("Starting search/osdd")
    page = context.get_wrapped_page() or context.get_admin_page()

    href = _assert_top_page_advertises_osdd(page, context)
    _assert_osdd_document_is_served(page, context, href)

    logger.info("search/osdd completed")


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
