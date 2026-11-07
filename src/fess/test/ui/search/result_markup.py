"""Markup in a result's title or snippet is neutralised, never run.

The theme renders content_title / content_description from /api/v2/search.
Those fields are HTML strings, so a document whose title carries markup must
not become elements of the page. The test rewrites the API response in the
browser, putting hostile markup into the first hit, and checks the page:

- no <img>, <script> or <iframe> comes from the markup,
- no javascript: link appears and no dialog opens,
- the plain words around the markup are still shown (the sanitizer drops the
  disallowed tags, it does not drop the whole field).
"""
import json
import logging

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_contains, assert_equal, assert_true
from fess.test.ui import FessContext
from fess.test.ui.version import skip_before_theme

logger = logging.getLogger(__name__)

HITS = "#results h3.title a.link"
EVIL_TITLE = 'evilmark <img src=x onerror="document.title=\'pwned\'"> <script>document.title="pwned"</script>'
EVIL_SNIPPET = ('snippetmark <a href="javascript:alert(1)">click</a> '
                '<iframe src="about:blank"></iframe> <svg onload="document.title=\'pwned\'"></svg>')


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def _tamper(route) -> None:
    response = route.fetch()
    body = response.json()
    first = body["response"]["data"][0]
    first["content_title"] = EVIL_TITLE
    first["content_description"] = EVIL_SNIPPET
    route.fulfill(response=response, body=json.dumps(body),
                  headers={**response.headers, "content-type": "application/json"})


def run(context: FessContext) -> None:
    if skip_before_theme(context, "search/result_markup"):
        return
    logger.info("Starting search/result_markup")
    with context.guest_page() as page:
        _check(page, context)
    logger.info("search/result_markup completed")


def _check(page: Page, context: FessContext) -> None:
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    page.route("**/api/v2/search*", _tamper)

    page.goto(context.url("/search/?q=intro"))
    page.wait_for_selector(HITS)
    first = page.locator("#result0")
    assert_contains(first.inner_text(), "evilmark", "the plain word of the title is shown")
    assert_contains(first.inner_text(), "snippetmark", "the plain word of the snippet is shown")

    injected = first.locator("img, script, iframe, svg, [onerror], [onload]").count()
    assert_equal(injected, 0, "elements created by the markup in the first hit")
    js_links = page.locator('#results a[href^="javascript:" i]').count()
    assert_equal(js_links, 0, "javascript: links in the results")
    assert_equal(dialogs, [], "dialogs opened by the results")
    assert_true("pwned" not in page.title(), "the markup ran: the document title was rewritten")


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
