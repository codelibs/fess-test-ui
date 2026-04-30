from playwright.sync_api import Playwright, sync_playwright
import logging

from fess.test.i18n import t
from fess.test.i18n.keys import Labels

logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    logger.info("Starting JSON response test")
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/login/
    logger.info("Step 1: Navigate to login page")
    page.goto("http://localhost:8080/login/")

    # Click [placeholder="ユーザー名"]
    page.click(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]')

    # Fill [placeholder="ユーザー名"]
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]', "admin")

    # Press Tab
    page.press(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]', "Tab")

    # Fill [placeholder="パスワード"]
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_PASSWORD)}"]', "admin1234")

    # Click button:has-text("ログイン")
    logger.info("Step 2: Login with admin credentials")
    page.click(f'button:has-text("{t(Labels.LOGIN)}")')
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    logger.info("Step 3: Navigate to System > General settings")
    page.click(f'a:has-text("{t(Labels.MENU_SYSTEM)}")')

    # Click a:has-text("全般")
    page.click(f'a:has-text("{t(Labels.MENU_CRAWL_CONFIG)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Uncheck input[name="webApiJson"]
    logger.info("Step 4: Disable JSON API")
    page.uncheck("input[name=\"webApiJson\"]")

    # Click button:has-text("更新")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/json?q=fess
    logger.info("Step 5: Verify JSON API is disabled")
    page.goto("http://localhost:8080/json?q=fess")

    # Click text=admin
    page.click("text=admin")

    # Click text=管理
    page.click("text=管理")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    page.click(f'a:has-text("{t(Labels.MENU_SYSTEM)}")')

    # Click a:has-text("全般")
    page.click(f'a:has-text("{t(Labels.MENU_CRAWL_CONFIG)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Check input[name="webApiJson"]
    logger.info("Step 6: Enable JSON API")
    page.check("input[name=\"webApiJson\"]")

    # Click button:has-text("更新")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/json?q=fess
    logger.info("Step 7: Verify JSON API is enabled")
    page.goto("http://localhost:8080/json?q=fess")

    # Go to http://localhost:8080/json/?type=ping
    page.goto("http://localhost:8080/json/?type=ping")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

    logger.info("JSON response test completed successfully")


with sync_playwright() as playwright:
    run(playwright)
