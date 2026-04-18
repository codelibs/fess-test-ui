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


def run(context: FessContext) -> None:
    logger.info("Starting search/seed")
    page = context.get_admin_page()

    _create_label(page, context, LABEL_A_NAME,
                  "http://sampledata01/docs/labels/a/.*")
    _create_label(page, context, LABEL_B_NAME,
                  "http://sampledata01/docs/labels/b/.*")

    # TODO(Task 9): create webconfig
    # TODO(Task 10): start Default Crawler
    # TODO(Task 11): poll for SEED_MIN_DOCS readiness

    logger.info("search/seed partial (labels only) completed")


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
