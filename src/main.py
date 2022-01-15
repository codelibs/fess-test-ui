import logging
import sys

from playwright.sync_api import sync_playwright

from fess.test.ui import FessContext
from fess.test.ui.admin import badword, boostdoc


def main():
    logger = logging.getLogger(__name__)
    with sync_playwright() as playwright:
        context: FessContext = FessContext(playwright)
        context.login()

        try:
            badword.run(context)
            boostdoc.run(context)
        except:
            page: "Page" = context.get_current_page()
            if page is not None:
                logger.info(f"URL: {page.url}")
                logger.info(f"Content:\n{page.content()}")
            raise

        context.close()

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
