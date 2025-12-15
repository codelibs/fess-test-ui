from playwright.sync_api import Playwright, sync_playwright
import logging

logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    logger.info("Starting login required test")
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

    # Check input[name="loginRequired"]
    logger.info("Step 4: Enable login required")
    page.check("input[name=\"loginRequired\"]")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Click .fa.fa-sign-out-alt
    logger.info("Step 5: Logout and verify login is required")
    # with page.expect_navigation(url="http://localhost:8080/login/"):
    with page.expect_navigation():
        page.click(".fa.fa-sign-out-alt")
    # assert page.url == "http://localhost:8080/login/"

    # Go to http://localhost:8080/
    page.goto("http://localhost:8080/")

    # Fill [placeholder="ユーザー名"]
    logger.info("Step 6: Login to disable login required")
    page.fill("[placeholder=\"ユーザー名\"]", "admin")

    # Fill [placeholder="パスワード"]
    page.fill("[placeholder=\"パスワード\"]", "admin1234")

    # Click button:has-text("ログイン")
    page.click("button:has-text(\"ログイン\")")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click text=システム
    page.click("text=システム")

    # Click text=全般
    page.click("text=全般")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Uncheck input[name="loginRequired"]
    logger.info("Step 7: Disable login required")
    page.uncheck("input[name=\"loginRequired\"]")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Click .fa.fa-sign-out-alt
    logger.info("Step 8: Logout and verify login is not required")
    # with page.expect_navigation(url="http://localhost:8080/"):
    with page.expect_navigation():
        page.click(".fa.fa-sign-out-alt")
    # assert page.url == "http://localhost:8080/login/"

    # Go to http://localhost:8080/
    page.goto("http://localhost:8080/")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()

    logger.info("Login required test completed successfully")


with sync_playwright() as playwright:
    run(playwright)
