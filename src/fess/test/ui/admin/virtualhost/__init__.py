"""Virtual host settings are a single textarea on /admin/general/, not a CRUD
resource. This module fills the textarea with a test rule, saves, verifies
persistence on reload, and restores the original value in a finally clause so
the test is idempotent and leaves no trace."""
import logging

from fess.test import assert_contains, assert_equal
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

FIELD_NAME = "virtualHostValue"
TEST_RULE = "Host:e2e-test:8080=e2e-host"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting virtualhost test")
    page = context.get_admin_page()

    page.goto(context.url("/admin/general/"))
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/general/"))

    original = page.input_value(f"textarea[name=\"{FIELD_NAME}\"]")
    logger.debug(f"original virtualhost value length: {len(original)}")

    try:
        new_value = (original + "\n" if original else "") + TEST_RULE
        page.fill(f"textarea[name=\"{FIELD_NAME}\"]", new_value)
        page.click("button:has-text(\"更新\")")
        page.wait_for_load_state("domcontentloaded")

        # Re-open and verify persistence
        page.goto(context.url("/admin/general/"))
        page.wait_for_load_state("domcontentloaded")
        persisted = page.input_value(f"textarea[name=\"{FIELD_NAME}\"]")
        assert_contains(persisted, TEST_RULE,
                        f"TEST_RULE not in virtualhost textarea after save; got first 200 chars: {persisted[:200]}")
    finally:
        # Restore original value no matter what happened above
        try:
            page.goto(context.url("/admin/general/"))
            page.wait_for_load_state("domcontentloaded")
            page.fill(f"textarea[name=\"{FIELD_NAME}\"]", original)
            page.click("button:has-text(\"更新\")")
            page.wait_for_load_state("domcontentloaded")
            logger.info("virtualhost value restored")
        except Exception as e:
            logger.warning(f"virtualhost restore failed (continuing): {e}")

    logger.info("virtualhost test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
