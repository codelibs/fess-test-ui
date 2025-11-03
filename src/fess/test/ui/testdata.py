"""
Test data management utilities for Fess UI tests.

This module provides reusable test data patterns and builders
to ensure consistent and comprehensive test coverage.
"""

import logging

logger = logging.getLogger(__name__)


class TestDataBuilder:
    """Builder class for creating common test data patterns"""

    @staticmethod
    def create_webconfig_data(name: str) -> dict:
        """
        Create standard web crawl configuration test data

        Args:
            name: The name for the web config

        Returns:
            Dictionary containing all required fields for web config
        """
        return {
            "name": name,
            "urls": "https://example.com/",
            "includedUrls": "https://example.com/.*",
            "excludedUrls": "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico)",
            "maxAccessCount": "30",
            "numOfThread": "2",
            "description": f"Test web config for {name}"
        }

    @staticmethod
    def create_label_data(name: str, sort_order: int = 1) -> dict:
        """
        Create standard label test data

        Args:
            name: The name for the label
            sort_order: Sort order value (default: 1)

        Returns:
            Dictionary containing all required fields for label
        """
        return {
            "name": name,
            "value": name.lower(),
            "includedPaths": "https://example.com/.*",
            "sortOrder": str(sort_order)
        }

    @staticmethod
    def create_user_data(name: str, password: str = "testpassword123") -> dict:
        """
        Create standard user test data

        Args:
            name: The username
            password: The password (default: testpassword123)

        Returns:
            Dictionary containing all required fields for user
        """
        return {
            "name": name,
            "password": password,
            "confirmPassword": password
        }


class ValidationPatterns:
    """Common validation patterns for testing input validation"""

    # XSS attack patterns
    XSS_PATTERNS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg/onload=alert('xss')>"
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        "' OR '1'='1",
        "1' AND '1'='1",
        "'; DROP TABLE users--",
        "1 UNION SELECT NULL--"
    ]

    # Special characters that should be handled
    SPECIAL_CHARS = [
        "!@#$%^&*()",
        "\\n\\r\\t",
        "ä

ö文字",  # Unicode
        "test<>\"'&",
    ]

    # Invalid URL patterns
    INVALID_URLS = [
        "not-a-url",
        "ftp://invalid",
        "javascript:void(0)",
        "file:///etc/passwd"
    ]

    # Boundary values
    EMPTY_STRING = ""
    VERY_LONG_STRING_300 = "x" * 300
    VERY_LONG_STRING_1000 = "x" * 1000

    @staticmethod
    def get_xss_test_string(base_name: str) -> str:
        """
        Get a test string with XSS pattern embedded

        Args:
            base_name: Base name to append XSS pattern to

        Returns:
            String with XSS pattern
        """
        return f"{base_name}<script>alert('xss')</script>"

    @staticmethod
    def get_sql_injection_test_string(base_name: str) -> str:
        """
        Get a test string with SQL injection pattern embedded

        Args:
            base_name: Base name to append SQL injection pattern to

        Returns:
            String with SQL injection pattern
        """
        return f"{base_name}' OR '1'='1"


class TestScenarios:
    """Pre-defined test scenarios for integration testing"""

    @staticmethod
    def get_basic_crawler_scenario(context) -> dict:
        """
        Get a basic crawler test scenario with all required components

        Args:
            context: FessContext instance

        Returns:
            Dictionary with crawler scenario data
        """
        base_name = context.create_label_name()
        return {
            "webconfig": TestDataBuilder.create_webconfig_data(f"Crawler_{base_name}"),
            "label": TestDataBuilder.create_label_data(f"Label_{base_name}"),
            "job_name": f"Job_{base_name}",
            "cron_expression": "0 0 * * *"  # Daily at midnight
        }

    @staticmethod
    def get_user_permission_scenario(context) -> dict:
        """
        Get a user permission test scenario with user, group, and role

        Args:
            context: FessContext instance

        Returns:
            Dictionary with user permission scenario data
        """
        base_name = context.create_label_name()
        return {
            "role_name": f"Role_{base_name}",
            "group_name": f"Group_{base_name}",
            "user": TestDataBuilder.create_user_data(f"User_{base_name}")
        }
