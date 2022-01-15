import logging
import os
import random
import string
from datetime import datetime

from playwright.sync_api import Playwright

logger = logging.getLogger(__name__)


class FessContext:
    def __init__(self, playwright: Playwright) -> None:
        self._playwright = playwright
        self._browser = self._create_browser()
        self._context = self._browser.new_context(
            locale=os.environ.get("BROWSER_LOCALE", "ja-JP"))
        self._base_url: str = os.environ.get(
            "FESS_URL", "http://localhost:8080")
        self._current_page: "Page" = None
        self._test_label_name: str = os.environ.get("TEST_LABEL")
        random.seed(datetime.now())

    def _create_browser(self):
        headless: bool = os.environ.get("HEADLESS", "false").lower() == "true"
        return self._playwright.chromium.launch(headless=headless, slow_mo=500)

    def login(self, username: str = os.environ.get("FESS_USERNAME", "admin"),
              password: str = os.environ.get("FESS_PASSWORD", "admin")) -> bool:
        page: "Page" = self._current_page if self._current_page is not None else self._context.new_page()

        page.goto(f"{self._base_url}/login/")
        logger.debug(f"URL: {page.url}")

        page.fill("[placeholder=\"ユーザー名\"]", username)
        page.fill("[placeholder=\"パスワード\"]", password)

        page.click("button:has-text(\"ログイン\")")

        logger.debug(f"URL: {page.url}")
        return True  # TODO

    def get_admin_page(self) -> "Page":
        page: "Page" = self._current_page if self._current_page is not None else self._context.new_page()
        self._current_page = page
        page.goto(f"{self._base_url}/admin/")
        logger.debug(f"URL: {page.url}")
        return page

    def get_current_page(self) -> "Page":
        return self._current_page

    def close(self) -> None:
        if self._current_page is not None:
            self._current_page.close()
        self._context.close()
        self._browser.close()

    def create_label_name(self, len: int = 20) -> str:
        if self._test_label_name is None:
            self._test_label_name = self.generate_str(len)
        return self._test_label_name

    def generate_str(self, len: int = 20) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=len))

    def url(self, path: str) -> str:
        return self._base_url+path
