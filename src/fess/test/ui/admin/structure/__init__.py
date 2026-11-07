"""Every admin screen has one page heading and a title that names it.

The screens are read from the sidebar rather than listed here, so a screen
added later is covered without anyone remembering to add it, and a screen
that loses its heading is caught in whichever language the run picked.

The dashboard (/admin/ and /admin/dashboard/) is left out: it is a set of
widgets with no page heading of its own.
"""
import logging
from typing import List
from urllib.parse import urlparse

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

DASHBOARD = ("/admin/", "/admin/dashboard/")
MIN_SCREENS = 30  # 37 screens on Fess 15.9; far fewer means the sidebar was not read


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _screens(page: Page, context: FessContext) -> List[str]:
    page.goto(context.url("/admin/"))
    page.wait_for_load_state("domcontentloaded")
    hrefs = page.eval_on_selector_all(
        ".main-sidebar a[href]", "els => els.map(e => e.getAttribute('href'))")
    paths = {urlparse(h).path for h in hrefs if h and h.startswith("/admin/")}
    return sorted(paths - set(DASHBOARD))


def run(context: FessContext) -> None:
    logger.info("Starting admin/structure")
    page = context.get_admin_page()
    screens = _screens(page, context)
    assert_true(len(screens) >= MIN_SCREENS,
                f"only {len(screens)} admin screens found in the sidebar: {screens}")

    problems: List[str] = []
    for path in screens:
        response = page.goto(context.url(path))
        page.wait_for_load_state("domcontentloaded")
        if response is None or response.status != 200:
            problems.append(f"{path}: HTTP {response.status if response else None}")
            continue
        headings = [h.inner_text().strip() for h in page.locator("h1").all()]
        if len(headings) != 1 or not headings[0]:
            problems.append(f"{path}: expected one non-empty <h1>, found {headings}")
        elif headings[0] not in page.title():
            problems.append(f"{path}: the title {page.title()!r} does not contain the heading {headings[0]!r}")
    assert_equal(problems, [], f"admin screens with a structure problem (of {len(screens)})")
    logger.info(f"admin/structure completed ({len(screens)} screens)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
