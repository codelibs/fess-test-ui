"""Log level is a select on /admin/general/.

This test verifies the form round-trip ONLY, and that is deliberate:
SystemHelper.setLogLevel() sets a JVM system property and calls Log4j's
Configurator.setLevel(). It is never persisted (not to system.properties, not
to the config index) and has no effect any HTTP client can observe, so there is
no honest way to assert "the log level changed" from here. What is observable
is that AdminGeneralAction.updateForm() repopulates the select from
SystemHelper.getLogLevel(), so saving a level and re-reading the page proves
the value reached the JVM and came back. Nothing here verifies that anything is
actually logged at the selected level.

Fess rounds an unknown level silently to WARN (Level.toLevel(level, WARN)), so
only values from the select's own option list are used.
"""
import logging

from fess.test import assert_equal
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)

GENERAL_PATH = "/admin/general/"
FIELD = "#logLevel"
# The save button is selected by element name, not label: the page carries a
# second submit button (name="sendmail") and `has-text` matches substrings, so
# the name attribute is the unambiguous, locale-independent choice.
SAVE_BUTTON = 'button[name="update"]'

# admin_general.jsp offers OFF/FATAL/ERROR/WARN/INFO/DEBUG/TRACE/ALL; default
# is WARN. Pick a level that differs from whatever is set now so the assertion
# below can never pass by accident.
PRIMARY_LEVEL = "DEBUG"
FALLBACK_LEVEL = "INFO"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info("Starting logLevel test")
    page = context.get_admin_page()

    page.goto(context.url(GENERAL_PATH))
    page.wait_for_load_state("domcontentloaded")

    original = page.input_value(FIELD)
    logger.debug(f"original logLevel: {original}")
    target = PRIMARY_LEVEL if original != PRIMARY_LEVEL else FALLBACK_LEVEL

    try:
        page.select_option(FIELD, target)
        page.click(SAVE_BUTTON)
        page.wait_for_load_state("domcontentloaded")
        # update() ends in redirect(getClass()); a validation failure instead
        # re-renders the form at the POST target (/admin/general/update), so
        # landing anywhere else means the save was rejected.
        assert_equal(page.url, context.url(GENERAL_PATH),
                     f"save did not redirect back to {GENERAL_PATH}; landed on {page.url}")

        page.goto(context.url(GENERAL_PATH))
        page.wait_for_load_state("domcontentloaded")
        persisted = page.input_value(FIELD)
        assert_equal(persisted, target,
                     f"logLevel select did not hold the saved value; expected {target}, got {persisted}")
    finally:
        try:
            page.goto(context.url(GENERAL_PATH))
            page.wait_for_load_state("domcontentloaded")
            page.select_option(FIELD, original)
            page.click(SAVE_BUTTON)
            page.wait_for_load_state("domcontentloaded")
            logger.info(f"logLevel restored to {original}")
        except Exception as e:
            logger.warning(f"logLevel restore failed (continuing): {e}")

    logger.info("logLevel test completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
