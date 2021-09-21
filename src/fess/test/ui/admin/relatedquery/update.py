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

    # Click text=関連クエリー
    page.click("text=関連クエリー")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=fess
    page.click("text=fess")
    # assert page.url == "http://localhost:8080/admin/relatedquery/details/4/2pih8nsBFFIjqpLeasuq"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Fill text=n2sm
    page.fill("text=n2sm", "elasticsearch")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"


    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
