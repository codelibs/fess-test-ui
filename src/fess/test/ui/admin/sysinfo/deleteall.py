"""Exercise the confirm-modal "delete all" on the sysinfo list pages.

DESTRUCTIVE. Runs last in the sysinfo composer, after backup_download has
taken its copy of the logs.

Two pages, not the four that have a deleteall() method:

  joblog        covered
  crawlinginfo  covered
  searchlog     NOT covered -- no UI, and the action is a no-op.
                AdminSearchlogAction:227-235 clears the pager, then
                `// TODO delete logs`, then reports success. There is no
                modal and no deleteall button in admin_searchlog.jsp
                (its only buttons are name="search" and name="reset"), so
                there is nothing to click and nothing to observe.
  failureurl    NOT covered -- the button does not exist on this instance.
                The trigger and modal live inside
                <c:if test="${failureUrlPager.allRecordCount > 0}">
                (admin_failureurl.jsp:108-191), and the list is always
                empty here: failure URLs are only written when a crawl
                fails, and sampledata01 has no broken links (every href in
                sampledata/content resolves to a file). Nothing else in the
                suite crawls -- webconfig/job.py and
                integration/crawler_workflow.py both create a job and
                delete it without launching. Reaching that handler needs a
                deliberately-failing crawl to be seeded first; see the
                Phase 4c/4d report.

The two covered pages render byte-identical modal markup apart from their
label keys, so the shared selectors below are asserted twice.

Bootstrap 4 (js/admin/bootstrap.min.js is v4.6.2): data-toggle /
data-target / data-dismiss. The public search UI is Bootstrap 5 and uses
data-bs-*; the two must not be mixed.

The cancel button needs its class: the modal header's x also carries
data-dismiss="modal", but as class="close" rather than .btn-outline-light.
"""
import logging
import time

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import t, tm
from fess.test.i18n.keys import Labels
from fess.test.i18n.message_keys import Messages
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

JOBLOG_URL = "/admin/joblog/"
CRAWLINGINFO_URL = "/admin/crawlinginfo/"

TRIGGER = 'button[data-target="#confirmToDeleteAll"]'
MODAL = "#confirmToDeleteAll"
MODAL_SHOWN = "#confirmToDeleteAll.show"
CANCEL = '#confirmToDeleteAll button[data-dismiss="modal"].btn-outline-light'
CONFIRM = '#confirmToDeleteAll button[name="deleteall"]'
ROWS = "table tbody tr"
SUCCESS_ALERT = "div.alert-success"

# A crawl outlives search_seed, which returns as soon as enough documents
# are indexed. While a job is in flight neither deleteall empties its list:
# AdminJoblogAction.deleteall() removes only ok/fail rows (:243-254) and
# crawlinginfo's deleteOldSessions() excludes running sessions. Both would
# then report success while deleting nothing.
IDLE_TIMEOUT = 900
IDLE_POLL = 5

# deleteall() deletes by query and then redirects straight into a list page
# that re-reads the index. The search engine is only near-real-time, so that
# read can land inside the refresh window and still see the rows that were
# just deleted -- observed live: the success alert rendered next to the row
# it had already removed. Reload until the delete becomes visible rather
# than sampling once. A deleteall that deleted nothing never converges, so
# the assertion this guards is still falsifiable; it just is not racy.
EMPTY_TIMEOUT = 30
EMPTY_POLL = 1


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _wait_until_no_job_running(page, context: FessContext) -> None:
    """Block until no job log carries the Running badge."""
    started = time.time()
    deadline = started + IDLE_TIMEOUT
    running = t(Labels.JOBLOG_STATUS_RUNNING)
    while True:
        page.goto(context.url(JOBLOG_URL))
        page.wait_for_load_state("domcontentloaded")
        if running not in page.inner_text("body"):
            logger.info(f"no job running after {time.time() - started:.0f}s")
            return
        assert_true(time.time() < deadline,
                    f"a job was still running after {IDLE_TIMEOUT}s; deleting "
                    f"logs now would silently delete nothing, because deleteall "
                    f"skips in-flight jobs and sessions")
        logger.info(f"a job is still running; waiting {IDLE_POLL}s")
        time.sleep(IDLE_POLL)


