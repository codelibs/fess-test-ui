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

    # Click text=en/stemmer_override.txt
    page.click("text=en/stemmer_override.txt")
    # assert page.url == "http://localhost:8080/admin/dict/stemmeroverride/?dictId=ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ="

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/dict/stemmeroverride/createnew/ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ%3D/"

    # Fill input[name="input"]
    page.fill("input[name=\"input\"]", "running")

    # Fill input[name="output"]
    page.fill("input[name=\"output\"]", "run")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/dict/stemmeroverride/list/1?dictId=ZW4vc3RlbW1lcl9vdmVycmlkZS50eHQ="

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
