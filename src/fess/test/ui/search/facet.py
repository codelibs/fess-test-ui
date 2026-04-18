"""Apply a label facet filter and verify the result count shrinks."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "label"  # label-tagged docs contain the word "label"; "page" docs don't carry labels
LABEL_A_VALUE = "e2e_label_a"  # stored value from PR-1 seed (underscores)


def _count_hits(context: FessContext, q: str, ex_q: str = None) -> int:
    """Use the JSON API for an authoritative hit count."""
    path = f"/api/v1/documents?q={q}&size=0"
    if ex_q:
        path += f"&ex_q={ex_q}"
    body = context.api_get(path)
    return int(body.get("record_count")
               or body.get("total_count")
               or body.get("total")
               or 0)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/facet")

    baseline = _count_hits(context, QUERY)
    filtered = _count_hits(context, QUERY, ex_q=f"label:{LABEL_A_VALUE}")
    logger.info(f"baseline={baseline} filtered-by-label-a={filtered}")

    assert_true(baseline > 0, f"baseline count is 0 for q={QUERY}")
    assert_true(filtered < baseline,
                f"facet filter did not reduce count: {filtered} >= {baseline}")

    page = context.get_wrapped_page() or context.get_admin_page()
    page.goto(context.url(f"/search/?q={QUERY}"))
    page.wait_for_load_state("domcontentloaded")
    facet_link = page.query_selector('a[href*="ex_q=label%3a"]')
    assert_true(facet_link is not None,
                "no label facet link on results page (ex_q=label:... anchor missing)")

    logger.info("search/facet completed")


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
