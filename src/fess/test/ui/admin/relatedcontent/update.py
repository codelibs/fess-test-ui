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

    # Click text=関連コンテンツ
    page.click("text=関連コンテンツ")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Click text=fess
    page.click("text=fess")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/details/4/b5hn8nsBFFIjqpLe9cts"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Fill input[name="sortOrder"]
    page.fill("input[name=\"sortOrder\"]", "99")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"



    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
