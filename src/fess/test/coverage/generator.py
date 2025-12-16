"""
Test Stub Generator.

Generates test code stubs from coverage analysis to help improve test coverage.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from .models import DOMElement, FormInventory, PageInventory, CoverageGap

logger = logging.getLogger(__name__)


class TestStubGenerator:
    """
    Generates test code stubs from HTML analysis.

    Creates Python test function stubs that can be used as starting
    points for implementing new tests.
    """

    # Template for test file header
    FILE_HEADER_TEMPLATE = '''"""
Auto-generated test stubs for {page_title}.

Source: {source_url}
Generated: {generated_at}

These stubs provide starting points for test implementation.
Review and modify as needed before use.
"""

from fess.test.ui import FessContext
from fess.test import assert_equal, assert_true


'''

    # Template for form test function
    FORM_TEST_TEMPLATE = '''def test_{form_name}_form(context: FessContext) -> None:
    """
    Test form: {form_description}

    Form action: {form_action}
    Method: {form_method}
    """
    page = context.get_admin_page()
    page.goto(context.url("{page_path}"))

{field_tests}
{submit_test}
'''

    # Template for navigation test function
    NAV_TEST_TEMPLATE = '''def test_navigation_{nav_name}(context: FessContext) -> None:
    """
    Test navigation to: {nav_description}
    """
    page = context.get_admin_page()
    page.goto(context.url("{start_path}"))

    # Click navigation link
    page.click("{link_selector}")

    # Verify navigation
    # TODO: Add assertion for expected page
    # assert_true("{expected_path}" in page.url)

'''

    # Template for validation test function
    VALIDATION_TEST_TEMPLATE = '''def test_{field_name}_validation(context: FessContext) -> None:
    """
    Test validation for field: {field_description}

    Element: {element_type}
    Selector: {selector}
    """
    page = context.get_admin_page()
    page.goto(context.url("{page_path}"))

    # Test empty value
    page.fill("{selector}", "")
    # TODO: Add assertion for validation error

    # Test invalid value
    # page.fill("{selector}", "invalid_value")
    # TODO: Add assertion for validation error

    # Test valid value
    page.fill("{selector}", "{valid_value}")
    # TODO: Verify no validation error

'''

    def __init__(self, output_dir: str = "generated_tests"):
        """
        Initialize test stub generator.

        Args:
            output_dir: Directory for generated test files
        """
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_from_inventory(
        self,
        inventory: PageInventory,
        filename: str = None
    ) -> str:
        """
        Generate test stubs from a page inventory.

        Args:
            inventory: PageInventory to generate tests from
            filename: Output filename (without extension)

        Returns:
            Path to generated file
        """
        if filename is None:
            # Generate filename from URL path
            path = urlparse(inventory.url).path
            safe_name = path.replace('/', '_').strip('_') or "index"
            filename = f"test_{safe_name}"

        # Generate file content
        content = self._generate_file_header(inventory)

        # Generate form tests
        for form in inventory.forms:
            content += self._generate_form_test(form, inventory.url)
            content += "\n"

        # Generate navigation tests
        nav_links = inventory.navigation_links[:10]  # Limit to 10
        if nav_links:
            content += self._generate_navigation_tests(nav_links, inventory.url)

        # Generate field validation tests
        for element in inventory.elements:
            if element.element_type.startswith('input[') and element.is_interactive:
                if element.attributes.get('required'):
                    content += self._generate_validation_test(element, inventory.url)
                    content += "\n"

        output_path = os.path.join(self._output_dir, f"{filename}.py")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"[GENERATOR] Generated test stubs: {output_path}")
        return output_path

    def generate_from_gaps(
        self,
        gaps: List[CoverageGap],
        filename: str = "test_coverage_gaps"
    ) -> str:
        """
        Generate test stubs from coverage gaps.

        Args:
            gaps: List of coverage gaps to generate tests for
            filename: Output filename (without extension)

        Returns:
            Path to generated file
        """
        content = f'''"""
Auto-generated test stubs for coverage gaps.

Generated: {datetime.now().isoformat()}

