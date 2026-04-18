"""Verify that the thumbnail page is indexed and img.thumbnail renders when enabled.

Thumbnail images (img.thumbnail) only appear when the Fess 'Thumbnail Support'
setting is active AND the document has a thumbnail URL (e.g. extracted from
og:image).  This test therefore checks two things:
  1. Searching for 'thumbnail' returns at least one result (the sampledata
     thumbnail/with_og.html page is indexed).
  2. If thumbnail support is enabled in admin, at least one img.thumbnail
     element is present in the results page.  When support is disabled the
     absence of img.thumbnail is expected and the test passes with a warning.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _thumbnail_support_enabled(context: FessContext) -> bool:
    """Return True if the Fess 'Thumbnail Support' checkbox is checked."""
    try:
        page = context.get_wrapped_page() or context.get_admin_page()
        page.goto(context.url("/admin/general/"))
        page.wait_for_load_state("domcontentloaded")
        cb = page.query_selector("input#thumbnail[type='checkbox']")
        if cb is None:
            return False
        return cb.is_checked()
    except Exception as exc:
        logger.warning(f"Could not read thumbnail support flag: {exc}")
        return False


def run(context: FessContext) -> None:
    logger.info("Starting search/thumbnail")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/search/?q=thumbnail"))
    page.wait_for_load_state("domcontentloaded")

    # 1. The thumbnail sampledata page must appear in results.
    results = page.query_selector_all(".result-item, .searchResult, .hit, li.d-flex")
    # Fallback: count anchor tags inside the result area
    if len(results) == 0:
        results = page.query_selector_all("div#result a.title-link, div.result a")
    record_count_el = page.query_selector(".record-count, #recordCount, [class*='count']")
    logger.info(f"result elements found: {len(results)}, "
                f"record_count_el: {record_count_el is not None}")

    # Verify at least one link to the sampledata thumbnail page.
    links = page.query_selector_all("a[href*='thumbnail']")
    assert_true(len(links) > 0,
                "no link to thumbnail page in search results for q=thumbnail")
    logger.info(f"found {len(links)} link(s) referencing 'thumbnail' in href")

    # 2. img.thumbnail — conditional on thumbnailSupport being active.
    thumb_enabled = _thumbnail_support_enabled(context)
    logger.info(f"thumbnail support enabled: {thumb_enabled}")

    # Re-navigate to results page after visiting admin.
    page.goto(context.url("/search/?q=thumbnail"))
    page.wait_for_load_state("domcontentloaded")

    imgs = page.query_selector_all("img.thumbnail")
    if thumb_enabled:
        assert_true(len(imgs) > 0,
                    "thumbnail support is ON but no img.thumbnail found for q=thumbnail")
        logger.info(f"search/thumbnail completed: {len(imgs)} thumbnail img(s) rendered")
    else:
        logger.warning(
            f"thumbnail support is OFF — img.thumbnail not rendered (expected); "
            f"found {len(imgs)} img.thumbnail element(s)")
        logger.info("search/thumbnail completed (thumbnailSupport disabled)")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try: run(ctx)
        finally: destroy(ctx)
