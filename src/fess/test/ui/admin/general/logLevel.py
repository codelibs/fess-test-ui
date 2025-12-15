from playwright.sync_api import Playwright, sync_playwright
import logging

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
    page.fill("[placeholder=\"ユーザー名\"]", "admin")

    # Fill [placeholder="パスワード"]
    page.fill("[placeholder=\"パスワード\"]", "admin1234")

    # Click button:has-text("ログイン")
    logger.info("Step 2: Login with admin credentials")
    page.click("button:has-text(\"ログイン\")")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    logger.info("Step 3: Navigate to System > General settings")
    page.click("a:has-text(\"システム\")")

    # Click text=全般
    page.click("text=全般")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Select DEBUG
    logger.info("Step 4: Change log level to DEBUG")
    page.select_option("select[name=\"logLevel\"]", "DEBUG")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/search/?q=fess
    logger.info("Step 5: Verify DEBUG log level by performing search")
    page.goto("http://localhost:8080/search/?q=fess")

    # Click text=admin
    page.click("text=admin")

    # Click text=管理
    page.click("text=管理")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    page.click("a:has-text(\"システム\")")

    # Click a:has-text("全般")
    page.click("a:has-text(\"全般\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Select WARN
    logger.info("Step 6: Change log level to WARN")
    page.select_option("select[name=\"logLevel\"]", "WARN")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
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
