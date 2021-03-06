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

    # Click text=ユーザー
    page.click("text=ユーザー")

    # Click text=グループ
    page.click("text=グループ")
    # assert page.url == "http://localhost:8080/admin/group/"

    # Click text=test
    page.click("text=test")
    # assert page.url == "http://localhost:8080/admin/group/details/4/dGVzdA%3D%3D"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/group/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/group/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/group/"

    # Fill input[name="attributes.gidNumber"]
    page.fill("input[name=\"attributes.gidNumber\"]", "300")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/group/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
