from playwright.sync_api import Playwright, sync_playwright
import logging

from fess.test.i18n import t
from fess.test.i18n.keys import Labels

logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    logger.info("Starting log level test")
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/login/
    logger.info("Step 1: Navigate to login page")
    page.goto("http://localhost:8080/login/")

    # Fill [placeholder="ユーザー名"]
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_USERNAME)}"]', "admin")

    # Fill [placeholder="パスワード"]
    page.fill(f'[placeholder="{t(Labels.LOGIN_PLACEHOLDER_PASSWORD)}"]', "admin1234")

    # Click button:has-text("ログイン")
    logger.info("Step 2: Login with admin credentials")
    page.click(f'button:has-text("{t(Labels.LOGIN)}")')
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    logger.info("Step 3: Navigate to System > General settings")
    page.click(f"text={t(Labels.MENU_SYSTEM)}")

    # Click text=全般
    page.click(f"text={t(Labels.MENU_CRAWL_CONFIG)}")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Select DEBUG
    logger.info("Step 4: Change log level to DEBUG")
    page.select_option("select[name=\"logLevel\"]", "DEBUG")

    # Click button:has-text("更新")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/search/?q=fess
    logger.info("Step 5: Verify DEBUG log level by performing search")
    page.goto("http://localhost:8080/search/?q=fess")

    # Click text=admin
    page.click("text=admin")

    # Click localized "Administration"
    page.click(f"text={t(Labels.MENU_ADMINISTRATION)}")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    page.click(f"text={t(Labels.MENU_SYSTEM)}")

    # Click a:has-text("全般")
    page.click(f"text={t(Labels.MENU_CRAWL_CONFIG)}")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Select WARN
    logger.info("Step 6: Change log level to WARN")
    page.select_option("select[name=\"logLevel\"]", "WARN")

    # Click button:has-text("更新")
    page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_UPDATE)}")')
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/search/?q=fess
    logger.info("Step 7: Verify WARN log level by performing search")
    page.goto("http://localhost:8080/search/?q=fess")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

    logger.info("Log level test completed successfully")


with sync_playwright() as playwright:
    run(playwright)
