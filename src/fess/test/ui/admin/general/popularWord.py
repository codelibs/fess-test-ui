from playwright.sync_api import Playwright, sync_playwright
import time


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/
    page.goto("http://localhost:8080/search/?q=fess")

    for i in range(10):

        time.sleep(60)

        # Click button[name="search"]
        page.click("button[name=\"search\"]")
        # assert page.url == "http://localhost:8080/search/?q=fess&num=10&sort="

    else:

        # Close page
        page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
