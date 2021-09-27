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

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/createnew/"

    # Fill input[name="regularName"]
    page.fill("input[name=\"regularName\"]", "fess.codelibs.org")

    # Fill input[name="duplicateHostName"]
    page.fill("input[name=\"duplicateHostName\"]", "www.fess.codelibs.org")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/duplicatehost/"

    # Click a:has-text("ウェブ")
    page.click("a:has-text(\"ウェブ\")")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/webconfig/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "Fess")

    # Fill textarea[name="urls"]
    page.fill("textarea[name=\"urls\"]", "https://www.fess.codelibs.org/")

    # Fill textarea[name="includedUrls"]
    page.fill("textarea[name=\"includedUrls\"]", "https://fess.codelibs.org/.*")

    # Fill textarea[name="excludedUrls"]
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")

    # Fill input[name="maxAccessCount"]
    page.fill("input[name=\"maxAccessCount\"]", "5")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
