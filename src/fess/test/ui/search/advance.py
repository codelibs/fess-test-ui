"""Exercise /search/advance: fill the advanced-search fields, submit, and assert
the query the form assembled from them.

Since fess#3460, /search/advance is the bootstrap static-theme SPA. The form
fields carry ids, not the JSP's as.* names, and advance.js compose()
assembles the query client-side, then pushState()s to /search?q=<query>. So
the q parameter of the URL it lands on is the assembly's observable output
(the SPA also copies it into the header #query box).

Asserts only on that query round-trip, never on hit counts, so it needs no
crawled data. The expected values are exact and follow compose() term for
term: the quoting of the exact phrase, the NOT prefixing of the excluded
words, site: before filetype:"...", and the allintitle: prefix glued to the
first term.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt

logger = logging.getLogger(__name__)

ALL_WORDS = "alpha"
EXACT_PHRASE = "beta gamma"
NONE_WORDS = "delta"
SITE = "example.com"

# Every field the form is expected to expose. Renaming or dropping one in
# advance.js turns the corresponding assertion red.
TEXT_FIELDS = ("#adv-all", "#adv-exact", "#adv-any", "#adv-none", "#adv-site")
SELECT_FIELDS = ("#adv-filetype", "#adv-occt", "#adv-time", "#adv-lang",
                 "#adv-num", "#adv-sort")
SUBMIT = "#advance-form button[type=submit]"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _open_advance(page, context: FessContext) -> None:
    page.goto(context.url("/search/advance"))
    # advance.js builds the form once the SPA has its config; the view is
    # hidden until then.
    page.wait_for_selector("#advance-form")
    # Compare the parsed path, not a substring of the whole URL: an unrouted
    # path is rendered in place too (ErrorPageServlet), so the URL alone
    # cannot tell the views apart -- the #advance-form wait above and the
    # heading check in _assert_form_contract do that.
    assert_equal(urlparse(page.url).path.rstrip("/"), "/search/advance",
                 f"expected /search/advance, got {page.url}")


def _submit_and_read_query(page) -> str:
    """Submit the form and return the q it navigated to (None when absent)."""
    page.click(SUBMIT)
    page.wait_for_url(lambda url: urlparse(url).path.rstrip("/") != "/search/advance")
    return (parse_qs(urlparse(page.url).query).get("q") or [None])[0]


def _assert_form_contract(page, context: FessContext) -> None:
    heading = page.inner_text("#advance-view h2").strip()
    assert_equal(heading, tt(context, ThemeKeys.ADVANCE_TITLE),
                 f"#advance-view does not carry the advanced-search heading; "
                 f"got {heading!r}")
    for field in TEXT_FIELDS:
        assert_true(page.query_selector(f"input{field}") is not None,
                    f"advance form is missing input{field}")
    for field in SELECT_FIELDS:
        assert_true(page.query_selector(f"select{field}") is not None,
                    f"advance form is missing select{field}")


def _assert_words_are_assembled(page, context: FessContext) -> None:
    """all + exact + none -> `alpha "beta gamma" NOT delta`."""
    _open_advance(page, context)
    page.fill("#adv-all", ALL_WORDS)
    page.fill("#adv-exact", EXACT_PHRASE)
    page.fill("#adv-none", NONE_WORDS)
    query = _submit_and_read_query(page)

    # Parsed path, not a substring: a URL that merely mentions /search in a
    # parameter would satisfy a substring test.
    assert_equal(urlparse(page.url).path, "/search",
                 f"expected /search after submit, got {page.url}")
    # Exact, not a substring check: this pins the quoting of the phrase and
    # the NOT prefixing, either of which could regress independently while
    # every loose `in` assertion stayed green.
    assert_equal(query, f'{ALL_WORDS} "{EXACT_PHRASE}" NOT {NONE_WORDS}',
                 f"assembled query mismatch at {page.url}")


def _assert_operators_are_assembled(page, context: FessContext) -> None:
    """all + occt + filetype + site ->
    `allintitle:alpha site:example.com filetype:"pdf"`."""
    _open_advance(page, context)
    page.fill("#adv-all", ALL_WORDS)
    page.fill("#adv-site", SITE)
    page.select_option("#adv-filetype", "pdf")
    page.select_option("#adv-occt", "allintitle")
    query = _submit_and_read_query(page)

    # compose() emits site: before filetype: and prefixes the whole string
    # with allintitle: (no space) once the rest is assembled.
    assert_equal(query, f'allintitle:{ALL_WORDS} site:{SITE} filetype:"pdf"',
                 f"assembled query mismatch at {page.url}")


def _assert_occurrence_alone_is_a_noop(page, context: FessContext) -> None:
    """The occurrence select on its own must not run a search.

    compose() only prefixes allintitle: onto a non-empty query, so with every
    other field blank the form navigates to /search with no q, and the
    results route sends a q-less visit back to the root.
    """
    _open_advance(page, context)
    page.select_option("#adv-occt", "allintitle")
    page.click(SUBMIT)
    page.wait_for_selector("#home-view")

    landed = urlparse(page.url)
    assert_equal(landed.path, "/",
                 f"the occurrence select alone should land on the root, "
                 f"got {page.url}")
    assert_true("q" not in parse_qs(landed.query),
                f"the root should carry no query, got {page.url}")


def run(context: FessContext) -> None:
    logger.info("Starting search/advance")
    page = context.get_wrapped_page() or context.get_admin_page()

    _open_advance(page, context)
    _assert_form_contract(page, context)

    _assert_words_are_assembled(page, context)
    _assert_operators_are_assembled(page, context)
    _assert_occurrence_alone_is_a_noop(page, context)

    logger.info("search/advance completed")


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
