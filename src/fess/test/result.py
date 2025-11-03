"""
Test result tracking and reporting for Fess UI tests.

This module provides classes for collecting and reporting test results
in a structured format suitable for CI/CD integration.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Represents the result of a single test module execution"""

    module: str
    status: str  # 'passed', 'failed', 'error'
    duration: float
    tests_run: int = 0
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    screenshot_path: Optional[str] = None
    url_at_failure: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class TestSummary:
    """Summary of all test results"""

    total_modules: int
    passed: int
    failed: int
    errors: int
    total_duration: float
    timestamp: str
    environment: dict
    results: List[TestResult]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_modules': self.total_modules,
            'passed': self.passed,
            'failed': self.failed,
            'errors': self.errors,
            'total_duration': round(self.total_duration, 2),
            'timestamp': self.timestamp,
            'environment': self.environment,
            'results': [r.to_dict() for r in self.results]
        }


class ResultCollector:
    """Collects test results and generates reports"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()

    def add_result(self, result: TestResult):
        """Add a test result to the collection"""
        self.results.append(result)
        logger.info(f"Module {result.module}: {result.status} ({result.duration:.2f}s)")

    def get_summary(self) -> TestSummary:
        """Generate summary of all test results"""
        total_duration = time.time() - self.start_time

        passed = sum(1 for r in self.results if r.status == 'passed')
        failed = sum(1 for r in self.results if r.status == 'failed')
        errors = sum(1 for r in self.results if r.status == 'error')

        environment = {
            'fess_url': os.environ.get('FESS_URL', 'unknown'),
            'browser_locale': os.environ.get('BROWSER_LOCALE', 'unknown'),
            'headless': os.environ.get('HEADLESS', 'unknown'),
            'test_label': os.environ.get('TEST_LABEL', 'unknown')
        }

        return TestSummary(
            total_modules=len(self.results),
            passed=passed,
            failed=failed,
            errors=errors,
            total_duration=total_duration,
            timestamp=datetime.now().isoformat(),
            environment=environment,
            results=self.results
        )

    def save_json(self, filename: str = 'test_results.json'):
        """Save test results to JSON file"""
        summary = self.get_summary()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Test results saved to {filename}")

    def print_summary(self):
        """Print human-readable summary to console"""
        summary = self.get_summary()

        print("\n" + "="*70)
        print("TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"Total Modules: {summary.total_modules}")
        print(f"Passed:        {summary.passed} ✓")
        print(f"Failed:        {summary.failed} ✗")
        print(f"Errors:        {summary.errors} ⚠")
        print(f"Duration:      {summary.total_duration:.2f}s")
        print(f"Timestamp:     {summary.timestamp}")
        print("="*70)

        if summary.failed > 0 or summary.errors > 0:
            print("\nFAILED/ERROR MODULES:")
            for result in summary.results:
                if result.status in ['failed', 'error']:
                    print(f"  - {result.module}: {result.status}")
                    if result.error_message:
                        # Print first line of error message
                        first_line = result.error_message.split('\n')[0]
                        print(f"    {first_line[:80]}")
                    if result.screenshot_path:
                        print(f"    Screenshot: {result.screenshot_path}")
            print("="*70)

        print("\nDETAILED RESULTS:")
        for result in summary.results:
            status_icon = "✓" if result.status == "passed" else ("✗" if result.status == "failed" else "⚠")
            print(f"  {status_icon} {result.module:<20} {result.duration:>6.2f}s  {result.status}")

        print("="*70 + "\n")
