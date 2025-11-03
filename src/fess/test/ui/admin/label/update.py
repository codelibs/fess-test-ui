import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info(f"start")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ラベル
    page.click("text=ラベル")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Click the label created in add test
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/labeltype/details/4/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Click text=戻る
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Click text=編集 again
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    # Update sortOrder
    page.fill("input[name=\"sortOrder\"]", "10")

    # Update includedPaths
    page.fill("textarea[name=\"includedPaths\"]", "https://example.com/updated/.*")

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/labeltype/"))

    page.wait_for_load_state("domcontentloaded")

    # Verify the update by checking the table content
    table_content = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not found in table after update")

    logger.info(f"Label {label_name} updated successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
