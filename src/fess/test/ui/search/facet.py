"""Apply a label facet filter and verify it narrows the results.

Since fess#3460, /search is the bootstrap static-theme SPA. Its facet
entries under #facet-body are `a href="#"` with click handlers, showing the
label's name and a count badge; a click re-runs /api/v2/search with
ex_q=label:<value>. So the click is verified through that request.

Counts are compared only within one search response. The seed's crawl keeps
indexing for minutes after seed returns, so two searches a moment apart can
count different documents; the page's own response and the click's response
each carry both a hit count and the label facet counted over the same hits:

- the page's response: the label is on some but not all of its hits, and
  the badge shows exactly the count that response gives the label;
- the click's response: every hit carries the label, i.e. its hit count
  equals the count it gives the label. A filter the server ignored would
  count the unlabelled hits too (the index only grows, so they are still
  there), one that matched nothing fails the check that it found hits.
"""
import logging
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.search.seed import LABEL_A_NAME

logger = logging.getLogger(__name__)

QUERY = "label"  # label-tagged docs contain the word "label"; "page" docs don't carry labels
LABEL_A_VALUE = "e2e_label_a"  # stored value from PR-1 seed (underscores)
LABEL_A_FILTER = f"label:{LABEL_A_VALUE}"


def _counts(response) -> tuple:
    """Return (hit count, label-a facet count) from one /api/v2/search
    response, both computed by the same search."""
    body = response.json()["response"]
    labels = next((f.get("result") or [] for f in body.get("facet_field") or []
                   if f.get("name") == "label"), [])
    label_a = next((int(r["count"]) for r in labels
                    if r.get("value") == LABEL_A_VALUE), 0)
    return int(body["record_count"]), label_a


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/facet")

    page = context.get_wrapped_page() or context.get_admin_page()
    with page.expect_response(lambda r: "/api/v2/search?" in r.url) as info:
        page.goto(context.url(f"/search/?q={QUERY}"))
    baseline, label_a = _counts(info.value)
    logger.info(f"baseline={baseline} label-a={label_a}")

    assert_true(baseline > 0, f"baseline count is 0 for q={QUERY}")
    assert_true(0 < label_a < baseline,
                f"q={QUERY} should hit documents with and without "
                f"{LABEL_A_VALUE}: {label_a} of {baseline} carry it")

    page.wait_for_selector("#facet-body a")
    # The entry shows the label's name (seed creates it with that name and
    # the underscored value above), followed by its count badge.
    entry = page.locator("#facet-body li.list-group-item a",
                         has_text=LABEL_A_NAME)
    assert_equal(entry.count(), 1,
                 f"expected one {LABEL_A_NAME!r} entry in #facet-body")
    advertised = int(entry.locator(".badge").inner_text().strip())
    assert_equal(advertised, label_a,
                 f"the {LABEL_A_NAME} facet advertises {advertised} hits, "
                 f"but the search that rendered it counts {label_a}")

    with page.expect_response(lambda r: "/api/v2/search?" in r.url) as info:
        entry.click()
    response = info.value
    ex_q = parse_qs(urlparse(response.url).query).get("ex_q")
    assert_equal(ex_q, [LABEL_A_FILTER],
                 f"clicking {LABEL_A_NAME} should search with "
                 f"ex_q={LABEL_A_FILTER}, got {response.url}")
    shown, shown_label_a = _counts(response)
    logger.info(f"filtered={shown} label-a={shown_label_a}")
    assert_true(shown > 0,
                f"the filtered search returned no hits, but the page's own "
                f"search counted {label_a} with {LABEL_A_VALUE}")
    assert_equal(shown, shown_label_a,
                 f"the filtered search returned {shown} hits, but counts "
                 f"{shown_label_a} of them with {LABEL_A_VALUE}")

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
