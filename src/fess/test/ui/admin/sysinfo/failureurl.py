"""Verify /admin/failureurl/ page renders with expected structure."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

PAGE_URL = "/admin/failureurl/"
EXPECTED_MARKERS = ["エラー回数", "種別"]


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting failureurl")
    page = context.get_admin_page()
    page.goto(context.url(PAGE_URL))
    page.wait_for_load_state("domcontentloaded")

    body = page.inner_text("body")
    matched = [m for m in EXPECTED_MARKERS if m in body]
    assert_true(len(matched) > 0,
                f"none of {EXPECTED_MARKERS} found in body; first 300 chars: {body[:300]}")

    logger.info(f"failureurl completed (matched: {matched})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
