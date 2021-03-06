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

    # Fill textarea[name="description"]
    page.fill("textarea[name=\"description\"]", "Fessのサイト")

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

    # Fill textarea[name="excludedDocUrls"]
    page.fill("textarea[name=\"excludedDocUrls\"]", ".*/fess/.*")

    # Fill input[name="depth"]
    page.fill("input[name=\"depth\"]", "1")

    # Fill input[name="maxAccessCount"]
    page.fill("input[name=\"maxAccessCount\"]", "30")

    # Fill input[name="numOfThread"]
    page.fill("input[name=\"numOfThread\"]", "2")

    # Fill input[name="boost"]
    page.fill("input[name=\"boost\"]", "100")

    # Fill textarea[name="description"]
    page.fill("textarea[name=\"description\"]", "N2SMのサイト")

    # Click button:has-text("作成")
    page.click("button:has-text(\"作成\")")
    # assert page.url == "http://localhost:8080/admin/webconfig/"


    # Click text=新規作成 >> em
    page.click("text=新規作成 >> em")
    # assert page.url == "http://localhost:8080/admin/webconfig/createnew/"

    # Fill input[name="name"]
    page.fill("input[name=\"name\"]", "Elasticsearch")

    # Fill textarea[name="urls"]
    page.fill("textarea[name=\"urls\"]", "https://www.elastic.co/jp/elasticsearch/")

    # Fill textarea[name="includedUrls"]
    page.fill("textarea[name=\"includedUrls\"]", "https://www.elastic.co/jp/elasticsearch/.*")

    # Fill textarea[name="excludedUrls"]
    page.fill("textarea[name=\"excludedUrls\"]", "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)")

    # Select false
    page.select_option("select[name=\"available\"]", "false")

    # Fill textarea[name="description"]
    page.fill("textarea[name=\"description\"]", "Elasticsearchのサイト")

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
