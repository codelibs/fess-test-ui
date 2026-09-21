"""Toggle sort=created.asc vs sort=created.desc and verify result order differs.

Since fess#3460, /search is the bootstrap static-theme SPA, whose result
links point at go/?rt=... rather than the document, so the document URL is
read from the title link's data-uri.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true, assert_not_equal
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "page"
FIRST_RESULT = "#result0 h3.title a.link"


def _first_url(context: FessContext, page, sort: str) -> str:
    page.goto(context.url(f"/search/?q={QUERY}&sort={sort}"))
    # Each goto reloads the SPA, so #result0 is the new sort's first result.
    first = page.wait_for_selector(FIRST_RESULT)
    uri = first.get_attribute("data-uri")
    assert_true(uri and "sampledata01" in uri,
                f"no sampledata01 result at {FIRST_RESULT} for q={QUERY} "
                f"sort={sort}; data-uri={uri!r}")
    return uri


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
