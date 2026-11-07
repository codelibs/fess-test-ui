"""Page helpers shared by the theme modules."""
from typing import List

from playwright.sync_api import Page

from fess.test import assert_true
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext

LIST_PATH = "/admin/theme/"
UPLOAD_PATH = "/admin/theme/uploadpage/"
BUILT_IN = "bootstrap"


def open_list(page: Page, context: FessContext) -> None:
    page.goto(context.url(LIST_PATH))
    page.wait_for_load_state("domcontentloaded")


def installed_names(page: Page, context: FessContext) -> List[str]:
    """Names of the themes in the list table, read from the details links."""
    open_list(page, context)
    return [a.inner_text().strip()
            for a in page.locator('table a[href*="details"]').all()]


def default_theme(page: Page, context: FessContext) -> str:
    """The value of the Default Theme select ('' for no default)."""
    open_list(page, context)
    return page.locator("#defaultTheme").input_value()


def set_default(page: Page, context: FessContext, name: str) -> None:
    """Pick `name` ('' for none) in the Default Theme select and press Set."""
    open_list(page, context)
    page.select_option("#defaultTheme", value=name)
    page.click(f'#setDefaultForm button:has-text("{t(Labels.THEME_SET_DEFAULT)}")')
    page.wait_for_load_state("domcontentloaded")


def upload(page: Page, context: FessContext, file_name: str, data: bytes) -> None:
    """Submit `data` on the upload page as `file_name`."""
    page.goto(context.url(UPLOAD_PATH))
    page.wait_for_load_state("domcontentloaded")
    page.set_input_files("#themeFile", files=[
        {"name": file_name, "mimeType": "application/zip", "buffer": data}])
    page.click('button[name="upload"]')
    page.wait_for_load_state("domcontentloaded")


def can_delete(page: Page, context: FessContext, name: str) -> bool:
    """Whether the list offers a Delete button on the row of `name`."""
    open_list(page, context)
    row = page.locator("tr", has=page.locator(f'a[href*="details"]:text-is("{name}")'))
    return row.locator('button[name="delete"][data-toggle="modal"]').count() > 0


def delete(page: Page, context: FessContext, name: str) -> None:
    """Press Delete on the row of `name` and confirm."""
    open_list(page, context)
    row = page.locator("tr", has=page.locator(f'a[href*="details"]:text-is("{name}")'))
    # The row holds both the trigger and its confirmation modal, and both
    # buttons are named "delete": the trigger is the one that opens a modal.
    row.locator('button[name="delete"][data-toggle="modal"]').click()
    modal = page.locator(".modal.show")
    modal.wait_for(state="visible")
    modal.locator('button[type="submit"][name="delete"]').click()
    page.wait_for_load_state("domcontentloaded")


def assert_on_upload_page(page: Page, why: str) -> None:
    assert_true("/admin/theme/upload" in page.url,
                f"{why}: expected to stay on the upload page, got {page.url}")
