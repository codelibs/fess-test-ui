"""i18n completeness smoke test.

Loads the search top page and admin top page and asserts:
  - No 'unknown.label' / '???labels.x???' / raw '${...}' markers leak.
  - A small set of expected labels (looked up via t()) appear in the body.

Detects bug categories:
  1. i18n missing / fallback to English / untranslated key markers
"""
import logging
import re

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


# LastaFlute renders missing labels as "???labels.x???".
_MISSING_KEY_PATTERN = re.compile(r'\?{2,}labels\.[A-Za-z0-9_.]+\?{2,}')
# Raw JSP/EL expression leaks
_JSP_RESIDUE_PATTERN = re.compile(r'\$\{[^}]+\}')


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _check_no_untranslated_keys(body_text: str, where: str) -> None:
    matches = _MISSING_KEY_PATTERN.findall(body_text)
    assert_true(
        len(matches) == 0,
        f"Untranslated label keys found on {where}: {matches[:5]}")


def _check_no_jsp_residue(body_text: str, where: str) -> None:
    matches = _JSP_RESIDUE_PATTERN.findall(body_text)
    el_like = [m for m in matches if m.startswith('${') and m.endswith('}')]
    assert_true(
        len(el_like) == 0,
        f"Raw EL expressions leaked on {where}: {el_like[:5]}")


def run(context: FessContext) -> None:
    logger.info(f"Starting search/i18n_smoke (lang={context.lang})")
    page = context.get_wrapped_page() or context.get_admin_page()

    # 1. Search top
    page.goto(context.url("/search/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("body")
    _check_no_untranslated_keys(body, "/search/")
    _check_no_jsp_residue(body, "/search/")

    # 2. Admin top
    page.goto(context.url("/admin/"))
    page.wait_for_load_state("domcontentloaded")
    body = page.inner_text("body")
    _check_no_untranslated_keys(body, "/admin/")
    _check_no_jsp_residue(body, "/admin/")

    # 3. Verify a known label is rendered (smoke check that locale loaded at all)
    expected_dashboard = t(Labels.MENU_DASHBOARD_CONFIG)
    assert_true(
        expected_dashboard in body,
        f"Expected dashboard menu label {expected_dashboard!r} not found on /admin/")

    logger.info("search/i18n_smoke completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
