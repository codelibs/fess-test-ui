"""Who can see what: documents crawled with permissions are visible only to
the matching role, group and nobody else.

The other search modules look at the public index as an administrator or an
anonymous visitor. None of them signs in as an ordinary user, so a regression
that shows a restricted document to the wrong person -- or hides it from the
person it was granted to -- goes unnoticed. This workflow builds the whole
chain through the admin UI and then asks as each kind of visitor:

1. Create a role, a group and three users: one with the role, one in the
   group, one with neither.
2. Create three crawl configs, each pointing at one page of the sample site
   that nothing links to, so the seed crawl never indexes them:
   permission {role}<role>, permission {group}<group>, permission {role}guest.
3. Start the Default Crawler, which crawls every config.
4. Search for each page's marker word as the role user, the group user, the
   user with neither, and an anonymous visitor.

The positive cases (each grantee sees the page) are checked first and
double as the wait for the crawl: an absence only proves something once the
crawl has demonstrably finished, otherwise "not found yet" would pass.

The search goes through the JSON API with the signed-in browser session
(/api/v2/search, /api/v1/documents on releases without v2), the same
permission filter the search page uses, without depending on which search
UI the Fess version serves.

Everything it creates is deleted again, the indexed pages included: deleting
a crawl config leaves its documents searchable until they expire.
"""
import logging
import os
import time
from typing import Dict, List, Optional

from playwright.sync_api import Page, Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from fess.test.ui.cleanup import Cleanup, assert_absent

logger = logging.getLogger(__name__)

SAMPLEDATA_URL = os.environ.get("SAMPLEDATA_URL", "http://sampledata01/")
CRAWL_TIMEOUT = int(os.environ.get("ROLE_SEARCH_CRAWL_TIMEOUT", "240"))
POLL_INTERVAL = 3
DEFAULT_CRAWLER = "Default Crawler"

# page -> word that appears only on that page (sampledata/content/restricted)
PAGES = ("role", "group", "public")
# The admin sees a page in the Search List (and can delete it) only through
# a permission of its own.
ADMIN_PERMISSION = "{role}admin"
SEARCH_LIST_QUERY = "Restricted"  # the title word of the three pages


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


# --- admin UI helpers -------------------------------------------------------


def _delete_via_details(page: Page, context: FessContext, list_path: str,
                        name: str, delete_label: str) -> None:
    page.goto(context.url(list_path))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={name}")
    page.wait_for_load_state("domcontentloaded")
    page.click(f'button:has-text("{delete_label}"), a:has-text("{delete_label}")')
    page.click('div.modal-footer button[name="delete"]')
    page.wait_for_load_state("domcontentloaded")
    assert_absent(page, name, list_path)


def _create_named(page: Page, context: FessContext, list_path: str, name: str) -> None:
    """Role and group share one form: a name and a Create button."""
    page.goto(context.url(list_path))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill('input[name="name"]', name)
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_true(name in page.inner_text("table"), f"{name} not in {list_path} after create")


def _create_user(page: Page, context: FessContext, name: str, password: str,
                 role: Optional[str] = None, group: Optional[str] = None) -> None:
    page.goto(context.url("/admin/user/"))
    page.wait_for_load_state("domcontentloaded")
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.fill('input[name="name"]', name)
    page.fill('input[name="password"]', password)
    page.fill('input[name="confirmPassword"]', password)
    if role is not None:
        page.select_option('select[name="roles"]', label=role)
    if group is not None:
        page.select_option('select[name="groups"]', label=group)
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_true(name in page.inner_text("table"), f"user {name} not in list after create")


def _create_webconfig(page: Page, context: FessContext, name: str, url: str,
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


def _start_job(page: Page, context: FessContext, job_name: str) -> None:
    """Start a scheduler job from its details page, once it is not running.

    A job that is running offers Stop instead of Start. The seed crawl can
    still be running when this workflow starts, and a crawl begun before the
    configs above were saved would not have picked them up.
    """
    deadline = time.time() + CRAWL_TIMEOUT
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
    raise AssertionError(f"{job_name} was still running after {CRAWL_TIMEOUT}s")


def _delete_indexed_pages(page: Page, context: FessContext) -> None:
    """Remove the crawled pages from the index with the Search List.

    The Search List shows an administrator only the documents the
    administrator may see, hence the extra {role}admin permission on every
    crawl config. All of them must be found: the pages were searchable a
    moment ago, so finding fewer means the clean-up could not work, not that
    there was nothing to clean.
    """
    deleted: set = set()
    deadline = time.time() + 60
    while time.time() < deadline:
        page.goto(context.url("/admin/searchlist/?search=Search&q=" + SEARCH_LIST_QUERY))
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
    assert_equal(len(deleted), len(PAGES), "documents removed from the index")


# --- search as a visitor ----------------------------------------------------


def _login(page: Page, context: FessContext, username: str, password: str) -> None:
    page.goto(context.url(f"/login/?browser_lang={context.lang}"))
    page.wait_for_load_state("domcontentloaded")
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]', username)
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_PASSWORD)}"]', password)
    page.click(f'button:has-text("{t(Labels.LOGIN)}")')
    page.wait_for_load_state("domcontentloaded")
    assert_true("/login" not in page.url, f"login as {username} did not leave the login page: {page.url}")


