"""Type partial text into the home search box and verify the suggest wiring.

Since fess#3460, / and /search are the bootstrap static-theme SPA. /search
without q sends the visitor back to the home view, so the home box
(#contentQuery) is where a user first types. search.js debounces the input
and asks /api/v2/suggest-words for the prefix; the answer fills
#home-suggest-dropdown, which is shown only when there is something to show.

On a fresh stack the suggest index is empty (it is built from search logs and
documents by a scheduled job the suite never runs), so the dropdown content is
not guaranteed. What is guaranteed, and asserted, is that typing issues the
suggest request for the typed prefix and that the dropdown agrees with the
answer: visible with every returned word when there are words, hidden when
there are none.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

PREFIX = "int"
DROPDOWN = "#home-suggest-dropdown"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/suggest")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/search/"))
    page.wait_for_selector("#home-view:not([hidden])")
    assert_equal(urlparse(page.url).path, "/",
                 f"/search/ without q should return to the home view, "
                 f"got {page.url}")

    page.click("#contentQuery")
    page.fill("#contentQuery", "")
    with page.expect_response(
            lambda r: "/api/v2/suggest-words?" in r.url
            and parse_qs(urlparse(r.url).query).get("q") == [PREFIX]) as info:
        page.type("#contentQuery", PREFIX, delay=100)
    response = info.value
    assert_equal(response.status, 200,
                 f"suggest request {response.url} answered HTTP {response.status}")
    words = [w.get("text", "") for w in
             response.json()["response"]["suggest_words"]]
    logger.info(f"suggest words for {PREFIX!r}: {words}")

    if words:
        page.wait_for_selector(f"{DROPDOWN}:not(.d-none)")
        shown = page.inner_text(DROPDOWN)
        for word in words:
            assert_contains(shown, word,
                            f"suggest word {word!r} missing from {DROPDOWN}")
    else:
        # Let the render that follows the response settle before asserting
        # the dropdown stayed closed.
        page.wait_for_timeout(500)
        assert_true(page.is_hidden(DROPDOWN),
                    f"{DROPDOWN} is shown although the suggest answer is empty")

    assert_equal(page.input_value("#contentQuery"), PREFIX,
                 "the home search box lost the typed text")

    logger.info("search/suggest completed")


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
