# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Playwright (Python) admin-UI test suite for [Fess](https://fess.codelibs.org/). Tests run end-to-end in Docker against a matrix of Fess builds and OpenSearch versions. See `README.md` for the user-facing docs, env-var tables, and the module list.

## How tests are run

- Entry point: `./run_test.sh <fess-variant> <search-engine>` from the repo root. Valid names are whichever `compose-<name>.yaml` files exist (`fess15`, `fess15-al2023`, `fess15-noble`, `fessx`, `fessx-al2023`, `fessx-noble`, `opensearch2`, `opensearch3`).
- The script layers compose files: `compose.yaml` + `compose-<fess>.yaml` + `compose-<engine>.yaml`. OpenSearch variants also `--env-file .env.opensearch` to set `FESS_DICTIONARY_PATH` on the Fess container.
- Build/rebuild the runner image with `docker compose build` (Dockerfile is `mcr.microsoft.com/playwright:v1.56.0-noble` + `playwright==1.56.0` + `beautifulsoup4`).
- Run a subset: `TEST_MODULES=user,badword,kuromoji ./run_test.sh fess15 opensearch2`. Keys must exist in the `all_modules` dict in `src/main.py`; unknown names log a warning and are skipped.
- Run a single module locally (requires a venv with `requirements.txt`, Playwright browsers installed, and Fess reachable at `FESS_URL`): from `src/`, `python -m fess.test.ui.admin.badword.add` or `python fess/test/ui/admin/user/add.py`. Every leaf module has its own `__main__` that calls its local `setup/run/destroy`.
- There is no `pytest`, no linter, no formatter. Don't invent commands that don't exist.

## Architecture notes (the non-obvious bits)

- **Three containers on the `searchtestnet` bridge**: `test01` (this repo's Playwright runner) + `fesstest01` (Fess) + `searchtest01` (OpenSearch). `src/run.sh` inside the runner polls `${FESS_URL}` (default `http://fesstest01:8080`) up to 60× at 1 s intervals before launching `python3 main.py`. Don't rename those hostnames without updating every `compose-*.yaml`.
- **Module registration in `src/main.py` is duplicated.** `get_modules_to_run()` has both an `all_modules` dict (for `TEST_MODULES` filtering) and a hard-coded default-order list. Adding a new top-level admin module means updating three places: the import block, the dict, and the default list. Dictionary submodules (`kuromoji`, `protwords`, `mapping`, `stemmeroverride`, …) are imported separately from `fess.test.ui.admin.dict`.
- **Test module contract**: each leaf exports `setup(playwright) -> FessContext`, `run(context)`, `destroy(context)`. Folder-level `__init__.py` composes leaves in a fixed order (e.g. `badword/__init__.py` runs `add → update → delete`) — order matters because tests share state through the label created by `add`. `main.py` only calls `module.run(context)`; it reuses one logged-in `FessContext` across every module.
- **`FessContext`** (`src/fess/test/ui/context.py`) owns the browser, Playwright context, `_current_page`, tracing state, and `HTMLCapture`. Prefer `context.get_admin_page()` / `context.get_wrapped_page()` — they return a `PageWrapper` that logs every `click`/`fill`/`goto`/`select_option` at DEBUG, masks password/secret/token/key/credential selectors, and triggers HTML capture on navigation. Tests must not launch their own browser.
- **Japanese selectors are the convention.** Login uses `[placeholder="ユーザー名"]` / `[placeholder="パスワード"]` and `button:has-text("ログイン")`. Navigation uses `text=サジェスト`, `text=新規作成`, `text=作成`, etc. Default `BROWSER_LOCALE=ja-JP`. Match this style in new tests; fall back to CSS/attribute selectors only when the element has no Japanese label.
- **Assertions**: import from `fess.test` (`assert_equal`, `assert_not_equal`, `assert_startswith`, `assert_contains`, `assert_true`). They wrap `assert` with DEBUG/WARNING logging and value truncation — don't use bare `assert` in tests.
- **Unique test data**: `context.create_label_name()` returns a 20-char random label memoized for the run (also overridable via `TEST_LABEL`); `context.generate_str()` produces fresh randoms. Reusable builders live in `src/fess/test/ui/testdata.py` — `TestDataBuilder` (webconfig/label/user dicts) and `ValidationPatterns` (XSS/SQLi fixtures).
- **Failure handling in `main.run_module()`**: saves `screenshots/failure_<module>_<ts>.png`, stops-and-saves the Playwright trace chunk when `TRACE_ON_FAILURE=true` (or always when `TRACE_ALL=true`) to `traces/`, and captures the URL at failure. `AssertionError` → status `failed`; any other exception → status `error`. Results go to `test_results.json`; `MetricsCollector` appends to `test_metrics_history.json`.
- **Coverage analysis is an opt-in post-processing pipeline driven by env vars, not a separate command.** `HTML_CAPTURE=true` makes `PageWrapper.goto` dump snapshots to `html_snapshots/`; then if `COVERAGE_ANALYSIS=true`, `main.run_coverage_analysis()` runs `CoverageAnalyzer → InventoryManager → CoverageReporter`, and if `COVERAGE_GENERATE_STUBS=true` also runs `TestStubGenerator`. All four live under `src/fess/test/coverage/`.
- **CI** (`.github/workflows/run-*.yml`): each Fess×engine combination runs on a weekly Saturday cron plus `workflow_dispatch`, uploading `test_results.json` and `screenshots/` as artifacts. Tests must not assume an interactive tty (the CI container runs with `HEADLESS=true`).
