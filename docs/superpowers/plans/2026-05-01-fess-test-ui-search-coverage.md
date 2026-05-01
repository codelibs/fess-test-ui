# fess-test-ui Search-Side Coverage Expansion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Playwright UI test coverage for the Fess search-side pages `/`, `/help/`, `/login/`, `/profile/`, and a real form-submit path, plus extend `console_errors` to sweep `/` and `/help/`.

**Architecture:** Follow the existing `src/fess/test/ui/search/*.py` pattern — each module is a leaf exporting `setup(playwright) → FessContext`, `run(context)`, `destroy(context)` plus a `__main__` block. `main.py` orchestrates them in a fixed default order using a single shared `FessContext`. No pytest, no harness — `run_test.sh` is the only entry point. New modules slot into `main.py` in three places (import / `all_modules` dict / default-order list), exactly like the existing `search_*` modules. All new selectors use locale-independent HTML `name=` attributes, so no new i18n keys are required.

**Tech Stack:** Python 3.11+, Playwright 1.56.0, BeautifulSoup4, Docker Compose. Local single-module runs use `python -m fess.test.ui.search.<module>` with `FESS_URL` and `FESS_LABEL_DIR` env vars.

**Spec:** `docs/superpowers/specs/2026-05-01-fess-test-ui-search-coverage-design.md`

**Branch strategy:** Single feature branch `feat/search-side-coverage`. One PR at the end. Each task ends with a commit so progress is easy to review.

---

## Pre-flight (do once before Task 1)

- [ ] **PF-1: Create the feature branch**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git checkout main
git pull --ff-only origin main
git checkout -b feat/search-side-coverage
```

- [ ] **PF-2: Confirm a local Fess instance is reachable**

Tests in this plan are validated by running each new module against the running Fess at `http://localhost:8080`. Confirm it:

```bash
/usr/bin/curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
```

Expected: `200`. If not, start Fess (e.g. `./scripts/fess-server.sh start` from fess-workspace, or `repos/fess/bin/fess`) before continuing.

- [ ] **PF-3: Make Fess label files available for local single-module runs**

`FessContext` requires `FESS_LABEL_DIR` to point at a directory holding `fess_label_*.properties` and `fess_message_*.properties`. The convenience approach for local validation is to copy the source-tree label files (the running Fess uses the same files):

```bash
mkdir -p /tmp/fess-test-ui-labels
cp /Users/shinsuke/workspace/fess-workspace/repos/fess/src/main/resources/fess_label*.properties /tmp/fess-test-ui-labels/
cp /Users/shinsuke/workspace/fess-workspace/repos/fess/src/main/resources/fess_message*.properties /tmp/fess-test-ui-labels/
ls /tmp/fess-test-ui-labels | wc -l
```

Expected: ~33 (16 label locales + 16 message locales + base files). This dir is referenced by every local-run command in this plan.

- [ ] **PF-4: Confirm Python deps are installed**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
python3 -c "import playwright, bs4, requests" && echo OK
```

If it errors, run `pip install -r requirements.txt && playwright install chromium`.

---

## Task 1: `search/root_top.py` — verify `/` renders the search form

**Files:**
- Create: `src/fess/test/ui/search/root_top.py`

- [ ] **Step 1: Write the new module**

Create `src/fess/test/ui/search/root_top.py` with this exact content:

```python
"""Open / (RootAction) and assert the search form + Help header link render.

Distinct from search/top.py, which exercises /search/.
"""
import logging
import re

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


# LastaFlute renders missing labels as "???labels.x???".
_MISSING_KEY_PATTERN = re.compile(r'\?{2,}labels\.[A-Za-z0-9_.]+\?{2,}')


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/root_top")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    page.wait_for_load_state("domcontentloaded")

    assert_true(page.query_selector('input[name="q"]') is not None,
                'search input[name="q"] missing on /')
    assert_true(page.query_selector('button[name="search"]') is not None,
                'search button[name="search"] missing on /')

    # Help link is always present in the header on /.
    # AI Search link is feature-flag gated, so we don't assert it here.
    assert_true(page.query_selector('a[href="/help/"]') is not None,
                'help link a[href="/help/"] missing on /')

    body = page.inner_text("body")
    matches = _MISSING_KEY_PATTERN.findall(body)
    assert_true(len(matches) == 0,
                f"untranslated label keys on /: {matches[:5]}")

    logger.info("search/root_top completed")


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
```

- [ ] **Step 2: Run the module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.root_top
```

