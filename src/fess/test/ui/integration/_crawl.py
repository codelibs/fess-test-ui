"""Helpers for the workflows that crawl a sample page and look at the result."""
import os
import time
from typing import List

from playwright.sync_api import Page

from fess.test import assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.cleanup import assert_absent

SAMPLEDATA_URL = os.environ.get("SAMPLEDATA_URL", "http://sampledata01/")
CRAWL_TIMEOUT = int(os.environ.get("CRAWL_TIMEOUT", "240"))
# The Default Crawler also re-crawls the seed site, which takes minutes even
# when nothing changed, and a workflow that follows another one has to wait
# for that crawl to end before it can start its own.
START_TIMEOUT = int(os.environ.get("CRAWL_START_TIMEOUT", "600"))
POLL_INTERVAL = 3
DEFAULT_CRAWLER = "Default Crawler"

# The admin sees a page in the Search List (and can delete it) only through
# a permission of its own.
ADMIN_PERMISSION = "{role}admin"


def delete_via_details(page: Page, context: FessContext, list_path: str,
                        name: str, delete_label: str) -> None:
    page.goto(context.url(list_path))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    page.click(f'button:has-text("{delete_label}"), a:has-text("{delete_label}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")
    assert_absent(page, name, list_path)


def create_webconfig(page: Page, context: FessContext, name: str, url: str,
                      permission: str) -> None:
    """Create a crawl config that fetches just `url`, with `permission`."""
    page.goto(context.url("/admin/webconfig/"))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill('input[name="name"]', name)
    page.fill('textarea[name="urls"]', url)
    page.fill('textarea[name="includedUrls"]', url)
    page.fill('input[name="maxAccessCount"]', "1")
    page.fill('input[name="numOfThread"]', "1")
    page.fill('textarea[name="permissions"]', f"{permission}\n{ADMIN_PERMISSION}")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_true(name in page.inner_text("table"), f"webconfig {name} not in list after create")


def start_job(page: Page, context: FessContext, job_name: str) -> None:
    """Start a scheduler job from its details page, once it is not running.

    A job that is running offers Stop instead of Start. The seed crawl can
    still be running when this workflow starts, and a crawl begun before the
    configs above were saved would not have picked them up.
    """
    deadline = time.time() + START_TIMEOUT
    while time.time() < deadline:
        page.goto(context.url("/admin/scheduler/"))
        page.wait_for_load_state("domcontentloaded")
        page.click(f"text={job_name}")
        page.wait_for_load_state("domcontentloaded")
        assert_true("/admin/scheduler/details/" in page.url,
                    f"expected the scheduler details page, got {page.url}")
        if page.locator('button[name="start"]').count() > 0:
            page.click('button[name="start"]')
            page.wait_for_load_state("domcontentloaded")
            return
        time.sleep(POLL_INTERVAL)
    raise AssertionError(f"{job_name} was still running after {START_TIMEOUT}s")


def delete_indexed_pages(page: Page, context: FessContext, query: str, expected: int) -> None:
    """Remove the crawled pages matching `query` from the index with the Search List.

    The Search List shows an administrator only the documents the
    administrator may see, hence the extra {role}admin permission on every
    crawl config. Exactly `expected` must be found: the pages were searchable
    a moment ago, so finding fewer means the clean-up could not work, not
    that there was nothing to clean.
    """
    deleted: set = set()
    deadline = time.time() + 60
    while time.time() < deadline:
        page.goto(context.url("/admin/searchlist/?search=Search&q=" + query))
        page.wait_for_load_state("domcontentloaded")
        buttons = page.locator('button[data-target="#confirmToDelete"]')
        # A document deleted a moment ago can still be listed until the index
        # refreshes. Ask again rather than delete it twice or count it twice.
        pending = [b for b in range(buttons.count())
                   if buttons.nth(b).get_attribute("data-docid") not in deleted]
        if buttons.count() == 0:
            break
        if not pending:
            time.sleep(1)
            continue
        button = buttons.nth(pending[0])
        deleted.add(button.get_attribute("data-docid"))
        button.click()
        page.wait_for_selector('#confirmToDelete button[name="delete"]', state="visible")
        page.click('#confirmToDelete button[name="delete"]')
        page.wait_for_load_state("domcontentloaded")
    else:
        raise AssertionError("the deleted pages are still listed in the Search List after 60s")
    assert_equal(len(deleted), expected, "documents removed from the index")


def search_urls(page: Page, context: FessContext, query: str) -> List[str]:
    """URLs of the hits for `query`, as the visitor behind `page` sees them."""
    resp = page.request.get(context.url(f"/api/v2/search?q={query}&num=20"))
    if resp.ok:
        try:
            payload = resp.json().get("response", {})
            return [d.get("url", "") for d in payload.get("data", [])]
        except ValueError:
            pass
    resp = page.request.get(context.url(f"/api/v1/documents?q={query}&size=20"))
    assert_true(resp.ok, f"search for {query} answered HTTP {resp.status}")
    return [d.get("url", "") for d in resp.json().get("data", [])]

