from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=1500)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/login/
    page.goto("http://localhost:8080/login/")

    # Fill [placeholder="ユーザー名"]
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

    # Fill textarea[name="notificationLogin"]
    page.fill("textarea[name=\"notificationLogin\"]", "login page test")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Click .fa.fa-sign-out-alt
    page.click(".fa.fa-sign-out-alt")
    # assert page.url == "http://localhost:8080/login/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
