"""Multibyte search query smoke test.

Submits a fixed set of queries covering CJK, Cyrillic, Hindi, Turkish-cased,
RTL, emoji, SQL-injection-like, XSS-like, and very long input. For each:
  - Navigates to /search/?q=<encoded>
  - Asserts no server error markers (HTTP 500, Java stack traces).
  - Asserts the search page DOM is intact.

Detects bug categories:
  3. Functional failure on multibyte input
  4. Fess-side server error / stack trace bleed-through
  5. Multibyte input handling errors
"""
import logging
import urllib.parse

from playwright.sync_api import Playwright, sync_playwright

from fess.test import assert_true
from fess.test.ui import FessContext

logger = logging.getLogger(__name__)


SAMPLE_QUERIES = {
    "ja_kana": "テスト",
    "ja_kanji": "検索",
    "ko": "테스트",
    "zh_cn": "测试",
    "zh_tw": "測試",
    "ru": "тест",
    "hi": "परीक्षण",
    "tr_dotted_i": "İğüş",
    "ar_rtl": "اختبار",
    "emoji": "🔍 search",
    "sqli_like": "test' OR '1'='1",
    "xss_like": "<script>alert(1)</script>",
    "long": "a" * 500,
    "mixed": "tést café αβγ 测试",
}


_SERVER_ERROR_MARKERS = [
    "HTTP Status 500",
    "java.lang.",
    "javax.servlet.",
    "org.codelibs.fess.exception",
    "Whitelabel Error Page",
]


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def _assert_no_server_error(body_text: str, q: str) -> None:
    for marker in _SERVER_ERROR_MARKERS:
        assert_true(
            marker not in body_text,
            f"Server error marker {marker!r} found in body for q={q!r}")


def run(context: FessContext) -> None:
    logger.info(f"Starting search/multibyte_query (lang={context.lang})")
    page = context.get_wrapped_page() or context.get_admin_page()

    failures = []
    for label, q in SAMPLE_QUERIES.items():
        encoded = urllib.parse.quote(q, safe="")
        url = context.url(f"/search/?q={encoded}")
        try:
            response = page.goto(url, timeout=20000)
            page.wait_for_load_state("domcontentloaded")
            status = response.status if response else 0
            if status >= 500:
                failures.append(f"{label}: HTTP {status} for q={q!r}")
                continue
            body_text = page.inner_text("body")
            _assert_no_server_error(body_text, q)
            assert_true(
                page.query_selector('input[name="q"]') is not None,
                f"search input missing after q={q!r}")
        except AssertionError:
            raise
        except Exception as e:
            failures.append(f"{label}: {type(e).__name__}: {e} for q={q!r}")

    assert_true(len(failures) == 0,
                f"multibyte_query failures: {failures[:5]}")
    logger.info("search/multibyte_query completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with sync_playwright() as p:
        ctx = setup(p)
        try:
            run(ctx)
        finally:
            destroy(ctx)
