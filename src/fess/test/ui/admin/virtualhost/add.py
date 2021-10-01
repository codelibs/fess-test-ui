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

    # Click text=全般
    page.click("text=全般")
    # assert page.url == "http://localhost:8080/admin/general/"

    # Fill textarea[name="virtualHostValue"]
    page.fill("textarea[name=\"virtualHostValue\"]", "Host:localhost:8080=host1\nHost:127.0.0.1:8080=host2")

    # Click button:has-text("更新")
    page.click("button:has-text(\"更新\")")
    # assert page.url == "http://localhost:8080/admin/general/"


    # Click text=クローラー
    page.click("text=クローラー")

    # Click text=ウェブ
    page.click("text=ウェブ")
    # assert page.url == "http://localhost:8080/admin/webconfig/"

    # Click text=新規作成 >> em
    page.click("text=新規作成 >> em")
    # assert page.url == "http://localhost:8080/admin/webconfig/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "Fess")

    # Fill textarea[name="urls"]
    page.fill("textarea[name=\"urls\"]", "https://fess.codelibs.org/ja/")

    # Fill textarea[name="includedUrls"]
    page.fill("textarea[name=\"includedUrls\"]", "https://fess.codelibs.org/ja/.*")

    # Fill textarea[name="excludedUrls"]
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")

    # Fill input[name="maxAccessCount"]
    page.fill("input[name=\"maxAccessCount\"]", "30")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "2")

    # Fill textarea[name="virtualHosts"]
    page.fill("textarea[name=\"virtualHosts\"]", "host1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/webconfig/"


    # Click text=新規作成 >> em
    page.click("text=新規作成 >> em")
    # assert page.url == "http://localhost:8080/admin/webconfig/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "N2SM")

    # Fill textarea[name="urls"]
    page.fill("textarea[name=\"urls\"]", "https://www.n2sm.net/products/")

    # Fill textarea[name="includedUrls"]
    page.fill("textarea[name=\"includedUrls\"]", "https://www.n2sm.net/products/.*")

    # Fill textarea[name="excludedUrls"]
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")

    # Fill input[name="maxAccessCount"]
    page.fill("input[name=\"maxAccessCount\"]", "30")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "2")

    # Fill textarea[name="virtualHosts"]
    page.fill("textarea[name=\"virtualHosts\"]", "host2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/webconfig/"



    # Click text=ラベル
    page.click("text=ラベル")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/labeltype/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "FESS")

    # Fill input[name="value"]
    page.fill("input[name=\"value\"]", "fess")

    # Fill textarea[name="includedPaths"]
    page.fill("textarea[name=\"includedPaths\"]", "https://fess.codelibs.org/ja/.*")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/labeltype/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/labeltype/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "N2SM")

    # Fill input[name="value"]
    page.fill("input[name=\"value\"]", "n2sm")

    # Fill textarea[name="includedPaths"]
    page.fill("textarea[name=\"includedPaths\"]", "https://www.n2sm.net/products/.*")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/labeltype/"



    # Click text=キーマッチ
    page.click("text=キーマッチ")
    # assert page.url == "http://localhost:8080/admin/keymatch/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/keymatch/createnew/"

    # Fill input[name="term"]
    page.fill("input[name=\"term\"]", "fess")

    # Fill input[name="query"]
    page.fill("input[name=\"query\"]", "url:*install*")

    # Fill input[name="maxSize"]
    page.fill("input[name=\"maxSize\"]", "10")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/keymatch/"

    # Click text=キーマッチ
    page.click("text=キーマッチ")
    # assert page.url == "http://localhost:8080/admin/keymatch/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/keymatch/createnew/"

    # Fill input[name="term"]
    page.fill("input[name=\"term\"]", "n2sm")

    # Fill input[name="query"]
    page.fill("input[name=\"query\"]", "url:*products*")

    # Fill input[name="maxSize"]
    page.fill("input[name=\"maxSize\"]", "10")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/keymatch/"



    # Click text=関連コンテンツ
    page.click("text=関連コンテンツ")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"term\"]", "fess")

    # Fill textarea[name="content"]
    page.fill("textarea[name=\"content\"]", "<a href=\"https://fess.codelibs.org/ja/\">Fess</a>のサイトはこちら。")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"term\"]", "n2sm")

    # Fill textarea[name="content"]
    page.fill("textarea[name=\"content\"]", "<a href=\"https://www.n2sm.net/\">N2SM,Inc.</a>のサイトはこちら。")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/relatedcontent/"


    # Click text=関連クエリー
    page.click("text=関連クエリー")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/relatedquery/createnew/"

    # Fill input[name="term"]
    page.fill("input[name=\"term\"]", "fess")

    # Fill textarea[name="queries"]
    page.fill("textarea[name=\"queries\"]", "全文検索")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host1")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=関連クエリー
    page.click("text=関連クエリー")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"

    # Click text=新規作成
    page.click("text=新規作成")
    # assert page.url == "http://localhost:8080/admin/relatedquery/createnew/"

    # Fill input[name="term"]
    page.fill("input[name=\"term\"]", "n2sm")

    # Fill textarea[name="queries"]
    page.fill("textarea[name=\"queries\"]", "サービス")

    # Fill input[name="virtualHost"]
    page.fill("input[name=\"virtualHost\"]", "host2")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/relatedquery/"


    # Close page
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
