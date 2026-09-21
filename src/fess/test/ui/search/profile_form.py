"""Verify /profile renders the password-change form and rejects a mismatched
confirmation.

Since fess#3460, /profile is the bootstrap static-theme SPA: profile.js
builds #password-form with #old-password / #new-password /
#confirm-password and checks new != confirm client-side, before any
request. The mismatch shows profile.error_mismatch in #profile-error and
the page stays at /profile.

NEVER submits a successful password change -- the whole suite reuses
admin/admin credentials. Nor does it submit a wrong current password: that
would reach /api/v2/auth/password, burn a login rate-limit slot, and may end
the session the rest of the suite runs on.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.search._theme import ThemeKeys, tt

logger = logging.getLogger(__name__)

OLD_PASSWORD = "admin"
NEW_PASSWORD = "Mismatch1!Aaaa"
CONFIRM_NEW_PASSWORD = "Mismatch1!Bbbb"  # intentionally != NEW_PASSWORD

FIELDS = ("#old-password", "#new-password", "#confirm-password")
SUBMIT = "#password-form button[type=submit]"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/profile_form")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/profile/"))
    # profile.js renders the form only for a logged-in user; a guest gets a
    # login prompt instead, so waiting on the form also pins the session.
    page.wait_for_selector("#password-form")

    for field in FIELDS:
        assert_true(page.is_visible(f'{field}[type="password"]'),
                    f"profile password field {field} missing on /profile")
    assert_true(page.is_visible(SUBMIT),
                f"profile submit {SUBMIT} missing on /profile")

    page.fill("#old-password", OLD_PASSWORD)
    page.fill("#new-password", NEW_PASSWORD)
    page.fill("#confirm-password", CONFIRM_NEW_PASSWORD)
    page.click(SUBMIT)

    error = page.wait_for_selector("#profile-error:not(.d-none)")
    expected = tt(context, ThemeKeys.PROFILE_ERROR_MISMATCH)
    assert_equal(error.inner_text().strip(), expected,
                 f"mismatched confirm should show {expected!r} in "
                 f"#profile-error, got {error.inner_text().strip()!r}")
    assert_true(page.is_hidden("#profile-success"),
                "mismatched confirm must not show the success message")
    assert_equal(urlparse(page.url).path.rstrip("/"), "/profile",
                 f"after mismatched-confirm submit, expected /profile, "
                 f"got {page.url}")

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
