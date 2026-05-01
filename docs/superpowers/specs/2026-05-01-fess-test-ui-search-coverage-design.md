# Search-side UI Coverage Expansion (root / help / login / profile / form-submit)

Date: 2026-05-01
Status: approved scope (chat is excluded — handled separately)
Target repo: `repos/fess-test-ui`

## Goal

Close concrete gaps in `repos/fess-test-ui` coverage of Fess search-side
(non-admin) pages. Today only `/search/` and a few cross-cutting smoke
tests run; the user-facing landing page (`/`), `/help/`, `/login/`, and
`/profile/` are unverified, and no test exercises the search form via
real UI submission. This spec adds five new modules and extends one
existing module in a single PR, deliberately excluding `/chat/` (which
requires LLM plugin setup and will be addressed in a separate change).

## Out of scope (stated explicitly)

- **`/chat/` (RAG)** — requires LLM plugin install. Tracked separately.
- **Actually changing the admin password** — would break subsequent test
  modules that re-use the `admin` credentials. `profile_form` validates
  the form but never submits a successful password change.
- **`/cache/`, `/go/`, `/osdd/`, `/error/*`** — out of scope this round;
  may be added in a future iteration.
- **End-to-end semantic-search / multimodal / theme variants** — these
  live in separate plugin repos.

## Modules

### 1. `search/root_top.py` (new)

Verify the application root (`/`, served by `RootAction`) renders the
search form.

- GET `/`.
- Assert `input[name="q"]` and `button[name="search"]` exist.
- Assert at least one of the two header links present in the running
  Fess UI exists: AI Search (`a[href="/chat/"]`) **or** Help
  (`a[href="/help/"]`). Use a soft check on AI Search (it is hidden
  when chat is disabled at the JSP level, but Help is always present).
- Assert no untranslated label markers (`???labels.x???`) appear in
  body text (cheap reuse of the i18n-smoke pattern).

### 2. `search/help.py` (new)

Verify `/help/` renders.

- GET `/help/`.
- `HelpAction` redirects to `/login/` if `isLoginRequired()` is true,
  so the test runs after `context.login()` (other admin modules already
  rely on the same authenticated session).
- Assert the search form (`input[name="q"]`, `button[name="search"]`)
  appears in the header.
- Assert the help body region renders (a non-empty `<main>`/`<body>`
  inner text beyond the header).