Expected: process exits 0, last log line `search/root_top completed`.

- [ ] **Step 3: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/root_top.py
git commit -m "feat(test): add search/root_top module exercising / (RootAction)"
```

---

## Task 2: `search/help.py` — verify `/help/` renders

**Files:**
- Create: `src/fess/test/ui/search/help.py`

- [ ] **Step 1: Write the new module**

Create `src/fess/test/ui/search/help.py` with this exact content:

```python
"""Open /help/ (HelpAction) and assert the search form + a non-empty body render."""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/help")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/help/"))
    page.wait_for_load_state("domcontentloaded")

    # If HelpAction redirected to /login/, isLoginRequired() is misconfigured for
    # this run — surface it as a failure rather than silently skipping.
    assert_true("/help/" in page.url,
                f"expected /help/ in URL after navigation, got {page.url}")

    assert_true(page.query_selector('input[name="q"]') is not None,
                'search input[name="q"] missing on /help/')
    assert_true(page.query_selector('button[name="search"]') is not None,
                'search button[name="search"] missing on /help/')

    # Body must render some content beyond an empty shell.
    body_text = page.inner_text("body")
    assert_true(len(body_text.strip()) > 0,
                "/help/ rendered an empty body")

    logger.info("search/help completed")


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
```

- [ ] **Step 2: Run the module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.help
```

Expected: exit 0, `search/help completed` in log.

- [ ] **Step 3: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/help.py
git commit -m "feat(test): add search/help module exercising /help/ (HelpAction)"
```

---

## Task 3: `search/login_form.py` — verify `/login/` renders + empty submit yields validation error

**Files:**
- Create: `src/fess/test/ui/search/login_form.py`

This module deliberately does NOT call `context.login()` for its own assertions — it needs an unauthenticated context, otherwise LastaFlute redirects `/login/` to `/`. It still goes through the suite-wide `setup`/`destroy` so screenshot/trace plumbing works on failure.

- [ ] **Step 1: Write the new module**

Create `src/fess/test/ui/search/login_form.py` with this exact content:

```python
"""Verify /login/ renders the form and surfaces a validation/error response on empty submit.

Uses a fresh, unauthenticated Playwright BrowserContext so an
already-logged-in suite session does not redirect /login/ to /.
"""
import logging
import os

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    # Reuse the suite-wide login/teardown plumbing so tracing/screenshots work,
    # but the actual login_form test below opens its own ephemeral context.
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/login_form")

    base_url = os.environ.get("FESS_URL", "http://localhost:8080")
    fresh_browser = context._playwright.chromium.launch(
        headless=os.environ.get("HEADLESS", "false").lower() == "true",
        slow_mo=500,
    )
    try:
        fresh_ctx = fresh_browser.new_context(locale=context.browser_locale)
        try:
            page = fresh_ctx.new_page()
            page.goto(f"{base_url}/login/?browser_lang={context.lang}")
            page.wait_for_load_state("domcontentloaded")

            assert_true("/login/" in page.url,
                        f"expected /login/ in URL, got {page.url}")
            assert_true(page.query_selector('input[name="username"]') is not None,
                        'login input[name="username"] missing on /login/')
            assert_true(page.query_selector('input[name="password"]') is not None,
                        'login input[name="password"] missing on /login/')
            assert_true(page.query_selector('button[name="login"]') is not None,
                        'login button[name="login"] missing on /login/')

            # Empty submit: the inputs do not have HTML5 `required`, so the form
            # actually POSTs. Server-side validation should keep us on /login/
            # and re-render the form.
            page.click('button[name="login"]')
            page.wait_for_load_state("domcontentloaded")

            assert_true("/login/" in page.url,
                        f"after empty submit, expected to stay on /login/, got {page.url}")
            assert_true(page.query_selector('input[name="username"]') is not None,
                        "after empty submit, login form not re-rendered")
        finally:
            fresh_ctx.close()
    finally:
        fresh_browser.close()

    logger.info("search/login_form completed")


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
```

- [ ] **Step 2: Run the module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.login_form
```

