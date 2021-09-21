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

    # Click text=辞書
    page.click("text=辞書")
    # assert page.url == "http://localhost:8080/admin/dict/"

    # Click text=synonym.txt
    page.click("text=synonym.txt")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/?dictId=c3lub255bS50eHQ="

    # Click text=[TV]
    page.click("text=[TV]")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/details/c3lub255bS50eHQ%3D/4/2"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/"

    # Click text=TV
    page.click("text=TV")

    # Fill text=TV
    page.fill("text=TV", "TV\nテレビ")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/dict/synonym/list/1?dictId=c3lub255bS50eHQ="

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
