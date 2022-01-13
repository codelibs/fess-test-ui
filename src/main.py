import logging
import sys

from playwright.sync_api import sync_playwright

from fess.test.ui import FessContext
from fess.test.ui.admin import badword, boostdoc


def main():
    with sync_playwright() as playwright:
        context: FessContext = FessContext(playwright)
        context.login()

        badword.run(context)
        boostdoc.run(context)

        context.close()

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
