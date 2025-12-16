"""
Coverage Report Generator.

Generates coverage reports in JSON, HTML, and Markdown formats.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from .models import PageCoverage, CoverageGap

logger = logging.getLogger(__name__)


class CoverageReporter:
    """
    Generates coverage reports in various formats.

    Supports JSON, HTML, and Markdown output formats.
    """

    def __init__(self, output_dir: str = "coverage_reports"):
        """
        Initialize coverage reporter.

        Args:
            output_dir: Directory for report output
        """
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(
        self,
        page_coverages: Dict[str, PageCoverage],
        gaps: List[CoverageGap],
        format: str = "json",
        filename: str = None
    ) -> str:
        """
        Generate coverage report in specified format.

        Args:
            page_coverages: Dictionary of URL path to PageCoverage
            gaps: List of coverage gaps
            format: Report format ('json', 'html', 'md', 'all')
            filename: Output filename (without extension)

        Returns:
            Path to generated report (or directory if format='all')
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"coverage_report_{timestamp}"

        if format == "all":
            self._generate_json(page_coverages, gaps, filename)
            self._generate_html(page_coverages, gaps, filename)
            self._generate_markdown(page_coverages, gaps, filename)
            return self._output_dir

        if format == "json":
            return self._generate_json(page_coverages, gaps, filename)
        elif format == "html":
            return self._generate_html(page_coverages, gaps, filename)
        elif format == "md":
            return self._generate_markdown(page_coverages, gaps, filename)
        else:
            logger.warning(f"Unknown format: {format}, using JSON")
            return self._generate_json(page_coverages, gaps, filename)

    def _calculate_summary(
        self,
        page_coverages: Dict[str, PageCoverage]
    ) -> dict:
        """Calculate summary statistics."""
        total_pages = len(page_coverages)
        total_elements = sum(pc.total_elements for pc in page_coverages.values())
        tested_elements = sum(pc.tested_elements for pc in page_coverages.values())

        overall_percentage = (
            (tested_elements / total_elements * 100) if total_elements > 0 else 0.0
        )

        return {
            "total_pages": total_pages,
            "total_elements": total_elements,
            "tested_elements": tested_elements,
            "untested_elements": total_elements - tested_elements,
            "coverage_percentage": round(overall_percentage, 1),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_json(
        self,
        page_coverages: Dict[str, PageCoverage],
        gaps: List[CoverageGap],
        filename: str
    ) -> str:
        """Generate JSON format report."""
        summary = self._calculate_summary(page_coverages)

        report = {
            "summary": summary,
            "pages": [
                {
                    "url_path": url_path,
                    **pc.to_dict()
                }
                for url_path, pc in sorted(
                    page_coverages.items(),
                    key=lambda x: x[1].coverage_percentage
                )
            ],
            "priority_gaps": [
                gap.to_dict() for gap in gaps[:50]  # Top 50 gaps
            ],
        }

        output_path = os.path.join(self._output_dir, f"{filename}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"[REPORT] JSON report saved: {output_path}")
        return output_path

    def _generate_html(
        self,
        page_coverages: Dict[str, PageCoverage],
        gaps: List[CoverageGap],
        filename: str
    ) -> str:
        """Generate HTML format report."""
        summary = self._calculate_summary(page_coverages)

        # Sort pages by coverage percentage
        sorted_pages = sorted(
            page_coverages.items(),
            key=lambda x: x[1].coverage_percentage
        )

        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.coverage {{
            background: {self._get_coverage_gradient(summary['coverage_percentage'])};
        }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .progress-fill.low {{ background: #dc3545; }}
        .progress-fill.medium {{ background: #ffc107; }}
        .progress-fill.high {{ background: #28a745; }}
        .gap-item {{
            background: #fff3cd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }}
        .gap-high {{ border-left-color: #dc3545; background: #f8d7da; }}
        .priority-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .priority-high {{ background: #dc3545; color: white; }}
        .priority-medium {{ background: #ffc107; color: black; }}
        .priority-low {{ background: #28a745; color: white; }}
        code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9em;
        }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Coverage Report</h1>
        <p class="timestamp">Generated: {summary['generated_at']}</p>

        <div class="summary">
            <div class="stat-card coverage">
                <div class="stat-value">{summary['coverage_percentage']}%</div>
                <div class="stat-label">Overall Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['total_pages']}</div>
                <div class="stat-label">Pages Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['tested_elements']}/{summary['total_elements']}</div>
                <div class="stat-label">Elements Tested</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(gaps)}</div>
                <div class="stat-label">Coverage Gaps</div>
            </div>
        </div>

        <h2>Page Coverage</h2>
        <table>
            <thead>
                <tr>
                    <th>Page</th>
                    <th>Elements</th>
                    <th>Tested</th>
                    <th>Coverage</th>
                </tr>
            </thead>
            <tbody>
{self._generate_page_rows(sorted_pages)}
            </tbody>
        </table>

        <h2>Priority Coverage Gaps</h2>
        <p>Top untested elements that should be prioritized:</p>
{self._generate_gap_items(gaps[:20])}

    </div>
</body>
</html>"""

        output_path = os.path.join(self._output_dir, f"{filename}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"[REPORT] HTML report saved: {output_path}")
        return output_path

    def _get_coverage_gradient(self, percentage: float) -> str:
        """Get gradient color based on coverage percentage."""
        if percentage >= 80:
            return "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
        elif percentage >= 50:
            return "linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)"
        else:
            return "linear-gradient(135deg, #dc3545 0%, #e83e8c 100%)"

    def _generate_page_rows(self, sorted_pages: List) -> str:
        """Generate HTML table rows for pages."""
        rows = []
        for url_path, pc in sorted_pages:
            progress_class = "high" if pc.coverage_percentage >= 80 else (
                "medium" if pc.coverage_percentage >= 50 else "low"
            )
            row = f"""                <tr>
                    <td><code>{url_path or pc.url}</code><br><small>{pc.page_title}</small></td>
                    <td>{pc.total_elements}</td>
                    <td>{pc.tested_elements}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill {progress_class}" style="width: {pc.coverage_percentage}%"></div>
                        </div>
                        {pc.coverage_percentage}%
                    </td>
                </tr>"""
            rows.append(row)
        return "\n".join(rows)

    def _generate_gap_items(self, gaps: List[CoverageGap]) -> str:
        """Generate HTML for coverage gap items."""
        items = []
        for gap in gaps:
            priority_class = "high" if gap.priority >= 0.8 else (
                "medium" if gap.priority >= 0.5 else "low"
            )
            gap_class = "gap-high" if gap.priority >= 0.8 else ""

            suggestions = "<br>".join(
                f"- {s}" for s in gap.suggested_tests[:3]
            )

            item = f"""        <div class="gap-item {gap_class}">
            <span class="priority-badge priority-{priority_class}">
                Priority: {gap.priority:.2f}
            </span>
            <strong>{gap.element.element_type}</strong> -
            <code>{gap.element.selector}</code>
            <br>
            <small>Page: {gap.page_url}</small>
            <br>
            <small>Reason: {gap.priority_reason}</small>
            <br>
            <small><strong>Suggested tests:</strong><br>{suggestions}</small>
        </div>"""
            items.append(item)

        return "\n".join(items) if items else "<p>No significant coverage gaps found!</p>"

    def _generate_markdown(
        self,
        page_coverages: Dict[str, PageCoverage],
        gaps: List[CoverageGap],
        filename: str
    ) -> str:
        """Generate Markdown format report."""
        summary = self._calculate_summary(page_coverages)

        # Sort pages by coverage percentage
        sorted_pages = sorted(
            page_coverages.items(),
            key=lambda x: x[1].coverage_percentage
        )

        md_content = f"""# Test Coverage Report

Generated: {summary['generated_at']}

## Summary

| Metric | Value |
|--------|-------|
| Overall Coverage | **{summary['coverage_percentage']}%** |
| Total Pages | {summary['total_pages']} |
| Total Elements | {summary['total_elements']} |
| Tested Elements | {summary['tested_elements']} |
| Untested Elements | {summary['untested_elements']} |
| Coverage Gaps | {len(gaps)} |

## Page Coverage

| Page | Title | Elements | Tested | Coverage |
|------|-------|----------|--------|----------|
"""

        for url_path, pc in sorted_pages:
            status = self._get_status_emoji(pc.coverage_percentage)
            md_content += f"| `{url_path or pc.url}` | {pc.page_title[:30]} | {pc.total_elements} | {pc.tested_elements} | {status} {pc.coverage_percentage}% |\n"

        md_content += """
## Priority Coverage Gaps

Untested elements that should be addressed:

"""

        for i, gap in enumerate(gaps[:20], 1):
            md_content += f"""### {i}. {gap.element.element_type} (Priority: {gap.priority:.2f})

- **Selector:** `{gap.element.selector}`
- **Page:** {gap.page_url}
- **Reason:** {gap.priority_reason}
- **Suggested tests:**
"""
            for suggestion in gap.suggested_tests[:3]:
                md_content += f"  - {suggestion}\n"
            md_content += "\n"

        output_path = os.path.join(self._output_dir, f"{filename}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"[REPORT] Markdown report saved: {output_path}")
        return output_path

    def _get_status_emoji(self, percentage: float) -> str:
        """Get status emoji based on coverage percentage."""
        if percentage >= 80:
            return "🟢"
        elif percentage >= 50:
            return "🟡"
        else:
            return "🔴"

    def print_console_summary(
        self,
        page_coverages: Dict[str, PageCoverage],
        gaps: List[CoverageGap]
    ) -> None:
        """Print summary to console."""
        summary = self._calculate_summary(page_coverages)

        print("\n" + "=" * 60)
        print("COVERAGE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Overall Coverage: {summary['coverage_percentage']}%")
        print(f"Pages Analyzed: {summary['total_pages']}")
        print(f"Elements: {summary['tested_elements']}/{summary['total_elements']} tested")
        print(f"Coverage Gaps: {len(gaps)}")
        print("-" * 60)

        # Show pages with lowest coverage
        if page_coverages:
            print("\nPages with lowest coverage:")
            sorted_pages = sorted(
                page_coverages.items(),
                key=lambda x: x[1].coverage_percentage
            )
            for url_path, pc in sorted_pages[:5]:
                print(f"  {pc.coverage_percentage:5.1f}% - {url_path or pc.url}")

        # Show top priority gaps
        if gaps:
            print("\nTop priority gaps:")
            for gap in gaps[:5]:
                print(f"  [{gap.priority:.2f}] {gap.element.element_type}: {gap.element.selector[:40]}")

        print("=" * 60 + "\n")