Expected: exit 0, `search/login_form completed` in log.

- [ ] **Step 3: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/login_form.py
git commit -m "feat(test): add search/login_form module exercising /login/ (LoginAction)"
```

---

## Task 4: `search/profile_form.py` — verify `/profile/` validation without changing the password

**Files:**
- Create: `src/fess/test/ui/search/profile_form.py`

⚠️ **Critical safety property:** this test must never submit a successful password change. The whole suite re-uses `admin/admin`. The submission below uses a **mismatched** new/confirm password, which `ProfileAction.validatePasswordForm` rejects before any DB write.

- [ ] **Step 1: Write the new module**

Create `src/fess/test/ui/search/profile_form.py` with this exact content:

```python
"""Verify /profile/ renders the password-change form and rejects mismatched confirm.

NEVER submits a successful password change — the whole suite reuses
admin/admin credentials. The submission deliberately uses
newPassword != confirmNewPassword, which ProfileAction validates
before any persistence.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

OLD_PASSWORD = "admin"
NEW_PASSWORD = "Mismatch1!Aaaa"
CONFIRM_NEW_PASSWORD = "Mismatch1!Bbbb"  # intentionally != NEW_PASSWORD


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/profile_form")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/profile/"))
    page.wait_for_load_state("domcontentloaded")

    assert_true("/profile/" in page.url,
                f"expected /profile/ in URL, got {page.url}")
    for field in ("oldPassword", "newPassword", "confirmNewPassword"):
        assert_true(page.query_selector(f'input[name="{field}"]') is not None,
                    f'profile input[name="{field}"] missing on /profile/')
    assert_true(page.query_selector('button[name="changePassword"]') is not None,
                'profile submit button[name="changePassword"] missing on /profile/')

    # Submit with mismatched confirm. ProfileAction rejects this in
    # validatePasswordForm without writing to the user store.
    page.fill('input[name="oldPassword"]', OLD_PASSWORD)
    page.fill('input[name="newPassword"]', NEW_PASSWORD)
    page.fill('input[name="confirmNewPassword"]', CONFIRM_NEW_PASSWORD)
    page.click('button[name="changePassword"]')
    page.wait_for_load_state("domcontentloaded")

    # After validation error, ProfileAction re-renders the profile page.
    assert_true("/profile/" in page.url,
                f"after mismatched-confirm submit, expected /profile/, got {page.url}")
    # Form is still rendered (validation path, not a 5xx).
    assert_true(page.query_selector('input[name="newPassword"]') is not None,
                "after mismatched-confirm submit, profile form not re-rendered")

    logger.info("search/profile_form completed")


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
```

- [ ] **Step 2: Run the module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.profile_form
```

Expected: exit 0, `search/profile_form completed` in log.

- [ ] **Step 3: Verify admin password is still `admin`**

Quick sanity check that the test did not actually change the password:

```bash
/usr/bin/curl -s -c /tmp/fessauth.txt -b /tmp/fessauth.txt http://localhost:8080/login/ > /dev/null
/usr/bin/curl -s -o /dev/null -w "Login attempt: %{http_code}\n" \
  -c /tmp/fessauth.txt -b /tmp/fessauth.txt \
  -X POST http://localhost:8080/login/login \
  --data-urlencode "username=admin" \
  --data-urlencode "password=admin"
rm -f /tmp/fessauth.txt
```

Expected: `200`. Anything else → STOP and investigate before proceeding.

- [ ] **Step 4: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/profile_form.py
git commit -m "feat(test): add search/profile_form exercising /profile/ validation path"
```

---

## Task 5: `search/form_submit.py` — verify the search form submits via real UI click

**Files:**
- Create: `src/fess/test/ui/search/form_submit.py`

- [ ] **Step 1: Write the new module**

Create `src/fess/test/ui/search/form_submit.py` with this exact content:

```python
"""Verify the search form submits via UI: fill q on / and click search → /search/?q=...

