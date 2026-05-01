"""Verify the search form submits via UI: fill q on / and click search → /search/?q=...

Existing search/* modules construct the URL directly. This module exercises
the GET-form action wiring so a regression in form submission would surface.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "a"  # single-character query — locale-neutral, always submittable.


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/form_submit")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    page.wait_for_load_state("domcontentloaded")

    page.fill('input[name="q"]', QUERY)
    page.click('button[name="search"]')
    page.wait_for_load_state("domcontentloaded")

    assert_true("/search/" in page.url,
                f"after form submit, expected /search/ in URL, got {page.url}")
    assert_true(f"q={QUERY}" in page.url,
                f"after form submit, expected q={QUERY} in URL, got {page.url}")

    # Page rendered without raising — body text just has to be non-empty.
    body_text = page.inner_text("body")
    assert_true(len(body_text.strip()) > 0,
                "/search/ after form submit rendered an empty body")

    logger.info("search/form_submit completed")


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
