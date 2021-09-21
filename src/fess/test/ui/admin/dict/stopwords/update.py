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

    # Click text=en/stopwords.txt
    page.click("text=en/stopwords.txt")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="

    # Click a:has-text("2")
    page.click("a:has-text(\"2\")")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/list/2?dictId=ZW4vc3RvcHdvcmRzLnR4dA%3D%3D"

    # Click :nth-match(:text("he"), 4)
    page.click(":nth-match(:text(\"he\"), 4)")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/details/ZW4vc3RvcHdvcmRzLnR4dA%3D%3D/4/34"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/"

    # Click text=戻る
    page.click("text=戻る")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/"

    # Click text=編集
    page.click("text=編集")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/"

    # Fill input[name="input"]
    page.fill("input[name=\"input\"]", "she")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/admin/dict/stopwords/list/1?dictId=ZW4vc3RvcHdvcmRzLnR4dA=="

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
