"""Run a query with >10 hits and verify pagination works."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_contains
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "page"
PAGE_SIZE = 10


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/pagination")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url(f"/search/?q={QUERY}&num={PAGE_SIZE}"))
    page.wait_for_load_state("domcontentloaded")

    pagination = page.query_selector("ul.pagination")
    assert_true(pagination is not None,
                f"expected ul.pagination for q={QUERY} num={PAGE_SIZE} (>{PAGE_SIZE} hits required)")

    next_link = page.query_selector('a[href*="/search/next"]')
    assert_true(next_link is not None, "next-page link missing")

    next_link.click()
    page.wait_for_load_state("domcontentloaded")
    # Fess 15 stays at /search/next/?pn=1 URL; verify page 2 is active in pagination
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
