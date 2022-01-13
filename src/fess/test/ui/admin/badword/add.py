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

    # Click text=サジェスト
    page.click("text=サジェスト")

    # Click text=除外ワード
    page.click("text=除外ワード")
    assert_equal(page.url, "http://localhost:8080/admin/badword/")

    # Click text=新規作成
    page.click("text=新規作成")
    assert_equal(page.url, "http://localhost:8080/admin/badword/createnew/")

    # Fill input[name="suggestWord"]
    page.fill("input[name=\"suggestWord\"]", label_name)

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, "http://localhost:8080/admin/badword/")

    assert_not_equal(page.inner_text("table").find(label_name), -1)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
