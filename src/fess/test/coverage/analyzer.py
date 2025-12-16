"""
DOM Analysis Engine for Coverage Analysis.

Parses HTML files and extracts interactive elements for coverage tracking.
"""

import logging
import os
import json
import re
import hashlib
from typing import List, Optional, Dict, Tuple
from urllib.parse import urlparse

from .models import DOMElement, FormInventory, PageInventory

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """
    Analyzes HTML files to extract interactive DOM elements.

    Uses BeautifulSoup to parse HTML and identify forms, inputs,
    buttons, links, and other interactive elements.
    """

    # CSS selectors for different element categories
    ELEMENT_SELECTORS = {
        "forms": "form",
        "inputs": "input, textarea, select",
        "buttons": "button, input[type='submit'], input[type='button']",
        "links": "a[href]",
        "tables": "table",
    }

    # Element types that are interactive
    INTERACTIVE_TYPES = {
        "input", "textarea", "select", "button", "a"
    }

    # Input types that are not typically tested
    SKIP_INPUT_TYPES = {"hidden"}

    def __init__(self):
        """Initialize the coverage analyzer."""
        self._bs4_available = self._check_bs4()

    def _check_bs4(self) -> bool:
        """Check if BeautifulSoup is available."""
        try:
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            logger.warning(
                "[COVERAGE] BeautifulSoup not installed. "
                "Install with: pip install beautifulsoup4"
            )
            return False

    def analyze_html(self, html_path: str) -> Optional[PageInventory]:
        """
        Analyze an HTML file and extract interactive elements.

        Args:
            html_path: Path to the HTML file

        Returns:
            PageInventory containing all discovered elements, or None if failed
        """
        if not self._bs4_available:
            logger.error("[COVERAGE] Cannot analyze HTML without BeautifulSoup")
            return None

        if not os.path.exists(html_path):
            logger.error(f"[COVERAGE] HTML file not found: {html_path}")
            return None

        try:
            from bs4 import BeautifulSoup

            # Read HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Load metadata if available
            metadata = self._load_metadata(html_path)
            url = metadata.get("url", "")
            url_path = metadata.get("url_path", "")
            page_title = metadata.get("page_title", "") or self._extract_title(soup)

            # Extract elements
            elements = self._extract_elements(soup, url)
            forms = self._extract_forms(soup, url)
            nav_links = self._extract_navigation_links(soup)

            inventory = PageInventory(
                url=url,
                url_path=url_path,
                page_title=page_title,
                elements=elements,
                forms=forms,
                navigation_links=nav_links,
                html_snapshot_path=html_path,
            )

            logger.debug(
                f"[COVERAGE] Analyzed {html_path}: "
                f"{len(elements)} elements, {len(forms)} forms"
            )

            return inventory

        except Exception as e:
            logger.error(f"[COVERAGE] Failed to analyze HTML: {e}")
            return None

    def analyze_directory(self, dir_path: str) -> List[PageInventory]:
        """
        Analyze all HTML files in a directory.

        Args:
            dir_path: Path to directory containing HTML files

        Returns:
            List of PageInventory objects
        """
        inventories = []

        if not os.path.isdir(dir_path):
            logger.error(f"[COVERAGE] Directory not found: {dir_path}")
            return inventories

        for root, _, files in os.walk(dir_path):
            for filename in files:
                if filename.endswith('.html'):
                    html_path = os.path.join(root, filename)
                    inventory = self.analyze_html(html_path)
                    if inventory:
                        inventories.append(inventory)

        logger.info(f"[COVERAGE] Analyzed {len(inventories)} HTML files from {dir_path}")
        return inventories

    def _load_metadata(self, html_path: str) -> dict:
        """Load metadata JSON file if it exists."""
        metadata_path = html_path.replace('.html', '.json')
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _extract_title(self, soup) -> str:
        """Extract page title from HTML."""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _extract_elements(self, soup, page_url: str) -> List[DOMElement]:
        """Extract all interactive elements from HTML."""
        elements = []

        # Extract inputs, textareas, selects
        for tag_name in ['input', 'textarea', 'select']:
            for element in soup.find_all(tag_name):
                dom_element = self._parse_element(element, page_url)
                if dom_element and self._should_include_element(dom_element):
                    elements.append(dom_element)

        # Extract buttons
        for button in soup.find_all('button'):
            dom_element = self._parse_element(button, page_url)
            if dom_element:
                elements.append(dom_element)

        # Extract submit inputs
        for submit in soup.find_all('input', {'type': ['submit', 'button']}):
            dom_element = self._parse_element(submit, page_url)
            if dom_element:
                elements.append(dom_element)

        # Extract links with meaningful hrefs
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                dom_element = self._parse_element(link, page_url)
                if dom_element:
                    elements.append(dom_element)

        return elements

    def _parse_element(self, element, page_url: str) -> Optional[DOMElement]:
        """Parse a BeautifulSoup element into a DOMElement."""
        tag_name = element.name

        # Get identifier
        identifier = (
            element.get('id') or
            element.get('name') or
            self._generate_identifier(element)
        )

        # Build selector
        selector = self._build_selector(element)

        # Get text content
        text_content = self._get_text_content(element)

        # Get relevant attributes
        attributes = self._get_relevant_attributes(element)

        # Determine element type
        element_type = self._determine_element_type(element)

        # Check if interactive
        is_interactive = self._is_interactive(element)

        # Get parent form ID
        parent_form = element.find_parent('form')
        parent_form_id = parent_form.get('id') if parent_form else None

        return DOMElement(
            element_type=element_type,
            selector=selector,
            identifier=identifier,
            text_content=text_content[:100] if text_content else "",
            attributes=attributes,
            page_url=page_url,
            is_interactive=is_interactive,
            parent_form_id=parent_form_id,
        )

    def _build_selector(self, element) -> str:
        """Build a CSS selector for an element."""
        tag_name = element.name

        # Prefer ID selector
        if element.get('id'):
            return f"#{element['id']}"

        # Use name attribute for form fields
        if element.get('name'):
            return f"{tag_name}[name=\"{element['name']}\"]"

        # Use type for inputs
        if tag_name == 'input' and element.get('type'):
            input_type = element['type']
            if element.get('placeholder'):
                return f"input[type=\"{input_type}\"][placeholder=\"{element['placeholder']}\"]"
            return f"input[type=\"{input_type}\"]"

        # Use text content for buttons
        if tag_name == 'button':
            text = element.get_text(strip=True)
            if text:
                return f"button:has-text(\"{text[:30]}\")"

        # Use href for links
        if tag_name == 'a' and element.get('href'):
            href = element['href']
            return f"a[href=\"{href}\"]"

        # Fallback to tag name
        return tag_name

    def _get_text_content(self, element) -> str:
        """Get visible text content of an element."""
        if element.name in ['input', 'textarea']:
            return element.get('placeholder', '') or element.get('value', '')
        return element.get_text(strip=True)

    def _get_relevant_attributes(self, element) -> Dict[str, str]:
        """Get relevant HTML attributes."""
        relevant_attrs = [
            'id', 'name', 'type', 'placeholder', 'required',
            'pattern', 'maxlength', 'minlength', 'href', 'action',
            'method', 'class', 'disabled', 'readonly'
        ]

        attributes = {}
        for attr in relevant_attrs:
            value = element.get(attr)
            if value:
                if isinstance(value, list):
                    value = ' '.join(value)
                attributes[attr] = str(value)

        return attributes

    def _determine_element_type(self, element) -> str:
        """Determine the type of element."""
        tag_name = element.name

        if tag_name == 'input':
            input_type = element.get('type', 'text')
            return f"input[{input_type}]"
        elif tag_name == 'select':
            return 'select'
        elif tag_name == 'textarea':
            return 'textarea'
        elif tag_name == 'button':
            return 'button'
        elif tag_name == 'a':
            return 'link'

        return tag_name

    def _is_interactive(self, element) -> bool:
        """Check if an element is interactive."""
        if element.get('disabled'):
            return False
        if element.get('readonly') and element.name in ['input', 'textarea']:
            return False
        return element.name in self.INTERACTIVE_TYPES

    def _should_include_element(self, element: DOMElement) -> bool:
        """Check if element should be included in inventory."""
        # Skip hidden inputs
        if element.element_type == 'input[hidden]':
            return False

        # Skip CSRF tokens and similar
        identifier_lower = element.identifier.lower()
        skip_patterns = ['csrf', 'token', '_method', '__']
        if any(pattern in identifier_lower for pattern in skip_patterns):
            return False

        return True

    def _generate_identifier(self, element) -> str:
        """Generate a unique identifier for an element."""
        tag_name = element.name
        attrs = str(element.attrs)
        text = element.get_text(strip=True)[:20]
        combined = f"{tag_name}:{attrs}:{text}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]

    def _extract_forms(self, soup, page_url: str) -> List[FormInventory]:
        """Extract all forms from HTML."""
        forms = []

        for form in soup.find_all('form'):
            form_id = form.get('id') or self._generate_identifier(form)
            form_selector = f"#{form['id']}" if form.get('id') else "form"

            # Get form fields
            fields = []
            for tag_name in ['input', 'textarea', 'select']:
                for element in form.find_all(tag_name):
                    dom_element = self._parse_element(element, page_url)
                    if dom_element and self._should_include_element(dom_element):
                        fields.append(dom_element)

            # Get submit buttons
            submit_buttons = []
            for button in form.find_all(['button', 'input']):
                if button.name == 'button' or button.get('type') in ['submit', 'button']:
                    dom_element = self._parse_element(button, page_url)
                    if dom_element:
                        submit_buttons.append(dom_element)

            form_inventory = FormInventory(
                form_id=form_id,
                form_selector=form_selector,
                action=form.get('action', ''),
                method=form.get('method', 'POST').upper(),
                fields=fields,
                submit_buttons=submit_buttons,
                page_url=page_url,
            )
            forms.append(form_inventory)

        return forms

    def _extract_navigation_links(self, soup) -> List[str]:
        """Extract navigation links."""
        nav_links = []

        # Look for nav elements and sidebar links
        nav_elements = soup.find_all(['nav', 'aside'])
        for nav in nav_elements:
            for link in nav.find_all('a', href=True):
                href = link['href']
                if href and not href.startswith('#') and not href.startswith('javascript:'):
                    nav_links.append(href)

        # Also look for links in common navigation classes
        nav_classes = ['nav', 'sidebar', 'menu', 'navigation']
        for nav_class in nav_classes:
            for element in soup.find_all(class_=re.compile(nav_class, re.I)):
                for link in element.find_all('a', href=True):
                    href = link['href']
                    if href not in nav_links and not href.startswith('#'):
                        nav_links.append(href)

        return list(set(nav_links))  # Remove duplicates

    def compare_with_test_logs(self, inventory: PageInventory,
                               test_log_content: str) -> Dict[str, bool]:
        """
        Compare page inventory with test logs to identify tested elements.

        Args:
            inventory: PageInventory to check
            test_log_content: Content of test logs to search

        Returns:
            Dictionary mapping element identifiers to tested status
        """
        tested_elements = {}

        for element in inventory.elements:
            # Check if element's selector appears in logs
            selector = element.selector
            identifier = element.identifier

            is_tested = (
                selector in test_log_content or
                identifier in test_log_content or
                (element.attributes.get('name') and
                 element.attributes['name'] in test_log_content)
            )

            tested_elements[element.identifier] = is_tested

        return tested_elements
