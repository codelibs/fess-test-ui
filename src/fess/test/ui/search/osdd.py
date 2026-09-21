"""Verify the OpenSearch description document is advertised and served.

Two halves that can regress independently: the top page must advertise the
document with a <link rel="search">, and OsddAction must actually serve it at
the advertised href.

Since fess#3460, / is the bootstrap static-theme SPA: search.js adds the
<link rel="search"> to <head> once /api/v2/ui/config has answered, with a
relative href ("osdd", resolved against the <base href> Fess injects) and the
site name from that config as its title.

/osdd is behind the loginRequired gate (OsddAction.java:57), so this must not
run while a test has the UI closed to anonymous users. In the default order
that test (general/loginRequired) runs last, after every search module.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

OSDD_LINK = 'link[rel="search"][type="application/opensearchdescription+xml"]'
OSDD_PATH = "/osdd"
# /osdd 301s to /osdd/, so this is where the fetch actually lands.
OSDD_SERVED_PATH = "/osdd/"
# The OpenSearch 1.1 spec namespace: what makes the document an OSDD at all.
OSDD_NAMESPACE = "http://a9.com/-/spec/opensearch/1.1/"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _assert_top_page_advertises_osdd(page, context: FessContext) -> str:
    """The search top page must carry the <link rel="search"> discovery tag.
    Returns the path its href resolves to."""
    with page.expect_response(lambda r: "/api/v2/ui/config" in r.url) as info:
        page.goto(context.url("/"))
    # search.js falls back to "Fess" when the config names no site.
    site_name = info.value.json()["response"].get("site_name") or "Fess"

    # A <link> in <head> is never visible, so wait for it to be attached.
    link = page.wait_for_selector(OSDD_LINK, state="attached")

    href = urlparse(link.evaluate("l => l.href")).path
    assert_equal(href, OSDD_PATH,
                 f"OSDD link resolves somewhere unexpected: {href!r}")
    # The title is the site name the SPA got from /api/v2/ui/config.
    assert_equal(link.get_attribute("title"), site_name,
                 "OSDD link title is not the configured site name")
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

    assert_equal(response.status, 200,
                 f"{href} answered HTTP {response.status}")
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
