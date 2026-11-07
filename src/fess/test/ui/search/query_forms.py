"""How the search box reads what was typed: a question mark, a wildcard,
a typo and a quoted word.

- A multi-word question typed with a trailing ? finds what the same words
  without it find, and the box keeps what was typed (fess#3571).
- A ? inside a single word is still a wildcard, not stripped punctuation.
- From Fess 15.10 an unquoted word is matched fuzzily, so a typo still finds
  the page, while the same word in quotes is exact and finds nothing
  (fess#3670).

Runs against search/seed's sample pages: "English Intro" is the title of
docs/en/intro.html.
"""
import logging
from typing import List

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.version import QUOTED_EXACT_SINCE, fess_version, skip_before_theme

logger = logging.getLogger(__name__)

HITS = "#results h3.title a.link"
ERROR_BANNER = "#search-error"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _search(page: Page, context: FessContext, query: str) -> List[str]:
    """Hit URLs for `query`, once the page has settled on hits or the empty state."""
    page.goto(context.url("/search/?q=" + query))
    page.wait_for_selector(f"{HITS}, #empty-state:not(.d-none)")
    assert_equal(page.input_value("#query"), query, f"the search box after searching for {query!r}")
    assert_true(page.is_hidden(ERROR_BANNER), f"searching for {query!r} showed an error banner")
    return sorted(a.get_attribute("data-uri") for a in page.locator(HITS).all())


def run(context: FessContext) -> None:
    if skip_before_theme(context, "search/query_forms"):
        return
    logger.info("Starting search/query_forms")
    page = context.get_wrapped_page() or context.get_admin_page()

    plain = _search(page, context, "English Intro")
    assert_true(plain, "the words of the title find nothing: is the index seeded?")
    assert_equal(_search(page, context, "English Intro?"), plain,
                 "a trailing ? after two words changes the result")

    # Falsification of the above: the ? is only dropped when it ends a
    # question. Inside a word it is a wildcard and still has to match.
    assert_true(_search(page, context, "intr?"), "intr? matches nothing: the wildcard was stripped")

    if fess_version(context) >= QUOTED_EXACT_SINCE:
        assert_true(_search(page, context, "introo"), "an unquoted typo finds nothing")
        assert_equal(_search(page, context, '"introo"'), [], 'the quoted typo "introo" still matches')
        assert_true(_search(page, context, '"intro"'), 'the quoted exact word "intro" finds nothing')

    logger.info("search/query_forms completed")


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