def _open_modal(page) -> None:
    page.click(TRIGGER)
    # Bootstrap 4 fades the modal in; .show lands when the transition ends.
    page.wait_for_selector(MODAL_SHOWN, state="visible")


def _delete_all(page, context: FessContext, page_url: str,
                success_key: str) -> None:
    """Cancel the modal, prove nothing was deleted, then confirm."""
    page.goto(context.url(page_url))
    page.wait_for_load_state("domcontentloaded")

    before = page.locator(ROWS).count()
    # Red on an empty list, which is the state this cannot run in: the
    # trigger sits inside <c:if test="${pager.allRecordCount > 0}">, so it
    # is absent rather than disabled. Failing loudly here beats skipping.
    assert_true(page.locator(TRIGGER).count() == 1,
                f"{page_url} rendered no {TRIGGER}. The list holds {before} "
                f"row(s); the button only renders when allRecordCount > 0 and "
                f"the user is editable.")
    assert_true(before > 0,
                f"{page_url} rendered the delete-all trigger but no rows")

    logger.info(f"{page_url}: cancel leaves the data alone")
    _open_modal(page)
    page.click(CANCEL)
    page.wait_for_selector(MODAL, state="hidden")
    # The real assertion of the cancel path. Red if cancel ever submits the
    # form -- .btn-outline-light matches both footer buttons, and only the
    # data-dismiss attribute separates cancel from deleteall.
    after_cancel = page.locator(ROWS).count()
    assert_equal(after_cancel, before,
                 f"{page_url}: cancelling the modal changed the list from "
                 f"{before} to {after_cancel} row(s); it must not delete")

    logger.info(f"{page_url}: confirm deletes")
    _open_modal(page)
    page.click(CONFIRM)
    page.wait_for_load_state("domcontentloaded")

    # deleteall() ends in redirect(getClass()), and saveInfo survives it in
    # the session. This alert is the only discriminator: a failed
    # verifyToken renders the very same list page via asListHtml, at the
    # very same URL, just without it.
    assert_true(page.locator(SUCCESS_ALERT).count() > 0,
                f"{page_url}: no {SUCCESS_ALERT} after confirming delete-all; "
                f"the submit did not reach deleteall() (URL is {page.url} "
                f"either way)")
    expected = tm(success_key)
    alert = page.locator(SUCCESS_ALERT).first.inner_text().strip()
    # Each page has its own key, so this is red if the modal's submit
    # dispatched to a different page's action.
    assert_equal(alert, expected,
                 f"{page_url}: expected {expected!r}, got {alert!r}")

    # The list really is empty now, so the <c:if> drops the table and the
    # trigger and renders the empty-list notice instead. Red if deleteall
    # reports success without deleting -- exactly what searchlog's no-op
    # implementation does. The reload also drops the flash message asserted
    # above, which is why that came first.
    deadline = time.time() + EMPTY_TIMEOUT
    while page.locator(ROWS).count() > 0 and time.time() < deadline:
        time.sleep(EMPTY_POLL)
        page.goto(context.url(page_url))
        page.wait_for_load_state("domcontentloaded")
    rows_left = page.locator(ROWS).count()
    assert_equal(rows_left, 0,
                 f"{page_url}: {rows_left} row(s) survived a delete-all that "
                 f"reported success, and were still there {EMPTY_TIMEOUT}s later "
                 f"-- so this is a failed delete, not a slow index refresh")
    assert_true(t(Labels.LIST_COULD_NOT_FIND_CRUD_TABLE) in page.inner_text("body"),
                f"{page_url}: the emptied list did not render the empty-list "
                f"notice")
    assert_true(page.locator(TRIGGER).count() == 0,
                f"{page_url}: the delete-all trigger still renders on an empty "
                f"list")


def run(context: FessContext) -> None:
    logger.info("Starting sysinfo deleteall")
    page = context.get_admin_page()

    _wait_until_no_job_running(page, context)

    _delete_all(page, context, JOBLOG_URL, Messages.SUCCESS_JOB_LOG_DELETE_ALL)
    _delete_all(page, context, CRAWLINGINFO_URL,
                Messages.SUCCESS_CRAWLING_INFO_DELETE_ALL)

    logger.info("sysinfo deleteall completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
