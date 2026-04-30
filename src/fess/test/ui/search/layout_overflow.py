"""Layout overflow detector for long-translation languages.

For a fixed set of pages, evaluates DOM elements (.nav-link, .btn) and
checks that none are completely off-screen. Soft-warns on text overflow
within their container (since some ellipsis is acceptable).

Detects bug categories:
  2. Layout broken from long translations
"""
import logging

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


PAGES_TO_CHECK = [
    "/search/",
    "/admin/",
    "/admin/dashboard/",
    "/admin/scheduler/",
]


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    logger.info(f"Starting search/layout_overflow (lang={context.lang})")
    page = context.get_wrapped_page() or context.get_admin_page()

    hard_failures = []
    for path in PAGES_TO_CHECK:
        page.goto(context.url(path))
        page.wait_for_load_state("domcontentloaded")

        soft_overflow = page.evaluate("""
            () => {
              const items = document.querySelectorAll('.nav-link, .btn');
              return [...items].filter(el => el.scrollWidth > el.clientWidth + 2)
                                .map(el => ({
                                  text: (el.innerText || '').slice(0, 50),
                                  tag: el.tagName,
                                  scroll: el.scrollWidth,
                                  client: el.clientWidth,
                                }));
            }
        """)
        if soft_overflow:
            logger.warning(
                f"[layout] Soft-overflow on {path} ({len(soft_overflow)} elements): "
                f"{soft_overflow[:3]}")

        offscreen = page.evaluate("""
            () => {
              const items = document.querySelectorAll('.nav-link, .btn');
              return [...items].filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && (r.left < -100 || r.top < -100);
              }).map(el => (el.innerText || '').slice(0, 50));
            }
        """)
        if offscreen:
            hard_failures.append(f"{path}: {len(offscreen)} elements off-screen ({offscreen[:3]})")

    assert_true(
        len(hard_failures) == 0,
        f"Off-screen elements detected: {hard_failures}")

    logger.info("search/layout_overflow completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
