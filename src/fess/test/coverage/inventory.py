"""
Element Inventory Manager for Coverage Analysis.

Manages the inventory of discovered elements and tracks coverage status.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Set

from .models import (
    DOMElement, PageInventory, PageCoverage, ElementCoverage, CoverageGap
)

logger = logging.getLogger(__name__)


class InventoryManager:
    """
    Manages element inventory and coverage tracking.

    Stores discovered elements, tracks which have been tested,
    and calculates coverage metrics.
    """

    # Priority weights for different element types
    ELEMENT_PRIORITY = {
        "input[password]": 0.95,
        "input[email]": 0.9,
        "button": 0.9,
        "input[submit]": 0.9,
        "select": 0.85,
        "textarea": 0.8,
        "input[text]": 0.8,
        "input[number]": 0.75,
        "input[checkbox]": 0.7,
        "input[radio]": 0.7,
        "link": 0.6,
        "input[file]": 0.5,
    }

    DEFAULT_PRIORITY = 0.5

    def __init__(self, storage_dir: str = "coverage_data"):
        """
        Initialize inventory manager.

        Args:
            storage_dir: Directory for storing inventory data
        """
        self._storage_dir = storage_dir
        self._inventories: Dict[str, PageInventory] = {}  # url_path -> inventory
        self._tested_selectors: Set[str] = set()
        self._test_module_map: Dict[str, List[str]] = {}  # selector -> modules

    def add_inventory(self, inventory: PageInventory) -> None:
        """
        Add a page inventory to the manager.

        Args:
            inventory: PageInventory to add
        """
        key = inventory.url_path or inventory.url
        if key in self._inventories:
            # Merge with existing inventory
            self._merge_inventory(key, inventory)
        else:
            self._inventories[key] = inventory

        logger.debug(f"[INVENTORY] Added inventory for: {key}")

    def _merge_inventory(self, key: str, new_inventory: PageInventory) -> None:
        """Merge new inventory with existing one."""
        existing = self._inventories[key]

        # Merge elements (avoid duplicates by identifier)
        existing_ids = {e.identifier for e in existing.elements}
        for element in new_inventory.elements:
            if element.identifier not in existing_ids:
                existing.elements.append(element)
                existing_ids.add(element.identifier)

        # Merge forms
        existing_form_ids = {f.form_id for f in existing.forms}
        for form in new_inventory.forms:
            if form.form_id not in existing_form_ids:
                existing.forms.append(form)

        # Merge navigation links
        existing.navigation_links = list(set(
            existing.navigation_links + new_inventory.navigation_links
        ))

    def mark_as_tested(self, selector: str, module_name: str = None) -> None:
        """
        Mark an element as tested.

        Args:
            selector: CSS selector of the tested element
            module_name: Name of the test module
        """
        self._tested_selectors.add(selector)

        if module_name:
            if selector not in self._test_module_map:
                self._test_module_map[selector] = []
            if module_name not in self._test_module_map[selector]:
                self._test_module_map[selector].append(module_name)

    def import_test_logs(self, log_content: str, module_name: str = None) -> int:
        """
        Import test logs to identify tested elements.

        Args:
            log_content: Content of test logs
            module_name: Name of the test module

        Returns:
            Number of elements identified as tested
        """
        count = 0

        # Parse log entries for selectors
        # Look for patterns like [CLICK] selector='...', [FILL] selector='...'
        import re

        selector_pattern = r"\[(CLICK|FILL|SELECT_OPTION)\]\s+selector='([^']+)'"
        matches = re.findall(selector_pattern, log_content)

        for action, selector in matches:
            self.mark_as_tested(selector, module_name)
            count += 1

        logger.info(f"[INVENTORY] Imported {count} tested selectors from logs")
        return count

    def calculate_coverage(self, url_path: str = None) -> Optional[PageCoverage]:
        """
        Calculate coverage for a specific page or all pages.

        Args:
            url_path: Specific page URL path, or None for overall

        Returns:
            PageCoverage object or None if no data
        """
        if url_path:
            inventory = self._inventories.get(url_path)
            if not inventory:
                return None
            return self._calculate_page_coverage(inventory)

        # Calculate overall coverage
        all_elements = []
        for inv in self._inventories.values():
            all_elements.extend(inv.elements)

        if not all_elements:
            return PageCoverage(
                url="(all pages)",
                total_elements=0,
                tested_elements=0,
                coverage_percentage=0.0,
            )

        return self._calculate_elements_coverage(all_elements, "(all pages)")

    def _calculate_page_coverage(self, inventory: PageInventory) -> PageCoverage:
        """Calculate coverage for a single page inventory."""
        return self._calculate_elements_coverage(
            inventory.elements,
            inventory.url,
            inventory.url_path,
            inventory.page_title
        )

    def _calculate_elements_coverage(
        self,
        elements: List[DOMElement],
        url: str,
        url_path: str = "",
        page_title: str = ""
    ) -> PageCoverage:
        """Calculate coverage for a list of elements."""
        interactive_elements = [e for e in elements if e.is_interactive]
        total = len(interactive_elements)

        if total == 0:
            return PageCoverage(
                url=url,
                url_path=url_path,
                page_title=page_title,
                total_elements=0,
                tested_elements=0,
                coverage_percentage=100.0,  # No elements = 100% coverage
            )

        element_coverages = []
        untested_elements = []
        tested_count = 0

        for element in interactive_elements:
            is_tested = self._is_element_tested(element)
            modules = self._get_test_modules(element)

            coverage = ElementCoverage(
                element=element,
                tested=is_tested,
                test_modules=modules,
                coverage_score=1.0 if is_tested else 0.0,
            )
            element_coverages.append(coverage)

            if is_tested:
                tested_count += 1
            else:
                untested_elements.append(element)

        coverage_percentage = (tested_count / total) * 100 if total > 0 else 0.0

        return PageCoverage(
            url=url,
            url_path=url_path,
            page_title=page_title,
            total_elements=total,
            tested_elements=tested_count,
            coverage_percentage=round(coverage_percentage, 1),
            element_coverages=element_coverages,
            untested_elements=untested_elements,
        )

    def _is_element_tested(self, element: DOMElement) -> bool:
        """Check if an element has been tested."""
        # Check by selector
        if element.selector in self._tested_selectors:
            return True

        # Check by name attribute
        name = element.attributes.get('name')
        if name:
            # Check various selector formats
            name_selectors = [
                f"[name=\"{name}\"]",
                f"input[name=\"{name}\"]",
                f"select[name=\"{name}\"]",
                f"textarea[name=\"{name}\"]",
            ]
            for sel in name_selectors:
                if sel in self._tested_selectors:
                    return True

        # Check by ID
        elem_id = element.attributes.get('id')
        if elem_id and f"#{elem_id}" in self._tested_selectors:
            return True

        return False

    def _get_test_modules(self, element: DOMElement) -> List[str]:
        """Get list of test modules that tested this element."""
        modules = set()

        for selector, mods in self._test_module_map.items():
            if selector == element.selector:
                modules.update(mods)
            elif element.attributes.get('name') and element.attributes['name'] in selector:
                modules.update(mods)

        return list(modules)

    def identify_gaps(self, min_priority: float = 0.5) -> List[CoverageGap]:
        """
        Identify coverage gaps (untested elements) sorted by priority.

        Args:
            min_priority: Minimum priority threshold (0.0 to 1.0)

        Returns:
            List of CoverageGap objects sorted by priority (highest first)
        """
        gaps = []

        for url_path, inventory in self._inventories.items():
            for element in inventory.elements:
                if not element.is_interactive:
                    continue

                if self._is_element_tested(element):
                    continue

                priority = self._calculate_priority(element)
                if priority < min_priority:
                    continue

                gap = CoverageGap(
                    element=element,
                    page_url=inventory.url,
                    priority=priority,
                    priority_reason=self._get_priority_reason(element),
                    suggested_tests=self._suggest_tests(element),
                )
                gaps.append(gap)

        # Sort by priority (highest first)
        gaps.sort(key=lambda g: g.priority, reverse=True)

        return gaps

    def _calculate_priority(self, element: DOMElement) -> float:
        """Calculate priority score for an element."""
        base_priority = self.ELEMENT_PRIORITY.get(
            element.element_type, self.DEFAULT_PRIORITY
        )

        # Boost priority for required fields
        if element.attributes.get('required'):
            base_priority = min(base_priority + 0.1, 1.0)

        # Boost priority for password/email fields
        if any(p in element.identifier.lower() for p in ['password', 'email', 'login']):
            base_priority = min(base_priority + 0.1, 1.0)

        return round(base_priority, 2)

    def _get_priority_reason(self, element: DOMElement) -> str:
        """Get human-readable reason for priority."""
        reasons = []

        if element.attributes.get('required'):
            reasons.append("Required field")

        if 'password' in element.element_type:
            reasons.append("Security-sensitive input")

        if element.element_type in ['button', 'input[submit]']:
            reasons.append("Form submission action")

        if 'email' in element.identifier.lower():
            reasons.append("User identity field")

        if not reasons:
            reasons.append(f"Standard {element.element_type} element")

        return "; ".join(reasons)

    def _suggest_tests(self, element: DOMElement) -> List[str]:
        """Suggest test actions for an element."""
        suggestions = []
        elem_type = element.element_type

        if elem_type.startswith('input['):
            suggestions.append(f"Fill with valid value: page.fill(\"{element.selector}\", \"test_value\")")
            suggestions.append("Test with empty value (validation)")
            if elem_type in ['input[text]', 'input[email]', 'input[password]']:
                suggestions.append("Test with maximum length value")
                suggestions.append("Test with special characters")

        elif elem_type == 'select':
            suggestions.append(f"Select each option: page.select_option(\"{element.selector}\", value)")
            suggestions.append("Verify all options are selectable")

        elif elem_type == 'textarea':
            suggestions.append(f"Fill with text: page.fill(\"{element.selector}\", \"test_text\")")
            suggestions.append("Test with multi-line content")

        elif elem_type == 'button':
            suggestions.append(f"Click button: page.click(\"{element.selector}\")")
            suggestions.append("Verify expected action occurs")

        elif elem_type == 'link':
            suggestions.append(f"Click link: page.click(\"{element.selector}\")")
            suggestions.append("Verify navigation to correct page")

        return suggestions

    def save_inventory(self, path: str = None) -> str:
        """
        Save inventory data to JSON file.

        Args:
            path: Output path (default: {storage_dir}/inventory.json)

        Returns:
            Path to saved file
        """
        if path is None:
            os.makedirs(self._storage_dir, exist_ok=True)
            path = os.path.join(self._storage_dir, "inventory.json")

        data = {
            "generated_at": datetime.now().isoformat(),
            "pages": {k: v.to_dict() for k, v in self._inventories.items()},
            "tested_selectors": list(self._tested_selectors),
            "test_module_map": self._test_module_map,
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[INVENTORY] Saved inventory to: {path}")
        return path

    def load_inventory(self, path: str) -> bool:
        """
        Load inventory data from JSON file.

        Args:
            path: Path to inventory JSON file

        Returns:
            True if loaded successfully
        """
        if not os.path.exists(path):
            logger.warning(f"[INVENTORY] File not found: {path}")
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for url_path, page_data in data.get("pages", {}).items():
                inventory = PageInventory.from_dict(page_data)
                self._inventories[url_path] = inventory

            self._tested_selectors = set(data.get("tested_selectors", []))
            self._test_module_map = data.get("test_module_map", {})

            logger.info(f"[INVENTORY] Loaded inventory from: {path}")
            return True

        except Exception as e:
            logger.error(f"[INVENTORY] Failed to load inventory: {e}")
            return False

    def get_summary(self) -> dict:
        """Get summary of inventory status."""
        total_pages = len(self._inventories)
        total_elements = sum(
            len([e for e in inv.elements if e.is_interactive])
            for inv in self._inventories.values()
        )
        total_forms = sum(len(inv.forms) for inv in self._inventories.values())
        tested_selectors = len(self._tested_selectors)

        return {
            "total_pages": total_pages,
            "total_elements": total_elements,
            "total_forms": total_forms,
            "tested_selectors": tested_selectors,
        }
