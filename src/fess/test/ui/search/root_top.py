"""Open / and assert the static-theme home view renders its search form and
the Help header link.

Since fess#3460, / is the bootstrap static-theme SPA. The page carries two
copies of input[name=q] / button[name=search]: the header form (#query /
#searchButton), which the home view hides, and the home form
(#contentQuery / #home-search-submit). The header copy comes first in the
DOM, so the assertions address the home copy by id.

Distinct from search/top.py, which exercises /search/.
"""
import logging
from urllib.parse import urlparse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_equal, assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


# i18n.js applyDom() fills every [data-i18n] element (and every
# [data-i18n-placeholder] placeholder) from the theme bundle, and t() falls
# back to the key itself when the bundle lacks it. So an element still showing
# its own key is untranslated. Returns [elements checked, untranslated keys].
_UNTRANSLATED_KEYS_JS = """() => {
  const text = [...document.querySelectorAll('[data-i18n]')];
  const ph = [...document.querySelectorAll('[data-i18n-placeholder]')];
  return [text.length + ph.length, [
    ...text.filter(e => e.textContent.trim() === e.dataset.i18n)
           .map(e => e.dataset.i18n),
    ...ph.filter(e => e.getAttribute('placeholder') === e.dataset.i18nPlaceholder)
         .map(e => e.dataset.i18nPlaceholder)]];
}"""


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def run(context: FessContext) -> None:
    logger.info("Starting search/root_top")
    page = context.get_wrapped_page() or context.get_admin_page()

    page.goto(context.url("/"))
    # The SPA renders after /api/v2/ui/config answers; the home view is
    # hidden until then.
    page.wait_for_selector("#home-view:not([hidden])")

    assert_true(page.is_visible('#contentQuery[name="q"]'),
                'home search input #contentQuery[name="q"] not visible on /')
    assert_true(page.is_visible('#home-search-submit[name="search"]'),
                'home search button #home-search-submit[name="search"] not '
                'visible on /')

    # Help link is always present in the header on /.
    # AI Search link is feature-flag gated, so we don't assert it here.
    # Its href is relative ("help") and resolves against the <base href>
    # Fess injects, so compare the resolved path, not the attribute.
    help_link = page.wait_for_selector("#help-link")
    help_path = urlparse(help_link.evaluate("a => a.href")).path
    assert_equal(help_path, "/help",
                 f"help link resolves to {help_path}, expected /help")

    checked, untranslated = page.evaluate(_UNTRANSLATED_KEYS_JS)
    assert_true(checked > 0, "no [data-i18n] elements on /; nothing was checked")
    assert_equal(untranslated, [],
                 f"untranslated theme keys on /: {untranslated[:5]}")

    logger.info("search/root_top completed")


def destroy(context: FessContext) -> None:
    context.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