These tests address the highest priority untested elements.
"""

from fess.test.ui import FessContext
from fess.test import assert_equal, assert_true


'''

        # Group gaps by page
        gaps_by_page = {}
        for gap in gaps:
            page_url = gap.page_url
            if page_url not in gaps_by_page:
                gaps_by_page[page_url] = []
            gaps_by_page[page_url].append(gap)

        # Generate tests for each page's gaps
        for page_url, page_gaps in gaps_by_page.items():
            content += f"# Tests for page: {page_url}\n\n"
            for i, gap in enumerate(page_gaps[:5], 1):  # Limit to 5 per page
                content += self._generate_gap_test(gap, i)
                content += "\n"

        output_path = os.path.join(self._output_dir, f"{filename}.py")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"[GENERATOR] Generated gap tests: {output_path}")
        return output_path

    def _generate_file_header(self, inventory: PageInventory) -> str:
        """Generate file header from inventory."""
        return self.FILE_HEADER_TEMPLATE.format(
            page_title=inventory.page_title or "Unknown Page",
            source_url=inventory.url,
            generated_at=datetime.now().isoformat(),
        )

    def _generate_form_test(self, form: FormInventory, page_url: str) -> str:
        """Generate test stub for a form."""
        # Extract path from URL
        page_path = urlparse(page_url).path

        # Generate safe function name
        form_name = self._safe_name(form.form_id)

        # Generate field tests
        field_tests = []
        for field in form.fields:
            field_test = self._generate_field_fill(field)
            if field_test:
                field_tests.append(field_test)

        # Generate submit test
        submit_test = ""
        if form.submit_buttons:
            button = form.submit_buttons[0]
            submit_test = f'    # Submit form\n    page.click("{button.selector}")\n'
            submit_test += '    # TODO: Add assertion for expected result\n'

        return self.FORM_TEST_TEMPLATE.format(
            form_name=form_name,
            form_description=f"Form {form.form_id}",
            form_action=form.action,
            form_method=form.method,
            page_path=page_path,
            field_tests="\n".join(field_tests) if field_tests else "    # No form fields found\n    pass\n",
            submit_test=submit_test,
        )

    def _generate_field_fill(self, element: DOMElement) -> Optional[str]:
        """Generate fill statement for a form field."""
        if not element.is_interactive:
            return None

        elem_type = element.element_type
        selector = element.selector
        placeholder = element.text_content or element.attributes.get('placeholder', '')

        # Determine test value based on element type
        test_value = self._get_test_value(element)

        if elem_type == 'select':
            return f'    # Select option for {element.identifier}\n    # page.select_option("{selector}", value="option_value")\n'
        elif elem_type == 'textarea':
            return f'    # Fill textarea: {placeholder[:30]}\n    page.fill("{selector}", "{test_value}")\n'
        elif elem_type.startswith('input[checkbox]'):
            return f'    # Check/uncheck: {element.identifier}\n    # page.check("{selector}")  # or page.uncheck()\n'
        elif elem_type.startswith('input[radio]'):
            return f'    # Select radio: {element.identifier}\n    # page.click("{selector}")\n'
        elif elem_type.startswith('input['):
            required = " (required)" if element.attributes.get('required') else ""
            return f'    # Fill {elem_type}{required}: {placeholder[:30]}\n    page.fill("{selector}", "{test_value}")\n'

        return None

    def _get_test_value(self, element: DOMElement) -> str:
        """Get appropriate test value for an element."""
        elem_type = element.element_type
        identifier = element.identifier.lower()

        if 'password' in identifier:
            return "test_password123"
        elif 'email' in identifier:
            return "test@example.com"
        elif 'url' in identifier or 'http' in identifier:
            return "https://example.com"
        elif 'phone' in identifier or 'tel' in identifier:
            return "0312345678"
        elif 'name' in identifier:
            return "test_name"
        elif elem_type == 'input[number]':
            return "100"
        elif elem_type == 'textarea':
            return "Test content for textarea field."
        else:
            return "test_value"

    def _generate_navigation_tests(
        self,
        nav_links: List[str],
        page_url: str
    ) -> str:
        """Generate navigation test stubs."""
        start_path = urlparse(page_url).path
        content = "# Navigation tests\n\n"

        for i, link in enumerate(nav_links, 1):
            nav_name = f"link_{i}"
            link_path = link if link.startswith('/') else f"/{link}"

            test = self.NAV_TEST_TEMPLATE.format(
                nav_name=nav_name,
                nav_description=link,
                start_path=start_path,
                link_selector=f'a[href="{link}"]',
                expected_path=link_path,
            )
            content += test

        return content

    def _generate_validation_test(
        self,
        element: DOMElement,
        page_url: str
    ) -> str:
        """Generate validation test stub for a field."""
        page_path = urlparse(page_url).path
        field_name = self._safe_name(element.identifier)
        valid_value = self._get_test_value(element)

        return self.VALIDATION_TEST_TEMPLATE.format(
            field_name=field_name,
            field_description=element.text_content[:50] or element.identifier,
            element_type=element.element_type,
            selector=element.selector,
            page_path=page_path,
            valid_value=valid_value,
        )

    def _generate_gap_test(self, gap: CoverageGap, index: int) -> str:
        """Generate test stub from a coverage gap."""
        page_path = urlparse(gap.page_url).path
        element = gap.element
        safe_name = self._safe_name(element.identifier)

        content = f'''def test_gap_{index}_{safe_name}(context: FessContext) -> None:
    """
    Test for coverage gap: {element.element_type}

    Priority: {gap.priority:.2f}
    Reason: {gap.priority_reason}
    Selector: {element.selector}
    """
    page = context.get_admin_page()
    page.goto(context.url("{page_path}"))

'''

        # Add suggested test actions
        for suggestion in gap.suggested_tests[:2]:
            # Convert suggestion to code comment
            content += f"    # {suggestion}\n"

        content += "    pass  # TODO: Implement test\n\n"

        return content

    def _safe_name(self, name: str) -> str:
        """Convert string to safe Python identifier."""
        # Replace non-alphanumeric characters with underscore
        safe = ''.join(c if c.isalnum() else '_' for c in name)
        # Remove consecutive underscores
        while '__' in safe:
            safe = safe.replace('__', '_')
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        # Ensure it doesn't start with a number
        if safe and safe[0].isdigit():
            safe = 'field_' + safe
        return safe[:50] or "unnamed"

    def generate_summary_report(
        self,
        generated_files: List[str]
    ) -> str:
        """
        Generate summary report of generated test stubs.

        Args:
            generated_files: List of generated file paths

        Returns:
            Summary report string
        """
        report = f"""
Test Stub Generation Summary
============================
Generated: {datetime.now().isoformat()}
Output directory: {self._output_dir}

Generated files:
"""
        for filepath in generated_files:
            report += f"  - {filepath}\n"

        report += f"""
Total files generated: {len(generated_files)}

Next steps:
1. Review generated test stubs
2. Modify test values and assertions as needed
3. Remove or update TODO comments
4. Run tests to verify implementation
"""
        return report
