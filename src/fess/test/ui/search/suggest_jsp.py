"""Type partial text into the search box and verify the page remains functional.

Suggest is an async dropdown populated from search history and admin suggest
dict. On a fresh stack the dict is empty; this test therefore asserts DOM
integrity (input still exists, page did not crash) rather than dropdown
content."""
import logging
import time

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/suggest")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/search/"))
    page.wait_for_load_state("domcontentloaded")

    page.click("input[name=\"q\"]")
    page.fill("input[name=\"q\"]", "")
    page.type("input[name=\"q\"]", "int", delay=100)

    time.sleep(3)

    dropdown = (page.query_selector(".suggestor-result")
                or page.query_selector(".suggest-result")
                or page.query_selector("ul.dropdown-menu.show"))
    if dropdown is None:
        logger.warning("suggest dropdown not present — suggest dict may be empty; "
                       "DOM integrity is OK as long as the input still exists")
    else:
        logger.info(f"suggest dropdown found")

    assert_true(page.query_selector("input[name=\"q\"]") is not None,
                "search input disappeared after typing")

    logger.info("search/suggest completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try: run(ctx)
        finally: destroy(ctx)
