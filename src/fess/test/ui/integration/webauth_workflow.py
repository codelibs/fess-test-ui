"""A page behind BASIC authentication is crawled once a Web Authentication
entry is linked to the crawl config, and fails visibly without one.

The sample site serves /secured/page.html behind BASIC authentication (see
sampledata/default.conf). A Web Authentication entry applies only to the
crawl config it is linked to, so one crawl can contain both cases:

- config "with" is linked to an entry holding the site's host, port, realm
  and the fixture account: its page must become searchable;
- config "without" points at the same page and has no entry: the 401 must
  show up in /admin/failureurl/.

Together they show that the credentials are what made the difference: were
the failure record the "with" config's, that config's page would not be
searchable. Everything it creates is removed again, the indexed page and
the failure URL record included.
"""
import logging
import time
from typing import List
from urllib.parse import urlparse

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup
from fess.test.ui.integration import _crawl

logger = logging.getLogger(__name__)

SECURED_PATH = "secured/page.html"
MARKER = "authmarkerbasic"
# The fixture account of sampledata/e2e.htpasswd. It only opens the sample
# site's /secured/ page.
FIXTURE_USER = "e2euser"
FIXTURE_PASSWORD = "e2e-fixture-only"
FIXTURE_REALM = "e2e-secured"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _found(context: FessContext) -> bool:
    """Whether an anonymous visitor finds the secured page."""
    with context.guest_page() as visitor:
        return any(url.endswith(SECURED_PATH) for url in _crawl.search_urls(visitor, context, MARKER))


def _failure_urls(page: Page, context: FessContext) -> str:
    page.goto(context.url("/admin/failureurl/"))
    page.wait_for_load_state("domcontentloaded")
    return page.inner_text("section.content")


def _create_webauth(page: Page, context: FessContext, config_name: str) -> None:
    host = urlparse(_crawl.SAMPLEDATA_URL)
    page.goto(context.url("/admin/webauth/"))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill('input[name="hostname"]', host.hostname)
    page.fill('input[name="port"]', str(host.port or 80))
    page.fill('input[name="authRealm"]', FIXTURE_REALM)
    page.select_option('select[name="protocolScheme"]', "BASIC")
    page.fill('input[name="username"]', FIXTURE_USER)
    page.fill('input[name="password"]', FIXTURE_PASSWORD)
    page.select_option('select[name="webConfigId"]', label=config_name)
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_equal(page.url, context.url("/admin/webauth/"), "after creating the web authentication")


def _delete_webauth(page: Page, context: FessContext, config_name: str) -> None:
    page.goto(context.url("/admin/webauth/"))
    page.wait_for_load_state("domcontentloaded")
    row = page.locator("tr", has_text=config_name)
    assert_equal(row.count(), 1, "web authentication rows for the crawl config")
    row.click()
    page.wait_for_load_state("domcontentloaded")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")
    assert_true(config_name not in page.inner_text("section.content"),
                "the web authentication is still listed")


def _delete_failure_urls(page: Page, context: FessContext, url: str) -> None:
    """Empty the failure URL list, which must hold only the record made here."""
    text = _failure_urls(page, context)
    assert_contains(text, url, "the failure URL record made by this workflow")
    rows = page.locator("tr[data-href]").count()
    assert_equal(rows, 1, "failure URL records before the clean-up (deleting all would remove others')")
    page.click('button[data-target="#confirmToDeleteAll"]')
    page.wait_for_selector('#confirmToDeleteAll button[name="deleteall"]', state="visible")
    page.click('#confirmToDeleteAll button[name="deleteall"]')
    page.wait_for_load_state("domcontentloaded")
    deadline = time.time() + 30
    while url in _failure_urls(page, context):
        assert_true(time.time() < deadline, "the failure URL record is still listed")
        time.sleep(1)


def run(context: FessContext) -> None:
    logger.info("start web authentication workflow integration test")

    page = context.get_admin_page()
    base = context.generate_str(8).lower()
    with_auth, without_auth = f"WebAuthWith_{base}", f"WebAuthWithout_{base}"
    url = f"{_crawl.SAMPLEDATA_URL}{SECURED_PATH}"
    created: List[str] = []

    try:
        logger.info("Step 1: two crawl configs for the secured page, one with credentials")
        _crawl.create_webconfig(page, context, without_auth, url, "{role}guest")
        created.append("without")
        _crawl.create_webconfig(page, context, with_auth, url, "{role}guest")
        created.append("with")
        _create_webauth(page, context, with_auth)
        created.append("webauth")

        logger.info("Step 2: crawl")
        _crawl.start_job(page, context, _crawl.DEFAULT_CRAWLER)
        created.append("crawl")

        logger.info("Step 3: the page is searchable and the 401 is on the failure list")
        deadline = time.time() + _crawl.CRAWL_TIMEOUT
        while not (_found(context) and url in _failure_urls(page, context)):
            assert_true(time.time() < deadline,
                        f"after {_crawl.CRAWL_TIMEOUT}s: searchable={_found(context)}, "
                        f"on the failure list={url in _failure_urls(page, context)}")
            time.sleep(_crawl.POLL_INTERVAL)
        logger.info("✓ credentials make the secured page crawlable; without them the failure is reported")
    finally:
        cleanup = Cleanup()
        if "crawl" in created:
            with cleanup.guard("indexed secured page"):
                _crawl.delete_indexed_pages(page, context, "Secured", 1)
        if "webauth" in created:
            with cleanup.guard(f"web authentication for '{with_auth}' (fixture account)"):
                _delete_webauth(page, context, with_auth)
        for key, name in (("with", with_auth), ("without", without_auth)):
            if key in created:
                with cleanup.guard(f"webconfig '{name}'"):
                    _crawl.delete_via_details(page, context, "/admin/webconfig/", name,
                                              t(Labels.CRUD_BUTTON_DELETE))
        if "crawl" in created:
            with cleanup.guard("failure URL record"):
                _delete_failure_urls(page, context, url)
        cleanup.escalate()

    logger.info("✓ web authentication workflow integration test completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
