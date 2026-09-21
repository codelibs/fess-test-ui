"""Verify the search form submits via UI: fill q on / and click search -> /search?q=...

Existing search/* modules construct the URL directly. This module exercises
the form wiring so a regression in form submission would surface.

Since fess#3460, / is the bootstrap static-theme SPA. The home form
(#contentQuery / #home-search-submit) does not GET a page: search.js
pushState()s to /search?q=... and renders #results-view in place, so the
checks wait for the URL and the view rather than for a page load.
"""
import logging
import re
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "a"  # single-character query — locale-neutral, always submittable.


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/form_submit")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    page.wait_for_selector("#home-view:not([hidden])")

    # The header form's input[name=q] precedes the home one in the DOM and is
    # hidden on the home view, so address the home copy by id.
    page.fill("#contentQuery", QUERY)
    with page.expect_response(lambda r: "/api/v2/search?" in r.url) as searched:
        page.click("#home-search-submit")
    page.wait_for_url(re.compile(r"/search\?(.*&)?q=" + re.escape(QUERY) + r"(&|$)"))
    page.wait_for_selector("#results-view")

    assert_equal(searched.value.status, 200,
                 f"the submitted search failed: {searched.value.url} answered "
                 f"HTTP {searched.value.status}")
    assert_equal(parse_qs(urlparse(searched.value.url).query).get("q"), [QUERY],
                 f"the search request did not carry q={QUERY}: "
                 f"{searched.value.url}")

    landed = urlparse(page.url)
    assert_equal(landed.path, "/search",
                 f"after form submit, expected /search, got {page.url}")
    assert_equal(parse_qs(landed.query).get("q"), [QUERY],
                 f"after form submit, expected q={QUERY} in URL, got {page.url}")
    assert_true(page.is_hidden("#home-view"),
                "the home view is still shown after the search was submitted")

    logger.info("search/form_submit completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
