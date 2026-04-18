"""Verify pagination works with a query that returns enough hits to paginate.

The test queries the JSON API for an authoritative hit count first, then
chooses a page size that guarantees multiple pages. This keeps the test
robust across Fess/OpenSearch combinations where default analyzers tokenize
content differently (observed: `q=page` returns 23 hits on OpenSearch 2 but
≤10 hits on OpenSearch 3 because of analyzer differences)."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_contains
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "*"
MIN_HITS = 12


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/pagination")

    body = context.api_get(f"/api/v1/documents?q={QUERY}&size=0")
    total = int(body.get("record_count") or body.get("total_count") or 0)
    logger.info(f"total hits for q={QUERY}: {total}")
    assert_true(total >= MIN_HITS,
                f"need >={MIN_HITS} hits for pagination test, got {total}")

    page_size = max(3, total // 4)
    logger.info(f"chosen page_size={page_size} (expecting ~{total // page_size} pages)")

    page = context.get_wrapped_page() or context.get_admin_page()
    page.goto(context.url(f"/search/?q={QUERY}&num={page_size}"))
    page.wait_for_load_state("domcontentloaded")

    pagination = page.query_selector("ul.pagination")
    assert_true(pagination is not None,
                f"expected ul.pagination for q={QUERY} num={page_size} total={total}")

    next_link = page.query_selector('a[href*="/search/next"]')
    assert_true(next_link is not None,
                f"next-page link missing (total={total}, page_size={page_size})")

    next_link.click()
    page.wait_for_load_state("domcontentloaded")
    active = page.query_selector("li.page-item.active a")
    assert_true(active is not None, "active page item missing after next click")
    active_href = active.get_attribute("href") or ""
    assert_contains(active_href, "pn=2",
                    f"expected pn=2 in active page link after next click, got href={active_href}")

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
