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

    # Click text=testtoken
    page.click("text=testtoken")
    # assert page.url == "http://localhost:8080/admin/accesstoken/details/4/aumjKnwB4cOxITidPMau"

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル
    page.click("text=キャンセル")

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/accesstoken/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
