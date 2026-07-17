"""Download backup targets from /admin/backup/ and verify what comes back.

Sits next to backup.py, which only asserts the page renders; this drives
the download links it renders.

Three things about this endpoint drive the whole design:

1. There is no <a href>. admin_backup.jsp:77-83 puts the URL on
   <tr data-href> and js/admin/admin.js:21-35 navigates on row click. The
   data-href values are read off the page and requested directly: that
   still proves the JSP built the right URL, without asking Playwright to
   catch ten browser downloads.

2. HTTP status proves nothing. An unknown id does NOT 404 -- download()
   falls through to throwValidationError(..., this::asListHtml)
   (AdminBackupAction:477), which forward-renders admin_backup.jsp with an
   error alert as HTTP 200. Verified live: a bogus id returns 200 with 21015
   bytes of HTML. So every assertion here keys off Content-Disposition,
   which LastaFlute sets only on a real StreamResponse
   (SimpleResponseManager:349), and BOGUS_ID below is the negative control
   that keeps those assertions honest.

3. Content-Type splits by target. Only the six non-ndjson targets go
   through contentTypeOctetStream(); writeNdjsonResponse (:490-503) sets
   Content-Type: application/x-ndjson explicitly and never calls it.

Targets are picked, not swept. All ten would be slow and two are traps:
click_log.ndjson and favorite_log.ndjson are legitimately EMPTY on an
instance where nothing was clicked (click_log.ndjson measured 0 bytes),
so a line-count assertion against them could never pass. The upload form
(input[name="bulkFile"], admin_backup.jsp:53-64) overwrites index data and
is not touched.
"""
import json
import logging
import time

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

PAGE_URL = "/admin/backup/"

SYSTEM_PROPERTIES = "system.properties"
CONFIG_BULK = "fess_config.bulk"
SEARCH_LOG_NDJSON = "search_log.ndjson"

# Not in fessConfig.getIndexBackupAllTargets(), so download() cannot match
# it and falls through to the validation-error branch.
BOGUS_ID = "e2e-no-such-backup-target"

OCTET_STREAM = "application/octet-stream"
NDJSON = "application/x-ndjson"

# The ten ids of index.backup.targets + index.backup.log.targets
# (fess_config.properties:1018,1020), in the order getBackupItems() renders.
EXPECTED_TARGETS = [
    "fess_basic_config.bulk", "fess_config.bulk", "fess_user.bulk",
    "system.properties", "fess.json", "doc.json",
    "click_log.ndjson", "favorite_log.ndjson", "search_log.ndjson",
    "user_info.ndjson",
]

# Search logs reach the index only when the Log Aggregator job drains the
# queue (AggregateLogJob:50), and it is scheduled "* * * * *". In the
# default order this module runs long after search_seed, so the logs are
# already there and the first poll returns; the wait only pays out when
# someone runs this module alone against a fresh instance.
LOG_FLUSH_TIMEOUT = 90
LOG_FLUSH_POLL = 5


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _download(page, context: FessContext, href: str):
    """GET a data-href with the UI's session; returns (response, lines)."""
    response = page.request.get(context.url(href))
    body = response.body()
    lines = [ln for ln in body.decode("utf-8", "replace").split("\n") if ln.strip()]
    logger.debug(f"{href} -> {response.status} "
                 f"ct={response.headers.get('content-type')!r} "
                 f"bytes={len(body)} lines={len(lines)}")
    return response, lines


def _assert_attachment(response, target: str, content_type: str) -> None:
    """Assert this really is the file download it claims to be.

    Red for any id the action does not serve: the validation-error branch
    renders HTML with no Content-Disposition at all (asserted on BOGUS_ID
    below), and red again if the filename or the Content-Type drifts.
    """
    disposition = response.headers.get("content-disposition")
    assert_true(disposition is not None,
                f"{target}: no Content-Disposition. The response is not a "
                f"download -- an id the action cannot serve renders the list "
                f"page as HTTP {response.status} instead.")
    assert_equal(disposition, f'attachment; filename="{target}"',
                 f"{target}: unexpected Content-Disposition {disposition!r}")
    assert_equal(response.headers.get("content-type"), content_type,
                 f"{target}: unexpected Content-Type")


def _assert_json_lines(lines, target: str) -> None:
    for index, line in enumerate(lines):
        try:
            json.loads(line)
        except ValueError as e:
            assert_true(False,
                        f"{target}: line {index + 1} is not valid JSON ({e}): "
                        f"{line[:200]!r}")


def _href_for(hrefs: dict, target: str) -> str:
    assert_true(target in hrefs,
                f"{PAGE_URL} rendered no data-href for {target}; got "
                f"{sorted(hrefs)}")
    return hrefs[target]


