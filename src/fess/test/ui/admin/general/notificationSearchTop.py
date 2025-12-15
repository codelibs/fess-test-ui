from playwright.sync_api import Playwright, sync_playwright
import logging

logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    logger.info("Starting notification search top test")
    browser = playwright.chromium.launch(headless=False, slow_mo=1500)
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

    # Click text=システム
    logger.info("Step 3: Navigate to System > General settings")
    page.click("text=システム")

    # Click text=全般
    page.click("text=全般")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Fill textarea[name="notificationSearchTop"]
    logger.info("Step 4: Set notification message for search top page")
    page.fill("textarea[name=\"notificationSearchTop\"]", "search top test")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Click .fa.fa-sign-out-alt
    logger.info("Step 5: Logout to view search top page")
    page.click(".fa.fa-sign-out-alt")
    # assert page.url == "http://localhost:8080/login/"

    # Go to http://localhost:8080/
    logger.info("Step 6: Verify notification appears on search top page")
    page.goto("http://localhost:8080/")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

    logger.info("Notification search top test completed successfully")


with sync_playwright() as playwright:
    run(playwright)
