"""Open /help/ (HelpAction) and assert the search form + a non-empty body render."""
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
    logger.info("Starting search/help")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/help/"))
    page.wait_for_load_state("domcontentloaded")

    # If HelpAction redirected to /login/, isLoginRequired() is misconfigured for
    # this run — surface it as a failure rather than silently skipping.
    assert_true("/help/" in page.url,
                f"expected /help/ in URL after navigation, got {page.url}")

    assert_true(page.query_selector('input[name="q"]') is not None,
                'search input[name="q"] missing on /help/')
    assert_true(page.query_selector('button[name="search"]') is not None,
                'search button[name="search"] missing on /help/')

    # Body must render some content beyond an empty shell.
    body_text = page.inner_text("body")
    assert_true(len(body_text.strip()) > 0,
                "/help/ rendered an empty body")

    logger.info("search/help completed")


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
