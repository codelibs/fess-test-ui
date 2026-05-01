"""Verify /login/ renders the form and surfaces a validation/error response on empty submit.

Uses a fresh, unauthenticated Playwright BrowserContext so an
already-logged-in suite session does not redirect /login/ to /.
"""
import logging
import os

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    # Reuse the suite-wide login/teardown plumbing so tracing/screenshots work,
    # but the actual login_form test below opens its own ephemeral context.
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/login_form")

    base_url = os.environ.get("FESS_URL", "http://localhost:8080")
    fresh_browser = context._playwright.chromium.launch(
        headless=os.environ.get("HEADLESS", "false").lower() == "true",
        slow_mo=500,
    )
    try:
        fresh_ctx = fresh_browser.new_context(locale=context.browser_locale)
        try:
            page = fresh_ctx.new_page()
            page.goto(f"{base_url}/login/?browser_lang={context.lang}")
            page.wait_for_load_state("domcontentloaded")

            assert_true("/login/" in page.url,
                        f"expected /login/ in URL, got {page.url}")
            assert_true(page.query_selector('input[name="username"]') is not None,
                        'login input[name="username"] missing on /login/')
            assert_true(page.query_selector('input[name="password"]') is not None,
                        'login input[name="password"] missing on /login/')
            assert_true(page.query_selector('button[name="login"]') is not None,
                        'login button[name="login"] missing on /login/')

            # Empty submit: the inputs do not have HTML5 `required`, so the form
            # actually POSTs. Server-side validation should keep us on /login/
            # and re-render the form.
            page.click('button[name="login"]')
            page.wait_for_load_state("domcontentloaded")

            assert_true("/login/" in page.url,
                        f"after empty submit, expected to stay on /login/, got {page.url}")
            assert_true(page.query_selector('input[name="username"]') is not None,
                        "after empty submit, login form not re-rendered")
        finally:
            fresh_ctx.close()
    finally:
        fresh_browser.close()

    logger.info("search/login_form completed")


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
