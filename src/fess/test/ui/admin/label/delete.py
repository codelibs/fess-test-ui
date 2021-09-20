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
    # Click text=ラベル
    page.click("text=ラベル")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Click text=FESS
    page.click("text=FESS")
    # assert page.url == "http://localhost:8080/admin/labeltype/details/4/PELS7XsB16rL45wtffzM"
    # Click text=削除
    page.click("text=削除")
    # Click text=キャンセル
    page.click("text=キャンセル")
    # Click text=削除
    page.click("text=削除")
    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Click text=N2SM
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/labeltype/details/4/PELS7XsB16rL45wtffzM"
    # Click text=削除
    page.click("text=削除")
    # Click text=キャンセル
    page.click("text=キャンセル")
    # Click text=削除
    page.click("text=削除")
    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=Fess
    page.click("text=Fess")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/DjOI43sBmGFYKOYwJjoF"

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=Fess
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/webconfig/details/4/DjOI43sBmGFYKOYwJjoF"

    # Click text=削除
    page.click("text=削除")

    # Click text=キャンセル 削除 >> button[name="delete"]
    page.click("text=キャンセル 削除 >> button[name=\"delete\"]")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
