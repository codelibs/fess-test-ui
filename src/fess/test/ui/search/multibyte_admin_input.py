"""Multibyte admin form input round-trip test.

Creates a label with a multibyte name in the script of the selected
language. Verifies the value round-trips through save -> re-read with
no mojibake. Cleans up afterward.

Detects bug categories:
  5. Multibyte input handling errors in admin forms
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_contains
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


# Fess locale -> sample multibyte name in the language's native script.
# For locales without a non-Latin script, fall back to ASCII (suffix only).
SCRIPT_SAMPLES = {
    "ja": "テストラベル日本語",
    "ko": "테스트라벨",
    "zh_CN": "测试标签",
    "zh_TW": "測試標籤",
    "ru": "ТестоваяМетка",
    "hi": "परीक्षणलेबल",
    "tr": "TestEtiketIğüş",
}


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info(f"Starting search/multibyte_admin_input (lang={context.lang})")
    name = SCRIPT_SAMPLES.get(context.lang, f"TestLabel_{context.lang}_") + context.generate_str(8)
    page = context.get_admin_page()

    # Navigate to label list -> create new
    page.goto(context.url("/admin/labeltype/"))
    page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
    page.wait_for_load_state("domcontentloaded")

    page.fill('input[name="name"]', name)
    page.fill('input[name="value"]', "mb_" + context.generate_str(8))
    page.fill('input[name="sortOrder"]', "1")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
    page.wait_for_load_state("domcontentloaded")

    try:
        # Verify round-trip: name appears verbatim in the list table
        table_text = page.inner_text("table")
        assert_contains(
            table_text, name,
            f"multibyte label name corrupted: expected {name!r} in table")
    finally:
        # Cleanup runs even on assertion failure to avoid leaking
        # multibyte test data into subsequent runs.
        try:
            page.goto(context.url("/admin/labeltype/"))
            page.wait_for_load_state("domcontentloaded")
            page.click(f"text={name}")
            page.wait_for_load_state("domcontentloaded")
            page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
            # Modal confirm button has name="delete" (locale-neutral)
            page.click('div.modal-footer button[name="delete"]')
            page.wait_for_load_state("domcontentloaded")
        except Exception as cleanup_err:
            logger.warning(
                f"multibyte_admin_input cleanup failed for {name!r}: {cleanup_err}")

    logger.info("search/multibyte_admin_input completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
