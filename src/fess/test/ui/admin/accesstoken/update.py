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

    # Click text=システム
    page.click("text=システム")

    # Click text=アクセストークン
    page.click("text=アクセストークン")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Click text=test
    page.click("text=test")
    # assert page.url == "http://localhost:8080/admin/accesstoken/details/4/aumjKnwB4cOxITidPMau"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "testtoken")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
