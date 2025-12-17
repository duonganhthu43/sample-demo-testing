"""
Visualization Tool
Creates charts and visualizations for reports
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class Visualizer:
    """
    Creates simple text-based visualizations and prepares data for charts
    """

    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir) / "visualizations"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_comparison_table(self, data: Dict[str, Dict[str, Any]], title: str = "") -> str:
        """
        Create a text-based comparison table

        Args:
            data: Dictionary of items to compare {item_name: {metric: value}}
            title: Table title

        Returns:
            Formatted table string
        """
        if not data:
            return "No data to display"

        # Get all unique metrics
        all_metrics = set()
        for item_data in data.values():
            all_metrics.update(item_data.keys())

        metrics = sorted(list(all_metrics))
        items = list(data.keys())

        # Build table
        lines = []
        if title:
            lines.append(f"\n{title}")
            lines.append("=" * len(title))

        # Header
        header = f"{'Metric':<30} | " + " | ".join(f"{item:<20}" for item in items)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for metric in metrics:
            row = f"{metric:<30} | "
            values = []
            for item in items:
                value = data[item].get(metric, "N/A")
                values.append(f"{str(value):<20}")
            row += " | ".join(values)
            lines.append(row)

        return "\n".join(lines)

    def create_ranking_list(self, items: List[Dict[str, Any]], rank_by: str, title: str = "") -> str:
        """
        Create a ranked list

        Args:
            items: List of items with metrics
            rank_by: Metric to rank by
            title: List title

        Returns:
            Formatted ranking string
        """
        if not items:
            return "No items to rank"

        # Sort items
        sorted_items = sorted(items, key=lambda x: x.get(rank_by, 0), reverse=True)

        lines = []
        if title:
            lines.append(f"\n{title}")
            lines.append("=" * len(title))

        for i, item in enumerate(sorted_items, 1):
            name = item.get("name", f"Item {i}")
            value = item.get(rank_by, "N/A")
            lines.append(f"{i}. {name}: {value}")

            # Add other metrics
            for key, val in item.items():
                if key not in ["name", rank_by]:
                    lines.append(f"   - {key}: {val}")

        return "\n".join(lines)

    def create_swot_matrix(self, swot_data: Dict[str, List[str]]) -> str:
        """
        Create a SWOT matrix visualization

        Args:
            swot_data: Dictionary with keys: strengths, weaknesses, opportunities, threats

        Returns:
            Formatted SWOT matrix
        """
        def format_items(items: List[str], max_items: int = 5) -> List[str]:
            formatted = []
            for item in items[:max_items]:
                # Wrap long items
                if len(item) > 35:
                    item = item[:32] + "..."
                formatted.append(f"• {item}")
            return formatted

        strengths = format_items(swot_data.get("strengths", []))
        weaknesses = format_items(swot_data.get("weaknesses", []))
        opportunities = format_items(swot_data.get("opportunities", []))
        threats = format_items(swot_data.get("threats", []))

        # Calculate max lines
        max_lines = max(len(strengths), len(weaknesses), len(opportunities), len(threats))

        # Pad lists
        strengths += [""] * (max_lines - len(strengths))
        weaknesses += [""] * (max_lines - len(weaknesses))
        opportunities += [""] * (max_lines - len(opportunities))
        threats += [""] * (max_lines - len(threats))

        # Build matrix
        lines = []
        lines.append("\n" + "="*80)
        lines.append(" " * 30 + "SWOT ANALYSIS")
        lines.append("="*80)

        # Top row (Strengths | Weaknesses)
        lines.append("╔" + "═"*38 + "╦" + "═"*38 + "╗")
        lines.append("║ " + "STRENGTHS".ljust(36) + " ║ " + "WEAKNESSES".ljust(36) + " ║")
        lines.append("╠" + "═"*38 + "╬" + "═"*38 + "╣")

        for s, w in zip(strengths, weaknesses):
            lines.append("║ " + s.ljust(36) + " ║ " + w.ljust(36) + " ║")

        # Middle separator
        lines.append("╠" + "═"*38 + "╬" + "═"*38 + "╣")
        lines.append("║ " + "OPPORTUNITIES".ljust(36) + " ║ " + "THREATS".ljust(36) + " ║")
        lines.append("╠" + "═"*38 + "╬" + "═"*38 + "╣")

        for o, t in zip(opportunities, threats):
            lines.append("║ " + o.ljust(36) + " ║ " + t.ljust(36) + " ║")

        lines.append("╚" + "═"*38 + "╩" + "═"*38 + "╝")

        return "\n".join(lines)

    def save_chart_data(self, data: Dict[str, Any], filename: str, chart_type: str = "bar") -> str:
        """
        Save data for chart generation (can be used with external tools)

        Args:
            data: Chart data
            filename: Output filename
            chart_type: Type of chart (bar, line, pie, etc.)

        Returns:
            Path to saved file
        """
        chart_spec = {
            "type": chart_type,
            "data": data,
            "metadata": {
                "created_for": "market_research_report"
            }
        }

        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(chart_spec, f, indent=2)

        print(f"Saved chart data to: {filepath}")
        return str(filepath)


# Convenience functions
def create_swot_visualization(swot_data: Dict[str, List[str]]) -> str:
    """Create SWOT matrix visualization"""
    viz = Visualizer()
    return viz.create_swot_matrix(swot_data)


def create_comparison(data: Dict[str, Dict[str, Any]], title: str = "") -> str:
    """Create comparison table"""
    viz = Visualizer()
    return viz.create_comparison_table(data, title)
