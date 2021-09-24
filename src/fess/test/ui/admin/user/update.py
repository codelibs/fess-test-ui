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

    # Click text=ユーザー ロール グループ >> p
    page.click("text=ユーザー ロール グループ >> p")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Click text=taro
    page.click("text=taro")
    # assert page.url == "http://localhost:8080/admin/user/details/4/dGFybw%3D%3D"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Fill input[name="password"]
    page.fill("input[name=\"password\"]", "taro1234")

    # Fill input[name="confirmPassword"]
    page.fill("input[name=\"confirmPassword\"]", "taro1234")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
