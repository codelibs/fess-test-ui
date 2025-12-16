"""
Data models for coverage analysis.

Defines data structures for DOM elements, page inventories,
and coverage tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class DOMElement:
    """
    Represents a discovered DOM element from HTML analysis.

    Attributes:
        element_type: Type of element (input, button, link, select, etc.)
        selector: CSS selector to locate the element
        identifier: Unique identifier (id, name, or generated)
        text_content: Visible text content (truncated)
        attributes: Relevant HTML attributes
        page_url: URL of the page where element was found
        is_interactive: Whether element can be interacted with
        parent_form_id: ID of parent form if applicable
        discovered_at: Timestamp when element was discovered
    """
    element_type: str
    selector: str
    identifier: str
    text_content: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    page_url: str = ""
    is_interactive: bool = True
    parent_form_id: Optional[str] = None
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "element_type": self.element_type,
            "selector": self.selector,
            "identifier": self.identifier,
            "text_content": self.text_content,
            "attributes": self.attributes,
            "page_url": self.page_url,
            "is_interactive": self.is_interactive,
            "parent_form_id": self.parent_form_id,
            "discovered_at": self.discovered_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DOMElement":
        """Create from dictionary."""
        return cls(
            element_type=data.get("element_type", ""),
            selector=data.get("selector", ""),
            identifier=data.get("identifier", ""),
            text_content=data.get("text_content", ""),
            attributes=data.get("attributes", {}),
            page_url=data.get("page_url", ""),
            is_interactive=data.get("is_interactive", True),
            parent_form_id=data.get("parent_form_id"),
            discovered_at=data.get("discovered_at", ""),
        )


@dataclass
class FormInventory:
    """
    Inventory of a form and its fields.

    Attributes:
        form_id: Form identifier (id attribute or generated)
        form_selector: CSS selector for the form
        action: Form action URL
        method: Form method (GET/POST)
        fields: List of form field elements
        submit_buttons: List of submit buttons
        page_url: URL of the page containing the form
    """
    form_id: str
    form_selector: str
    action: str = ""
    method: str = "POST"
    fields: List[DOMElement] = field(default_factory=list)
    submit_buttons: List[DOMElement] = field(default_factory=list)
    page_url: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "form_id": self.form_id,
            "form_selector": self.form_selector,
            "action": self.action,
            "method": self.method,
            "fields": [f.to_dict() for f in self.fields],
            "submit_buttons": [b.to_dict() for b in self.submit_buttons],
            "page_url": self.page_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormInventory":
        """Create from dictionary."""
        return cls(
            form_id=data.get("form_id", ""),
            form_selector=data.get("form_selector", ""),
            action=data.get("action", ""),
            method=data.get("method", "POST"),
            fields=[DOMElement.from_dict(f) for f in data.get("fields", [])],
            submit_buttons=[DOMElement.from_dict(b) for b in data.get("submit_buttons", [])],
            page_url=data.get("page_url", ""),
        )


@dataclass
class PageInventory:
    """
    Inventory of all interactive elements on a single page.

    Attributes:
        url: Page URL
        url_path: URL path (without host)
        page_title: Page title
        elements: List of all interactive DOM elements
        forms: List of form inventories
        navigation_links: List of navigation link URLs
        captured_at: Timestamp of capture
        html_snapshot_path: Path to the HTML snapshot file
    """
    url: str
    url_path: str = ""
    page_title: str = ""
    elements: List[DOMElement] = field(default_factory=list)
    forms: List[FormInventory] = field(default_factory=list)
    navigation_links: List[str] = field(default_factory=list)
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())
    html_snapshot_path: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "url_path": self.url_path,
            "page_title": self.page_title,
            "elements": [e.to_dict() for e in self.elements],
            "forms": [f.to_dict() for f in self.forms],
            "navigation_links": self.navigation_links,
            "captured_at": self.captured_at,
            "html_snapshot_path": self.html_snapshot_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageInventory":
        """Create from dictionary."""
        return cls(
            url=data.get("url", ""),
            url_path=data.get("url_path", ""),
            page_title=data.get("page_title", ""),
            elements=[DOMElement.from_dict(e) for e in data.get("elements", [])],
            forms=[FormInventory.from_dict(f) for f in data.get("forms", [])],
            navigation_links=data.get("navigation_links", []),
            captured_at=data.get("captured_at", ""),
            html_snapshot_path=data.get("html_snapshot_path", ""),
        )

    @property
    def total_interactive_elements(self) -> int:
        """Count total interactive elements."""
        return len([e for e in self.elements if e.is_interactive])

    @property
    def total_forms(self) -> int:
        """Count total forms."""
        return len(self.forms)


@dataclass
class ElementCoverage:
    """
    Coverage status for a single element.

    Attributes:
        element: The DOM element
        tested: Whether element has been tested
        tested_actions: List of tested actions (click, fill, etc.)
        test_modules: List of test modules that exercised this element
        coverage_score: Coverage score from 0.0 to 1.0
    """
    element: DOMElement
    tested: bool = False
    tested_actions: List[str] = field(default_factory=list)
    test_modules: List[str] = field(default_factory=list)
    coverage_score: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "element": self.element.to_dict(),
            "tested": self.tested,
            "tested_actions": self.tested_actions,
            "test_modules": self.test_modules,
            "coverage_score": self.coverage_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ElementCoverage":
        """Create from dictionary."""
        return cls(
            element=DOMElement.from_dict(data.get("element", {})),
            tested=data.get("tested", False),
            tested_actions=data.get("tested_actions", []),
            test_modules=data.get("test_modules", []),
            coverage_score=data.get("coverage_score", 0.0),
        )


@dataclass
class PageCoverage:
    """
    Coverage analysis for an entire page.

    Attributes:
        url: Page URL
        url_path: URL path
        page_title: Page title
        total_elements: Total number of interactive elements
        tested_elements: Number of tested elements
        coverage_percentage: Coverage percentage (0-100)
        element_coverages: Detailed coverage for each element
        untested_elements: List of untested elements
        partially_tested: List of partially tested elements
    """
    url: str
    url_path: str = ""
    page_title: str = ""
    total_elements: int = 0
    tested_elements: int = 0
    coverage_percentage: float = 0.0
    element_coverages: List[ElementCoverage] = field(default_factory=list)
    untested_elements: List[DOMElement] = field(default_factory=list)
    partially_tested: List[ElementCoverage] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "url_path": self.url_path,
            "page_title": self.page_title,
            "total_elements": self.total_elements,
            "tested_elements": self.tested_elements,
            "coverage_percentage": self.coverage_percentage,
            "element_coverages": [c.to_dict() for c in self.element_coverages],
            "untested_elements": [e.to_dict() for e in self.untested_elements],
            "partially_tested": [c.to_dict() for c in self.partially_tested],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageCoverage":
        """Create from dictionary."""
        return cls(
            url=data.get("url", ""),
            url_path=data.get("url_path", ""),
            page_title=data.get("page_title", ""),
            total_elements=data.get("total_elements", 0),
            tested_elements=data.get("tested_elements", 0),
            coverage_percentage=data.get("coverage_percentage", 0.0),
            element_coverages=[ElementCoverage.from_dict(c) for c in data.get("element_coverages", [])],
            untested_elements=[DOMElement.from_dict(e) for e in data.get("untested_elements", [])],
            partially_tested=[ElementCoverage.from_dict(c) for c in data.get("partially_tested", [])],
        )


@dataclass
class CoverageGap:
    """
    Represents a gap in test coverage that should be addressed.

    Attributes:
        element: The untested or under-tested element
        page_url: URL of the page containing the element
        priority: Priority score (0.0 to 1.0, higher = more important)
        priority_reason: Human-readable reason for priority
        suggested_tests: List of suggested test actions
    """
    element: DOMElement
    page_url: str
    priority: float = 0.5
    priority_reason: str = ""
    suggested_tests: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "element": self.element.to_dict(),
            "page_url": self.page_url,
            "priority": self.priority,
            "priority_reason": self.priority_reason,
            "suggested_tests": self.suggested_tests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoverageGap":
        """Create from dictionary."""
        return cls(
            element=DOMElement.from_dict(data.get("element", {})),
            page_url=data.get("page_url", ""),
            priority=data.get("priority", 0.5),
            priority_reason=data.get("priority_reason", ""),
            suggested_tests=data.get("suggested_tests", []),
        )
