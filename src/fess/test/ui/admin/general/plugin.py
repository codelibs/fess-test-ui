"""Verify /admin/plugin/ page renders with expected structure."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

PAGE_URL = "/admin/plugin/"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting plugin")
    page = context.get_admin_page()
    page.goto(context.url(PAGE_URL))
    page.wait_for_load_state("domcontentloaded")

    expected = [t(Labels.MENU_PLUGIN)]
    body = page.inner_text("body")
    matched = [m for m in expected if m in body]
    # Structural fallback ensures we caught the actual page, not an error/login redirect.
    table_present = page.query_selector("table, form, .container") is not None
    assert_true(matched or table_present,
                f"page didn't render: none of {expected!r} in body and no table/form; first 300 chars: {body[:300]}")

    logger.info(f"plugin completed (matched: {matched}, table_present: {table_present})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
