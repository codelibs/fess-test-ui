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

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/user/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "taro")

    # Fill input[name="password"]
    page.fill("input[name=\"password\"]", "taro1234")

    # Fill input[name="confirmPassword"]
    page.fill("input[name=\"confirmPassword\"]", "taro1234")

    # Fill input[name="attributes.surname"]
    page.fill("input[name=\"attributes.surname\"]", "Yamada")

    # Fill input[name="attributes.givenName"]
    page.fill("input[name=\"attributes.givenName\"]", "Taro")

    # Fill input[name="attributes.mail"]
    page.fill("input[name=\"attributes.mail\"]", "taro@example.com")

    # Click select[name="roles"]
    page.select_option('select#roles', ['YWRtaW4=', 'Z3Vlc3Q='])

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/user/"

    # Click .fa.fa-sign-out-alt
    page.click(".fa.fa-sign-out-alt")
    # assert page.url == "http://localhost:8080/login/"

    # Fill [placeholder="ユーザー名"]
    page.fill("[placeholder=\"ユーザー名\"]", "taro")

    # Fill [placeholder="パスワード"]
    page.fill("[placeholder=\"パスワード\"]", "taro1234")

    # Click button:has-text("ログイン")
    page.click("button:has-text(\"ログイン\")")
    # assert page.url == "http://localhost:8080/"

    # Click .fa
    page.click(".fa")
    # assert page.url == "http://localhost:8080/"

    # Click text=taro
    page.click("text=taro")

    # Click text=パスワード変更
    page.click("text=パスワード変更")
    # assert page.url == "http://localhost:8080/profile/"

    # Fill [placeholder="現在のパスワード"]
    page.fill("[placeholder=\"現在のパスワード\"]", "taro1234")

    # Fill [placeholder="新しいパスワード"]
    page.fill("[placeholder=\"新しいパスワード\"]", "taro5678")

    # Fill [placeholder="新しいパスワードの確認"]
    page.fill("[placeholder=\"新しいパスワードの確認\"]", "taro5678")

    # Click text=更新
    page.click("text=更新")
    # assert page.url == "http://localhost:8080/profile/"

    # Click text=戻る >> em
    page.click("text=戻る >> em")
    # assert page.url == "http://localhost:8080/"

    # Click text=taro
    page.click("text=taro")

    # Click text=ログアウト
    page.click("text=ログアウト")
    # assert page.url == "http://localhost:8080/login/"

    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
