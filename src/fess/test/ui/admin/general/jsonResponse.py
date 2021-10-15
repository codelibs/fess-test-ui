from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/login/
    page.goto("http://localhost:8080/login/")

    # Click [placeholder="ユーザー名"]
    page.click("[placeholder=\"ユーザー名\"]")

    # Fill [placeholder="ユーザー名"]
    page.fill("[placeholder=\"ユーザー名\"]", "admin")

    # Press Tab
    page.press("[placeholder=\"ユーザー名\"]", "Tab")

    # Fill [placeholder="パスワード"]
    page.fill("[placeholder=\"パスワード\"]", "admin1234")

    # Click button:has-text("ログイン")
    page.click("button:has-text(\"ログイン\")")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click a:has-text("システム")
    page.click("a:has-text(\"システム\")")

    # Click a:has-text("全般")
    page.click("a:has-text(\"全般\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Uncheck input[name="webApiJson"]
    page.uncheck("input[name=\"webApiJson\"]")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/json?q=fess
    page.goto("http://localhost:8080/json?q=fess")

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

    # Check input[name="webApiJson"]
    page.check("input[name=\"webApiJson\"]")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Go to http://localhost:8080/json?q=fess
    page.goto("http://localhost:8080/json?q=fess")

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
