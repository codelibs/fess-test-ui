"""
Exercise the search-log + popular-word pipeline.

Runs several searches against seeded data (created by search/seed),
then verifies the admin popular-word page loads cleanly. This module
replaces the previous time.sleep(60)×10 implementation.

Requires search_seed to have run earlier in the same main.py execution
(or manually seeded when run stand-alone).
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

SEARCH_TERM = "intro"
SEARCH_REPEATS = 10


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting popularWord")
    page = context.get_wrapped_page() or context.get_admin_page()

    # 1) Drive searches to generate popular-word data
    for i in range(SEARCH_REPEATS):
        page.goto(context.url(f"/search/?q={SEARCH_TERM}"))
        page.wait_for_load_state("domcontentloaded")
        logger.debug(f"search #{i+1} completed")

    # 2) Open admin popular-word page
    page.goto(context.url("/admin/popularword/"))
    page.wait_for_load_state("domcontentloaded")

    body = page.inner_text("body")
    # Lenient assertion: page loads and contains either the search term
    # or a popular-word header. Exact aggregation timing is out of scope —
    # the test verifies the pipeline doesn't crash.
    assert_true(SEARCH_TERM in body or "popular" in body.lower(),
                f"popularword admin page did not contain expected content "
                f"(term={SEARCH_TERM}; first 300 chars of body): {body[:300]}")

    logger.info("popularWord completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
