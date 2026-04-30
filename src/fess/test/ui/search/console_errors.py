"""JS console error / page error detector across key pages.

Listens for console.error() and pageerror events while navigating a
fixed page set. Filters known noise (favicon 404 etc.) and fails on
any remaining error.

Detects bug categories:
  3. Functional failure (locale-dependent JS breakage)
"""
import logging
from typing import List

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


PAGES_TO_VISIT = [
    "/search/",
    "/admin/",
    "/admin/dashboard/",
    "/admin/badword/",
]


_NOISE_PATTERNS = [
    "favicon",
    "ResizeObserver loop limit exceeded",
]


def _is_noise(message: str) -> bool:
    return any(p in message for p in _NOISE_PATTERNS)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info(f"Starting search/console_errors (lang={context.lang})")

    errors: List[str] = []

    page = context.get_wrapped_page() or context.get_admin_page()
    raw_page = page._page  # PageWrapper exposes the wrapped Playwright Page

    raw_page.on(
        "console",
        lambda msg: errors.append(f"console.{msg.type}: {msg.text}")
        if msg.type == "error" else None,
    )
    raw_page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    for path in PAGES_TO_VISIT:
        raw_page.goto(context.url(path))
        try:
            raw_page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            logger.warning(f"networkidle wait timed out on {path}: {e}")

    significant = [e for e in errors if not _is_noise(e)]
    assert_true(
        len(significant) == 0,
        f"JS errors detected: {[e[:120] for e in significant[:5]]}")

    logger.info("search/console_errors completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
