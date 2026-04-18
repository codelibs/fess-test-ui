"""Open /search/ (front page) and assert the search form is present."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/top")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/search/"))
    page.wait_for_load_state("domcontentloaded")

    assert_true(page.query_selector("input[name=\"q\"]") is not None,
                "search input[name=\"q\"] missing on /search/")
    assert_true(page.query_selector("button[name=\"search\"]") is not None,
                "search button[name=\"search\"] missing on /search/")

    logger.info("search/top completed")


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