- Defensive: tolerate variants where the page returns 200 but the
  customizable `helpPage` content is empty — the wrapper page must
  still render without JS errors. (No console-error assertion here;
  that is `console_errors`'s job.)

### 3. `search/login_form.py` (new)

Verify `/login/` form rendering and basic invalid-submit handling.

- Open `/login/` in a **new, unauthenticated browser context** (do NOT
  reuse the test-suite-wide logged-in session, or LastaFlute redirects
  to `/`).
- Assert `input[name="username"]`, `input[name="password"]`, and the
  login `button` exist (use the localized placeholder/text labels via
  `t(Labels.LOGIN_PLACEHOLDER_USERNAME)` etc., matching how
  `FessContext.login()` already locates them).
- Submit the form **with empty username/password** (no credentials
  guessed). Assert one of:
  - URL stays on `/login/` (LastaFlute re-renders the form), OR
  - the response body contains a Fess error/notification region
    (`.alert`, `[role="alert"]`, or the localized "login failed" text).
- Do **not** attempt invalid credentials with a guessed username —
  that risks tripping account-lockout / rate-limit logic on subsequent
  runs.

### 4. `search/profile_form.py` (new)

Verify `/profile/` (authenticated user's password-change form) renders
and surfaces validation errors, **without changing the password**.

- Reuse the suite-wide authenticated session.
- GET `/profile/`. Assert the three password fields exist:
  `input[name="oldPassword"]`, `input[name="newPassword"]`,
  `input[name="confirmNewPassword"]`.
- Submit with `newPassword != confirmNewPassword` (e.g. `"a1B!aaaa"`
  vs `"a1B!bbbb"`). Assert one of:
  - URL stays on `/profile/`, OR
  - body contains the localized confirm-password mismatch error
    (registered by `ProfileAction.validatePasswordForm`).
- Verify the form is still rendered on the response (so we know we
  hit a validation path, not a 5xx).
- Never call the success path — admin's password must remain `admin`
  for downstream modules.

### 5. `search/form_submit.py` (new)

Verify the search form actually submits via UI (rather than direct URL
construction, which is what every existing `search/*` test does).

- GET `/`.
- `fill('input[name="q"]', "a")` — single-character query keeps it
  locale-neutral.
- `click('button[name="search"]')`.
- Assert URL is now under `/search/` and contains `q=a`.
- Assert the page's `body` rendered without raising — no specific
  result-count expectation (covered by `query` / `no_results`).
- Goal: regression-detect breakage in the GET-form action wiring,
  not result quality.

### 6. `search/console_errors.py` (extension, not new)

Add `/` and `/help/` to `PAGES_TO_VISIT`. Do not add `/chat/` (per
scope). Existing noise filter is reused unchanged.

## Module registration (`src/main.py`)

Update three places, mirroring the existing `search_*` pattern:

1. **import block** — add the five new aliases:
   ```python
   from fess.test.ui.search import (
       ...
       root_top as search_root_top,
       help as search_help,
       login_form as search_login_form,
       profile_form as search_profile_form,
       form_submit as search_form_submit,
   )
   ```
2. **`all_modules` dict** — register each under its alias key.
3. **default-order list** — slot them in the `search_*` group, after
   `search_seed` (which must run first to ensure indexed content) and
   before `search_console_errors` (so console-error sweep covers the
   pages we just touched). Recommended order:
   ```
   search_seed,
   search_root_top, search_top, search_help, search_login_form,
   search_profile_form, search_form_submit,
   search_query, search_no_results, search_pagination,
   search_facet, search_sort, search_thumbnail,
   search_suggest, search_related,
   search_i18n_smoke, search_multibyte_query,
   search_layout_overflow, search_console_errors,
   search_multibyte_admin_input,
   ```

## i18n keys to add (`src/fess/test/i18n/keys.py`)

Add only keys actually referenced by assertions or selectors in the
new tests. Every key must be verified to exist in
`repos/fess/src/main/resources/fess_label.properties` before landing.

| Constant | Property key | Used by |
|----------|--------------|---------|
| `PROFILE_TITLE` | `labels.profile.title` | `profile_form` (sanity check the title appears on `/profile/`) |
| `PROFILE_BUTTON_UPDATE` | `labels.profile.update` | `profile_form` (locate the form-submit button by its localized text, mirroring how login uses `t(Labels.LOGIN)`) |

Other potential keys (`LOGIN_TITLE`, `INDEX_FORM_SEARCH_BTN`,
`PROFILE_PLACEHOLDER_*`) are intentionally NOT added — the corresponding
selectors use stable HTML `name=` attributes (`input[name="username"]`,
`button[name="search"]`, `input[name="oldPassword"]`, …) which are
locale-independent and already the convention in existing tests.

Help has no fixed body text — it is admin-customizable — so no help
key is added; assertions on `/help/` use structural selectors only.

## Module contract (unchanged from existing pattern)

Each new file exports `setup(playwright) -> FessContext`,
`run(context)`, `destroy(context)` plus an `if __name__ == "__main__"`
block that runs setup → run → destroy. `run_module()` in `main.py`
already handles screenshots, traces, and result collection; no new
plumbing is needed.

## Test data isolation

- `login_form`: opens a fresh Playwright browser context inside `setup`
  (separate from `FessContext`'s logged-in context). The new context is
  closed in `destroy`.
- `profile_form`: reuses the suite-wide context but never submits the
  success path. No state to clean up.
- `root_top`, `help`, `form_submit`: read-only navigation — no setup
  data, no teardown.

## Risk and mitigation

| Risk | Mitigation |
|------|------------|
| `profile_form` accidentally changes admin password | Test only submits mismatched-confirmation; does not exercise the success path. Code review focuses on this invariant. |
| `login_form` triggers account lockout | Submit only empty fields, never a guessed wrong password. |
| `help` page is admin-customized to empty | Assertion is structural (form + non-empty `<main>`); does not depend on specific copy. |
| `/chat/` link existence in `root_top` is locale/feature-flag dependent | Soft check — assert Help link exists (always present); AI Search is checked but not required. |
| `form_submit` is flaky on slow CI | Use `wait_for_load_state("domcontentloaded")` after click, same as existing `query.py`. |
| New i18n keys missing in non-default locales | The label files extracted by `run_test.sh` already cover all 16 supported locales; if a key is missing there, the test will fail loudly and that is the desired signal. |

## Acceptance criteria

1. `TEST_MODULES=search_root_top,search_help,search_login_form,search_profile_form,search_form_submit ./run_test.sh fessx opensearch3`
   passes locally.
2. Full default run with `TEST_MODULES=all` still passes (no
   regressions in the existing 15 search modules).
3. The five new modules each pass when run individually via
   `python -m fess.test.ui.search.<module>`.
4. `console_errors` reports zero unfiltered errors on the expanded page
   set (`/`, `/help/`).
5. Admin login still works after `profile_form` runs (verify by
   re-running any admin module afterwards).
