"""Coverage analysis module for test improvement."""

from .models import DOMElement, FormInventory, PageInventory, ElementCoverage, PageCoverage
from .analyzer import CoverageAnalyzer
from .inventory import InventoryManager
from .reporter import CoverageReporter
from .generator import TestStubGenerator

__all__ = [
    'DOMElement',
    'FormInventory',
    'PageInventory',
    'ElementCoverage',
    'PageCoverage',
    'CoverageAnalyzer',
    'InventoryManager',
    'CoverageReporter',
    'TestStubGenerator',
]
