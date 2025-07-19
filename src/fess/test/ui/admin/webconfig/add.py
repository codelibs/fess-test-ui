
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

    # Click text=ウェブ
    page.click("text=ウェブ")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    # Click text=新規作成 >> em
    page.click("text=新規作成 >> em")
    assert_equal(page.url, context.url("/admin/webconfig/createnew/"))

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", label_name)

    # Fill textarea[name="urls"]
    page.fill("textarea[name=\"urls\"]", "https://fess.codelibs.org/ja/")

    # Fill textarea[name="includedUrls"]
    page.fill("textarea[name=\"includedUrls\"]", "https://fess.codelibs.org/ja/.*")

    # Fill textarea[name="excludedUrls"]
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")

    # Fill input[name="maxAccessCount"]
    page.fill("input[name=\"maxAccessCount\"]", "30")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "2")

    # Fill textarea[name="description"]
    page.fill("textarea[name=\"description\"]", "Fessのサイト")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    assert_equal(page.url, context.url("/admin/webconfig/"))

    page.wait_for_load_state("domcontentloaded")
    table_content: str = page.inner_text("table")
    assert_not_equal(table_content.find(label_name), -1,
                     f"{label_name} not in {table_content}")

    page.click(f"text={label_name}")
    assert_startswith(
        page.url, context.url("/admin/webconfig/details/4/"))

    # Verify that the value entered in the "name" field is displayed
    name_value = page.input_value("input[name=\"name\"]")
    assert_equal(name_value, label_name, f"name value '{name_value}' != expected '{label_name}'")

    # Verify that the value entered in the "description" field is displayed
    desc_value = page.input_value("input[name=\"description\"]")
    assert_equal(desc_value, "Fessのサイト", f"description value '{desc_value}' != expected 'Fessのサイト'")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
