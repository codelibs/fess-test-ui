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
    # Click text=N2SM
    page.click("text=N2SM")
    # assert page.url == "http://localhost:8080/admin/labeltype/details/4/PELS7XsB16rL45wtffzM"
    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/labeltype/"
    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/labeltype/"
    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/labeltype/"
    # Fill input[name="sortOrder"]
    page.fill("input[name=\"sortOrder\"]", "0")
    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
