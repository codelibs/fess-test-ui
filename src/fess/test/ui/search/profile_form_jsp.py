"""Verify /profile/ renders the password-change form and rejects mismatched confirm.

NEVER submits a successful password change — the whole suite reuses
admin/admin credentials. The submission deliberately uses
newPassword != confirmNewPassword, which ProfileAction validates
before any persistence.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

OLD_PASSWORD = "admin"
NEW_PASSWORD = "Mismatch1!Aaaa"
CONFIRM_NEW_PASSWORD = "Mismatch1!Bbbb"  # intentionally != NEW_PASSWORD


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/profile_form")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/profile/"))
    page.wait_for_load_state("domcontentloaded")

    assert_true("/profile/" in page.url,
                f"expected /profile/ in URL, got {page.url}")
    for field in ("oldPassword", "newPassword", "confirmNewPassword"):
        assert_true(page.query_selector(f'input[name="{field}"]') is not None,
                    f'profile input[name="{field}"] missing on /profile/')
    assert_true(page.query_selector('button[name="changePassword"]') is not None,
                'profile submit button[name="changePassword"] missing on /profile/')

    # Submit with mismatched confirm. ProfileAction rejects this in
    # validatePasswordForm without writing to the user store.
    page.fill('input[name="oldPassword"]', OLD_PASSWORD)
    page.fill('input[name="newPassword"]', NEW_PASSWORD)
    page.fill('input[name="confirmNewPassword"]', CONFIRM_NEW_PASSWORD)
    page.click('button[name="changePassword"]')
    page.wait_for_load_state("domcontentloaded")

    # After validation error, ProfileAction re-renders the profile page.
    assert_true("/profile/" in page.url,
                f"after mismatched-confirm submit, expected /profile/, got {page.url}")
    # Form is still rendered (validation path, not a 5xx).
    assert_true(page.query_selector('input[name="newPassword"]') is not None,
                "after mismatched-confirm submit, profile form not re-rendered")

    logger.info("search/profile_form completed")


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
