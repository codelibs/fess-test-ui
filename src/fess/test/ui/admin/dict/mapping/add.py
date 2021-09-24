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

    # Click :nth-match(:text("mapping.txt"), 3)
    page.click(":nth-match(:text(\"mapping.txt\"), 3)")
    # assert page.url == "http://localhost:8080/admin/dict/mapping/?dictId=bWFwcGluZy50eHQ="

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/dict/mapping/createnew/bWFwcGluZy50eHQ%3D/"

    # Fill textarea[name="inputs"]
    page.fill("textarea[name=\"inputs\"]", "一")

    # Fill input[name="output"]
    page.fill("input[name=\"output\"]", "1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/dict/mapping/list/1?dictId=bWFwcGluZy50eHQ="

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
