import logging
import os
import random
import string
import time
from datetime import datetime
from typing import Callable, Any, Optional, TYPE_CHECKING

from playwright.sync_api import Playwright

if TYPE_CHECKING:
    from playwright.sync_api import Page, Response, ElementHandle

logger = logging.getLogger(__name__)


class PageWrapper:
    """
    Wrapper for Playwright Page that adds logging to browser operations.

    Logs click, fill, navigation, and other browser interactions at DEBUG level.
    """

    def __init__(self, page: "Page"):
        self._page = page
        self._logger = logging.getLogger(f"{__name__}.PageWrapper")

    def __getattr__(self, name: str):
        """Delegate unknown attributes to the wrapped page."""
        return getattr(self._page, name)

    def click(self, selector: str, **kwargs) -> None:
        """Click an element with logging."""
        self._logger.debug(f"[CLICK] selector='{selector}'")
        try:
            self._page.click(selector, **kwargs)
            self._logger.debug(f"[CLICK] completed: {selector}")
        except Exception as e:
            self._logger.error(f"[CLICK] failed: {selector} - {e}")
            raise

    def fill(self, selector: str, value: str, **kwargs) -> None:
        """Fill an input field with logging."""
        display_value = '***' if self._is_sensitive_field(selector) else self._truncate_value(value)
        self._logger.debug(f"[FILL] selector='{selector}' value='{display_value}'")
        try:
            self._page.fill(selector, value, **kwargs)
            self._logger.debug(f"[FILL] completed: {selector}")
        except Exception as e:
            self._logger.error(f"[FILL] failed: {selector} - {e}")
            raise

    def goto(self, url: str, **kwargs) -> "Response":
        """Navigate to a URL with logging."""
        self._logger.debug(f"[GOTO] url='{url}'")
        try:
            response = self._page.goto(url, **kwargs)
            status = response.status if response else 'N/A'
            self._logger.debug(f"[GOTO] completed: {url} status={status}")
            return response
        except Exception as e:
            self._logger.error(f"[GOTO] failed: {url} - {e}")
            raise

    def wait_for_selector(self, selector: str, **kwargs) -> "ElementHandle":
        """Wait for a selector with logging."""
        self._logger.debug(f"[WAIT_SELECTOR] selector='{selector}'")
        try:
            result = self._page.wait_for_selector(selector, **kwargs)
            self._logger.debug(f"[WAIT_SELECTOR] found: {selector}")
            return result
        except Exception as e:
            self._logger.error(f"[WAIT_SELECTOR] timeout: {selector} - {e}")
            raise

    def wait_for_load_state(self, state: str = "load", **kwargs) -> None:
        """Wait for load state with logging."""
        self._logger.debug(f"[WAIT_STATE] state='{state}'")
        self._page.wait_for_load_state(state, **kwargs)
        self._logger.debug(f"[WAIT_STATE] completed: {state}")

    def inner_text(self, selector: str, **kwargs) -> str:
        """Get inner text with logging."""
        self._logger.debug(f"[INNER_TEXT] selector='{selector}'")
        result = self._page.inner_text(selector, **kwargs)
        self._logger.debug(f"[INNER_TEXT] length={len(result)}")
        return result

    def input_value(self, selector: str, **kwargs) -> str:
        """Get input value with logging."""
        self._logger.debug(f"[INPUT_VALUE] selector='{selector}'")
        result = self._page.input_value(selector, **kwargs)
        display_result = '***' if self._is_sensitive_field(selector) else self._truncate_value(result)
        self._logger.debug(f"[INPUT_VALUE] value='{display_result}'")
        return result

    def select_option(self, selector: str, value=None, **kwargs):
        """Select option with logging."""
        self._logger.debug(f"[SELECT_OPTION] selector='{selector}' value='{value}'")
        try:
            result = self._page.select_option(selector, value, **kwargs)
            self._logger.debug(f"[SELECT_OPTION] completed: {selector}")
            return result
        except Exception as e:
            self._logger.error(f"[SELECT_OPTION] failed: {selector} - {e}")
            raise

    def screenshot(self, **kwargs) -> bytes:
        """Take screenshot with logging."""
        path = kwargs.get('path', 'unknown')
        self._logger.debug(f"[SCREENSHOT] path='{path}'")
        return self._page.screenshot(**kwargs)

    def _is_sensitive_field(self, selector: str) -> bool:
        """Check if a selector refers to a sensitive field."""
        sensitive_patterns = ['password', 'secret', 'token', 'key', 'credential']
        selector_lower = selector.lower()
        return any(pattern in selector_lower for pattern in sensitive_patterns)

    def _truncate_value(self, value: str, max_length: int = 50) -> str:
        """Truncate a value for display in logs."""
        if len(value) > max_length:
            return value[:max_length] + '...'
        return value

    @property
    def url(self) -> str:
        """Get current URL."""
        return self._page.url

    @property
    def content(self):
        """Get page content method."""
        return self._page.content


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
        random.seed(int(datetime.now().timestamp() * 1000))

        # Tracing configuration
        self._trace_on_failure = os.environ.get("TRACE_ON_FAILURE", "false").lower() == "true"
        self._trace_all = os.environ.get("TRACE_ALL", "false").lower() == "true"
        self._trace_dir = os.environ.get("TRACE_DIR", "traces")
        self._tracing_active = False
        self._current_module_name: str = None

        # Start tracing if enabled
        if self._trace_all or self._trace_on_failure:
            self._start_tracing()

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

    def _start_tracing(self) -> None:
        """Start Playwright tracing."""
        if not self._tracing_active:
            try:
                self._context.tracing.start(
                    screenshots=True,
                    snapshots=True,
                    sources=True
                )
                self._tracing_active = True
                logger.debug("[TRACE] Tracing started")
            except Exception as e:
                logger.warning(f"[TRACE] Failed to start tracing: {e}")

    def start_module_trace(self, module_name: str) -> None:
        """
        Start a new trace chunk for a test module.

        Args:
            module_name: Name of the test module
        """
        self._current_module_name = module_name
        if self._tracing_active:
            try:
                self._context.tracing.start_chunk()
                logger.debug(f"[TRACE] Started chunk for module: {module_name}")
            except Exception as e:
                logger.warning(f"[TRACE] Failed to start chunk: {e}")

    def stop_module_trace(self, save: bool = False, status: str = "passed") -> Optional[str]:
        """
        Stop the current trace chunk.

        Args:
            save: Whether to save the trace file
            status: Test status (passed/failed/error)

        Returns:
            Path to saved trace file or None
        """
        if not self._tracing_active:
            return None

        trace_path = None
        should_save = save or self._trace_all or (self._trace_on_failure and status != "passed")

        if should_save and self._current_module_name:
            try:
                os.makedirs(self._trace_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                trace_path = os.path.join(
                    self._trace_dir,
                    f"trace_{self._current_module_name}_{status}_{timestamp}.zip"
                )
                self._context.tracing.stop_chunk(path=trace_path)
                logger.info(f"[TRACE] Saved: {trace_path}")
            except Exception as e:
                logger.warning(f"[TRACE] Failed to save trace: {e}")
        else:
            try:
                self._context.tracing.stop_chunk()
                logger.debug("[TRACE] Stopped chunk (not saved)")
            except Exception as e:
                logger.debug(f"[TRACE] Stop chunk note: {e}")

        return trace_path

    def get_admin_page(self) -> PageWrapper:
        """Get admin page with logging wrapper."""
        page: "Page" = self._current_page if self._current_page is not None else self._context.new_page()
        self._current_page = page
        page.goto(f"{self._base_url}/admin/")
        logger.debug(f"URL: {page.url}")
        return PageWrapper(page)

    def get_current_page(self) -> "Page":
        """Get current raw page (for backwards compatibility)."""
        return self._current_page

    def get_wrapped_page(self) -> Optional[PageWrapper]:
        """Get current page with logging wrapper."""
        if self._current_page is None:
            return None
        return PageWrapper(self._current_page)

    def close(self) -> None:
        """Close browser context and stop tracing."""
        # Stop tracing if active
        if self._tracing_active:
            try:
                self._context.tracing.stop()
                logger.debug("[TRACE] Tracing stopped")
            except Exception as e:
                logger.debug(f"[TRACE] Stop tracing note: {e}")

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

    def retry_on_failure(self, func: Callable[[], Any], max_attempts: int = 3,
                        delay: float = 1.0, context_name: str = "operation") -> Any:
        """
        Retry a function on failure (for handling flaky tests).

        Args:
            func: Function to execute
            max_attempts: Maximum number of attempts (default: 3)
            delay: Delay between retries in seconds (default: 1.0)
            context_name: Name for logging context

        Returns:
            Result of the function

        Raises:
            Exception: If all attempts fail, raises the last exception
        """
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"[RETRY] {context_name}: attempt {attempt}/{max_attempts}")
                result = func()
                if attempt > 1:
                    logger.info(f"[RETRY] {context_name}: succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_exception = e
                if attempt < max_attempts:
                    logger.warning(
                        f"[RETRY] {context_name}: attempt {attempt} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"[RETRY] {context_name}: all {max_attempts} attempts failed"
                    )

        # If we get here, all attempts failed
        raise last_exception

    def log_step(self, step_name: str, capture_screenshot: bool = False):
        """
        Log a test step for better debugging.

        Args:
            step_name: Name of the step
            capture_screenshot: Whether to capture screenshot (default: False)
        """
        logger.info(f"[STEP] {step_name}")

        if capture_screenshot and self._current_page:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                os.makedirs('screenshots/steps', exist_ok=True)
                screenshot_path = f'screenshots/steps/step_{timestamp}.png'
                self._current_page.screenshot(path=screenshot_path)
                logger.debug(f"[STEP] Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.warning(f"[STEP] Failed to capture screenshot: {e}")

    def capture_screenshot(self, name: str) -> Optional[str]:
        """
        Capture a screenshot with a custom name.

        Args:
            name: Name for the screenshot file

        Returns:
            Path to saved screenshot or None if failed
        """
        if not self._current_page:
            logger.warning("No page available for screenshot")
            return None

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs('screenshots', exist_ok=True)
            screenshot_path = f'screenshots/{name}_{timestamp}.png'
            self._current_page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
