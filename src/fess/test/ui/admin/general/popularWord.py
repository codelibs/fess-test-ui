from playwright.sync_api import Playwright, sync_playwright
import time
import logging

logger = logging.getLogger(__name__)


def run(playwright: Playwright) -> None:
    logger.info("Starting popular word test")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://localhost:8080/
    logger.info("Step 1: Navigate to search page")
    page.goto("http://localhost:8080/search/?q=fess")

    logger.info("Step 2: Perform repeated searches to generate popular word data")
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

    logger.info("Popular word test completed successfully")


with sync_playwright() as playwright:
    run(playwright)
