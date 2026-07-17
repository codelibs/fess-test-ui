"""Verify /logout/ ends the session and redirects to the login page.

LogoutAction calls fessLoginAssist.logout() and then redirect(LoginAction),
so there are two separable things to check: that we land on /login/, and that
the session is genuinely gone. Landing on /login/ alone would still pass if
logout() stopped invalidating anything, so the test re-requests an
authenticated-only page afterwards and requires it to bounce.

Runs in its own browser context: the suite shares ONE logged-in FessContext
across every module, and logging that session out would break every module
scheduled after this one. Same reason search/login_form.py opens its own.

Only reached when sso.type=none (the default), where the redirect target is
always LoginAction. The fsid cookie that deleteUserCodeFromCookie clears is
deliberately not asserted on: Fess only sets it once a user code exists, so
on a fresh session there is nothing to delete and the call is a no-op.
"""
import logging
import os
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_startswith
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

ADMIN_PATH = "/admin/"
LOGIN_PATH = "/login/"
LOGOUT_PATH = "/logout/"


def setup(playwright: Playwright) -> FessContext:
    # Reuse the suite-wide login/teardown plumbing so tracing/screenshots work,
    # but the logout test below opens its own ephemeral context.
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _login(page, base_url: str, lang: str) -> None:
    page.goto(f"{base_url}{LOGIN_PATH}?browser_lang={lang}")
    page.wait_for_load_state("domcontentloaded")
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]',
              os.environ.get("FESS_USERNAME", "admin"))
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_PASSWORD)}"]',
              os.environ.get("FESS_PASSWORD", "admin"))
    page.click(f'button:has-text("{t(Labels.LOGIN)}")')
    page.wait_for_load_state("domcontentloaded")


def _goto_path(page, base_url: str, path: str) -> str:
    page.goto(f"{base_url}{path}")
    page.wait_for_load_state("domcontentloaded")
    return urlparse(page.url).path


def run(context: FessContext) -> None:
    logger.info("Starting search/logout")

    base_url = os.environ.get("FESS_URL", "http://localhost:8080")
    fresh_browser = context._playwright.chromium.launch(
        headless=os.environ.get("HEADLESS", "false").lower() == "true",
        slow_mo=500,
    )
    try:
        fresh_ctx = fresh_browser.new_context(locale=context.browser_locale)
        try:
            page = fresh_ctx.new_page()
            _login(page, base_url, context.lang)

            # Anonymous /admin/ redirects to /login/, so reaching the admin UI
            # proves the session this test is about to log out exists. An
            # authenticated /admin/ lands on /admin/dashboard/, hence the
            # prefix rather than an exact match.
            assert_startswith(_goto_path(page, base_url, ADMIN_PATH), ADMIN_PATH,
                              f"login did not establish a session; got {page.url}")

            assert_equal(_goto_path(page, base_url, LOGOUT_PATH), LOGIN_PATH,
                         f"logout did not redirect to {LOGIN_PATH}; got {page.url}")

            # The assertion that makes this test worth running: the session is
            # invalidated, not merely navigated away from.
            assert_equal(_goto_path(page, base_url, ADMIN_PATH), LOGIN_PATH,
                         f"session survived logout: {ADMIN_PATH} still reachable "
                         f"at {page.url}")
        finally:
            fresh_ctx.close()
    finally:
        fresh_browser.close()

    logger.info("search/logout completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        ctx = setup(playwright)
        try:
            run(ctx)
        finally:
            destroy(ctx)
