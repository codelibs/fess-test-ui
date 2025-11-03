
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

    # Click text=ユーザー
    page.click("text=ユーザー")

    # Click text=ロール
    page.click("text=ロール")
    assert_equal(page.url, context.url("/admin/role/"))

    # Click the role created in add test
    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/role/details/4/"))

    # Click text=編集
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/role/"))

    # Click text=戻る (test cancel button)
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/role/"))

    # Click text=編集 again
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/role/"))

    # Note: We don't actually change any field values here, just test the edit workflow
    # This is consistent with other modules like user which only changes password

    # Click text=更新
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/role/"))

    page.wait_for_load_state("domcontentloaded")

    # Verify the role still exists in the table
    table_content = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not found in table after update")

    logger.info(f"Role {label_name} update workflow tested successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
