import logging
import sys

from playwright.sync_api import sync_playwright

from fess.test.ui import FessContext
from fess.test.ui.admin import (accesstoken,
                                badword,
                                boostdoc,
                                duplicatehost,
                                elevateword,
                                keymatch,
                                relatedcontent,
                                relatedquery,
                                user,
                                group,
                                role,
                                webconfig)

from fess.test.ui.admin.dict import (kuromoji,
                                     protwords)

def main():
    logger = logging.getLogger(__name__)
    with sync_playwright() as playwright:
        context: FessContext = FessContext(playwright)
        context.login()

        try:
            accesstoken.run(context)
            badword.run(context)
            boostdoc.run(context)
            duplicatehost.run(context)
            elevateword.run(context)
            keymatch.run(context)
            relatedcontent.run(context)
            relatedquery.run(context)
            user.run(context)
            group.run(context)
            role.run(context)
            kuromoji.run(context)
            protwords.run(context)
            webconfig.run(context)
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
