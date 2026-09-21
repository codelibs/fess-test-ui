"""Verify pagination works with a query that returns enough hits to paginate.

The test queries the JSON API for an authoritative hit count first, then
chooses a page size that guarantees multiple pages. This keeps the test
robust across Fess/OpenSearch combinations where default analyzers tokenize
content differently (observed: `q=page` returns 23 hits on OpenSearch 2 but
<=10 hits on OpenSearch 3 because of analyzer differences).

Since fess#3460, /search is the bootstrap static-theme SPA. Its pager
(#pagination) is a list of `a.page-link href="#"` driven by click handlers
that re-run /api/v2/search with start=<offset>, so a page turn is observed
through that request and the re-rendered results, not a page load.

The last check -- that the URL records the new page as start=<page_size> --
pins codelibs/fess#3463: before it, paging left the URL unchanged (reload /
share / back lost the page). It runs last so the checks before it still
report on a Fess without that fix.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_not_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "*"
MIN_HITS = 12

PAGER = "#pagination"
# The pager ends with the Next item; its label is localized, its position
# is not.
NEXT_LINK = f"{PAGER} li.page-item:last-child a.page-link"
ACTIVE_ITEM = f"{PAGER} li.page-item.active"
FIRST_RESULT = "#result0 h3.title a.link"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/pagination")

    total = context.api_search(QUERY)["record_count"]
    logger.info(f"total hits for q={QUERY}: {total}")
    assert_true(total >= MIN_HITS,
                f"need >={MIN_HITS} hits for pagination test, got {total}")

    page_size = max(3, total // 4)
    logger.info(f"chosen page_size={page_size} (expecting ~{total // page_size} pages)")

    page = context.get_wrapped_page() or context.get_admin_page()
    page.goto(context.url(f"/search/?q={QUERY}&num={page_size}"))
    page.wait_for_selector(FIRST_RESULT)
    page.wait_for_selector(ACTIVE_ITEM)
    assert_equal(page.inner_text(ACTIVE_ITEM).strip(), "1",
                 f"expected page 1 to be active for q={QUERY} num={page_size} "
                 f"total={total}")
    first_on_page1 = page.get_attribute(FIRST_RESULT, "data-id")

    with page.expect_response(lambda r: "/api/v2/search?" in r.url) as info:
        page.click(NEXT_LINK)
    requested = parse_qs(urlparse(info.value.url).query)
    assert_equal(requested.get("start"), [str(page_size)],
                 f"Next should request start={page_size}, "
                 f"got {info.value.url}")

    page.wait_for_function(
        "([sel, before]) => { const a = document.querySelector(sel);"
        " return a && a.dataset.id !== before; }",
        arg=[FIRST_RESULT, first_on_page1])
    assert_equal(page.inner_text(ACTIVE_ITEM).strip(), "2",
                 "expected page 2 to be active after the Next click")
    assert_not_equal(page.get_attribute(FIRST_RESULT, "data-id"), first_on_page1,
                     "the first result did not change after the Next click")

    # Pending fix: paging must record the page in the URL (see docstring).
    landed = parse_qs(urlparse(page.url).query)
    assert_equal(landed.get("start"), [str(page_size)],
                 f"after paging, the URL should carry start={page_size}; "
                 f"got {page.url}")

    logger.info("search/pagination completed")


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
