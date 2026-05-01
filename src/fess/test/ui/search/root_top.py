"""Open / (RootAction) and assert the search form + Help header link render.

Distinct from search/top.py, which exercises /search/.
"""
import logging
import re

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


# LastaFlute renders missing labels as "???labels.x???".
_MISSING_KEY_PATTERN = re.compile(r'\?{2,}labels\.[A-Za-z0-9_.]+\?{2,}')


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/root_top")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    page.wait_for_load_state("domcontentloaded")

    assert_true(page.query_selector('input[name="q"]') is not None,
                'search input[name="q"] missing on /')
    assert_true(page.query_selector('button[name="search"]') is not None,
                'search button[name="search"] missing on /')

    # Help link is always present in the header on /.
    # AI Search link is feature-flag gated, so we don't assert it here.
    assert_true(page.query_selector('a[href="/help/"]') is not None,
                'help link a[href="/help/"] missing on /')

    body = page.inner_text("body")
    matches = _MISSING_KEY_PATTERN.findall(body)
    assert_true(len(matches) == 0,
                f"untranslated label keys on /: {matches[:5]}")

    logger.info("search/root_top completed")


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