Existing search/* modules construct the URL directly. This module exercises
the GET-form action wiring so a regression in form submission would surface.
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)

QUERY = "a"  # single-character query — locale-neutral, always submittable.


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/form_submit")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    page.wait_for_load_state("domcontentloaded")

    page.fill('input[name="q"]', QUERY)
    page.click('button[name="search"]')
    page.wait_for_load_state("domcontentloaded")

    assert_true("/search/" in page.url,
                f"after form submit, expected /search/ in URL, got {page.url}")
    assert_true(f"q={QUERY}" in page.url,
                f"after form submit, expected q={QUERY} in URL, got {page.url}")

    # Page rendered without raising — body text just has to be non-empty.
    body_text = page.inner_text("body")
    assert_true(len(body_text.strip()) > 0,
                "/search/ after form submit rendered an empty body")

    logger.info("search/form_submit completed")


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
```

- [ ] **Step 2: Run the module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.form_submit
```

Expected: exit 0, `search/form_submit completed` in log.

- [ ] **Step 3: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/form_submit.py
git commit -m "feat(test): add search/form_submit module exercising form-driven /search/ navigation"
```

---

## Task 6: Extend `search/console_errors.py` to cover `/` and `/help/`

**Files:**
- Modify: `src/fess/test/ui/search/console_errors.py:21-26`

- [ ] **Step 1: Add `/` and `/help/` to PAGES_TO_VISIT**

Edit `src/fess/test/ui/search/console_errors.py`. Replace the `PAGES_TO_VISIT` list with this expanded version (preserve order — root and help first, then search/admin):

```python
PAGES_TO_VISIT = [
    "/",
    "/search/",
    "/help/",
    "/admin/",
    "/admin/dashboard/",
    "/admin/badword/",
]
```

Do **not** add `/chat/` (out of scope per spec). Do **not** add `/login/` here — `console_errors` reuses the suite's logged-in session, which redirects `/login/` to `/`.

- [ ] **Step 2: Run the extended module standalone against local Fess**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_URL=http://localhost:8080 \
TEST_LANG=en \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
HEADLESS=true \
python -m fess.test.ui.search.console_errors
```

Expected: exit 0, `search/console_errors completed`. If a real JS error is detected on `/` or `/help/`, that is a genuine bug and should be reported — pause this plan and discuss before continuing.

- [ ] **Step 3: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/fess/test/ui/search/console_errors.py
git commit -m "feat(test): extend search/console_errors to sweep / and /help/"
```

---

## Task 7: Wire new modules into `main.py`

**Files:**
- Modify: `src/main.py:65-81` (import block)
- Modify: `src/main.py:121-180` (`all_modules` dict)
- Modify: `src/main.py:185-208` (default-order list)
- Modify: `src/fess/test/ui/search/__init__.py` (export new submodules)

- [ ] **Step 1: Update `src/fess/test/ui/search/__init__.py`**

Replace the file's contents with:

```python
from fess.test.ui.search import (
    facet,
    form_submit,
    help,
    login_form,
    no_results,
    pagination,
    profile_form,
    query,
    related,
    root_top,
    seed,
    sort,
    suggest,
    thumbnail,
    top,
)

__all__ = [
    "facet",
    "form_submit",
    "help",
    "login_form",
    "no_results",
    "pagination",
    "profile_form",
    "query",
    "related",
    "root_top",
    "seed",
    "sort",
    "suggest",
    "thumbnail",
    "top",
]
```

- [ ] **Step 2: Update the import block in `src/main.py`**

Find the `from fess.test.ui.search import (` block (currently around lines 65–81) and replace its contents with this expanded version (adds 5 new aliases, keeps all existing):

```python
from fess.test.ui.search import (
    facet as search_facet,
    form_submit as search_form_submit,
    help as search_help,
    login_form as search_login_form,
    no_results as search_no_results,
    pagination as search_pagination,
    profile_form as search_profile_form,
    query as search_query,
    related as search_related,
    root_top as search_root_top,
    seed as search_seed,
    sort as search_sort,
    suggest as search_suggest,
    thumbnail as search_thumbnail,
    top as search_top,
    i18n_smoke as search_i18n_smoke,
    multibyte_query as search_multibyte_query,
    layout_overflow as search_layout_overflow,
    console_errors as search_console_errors,
    multibyte_admin_input as search_multibyte_admin_input,
)
```

- [ ] **Step 3: Update the `all_modules` dict in `get_modules_to_run()`**

Find the `all_modules = { ... }` dict (currently around lines 121–180). Add five new entries near the existing `search_*` entries — place them right after `'search_seed': search_seed,`:

```python
        'search_seed': search_seed,
        'search_root_top': search_root_top,
        'search_top': search_top,
        'search_help': search_help,
        'search_login_form': search_login_form,
        'search_profile_form': search_profile_form,
        'search_form_submit': search_form_submit,
        'search_query': search_query,
```

(Leave the rest of the dict — `search_no_results`, `search_pagination`, etc. — untouched.)

- [ ] **Step 4: Update the default-order list (`if test_modules_env == 'all'` branch)**

Find the default-order `return [...]` list (currently around lines 187–208). Replace the existing `search_*` block (from `search_seed,` through `search_multibyte_admin_input,`) with this expanded order:

```python
            search_seed,
            search_root_top, search_top, search_help, search_login_form,
            search_profile_form, search_form_submit,
            search_query, search_no_results,
            search_pagination, search_facet, search_sort,
            search_thumbnail, search_suggest, search_related,
            search_i18n_smoke, search_multibyte_query,
            search_layout_overflow, search_console_errors,
            search_multibyte_admin_input,
```

- [ ] **Step 5: Verify imports resolve and the new modules are registered**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
FESS_LABEL_DIR=/tmp/fess-test-ui-labels TEST_LANG=en python3 -c "
import main
mods = main.get_modules_to_run()
names = [m.__name__.split('.')[-1] for m in mods]
print('count:', len(mods))
for n in ('root_top', 'help', 'login_form', 'profile_form', 'form_submit'):
    assert n in names, f'missing module: {n}'
print('OK — all 5 new modules registered in default order')
"
```

Expected: count printed (will be the existing count + 5), and `OK — all 5 new modules registered in default order`. If any assertion fires, fix the import/registration.

- [ ] **Step 6: Verify TEST_MODULES filter resolves the new keys**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
TEST_MODULES=search_root_top,search_help,search_login_form,search_profile_form,search_form_submit \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
TEST_LANG=en \
python3 -c "
import main
mods = main.get_modules_to_run()
print([m.__name__.split('.')[-1] for m in mods])
"
```

Expected: `['root_top', 'help', 'login_form', 'profile_form', 'form_submit']`

- [ ] **Step 7: Commit**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git add src/main.py src/fess/test/ui/search/__init__.py
git commit -m "feat(test): wire new search-side modules into main.py runner"
```

---

## Task 8: Run all five new modules together end-to-end against local Fess

**Files:** none (verification only)

- [ ] **Step 1: Run via TEST_MODULES filter end-to-end**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
TEST_MODULES=search_root_top,search_help,search_login_form,search_profile_form,search_form_submit \
FESS_URL=http://localhost:8080 \
FESS_LABEL_DIR=/tmp/fess-test-ui-labels \
TEST_LANG=en \
HEADLESS=true \
python3 main.py
```

Expected: exit 0. `test_results.json` shows all five modules with `status: passed`.

(`search_seed` is intentionally omitted from this local verification — local Fess is not Docker-Compose-managed and `http://sampledata01/` is unreachable. The new modules don't depend on indexed sample content. CI runs the full suite via `run_test.sh`.)

- [ ] **Step 2: Verify result file**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui/src
python3 -c "
import json
with open('test_results.json') as f:
    data = json.load(f)
for r in data['results']:
    print(r['module'], r['status'])
"
```

Expected: each of `root_top`, `help`, `login_form`, `profile_form`, `form_submit` printed with `passed`.

- [ ] **Step 3: Confirm admin password unchanged after the full run**

```bash
/usr/bin/curl -s -c /tmp/fessauth.txt -b /tmp/fessauth.txt http://localhost:8080/login/ > /dev/null
/usr/bin/curl -s -o /dev/null -w "Login: %{http_code}\n" \
  -c /tmp/fessauth.txt -b /tmp/fessauth.txt \
  -X POST http://localhost:8080/login/login \
  --data-urlencode "username=admin" --data-urlencode "password=admin"
rm -f /tmp/fessauth.txt
```

Expected: `200`.

- [ ] **Step 4: Confirm only generated artifacts are untracked**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git status --short
```

Expected: only the artifact files (`src/test_results.json`, `src/test_metrics_history.json`, `src/screenshots/`, `src/traces/`, `src/logs/`, `src/html_snapshots/`). None of these should be staged. If the repo doesn't gitignore them already, leave them alone — they're test outputs.

---

## Task 9: Open the pull request

**Files:** none (PR only)

- [ ] **Step 1: Push the branch**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
git push -u origin feat/search-side-coverage
```

- [ ] **Step 2: Create the PR via gh**

```bash
cd /Users/shinsuke/workspace/fess-workspace/repos/fess-test-ui
gh pr create --title "feat(test): add search-side UI coverage for /, /help/, /login/, /profile/, and form submit" --body "$(cat <<'EOF'
## Summary

Adds Playwright UI coverage for Fess search-side pages that previously had no tests:

- `search/root_top` — `/` (RootAction) renders the search form + Help link
- `search/help` — `/help/` (HelpAction) renders the search form + non-empty body
- `search/login_form` — `/login/` (LoginAction) renders inputs + empty submit re-renders the form
- `search/profile_form` — `/profile/` (ProfileAction) renders password fields and rejects mismatched confirm **without changing the password**
- `search/form_submit` — submitting the search form via UI navigates to `/search/?q=…`
- Extends `search/console_errors` to also sweep `/` and `/help/`

`/chat/` (RAG) is intentionally out of scope — it requires LLM plugin install and is tracked separately.

Spec: `docs/superpowers/specs/2026-05-01-fess-test-ui-search-coverage-design.md`
Plan: `docs/superpowers/plans/2026-05-01-fess-test-ui-search-coverage.md`

## Test plan

- [ ] `TEST_MODULES=search_root_top,search_help,search_login_form,search_profile_form,search_form_submit ./run_test.sh fessx opensearch3` passes
- [ ] Full `./run_test.sh fessx opensearch3` (TEST_MODULES=all) passes (no regressions)
- [ ] Each new module passes when run individually via `python -m fess.test.ui.search.<module>`
- [ ] Admin password is still `admin/admin` after the suite runs (profile_form uses validation-error path only)
EOF
)"
```

Expected: gh prints the PR URL.

---

## Self-Review Checklist

The plan was self-reviewed against the spec. Findings:

**1. Spec coverage:**
- ✅ root_top → Task 1
- ✅ help → Task 2
- ✅ login_form → Task 3
- ✅ profile_form → Task 4
- ✅ form_submit → Task 5
- ✅ console_errors extension → Task 6
- ✅ main.py wiring (3 places) + search/__init__.py → Task 7
- ✅ "No new i18n keys needed" (per updated spec) → consistent across all tasks
- ✅ Acceptance criteria 1, 3 → Task 8 Step 1
- ✅ Acceptance criteria 5 (admin password preserved) → Task 4 Step 3 + Task 8 Step 3

**2. Placeholder scan:** No TBD/TODO/"appropriate handling" found. Each task has full code blocks.

**3. Type/name consistency:** All `search_*` aliases are spelled identically across the import block, the dict entries, and the default-order list. The `search/__init__.py` `__all__` matches the new module list. No method or constant referenced anywhere is undefined.
