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

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=重複ホスト
    page.click("text=重複ホスト")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Click text=fess.codelibs.org
    page.click("text=fess.codelibs.org")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/details/4/SknvJXwBXaWIaqd-Zm-e"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Fill input[name="regularName"]
    page.fill("input[name=\"regularName\"]", "n2sm.net")

    # Fill input[name="duplicateHostName"]
    page.fill("input[name=\"duplicateHostName\"]", "www.n2sm.net")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
