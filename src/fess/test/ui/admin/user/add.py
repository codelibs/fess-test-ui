
import logging

from fess.test import assert_equal, assert_not_equal
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

    # Click text=ユーザー ロール グループ >> p
    page.click("text=ユーザー ロール グループ >> p")
    assert_equal(page.url, context.url("/admin/user/"))

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, context.url("/admin/user/createnew/"))

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", label_name)

    # Fill input[name="password"]
    page.fill("input[name=\"password\"]", "taro1234")

    # Fill input[name="confirmPassword"]
    page.fill("input[name=\"confirmPassword\"]", "taro1234")

    # Fill input[name="attributes.surname"]
    page.fill("input[name=\"attributes.surname\"]", "Yamada")

    # Fill input[name="attributes.givenName"]
    page.fill("input[name=\"attributes.givenName\"]", "Taro")

    # Fill input[name="attributes.mail"]
    page.fill("input[name=\"attributes.mail\"]", "taro@example.com")

    # Click select[name="roles"]
    page.select_option('select#roles', ['YWRtaW4=', 'Z3Vlc3Q='])

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/user/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