def _search_urls(page: Page, context: FessContext, query: str) -> List[str]:
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


def _visible_pages(page: Page, context: FessContext) -> Dict[str, bool]:
    """Which of the restricted pages this visitor finds."""
    return {
        name: any(url.endswith(f"/restricted/{name}.html")
                  for url in _search_urls(page, context, f"accessmarker{name}"))
        for name in PAGES
    }


def _wait_until_visible(page: Page, context: FessContext, who: str, name: str) -> None:
    deadline = time.time() + CRAWL_TIMEOUT
    while time.time() < deadline:
        if _visible_pages(page, context)[name]:
            return
        time.sleep(POLL_INTERVAL)
    raise AssertionError(
        f"{who} did not find the {name} page within {CRAWL_TIMEOUT}s of the crawl")


# --- the workflow -----------------------------------------------------------


def run(context: FessContext) -> None:
    logger.info("start role search workflow integration test")

    page = context.get_admin_page()
    base = context.generate_str(8).lower()
    role_name, group_name = f"rsrole{base}", f"rsgroup{base}"
    role_user, group_user, plain_user = (f"rsr{base}", f"rsg{base}", f"rsn{base}")
    password = "Pw-" + context.generate_str(16)
    permissions = {
        "role": f"{{role}}{role_name}",
        "group": f"{{group}}{group_name}",
        "public": "{role}guest",
    }
    configs: Dict[str, str] = {}
    created: List[str] = []

    try:
        logger.info("Step 1: role, group and users")
        _create_named(page, context, "/admin/role/", role_name)
        created.append("role")
        _create_named(page, context, "/admin/group/", group_name)
        created.append("group")
        _create_user(page, context, role_user, password, role=role_name)
        created.append("role_user")
        _create_user(page, context, group_user, password, group=group_name)
        created.append("group_user")
        _create_user(page, context, plain_user, password)
        created.append("plain_user")

        logger.info("Step 2: one crawl config per page, each with its permission")
        for name in PAGES:
            config_name = f"RoleSearch_{name}_{base}"
            configs[name] = config_name
            _create_webconfig(
                page, context, config_name,
                f"{SAMPLEDATA_URL}restricted/{name}.html", permissions[name])
            created.append(f"webconfig_{name}")

        logger.info("Step 3: start the Default Crawler")
        _start_job(page, context, DEFAULT_CRAWLER)
        created.append("crawl")

        logger.info("Step 4: search as each visitor")
        with context.guest_page() as anon, context.guest_page() as by_role, \
                context.guest_page() as by_group, context.guest_page() as by_none:
            _login(by_role, context, role_user, password)
            _login(by_group, context, group_user, password)
            _login(by_none, context, plain_user, password)

            # Positives first: they are also the wait for the crawl.
            _wait_until_visible(anon, context, "an anonymous visitor", "public")
            _wait_until_visible(by_role, context, f"user {role_user}", "role")
            _wait_until_visible(by_group, context, f"user {group_user}", "group")

            anon_sees = _visible_pages(anon, context)
            role_sees = _visible_pages(by_role, context)
            group_sees = _visible_pages(by_group, context)
            none_sees = _visible_pages(by_none, context)

            # What each visitor must see. The public page is left out for the
            # signed-in users: whether a user without the guest role finds
            # {role}guest pages is not what this workflow pins down.
            assert_equal(anon_sees, {"role": False, "group": False, "public": True},
                         "anonymous visitor: only the {role}guest page")
            assert_equal((role_sees["role"], role_sees["group"]), (True, False),
                         f"user {role_user}: the role page, not the group page")
            assert_equal((group_sees["role"], group_sees["group"]), (False, True),
                         f"user {group_user}: the group page, not the role page")
            assert_equal((none_sees["role"], none_sees["group"]), (False, False),
                         f"user {plain_user}: neither restricted page")
        logger.info("✓ every visitor saw exactly the pages granted to them")
    finally:
        cleanup = Cleanup()
        deletions = [
            *[(f"webconfig_{n}", "/admin/webconfig/", configs.get(n), t(Labels.CRUD_BUTTON_DELETE))
              for n in PAGES],
            ("role_user", "/admin/user/", role_user, t(Labels.CRUD_BUTTON_DELETE)),
            ("group_user", "/admin/user/", group_user, t(Labels.CRUD_BUTTON_DELETE)),
            ("plain_user", "/admin/user/", plain_user, t(Labels.CRUD_BUTTON_DELETE)),
            ("group", "/admin/group/", group_name, t(Labels.CRUD_BUTTON_DELETE)),
            ("role", "/admin/role/", role_name, t(Labels.CRUD_BUTTON_DELETE)),
        ]
        if "crawl" in created:
            with cleanup.guard("indexed restricted pages"):
                _delete_indexed_pages(page, context)
        for key, list_path, name, label in deletions:
            if key in created and name:
                with cleanup.guard(f"{key} '{name}' (user passwords are random per run)"):
                    _delete_via_details(page, context, list_path, name, label)
        cleanup.escalate()

    logger.info("✓ role search workflow integration test completed successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        try:
            run(context)
        finally:
            destroy(context)
