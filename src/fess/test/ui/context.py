import logging
import os
import random
import string
import time
from datetime import datetime
from typing import Callable, Any, Optional

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
        random.seed(int(datetime.now().timestamp() * 1000))

    def _create_browser(self):
        headless: bool = os.environ.get("HEADLESS", "false").lower() == "true"
        return self._playwright.chromium.launch(headless=headless, slow_mo=500)

    def login(self, username: str = os.environ.get("FESS_USERNAME", "admin"),
              password: str = os.environ.get("FESS_PASSWORD", "admin")) -> bool:
        page: "Page" = self._current_page if self._current_page is not None else self._context.new_page()

        # Navigate to login page
        page.goto(f"{self._base_url}/login/", wait_until="networkidle", timeout=60000)
        logger.debug(f"Login page URL: {page.url}")

        # Fill login form
        page.wait_for_selector("[placeholder=\"ユーザー名\"]", state="visible", timeout=30000)
        page.fill("[placeholder=\"ユーザー名\"]", username)
        page.fill("[placeholder=\"パスワード\"]", password)

        # Click login and wait for navigation
        page.click("button:has-text(\"ログイン\")")

        # Wait for navigation to complete (redirect after login)
        page.wait_for_load_state("networkidle", timeout=30000)

        logger.debug(f"After login URL: {page.url}")

        # Verify we're not still on the login page (login succeeded)
        if "/login" in page.url:
            logger.error("Login may have failed - still on login page")
            return False

        logger.info("Login successful")
        return True

    def get_admin_page(self) -> "Page":
        page: "Page" = self._current_page if self._current_page is not None else self._context.new_page()
        self._current_page = page

        # Navigate to admin page
        page.goto(f"{self._base_url}/admin/", wait_until="networkidle", timeout=60000)
        logger.debug(f"Navigated to: {page.url}")

        # Wait much longer for the admin dashboard to be fully loaded and rendered
        # The JavaScript needs time to execute and render the UI
        logger.info("Waiting for admin dashboard to fully render...")
        page.wait_for_timeout(5000)  # Give JavaScript time to execute

        # Wait for the page body to be ready
        try:
            page.wait_for_selector("body", state="attached", timeout=10000)
            logger.debug("Page body is attached")
        except Exception as e:
            logger.warning(f"Body selector timeout: {e}")

        # Additional wait for any AJAX/dynamic content to finish loading
        page.wait_for_load_state("networkidle", timeout=30000)

        # Final wait for UI to stabilize
        page.wait_for_timeout(3000)

        # Aggressively expand and make visible all menu items
        # This handles Fess admin UI's complex navigation structure
        try:
            page.evaluate("""
                // Force all elements with 'collapse' class to be visible
                document.querySelectorAll('.collapse').forEach(el => {
                    el.classList.add('show');
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.height = 'auto';
                });

                // Click all collapsed menu toggles and make them active
                document.querySelectorAll('[data-toggle="collapse"]').forEach(el => {
                    el.classList.remove('collapsed');
                    el.setAttribute('aria-expanded', 'true');
                    if (el.classList.contains('collapsed')) {
                        el.click();
                    }
                });

                // Force all dropdown menus to be visible and accessible
                document.querySelectorAll('.dropdown-menu').forEach(el => {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.position = 'static';
                    el.style.opacity = '1';
                });

                // Make all navigation links visible
                document.querySelectorAll('nav a, .navbar a, .sidebar a, [role="navigation"] a').forEach(el => {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                });

                // Force show all list items in navigation
                document.querySelectorAll('nav li, .navbar li, .sidebar li, [role="navigation"] li').forEach(el => {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                });

                // Remove any 'd-none' or 'hidden' classes
                document.querySelectorAll('.d-none, .hidden').forEach(el => {
                    el.classList.remove('d-none', 'hidden');
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                });

                // Expand any accordion-style menus
                document.querySelectorAll('.accordion-collapse').forEach(el => {
                    el.classList.add('show');
                    el.style.display = 'block';
                });
            """)
            logger.info("Aggressively expanded all navigation menus")
            page.wait_for_timeout(2000)  # Wait for all animations to complete
        except Exception as e:
            logger.warning(f"Could not expand menus: {e}")

        logger.info("Admin dashboard should now be fully loaded with all menus visible")
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
