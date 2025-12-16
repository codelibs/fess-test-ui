"""
HTML Capture Module for Test Coverage Analysis.

Captures HTML snapshots during test execution for later analysis
to identify untested UI elements and improve test coverage.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class HTMLCapture:
    """
    HTML snapshot capture manager.

    Captures page HTML at key points during test execution:
    - On page navigation
    - On test failures (when enabled)

    Environment Variables:
        HTML_CAPTURE: Enable capture ('true', 'false', 'on_failure')
        HTML_CAPTURE_DIR: Output directory (default: 'html_snapshots')
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize HTML capture manager.

        Args:
            base_dir: Base directory for HTML snapshots
        """
        self._base_dir = base_dir or os.environ.get("HTML_CAPTURE_DIR", "html_snapshots")
        self._capture_mode = os.environ.get("HTML_CAPTURE", "false").lower()
        self._enabled = self._capture_mode != "false"
        self._on_failure_only = self._capture_mode == "on_failure"

        self._current_module: Optional[str] = None
        self._current_test: Optional[str] = None
        self._counter: int = 0
        self._date_str: str = datetime.now().strftime('%Y%m%d')
        self._captured_files: list = []

        if self._enabled:
            logger.info(f"[HTML_CAPTURE] Enabled (mode={self._capture_mode}, dir={self._base_dir})")

    @property
    def enabled(self) -> bool:
        """Check if HTML capture is enabled."""
        return self._enabled

    @property
    def on_failure_only(self) -> bool:
        """Check if capture is only for failures."""
        return self._on_failure_only

    @property
    def captured_files(self) -> list:
        """Get list of captured HTML files."""
        return self._captured_files.copy()

    def set_context(self, module: str, test: str = None) -> None:
        """
        Set the current test context for file organization.

        Args:
            module: Name of the test module (e.g., 'label', 'user')
            test: Name of the test type (e.g., 'add', 'update', 'delete')
        """
        self._current_module = module
        self._current_test = test
        self._counter = 0
        logger.debug(f"[HTML_CAPTURE] Context set: module={module}, test={test}")

    def capture(self, page: "Page", action: str, url: str = None,
                step_description: str = None, force: bool = False) -> Optional[str]:
        """
        Capture current page HTML with metadata.

        Args:
            page: Playwright page object
            action: Action description (e.g., 'navigate', 'after_click')
            url: URL to record (defaults to page.url)
            step_description: Human-readable step description
            force: Force capture even if on_failure_only mode

        Returns:
            Path to saved HTML file or None if capture is disabled/failed
        """
        # Check if capture should proceed
        if not self._enabled:
            return None

        if self._on_failure_only and not force:
            return None

        if page is None:
            logger.warning("[HTML_CAPTURE] No page provided for capture")
            return None

        try:
            # Build directory path
            dir_path = self._build_dir_path()
            os.makedirs(dir_path, exist_ok=True)

            # Generate filename
            self._counter += 1
            timestamp = datetime.now().strftime('%H%M%S')
            base_name = f"{self._counter:03d}_{timestamp}_{action}"

            # Save HTML
            html_path = os.path.join(dir_path, f"{base_name}.html")
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Save metadata
            metadata = self._build_metadata(page, action, url, step_description)
            metadata_path = os.path.join(dir_path, f"{base_name}.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self._captured_files.append(html_path)
            logger.debug(f"[HTML_CAPTURE] Saved: {html_path}")

            return html_path

        except Exception as e:
            logger.error(f"[HTML_CAPTURE] Failed to capture: {e}")
            return None

    def capture_on_failure(self, page: "Page", error_message: str = None) -> Optional[str]:
        """
        Capture HTML when a test fails (always captures regardless of mode).

        Args:
            page: Playwright page object
            error_message: Error message from the failure

        Returns:
            Path to saved HTML file or None if failed
        """
        return self.capture(
            page=page,
            action="failure",
            step_description=f"Test failure: {error_message}" if error_message else "Test failure",
            force=True
        )

    def _build_dir_path(self) -> str:
        """Build directory path based on current context."""
        parts = [self._base_dir, self._date_str]

        if self._current_module:
            parts.append(self._current_module)

        if self._current_test:
            parts.append(self._current_test)

        return os.path.join(*parts)

    def _build_metadata(self, page: "Page", action: str,
                        url: str = None, step_description: str = None) -> dict:
        """Build metadata dictionary for the capture."""
        actual_url = url or page.url

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "module": self._current_module,
            "test": self._current_test,
            "action": action,
            "url": actual_url,
            "page_title": self._get_page_title(page),
            "counter": self._counter,
        }

        if step_description:
            metadata["step_description"] = step_description

        # Extract path from URL for easier analysis
        try:
            from urllib.parse import urlparse
            parsed = urlparse(actual_url)
            metadata["url_path"] = parsed.path
        except Exception:
            pass

        return metadata

    def _get_page_title(self, page: "Page") -> str:
        """Safely get page title."""
        try:
            return page.title()
        except Exception:
            return ""

    def get_summary(self) -> dict:
        """Get summary of captured files."""
        return {
            "enabled": self._enabled,
            "mode": self._capture_mode,
            "base_dir": self._base_dir,
            "total_captures": len(self._captured_files),
            "captured_files": self._captured_files
        }

    def reset(self) -> None:
        """Reset capture state for a new test run."""
        self._current_module = None
        self._current_test = None
        self._counter = 0
        self._captured_files = []
        self._date_str = datetime.now().strftime('%Y%m%d')
