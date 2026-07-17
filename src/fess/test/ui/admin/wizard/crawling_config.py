"""Drive /admin/wizard/ end to end, stopping short of starting a crawl.

The wizard is three JSPs that all POST to the same URL:

    admin_wizard.jsp:36         <la:form action="/admin/wizard/">
    admin_wizard_config.jsp:38  <la:form action="/admin/wizard/">
    admin_wizard_start.jsp:39   <la:form action="/admin/wizard/">

LastaFlute picks the @Execute method from the submit button's request
parameter name, so every selector here is button[name="..."] rather than
button text: the name IS the routing key, and text would be a substring
match against a localized label.

Covered: index, crawlingConfigForm, crawlingConfig, crawlingConfigNext,
startCrawlingForm.

NOT covered, deliberately: startCrawling. AdminWizardAction:393-410 loops
over scheduledJobService.getCrawlerJobList() -- every crawler job, not just
one for the config this wizard made -- and calls job.launchNow() on each.
That relaunches the Default Crawler over search_seed's sampledata-e2e
config, rewriting the index that every search module asserts against, and
it runs asynchronously so moving this module later in the order would not
contain it. The button's presence is asserted; it is never clicked.

`startCrawlingForm` is reached by redirect, not by a button: there is no
button[name="startCrawlingForm"] anywhere. crawlingConfigNext() ends in
redirectWith(getClass(), moreUrl("startCrawlingForm")) (:165), so the only
way to exercise that method is to follow the redirect crawlingConfigNext
emits.

The wizard writes a real WebConfig (crawlingConfigInternal :236 for an
http: path), so both configs this module creates are deleted in finally.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import t, tm
from fess.test.i18n.keys import Labels
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup, assert_absent

logger = logging.getLogger(__name__)

WIZARD_URL = "/admin/wizard/"
WIZARD_CONFIG_FORM_URL = "/admin/wizard/crawlingConfigForm"
WIZARD_START_FORM_URL = "/admin/wizard/startCrawlingForm"
WEBCONFIG_URL = "/admin/webconfig/"

# Kept inside sampledata01, which is on the compose network and serves no
# such path. Nothing crawls it (startCrawling is never clicked and the
# configs are deleted below), but if a later change ever did launch a
# crawler, an unroutable internal 404 is the cheapest thing for it to find.
CRAWLING_PATH = "http://sampledata01/wizard-e2e-not-crawled/"

SUCCESS_ALERT = "div.alert-success"
ERROR_LIST = "ul.has-error"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _assert_wizard_saved(page, config_name: str) -> None:
    """Assert the wizard accepted the save and named `config_name` back.

    Red when the save is rejected: validate() falls back to
    asHtml(path_AdminWizard_AdminWizardConfigJsp) and verifyToken to
    asIndexHtml, and neither renders a success alert. Asserting page.url
    instead would prove nothing -- the form posts to /admin/wizard/ and
    LastaFlute routes on the button name, so a rejected save comes back at
    the same URL a successful one redirects to.
    """
    if page.locator(SUCCESS_ALERT).count() == 0:
        errors = ""
        if page.locator(ERROR_LIST).count() > 0:
            errors = page.locator(ERROR_LIST).first.inner_text()
        assert_true(False,
                    f"the wizard save of '{config_name}' was rejected: no "
                    f"{SUCCESS_ALERT} rendered. Validation output: "
                    f"{errors or '(none)'}. URL is {page.url} either way.")

    expected = tm(Messages.SUCCESS_CREATE_CRAWLING_CONFIG_AT_WIZARD, config_name)
    alert = page.locator(SUCCESS_ALERT).first.inner_text().strip()
    assert_equal(alert, expected,
                 f"wizard reported a different config than it was asked to "
                 f"create: expected {expected!r}, got {alert!r}")


def _open_config_form(page, context: FessContext) -> None:
    """index -> crawlingConfigForm, via the button that dispatches it."""
    page.goto(context.url(WIZARD_URL))
    page.wait_for_load_state("domcontentloaded")
    assert_true(page.locator('button[name="crawlingConfigForm"]').count() == 1,
                "the wizard index rendered no button[name=\"crawlingConfigForm\"]; "
                "it is wrapped in <c:if test=\"${editable}\"> (admin_wizard.jsp:59), "
                "so this also fails if the test user lost admin/admin-wizard rights")

    page.click('button[name="crawlingConfigForm"]')
    page.wait_for_load_state("domcontentloaded")
    # Red if the button stops dispatching to crawlingConfigForm: the index
    # JSP has no such input, so we would still be sitting on the index.
    assert_true(page.locator('input[name="crawlingConfigName"]').count() == 1,
                f"clicking button[name=\"crawlingConfigForm\"] did not reach the "
                f"config form: no input[name=\"crawlingConfigName\"] at {page.url}")


def _fill_config(page, name: str) -> None:
    page.fill('input[name="crawlingConfigName"]', name)
    page.fill('input[name="crawlingConfigPath"]', CRAWLING_PATH)
    # Both optional. maxAccessCount is a Long and depth an Integer
    # (CrawlingConfigForm:55-66); each carries @ValidateTypeFailure, so a
    # non-numeric value here would come back as a rejected save.
    page.fill('input[name="maxAccessCount"]', "1")
    page.fill('input[name="depth"]', "0")


def _delete_webconfig(page, context: FessContext, name: str) -> None:
    """Delete a WebConfig the wizard created, by name."""
    page.goto(context.url(WEBCONFIG_URL))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")


def run(context: FessContext) -> None:
    logger.info("Starting wizard crawling_config test")
    page = context.get_admin_page()

    # Unique per run: the wizard has no name-collision check and these are
    # real persistent configs. context.create_label_name() is deliberately
    # NOT used -- it memoizes one name for the whole run and the admin CRUD
    # modules already own it.
    stay_name = f"e2e-wizard-stay-{context.generate_str(8)}"
    next_name = f"e2e-wizard-next-{context.generate_str(8)}"
    created = []

    try:
        logger.info("Step 1: index -> crawlingConfigForm")
        _open_config_form(page, context)

        logger.info(f"Step 2: crawlingConfig (save and stay) as {stay_name}")
        _fill_config(page, stay_name)
        page.click('button[name="crawlingConfig"]')
        created.append(stay_name)
        page.wait_for_load_state("domcontentloaded")
        _assert_wizard_saved(page, stay_name)
        # crawlingConfig() returns redirectWith(getClass(),
        # moreUrl("crawlingConfigForm")) (:149) while crawlingConfigNext()
        # redirects to startCrawlingForm. The two land on different URLs, so
        # this distinguishes which @Execute the button actually reached.
        assert_true(page.url.endswith(WIZARD_CONFIG_FORM_URL),
                    f"crawlingConfig should return to the config form; got {page.url}")
        assert_true(page.locator('input[name="crawlingConfigName"]').count() == 1,
                    "crawlingConfig should re-render an empty config form to "
                    f"create another config; no name input at {page.url}")

        logger.info(f"Step 3: crawlingConfigNext (save and advance) as {next_name}")
        # Reachable only because crawlingConfig() uses verifyTokenKeep
        # (:146), which leaves the token valid for this second submit.
        # crawlingConfigNext() uses verifyToken (:162) and consumes it.
        _fill_config(page, next_name)
        page.click('button[name="crawlingConfigNext"]')
        created.append(next_name)
        page.wait_for_load_state("domcontentloaded")
        _assert_wizard_saved(page, next_name)

        logger.info("Step 4: the startCrawlingForm redirect")
        # The whole point of this step: startCrawlingForm has no button, so
        # this redirect is the only path to it. Red if crawlingConfigNext
        # stops redirecting (e.g. reverts to re-rendering the config form).
        assert_true(page.url.endswith(WIZARD_START_FORM_URL),
                    f"crawlingConfigNext should redirect to {WIZARD_START_FORM_URL}; "
                    f"got {page.url}")
        assert_true(page.locator('button[name="startCrawling"]').count() == 1,
                    f"the start page rendered no button[name=\"startCrawling\"] at "
                    f"{page.url}; expected it present but deliberately unclicked")

        logger.info("Step 5: verify both configs were really persisted")
        # The success alert is a flash message; this proves the wizard wrote
        # WebConfig rows. Red if crawlingConfigInternal stops storing, or
        # routes an http: path to a FileConfig instead.
        page.goto(context.url(WEBCONFIG_URL))
        page.wait_for_load_state("domcontentloaded")
        listed = page.inner_text("section.content")
        for name in (stay_name, next_name):
            assert_true(name in listed,
                        f"the wizard reported creating '{name}' but it is absent "
                        f"from {WEBCONFIG_URL}")

        logger.info("Step 6: leave the wizard without starting a crawl")
        page.goto(context.url(WIZARD_START_FORM_URL))
        page.wait_for_load_state("domcontentloaded")
        page.click('button[name="index"]')
        page.wait_for_load_state("domcontentloaded")
        assert_true(page.locator('button[name="crawlingConfigForm"]').count() == 1,
                    f"the finish button should land back on the wizard index; "
                    f"no button[name=\"crawlingConfigForm\"] at {page.url}")
    finally:
        cleanup = Cleanup()
        for name in created:
            with cleanup.guard(f"web config '{name}' created by the wizard"):
                _delete_webconfig(page, context, name)
                assert_absent(page, name, WEBCONFIG_URL)
                logger.info(f"cleaned up wizard config {name}")
        cleanup.escalate()

    logger.info("wizard crawling_config test completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
