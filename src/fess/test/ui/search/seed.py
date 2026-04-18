"""
Seed module for search UI tests.

Registers a webconfig pointing at http://sampledata01/, attaches two
labels, triggers the Default Crawler via the scheduler, and polls
/api/v1/documents until at least SEED_MIN_DOCS documents are indexed.

Runs once per test run, before any search/* module.
"""
import logging
import os
import time

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

SAMPLEDATA_URL = os.environ.get("SAMPLEDATA_URL", "http://sampledata01/")
SEED_MIN_DOCS = int(os.environ.get("SEED_MIN_DOCS", "20"))
SEED_READY_TIMEOUT = int(os.environ.get("SEED_READY_TIMEOUT", "180"))
SEED_POLL_INTERVAL = int(os.environ.get("SEED_POLL_INTERVAL", "2"))

WEBCONFIG_NAME = "sampledata-e2e"
LABEL_A_NAME = "e2e-label-a"
LABEL_B_NAME = "e2e-label-b"


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _create_label(page, context: FessContext, name: str, included_paths: str) -> None:
    """Create a label with an included-URL pattern via the admin UI.
    Idempotent: if a label with the same name already exists, navigates
    to it and returns without error (the list-page assertion still holds)."""
    logger.info(f"Creating label: {name}")
    page.goto(context.url("/admin/labeltype/"))
    page.wait_for_load_state("domcontentloaded")

    # If already present, skip creation (table absent when list is empty)
    table_el = page.query_selector("table")
    table_text = table_el.inner_text() if table_el else ""
    if table_text.find(name) != -1:
        logger.info(f"Label {name} already exists; skipping creation")
        return

    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    page.fill("input[name=\"name\"]", name)
    page.fill("input[name=\"value\"]", name.lower().replace("-", "_"))
    page.fill("textarea[name=\"includedPaths\"]", included_paths)
    page.fill("input[name=\"sortOrder\"]", "1")
    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_true(page.url.endswith("/admin/labeltype/"),
                f"after create, expected labeltype list URL, got {page.url}")
    assert_true(page.inner_text("table").find(name) != -1,
                f"label {name} not in list after create")


def _create_webconfig(page, context: FessContext) -> None:
    """Create the sampledata webconfig. Idempotent on name collision."""
    logger.info(f"Creating webconfig: {WEBCONFIG_NAME}")
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")

    table_el = page.query_selector("table")
    table_text = table_el.inner_text() if table_el else ""
    if table_text.find(WEBCONFIG_NAME) != -1:
        logger.info(f"Webconfig {WEBCONFIG_NAME} already exists; skipping")
        return

    page.click("text=新規作成")
    page.wait_for_load_state("domcontentloaded")
    page.fill("input[name=\"name\"]", WEBCONFIG_NAME)
    page.fill("textarea[name=\"urls\"]", SAMPLEDATA_URL)
    page.fill("textarea[name=\"includedUrls\"]", f"{SAMPLEDATA_URL}.*")
    page.fill("textarea[name=\"excludedUrls\"]",
              "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")
    page.fill("input[name=\"maxAccessCount\"]", "100")
    page.fill("input[name=\"numOfThread\"]", "2")
    page.fill("textarea[name=\"description\"]", "E2E sampledata (managed by search/seed)")

    # Attach both labels. The labelTypeIds select is hidden by display:none in
    # Fess 15 — make the parent div visible first, then select by display text.
    page.evaluate(
        "document.querySelector('select[name=\"labelTypeIds\"]')"
        ".closest('.form-group').style.display = 'block'"
    )
    page.select_option("select[name=\"labelTypeIds\"]",
                       label=[LABEL_A_NAME, LABEL_B_NAME])

    page.click("button:has-text(\"作成\")")
    page.wait_for_load_state("domcontentloaded")
    assert_true(page.url.endswith("/admin/webconfig/"),
                f"after create, expected webconfig list URL, got {page.url}")
    assert_true(page.inner_text("table").find(WEBCONFIG_NAME) != -1,
                f"webconfig {WEBCONFIG_NAME} not in list after create")


def _start_default_crawler(page, context: FessContext) -> None:
    """Start the 'Default Crawler' scheduler job via the admin UI."""
    logger.info("Starting Default Crawler job")
    page.goto(context.url("/admin/scheduler/"))
    page.wait_for_load_state("domcontentloaded")

    # Open the Default Crawler details page by clicking its name in the table
    page.click("text=Default Crawler")
    page.wait_for_load_state("domcontentloaded")
    assert_true("/admin/scheduler/details/" in page.url,
                f"expected scheduler details URL, got {page.url}")

    # Click the start button. Fess uses a submit button typically with name="start"
    # or a link/button labelled 起動. Try name="start" first, then the Japanese text.
    try:
        page.click("button[name=\"start\"]", timeout=3000)
    except Exception as e:
        logger.info(f"button[name=\"start\"] not found ({e}); trying text=起動")
        page.click("text=起動")
    page.wait_for_load_state("domcontentloaded")
    logger.info("Default Crawler start clicked")


def _poll_until_indexed(context: FessContext) -> int:
    """Poll /api/v1/documents until at least SEED_MIN_DOCS are indexed.
    Returns the final doc count. Raises AssertionError on timeout."""
    deadline = time.time() + SEED_READY_TIMEOUT
    last_total = -1
    first_iter = True
    while time.time() < deadline:
        try:
            body = context.api_get("/api/v1/documents?q=*&size=0")
        except Exception as e:
            logger.debug(f"api_get failed during poll: {e}")
            time.sleep(SEED_POLL_INTERVAL)
            continue

        if first_iter:
            logger.info(f"api body keys: {list(body.keys())}")
            first_iter = False

        # Fess /api/v1/documents response shape varies by version:
        #   Fess 15+ : top-level flat with "record_count" or "total_count"
        #   older    : nested under "response"
        # Accept multiple keys to be defensive.
        total = (body.get("record_count")
                 or body.get("total_count")
                 or body.get("total")
                 or (body.get("response", {}) or {}).get("record_count")
                 or (body.get("response", {}) or {}).get("total_count")
                 or 0)
        if total != last_total:
            logger.info(f"Indexed doc count: {total}")
            last_total = total
        if total >= SEED_MIN_DOCS:
            return total
        time.sleep(SEED_POLL_INTERVAL)

    raise AssertionError(
        f"Seed readiness timeout: only {last_total} docs after "
        f"{SEED_READY_TIMEOUT}s (wanted >= {SEED_MIN_DOCS})")


def run(context: FessContext) -> None:
    logger.info("Starting search/seed")
    page = context.get_admin_page()

    _create_label(page, context, LABEL_A_NAME,
                  "http://sampledata01/docs/labels/a/.*")
    _create_label(page, context, LABEL_B_NAME,
                  "http://sampledata01/docs/labels/b/.*")
    _create_webconfig(page, context)
    _start_default_crawler(page, context)

    total = _poll_until_indexed(context)
    logger.info(f"search/seed completed: {total} docs indexed")


def destroy(context: FessContext) -> None:
    # TODO(Task 12): delete webconfig + labels
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