def _wait_for_search_logs(page, context: FessContext, href: str):
    """Poll until the search-log index holds more than one record."""
    deadline = time.time() + LOG_FLUSH_TIMEOUT
    while True:
        response, lines = _download(page, context, href)
        if len(lines) > 1:
            return response, lines
        if time.time() >= deadline:
            return response, lines
        # Generate traffic to log, then wait for the aggregator to drain it.
        context.api_search(q="*")
        context.api_search(q="fess")
        logger.info(f"search_log has {len(lines)} record(s); waiting for the "
                    f"Log Aggregator to flush the queue")
        time.sleep(LOG_FLUSH_POLL)


def run(context: FessContext) -> None:
    logger.info("Starting backup_download")
    page = context.get_admin_page()
    page.goto(context.url(PAGE_URL))
    page.wait_for_load_state("domcontentloaded")

    rows = page.locator("tr[data-href]")
    hrefs = {}
    for index in range(rows.count()):
        href = rows.nth(index).get_attribute("data-href")
        hrefs[href.rstrip("/").split("/")[-1]] = href

    logger.info("Step 1: the table offers every configured target")
    # Red if a target is dropped from the JSP or the properties, and red if
    # the trailing slash goes away -- download(String id) takes id as a path
    # parameter, so /download/system.properties would not route.
    for target in EXPECTED_TARGETS:
        href = _href_for(hrefs, target)
        assert_equal(href, f"/admin/backup/download/{target}/",
                     f"unexpected data-href for {target}")

    logger.info("Step 2: an id the action cannot serve is not a download")
    # The negative control. Without it, every Content-Disposition assertion
    # below could be passing for a reason unrelated to the file being
    # served. Note the status is 200 here, same as a real download.
    bogus, _ = _download(page, context, f"/admin/backup/download/{BOGUS_ID}/")
    assert_true(bogus.headers.get("content-disposition") is None,
                f"{BOGUS_ID} returned a Content-Disposition "
                f"({bogus.headers.get('content-disposition')!r}); the action is "
                f"serving an id that is not in index.backup.targets")
    assert_true("html" in (bogus.headers.get("content-type") or ""),
                f"{BOGUS_ID}: expected the list page to be re-rendered, got "
                f"Content-Type {bogus.headers.get('content-type')!r}")

    logger.info("Step 3: system.properties")
    # The cheapest real target: served from DynamicProperties in memory
    # (AdminBackupAction:404-413), never off disk, so it cannot be missing.
    response, lines = _download(page, context, _href_for(hrefs, SYSTEM_PROPERTIES))
    _assert_attachment(response, SYSTEM_PROPERTIES, OCTET_STREAM)
    assert_true(len(lines) > 0, "system.properties came back empty")

    logger.info("Step 4: fess_config.bulk")
    # Exercises the scroll-and-stream path (SearchEngineUtil.scroll,
    # :460-475), which writes an action line plus a source line per hit. The
    # config index is never empty -- Fess seeds its own scheduled jobs --
    # so the multi-record assertion here is deterministic, unlike the log
    # indices.
    response, lines = _download(page, context, _href_for(hrefs, CONFIG_BULK))
    _assert_attachment(response, CONFIG_BULK, OCTET_STREAM)
    assert_true(len(lines) > 1,
                f"{CONFIG_BULK} returned {len(lines)} line(s); the scroll should "
                f"emit an index action and a source line per document")
    _assert_json_lines(lines, CONFIG_BULK)
    first = json.loads(lines[0])
    assert_true("index" in first,
                f"{CONFIG_BULK} should open with a bulk index action; got "
                f"{lines[0][:200]!r}")

    logger.info("Step 5: search_log.ndjson")
    # The NDJSON writer is the path where a writer that closes the servlet
    # stream after the first record silently truncates the rest: the
    # response still looks fine, it is just short. Only >1 record can catch
    # that, hence the wait above rather than a bare 200 check.
    response, lines = _wait_for_search_logs(
        page, context, _href_for(hrefs, SEARCH_LOG_NDJSON))
    _assert_attachment(response, SEARCH_LOG_NDJSON, NDJSON)
    assert_true(len(lines) > 1,
                f"{SEARCH_LOG_NDJSON} returned {len(lines)} record(s) after "
                f"{LOG_FLUSH_TIMEOUT}s. Every search this suite ran should be "
                f"logged; one record can mean the writer closed the response "
                f"stream after the first.")
    _assert_json_lines(lines, SEARCH_LOG_NDJSON)

    logger.info(f"backup_download completed ({len(lines)} search_log records)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
