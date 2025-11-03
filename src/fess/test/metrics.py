"""
Test execution metrics tracking and analysis.

This module provides functionality to track test execution metrics over time,
detect performance regressions, and maintain historical data.
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModuleMetric:
    """Metrics for a single test module execution"""
    module: str
    duration: float
    status: str
    timestamp: str


@dataclass
class MetricsSummary:
    """Summary of metrics for comparison"""
    total_duration: float
    module_durations: Dict[str, float]
    timestamp: str
    environment: Dict[str, str]


class MetricsCollector:
    """Collects and analyzes test execution metrics"""

    def __init__(self, history_file: str = 'test_metrics_history.json'):
        self.history_file = history_file
        self.current_metrics: List[ModuleMetric] = []

    def add_metric(self, module: str, duration: float, status: str):
        """Add a metric for a module execution"""
        metric = ModuleMetric(
            module=module,
            duration=duration,
            status=status,
            timestamp=datetime.now().isoformat()
        )
        self.current_metrics.append(metric)

    def get_summary(self) -> MetricsSummary:
        """Get summary of current execution metrics"""
        total_duration = sum(m.duration for m in self.current_metrics)
        module_durations = {m.module: m.duration for m in self.current_metrics}

        return MetricsSummary(
            total_duration=total_duration,
            module_durations=module_durations,
            timestamp=datetime.now().isoformat(),
            environment={
                'fess_url': os.environ.get('FESS_URL', 'unknown'),
                'headless': os.environ.get('HEADLESS', 'unknown')
            }
        )

    def save_history(self):
        """Save current metrics to history file"""
        summary = self.get_summary()

        # Load existing history
        history = self._load_history()

        # Add current summary
        history.append(asdict(summary))

        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]

        # Save to file
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(f"Metrics history saved to {self.history_file}")

    def _load_history(self) -> List[Dict]:
        """Load historical metrics"""
        if not os.path.exists(self.history_file):
            return []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metrics history: {e}")
            return []

    def detect_regressions(self, threshold: float = 1.5) -> List[str]:
        """
        Detect performance regressions by comparing with baseline.

        Args:
            threshold: Multiplier for regression detection (e.g., 1.5 = 50% slower)

        Returns:
            List of modules with detected regressions
        """
        history = self._load_history()
        if len(history) < 2:
            logger.info("Not enough history for regression detection")
            return []

        # Calculate baseline (median of last 10 runs, excluding current)
        baseline = self._calculate_baseline(history[:-1])
        current = self.get_summary()

        regressions = []
        for module, duration in current.module_durations.items():
            if module in baseline:
                baseline_duration = baseline[module]
                if duration > baseline_duration * threshold:
                    regressions.append(module)
                    logger.warning(
                        f"Performance regression detected in {module}: "
                        f"{duration:.2f}s vs baseline {baseline_duration:.2f}s "
                        f"({duration/baseline_duration:.1f}x slower)"
                    )

        return regressions

    def _calculate_baseline(self, history: List[Dict]) -> Dict[str, float]:
        """Calculate baseline durations from historical data"""
        # Take last 10 entries
        recent = history[-10:] if len(history) >= 10 else history

        # Calculate median for each module
        module_durations: Dict[str, List[float]] = {}
        for entry in recent:
            for module, duration in entry.get('module_durations', {}).items():
                if module not in module_durations:
                    module_durations[module] = []
                module_durations[module].append(duration)

        # Calculate median
        baseline = {}
        for module, durations in module_durations.items():
            sorted_durations = sorted(durations)
            n = len(sorted_durations)
            if n == 0:
                continue
            if n % 2 == 0:
                median = (sorted_durations[n//2-1] + sorted_durations[n//2]) / 2
            else:
                median = sorted_durations[n//2]
            baseline[module] = median

        return baseline

    def print_metrics_summary(self):
        """Print human-readable metrics summary"""
        summary = self.get_summary()

        print("\n" + "="*70)
        print("TEST EXECUTION METRICS")
        print("="*70)
        print(f"Total Duration: {summary.total_duration:.2f}s")
        print(f"Timestamp:      {summary.timestamp}")
        print("="*70)

        print("\nMODULE EXECUTION TIMES:")
        # Sort by duration (slowest first)
        sorted_modules = sorted(
            summary.module_durations.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for module, duration in sorted_modules:
            print(f"  {module:<20} {duration:>8.2f}s")

        print("="*70)

        # Check for regressions
        regressions = self.detect_regressions()
        if regressions:
            print("\n⚠ PERFORMANCE REGRESSIONS DETECTED:")
            for module in regressions:
                print(f"  - {module}")
            print("="*70)

        print()
