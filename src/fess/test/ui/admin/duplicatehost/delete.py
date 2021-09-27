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

    # Click text=n2sm.net
    page.click("text=n2sm.net")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/details/4/SknvJXwBXaWIaqd-Zm-e"

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル
    page.click("text=キャンセル")

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=Fess
    page.click("text=Fess")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/S0nvJXwBXaWIaqd-eW8D"

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
