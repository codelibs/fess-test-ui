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

    # Click text=ja/kuromoji.txt
    page.click("text=ja/kuromoji.txt")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/?dictId=amEva3Vyb21vamkudHh0"

    # Click text=全文検索エンジン
    page.click("text=全文検索エンジン")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/details/amEva3Vyb21vamkudHh0/4/5"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/"

    # Fill input[name="token"]
    page.fill("input[name=\"token\"]", "全文検索システム")

    # Fill input[name="segmentation"]
    page.fill("input[name=\"segmentation\"]", "全文 検索 システム")

    # Fill input[name="reading"]
    page.fill("input[name=\"reading\"]", "ゼンブン ケンサク システム")

    # Fill input[name="pos"]
    page.fill("input[name=\"pos\"]", "カスタム")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/dict/kuromoji/list/1?dictId=amEva3Vyb21vamkudHh0"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
