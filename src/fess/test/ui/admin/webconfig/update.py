from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/login/
    page.goto("http://localhost:8080/login/")

    # Fill [placeholder="ユーザー名"]
    page.fill("[placeholder=\"ユーザー名\"]", "admin")

    # Press Tab
    page.press("[placeholder=\"ユーザー名\"]", "Tab")

    # Fill [placeholder="パスワード"]
    page.fill("[placeholder=\"パスワード\"]", "admin1234")

    # Click button:has-text("ログイン")
    page.click("button:has-text(\"ログイン\")")
    # assert page.url == "http://localhost:8080/admin/dashboard/"

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=N2SM
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/MkJZ7XsB16rL45wtKfxP"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Fill text=N2SMのサイト
    page.fill("text=N2SMのサイト", "N2SMのサイト(更新)")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
