"""Toggle sort=created.asc vs sort=created.desc and verify result order differs."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_not_equal
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "page"


def _first_url(context: FessContext, page, sort: str) -> str:
    page.goto(context.url(f"/search/?q={QUERY}&sort={sort}"))
    page.wait_for_load_state("domcontentloaded")
    first = page.query_selector('a[href*="sampledata01"]')
    assert_true(first is not None, f"no result link for q={QUERY} sort={sort}")
    return first.get_attribute("href")


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/sort")
    page = context.get_wrapped_page() or context.get_admin_page()

    asc = _first_url(context, page, "created.asc")
    desc = _first_url(context, page, "created.desc")
    logger.info(f"first(asc)={asc} first(desc)={desc}")

    assert_not_equal(asc, desc,
                     f"asc and desc sorts returned same first result: {asc}")

    logger.info("search/sort completed")


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
