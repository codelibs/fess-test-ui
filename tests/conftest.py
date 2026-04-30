"""Pytest config: make src/ importable as a top-level package root."""
import sys
from pathlib import Path

# repos/fess-test-ui/src is the package root
SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC))
