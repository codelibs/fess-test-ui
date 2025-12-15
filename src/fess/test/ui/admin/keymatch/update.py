import logging

from fess.test import assert_equal, assert_startswith
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
    logger.info("Starting keymatch update test")

    page: "Page" = context.get_admin_page()
    label_name: str = context.create_label_name()
    logger.debug(f"Using test label: {label_name}")

    # Click text=クローラー
    logger.info("Step 1: Navigate to Crawler menu")
    page.click("text=クローラー")

    # Click text=キーマッチ
    logger.info("Step 2: Navigate to Key Match page")
    page.click("text=キーマッチ")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Click text=n2sm
    logger.info("Step 3: Click on existing key match")
    page.click(f"text={label_name}")
    assert_startswith(page.url, context.url("/admin/keymatch/details/4/"))

    # Click text=編集
    logger.info("Step 4: Click edit button")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Click text=戻る
    logger.info("Step 5: Test back button")
    page.click("text=戻る")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Click text=編集
    logger.info("Step 6: Click edit button again")
    page.click("text=編集")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    # Fill input[name="maxSize"]
    logger.info("Step 7: Update max size value")
    page.fill("input[name=\"maxSize\"]", "5")

    # Click text=更新
    logger.info("Step 8: Submit update")
    page.click("text=更新")
    assert_equal(page.url, context.url("/admin/keymatch/"))

    logger.info("Keymatch update test completed successfully")

    # TODO check content


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
