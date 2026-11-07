"""The URL is the state of the search page: Back, Forward, reload and deep
links all land on the same view.

- Searching "intro" and then "guide" from the header box and pressing Back
  and Forward restores each URL, the value in the search box and the hits.
- A deep link carrying num and sort comes back with the same two selects
  after a reload.

The header Search button is disabled for 3 seconds after a submit, which
also blocks Enter in the box, so the second search waits that out.
"""
import logging
from typing import List
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.version import skip_before_theme

logger = logging.getLogger(__name__)

HITS = "#results h3.title a.link"
SUBMIT_LOCK_MS = 3200


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _hits(page: Page) -> List[str]:
    return sorted(a.get_attribute("data-uri") for a in page.locator(HITS).all())


def _query_of(page: Page) -> str:
    return parse_qs(urlparse(page.url).query).get("q", [""])[0]


def _settled_on(page: Page, query: str) -> List[str]:
    """Wait until the page shows `query` (URL, box and hits) and return the hits."""
    page.wait_for_function(
        "q => new URL(location.href).searchParams.get('q') === q && "
        "document.querySelector('#query').value === q", arg=query)
    page.wait_for_selector(HITS)
    return _hits(page)


def run(context: FessContext) -> None:
    if skip_before_theme(context, "search/history"):
        return
    logger.info("Starting search/history")
    with context.guest_page() as page:
        _back_and_forward(page, context)
        _deep_link(page, context)
    logger.info("search/history completed")


def _back_and_forward(page: Page, context: FessContext) -> None:
    page.goto(context.url("/search/?q=intro"))
    first = _settled_on(page, "intro")
    page.wait_for_timeout(SUBMIT_LOCK_MS)
    page.fill("#query", "guide")
    page.press("#query", "Enter")
    second = _settled_on(page, "guide")
    assert_true(first and second and first != second,
                f"intro and guide should find different pages: {first} / {second}")

    page.go_back()
    assert_equal(_settled_on(page, "intro"), first, "the hits after Back")
    page.go_forward()
    assert_equal(_settled_on(page, "guide"), second, "the hits after Forward")


def _deep_link(page: Page, context: FessContext) -> None:
    page.goto(context.url("/search/?q=intro&num=20&sort=filename.desc"))
    page.wait_for_selector(HITS)
    for step in ("deep link", "reload"):
        if step == "reload":
            page.reload()
            page.wait_for_selector(HITS)
        assert_equal(_query_of(page), "intro", f"q after the {step}")
        assert_equal(page.input_value("#numSearchOption"), "20", f"num select after the {step}")
        assert_equal(page.input_value("#sortSearchOption"), "filename.desc",
                     f"sort select after the {step}")


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
