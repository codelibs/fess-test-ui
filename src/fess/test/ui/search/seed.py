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


def run(context: FessContext) -> None:
    logger.info("Starting search/seed (skeleton; no-op)")
    # TODO(Task 8): create labels
    # TODO(Task 9): create webconfig
    # TODO(Task 10): start Default Crawler
    # TODO(Task 11): poll for SEED_MIN_DOCS readiness
    logger.info("search/seed skeleton completed")


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
