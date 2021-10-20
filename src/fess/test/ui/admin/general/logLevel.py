from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
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

    # Click a:has-text("システム")
    page.click("a:has-text(\"システム\")")

    # Click text=全般
    page.click("text=全般")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Select DEBUG
    page.select_option("select[name=\"logLevel\"]", "DEBUG")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/search/?q=fess
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
    page.select_option("select[name=\"logLevel\"]", "WARN")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/search/?q=fess
    page.goto("http://localhost:8080/search/?q=fess")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
