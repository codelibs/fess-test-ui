from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=1000)
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

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=N2SM
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/OEK07XsB16rL45wtjfyV"

    # Click text=新しいジョブの作成
    page.click("text=新しいジョブの作成")
    # assert page.url == "http://localhost:8080/admin/scheduler/createnewjob/web_crawling/OEK07XsB16rL45wtjfyV/TjJTTQ==/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/scheduler/"

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=N2SM
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/OEK07XsB16rL45wtjfyV"

    # Click text=新しいジョブの作成
    page.click("text=新しいジョブの作成")
    # assert page.url == "http://localhost:8080/admin/scheduler/createnewjob/web_crawling/OEK07XsB16rL45wtjfyV/TjJTTQ==/"

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/scheduler/"

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
