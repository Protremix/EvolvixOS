"""
EvolvixOS — Visualizer Skill
Create charts, graphs, dashboards from data.
100% local using matplotlib/plotly. Zero tokens.

Pip: pip install matplotlib plotly seaborn
License: PSF (matplotlib), MIT (plotly), BSD (seaborn)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Visualizer — charts, graphs, plots from data. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/charts"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "chart")

        if action == "chart":
            return self.create_chart(
                args.get("chart_type", "bar"),
                args.get("data", []),
                args.get("labels", []),
                args.get("title", ""),
                args.get("xlabel", ""),
                args.get("ylabel", ""),
            )
        elif action == "pie":
            return self.create_pie(args.get("data", []), args.get("labels", []),
                                   args.get("title", ""))
        elif action == "scatter":
            return self.create_scatter(args.get("x", []), args.get("y", []),
                                       args.get("title", ""),
                                       args.get("xlabel", ""), args.get("ylabel", ""))
        elif action == "histogram":
            return self.create_histogram(args.get("data", []), args.get("bins", 30),
                                         args.get("title", ""))
        elif action == "heatmap":
            return self.create_heatmap(args.get("matrix", []), args.get("title", ""))
        elif action == "timeline":
            return self.create_timeline(args.get("events", []))
        elif action == "line_multi":
            return self.create_multi_line(args.get("series", []), args.get("labels", []),
                                          args.get("title", ""))
        elif action == "box":
            return self.create_box(args.get("data", []), args.get("labels", []),
                                    args.get("title", ""))
        else:
            return (f"Unknown action: {action}. Use: chart, pie, scatter, histogram, "
                    "heatmap, timeline, line_multi, box")

    def create_chart(self, chart_type: str, data: list, labels: list = None,
                     title: str = "", xlabel: str = "", ylabel: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            if labels is None:
                labels = [f"Item {i+1}" for i in range(len(data))]

            fig, ax = plt.subplots(figsize=(10, 6))

            if chart_type == "bar":
                ax.bar(labels, data)
            elif chart_type == "line":
                ax.plot(labels, data, marker="o")
            elif chart_type == "area":
                ax.fill_between(range(len(data)), data, alpha=0.5)
                ax.plot(range(len(data)), data)
            else:
                ax.bar(labels, data)

            ax.set_title(title or "Chart")
            ax.set_xlabel(xlabel or "")
            ax.set_ylabel(ylabel or "")
            plt.xticks(rotation=45 if len(labels) > 5 else 0, ha="right")
            plt.tight_layout()

            out = self.output_dir / f"chart_{chart_type}_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Chart saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_pie(self, data: list, labels: list, title: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(data, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title(title or "Pie Chart")
            plt.tight_layout()

            out = self.output_dir / f"pie_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Pie chart saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_scatter(self, x: list, y: list, title: str = "",
                       xlabel: str = "", ylabel: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(x, y, alpha=0.6, s=50)
            ax.set_title(title or "Scatter Plot")
            ax.set_xlabel(xlabel or "X")
            ax.set_ylabel(ylabel or "Y")
            plt.tight_layout()

            out = self.output_dir / f"scatter_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Scatter plot saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_histogram(self, data: list, bins: int = 30, title: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(data, bins=bins, edgecolor="black", alpha=0.7)
            ax.set_title(title or "Histogram")
            ax.set_xlabel("Value")
            ax.set_ylabel("Frequency")
            plt.tight_layout()

            out = self.output_dir / f"histogram_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Histogram saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_heatmap(self, matrix: list, title: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np

            fig, ax = plt.subplots(figsize=(10, 8))
            data = np.array(matrix)
            im = ax.imshow(data, cmap="YlOrRd")
            ax.set_title(title or "Heatmap")
            fig.colorbar(im)
            plt.tight_layout()

            out = self.output_dir / f"heatmap_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Heatmap saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_timeline(self, events: list) -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime

            fig, ax = plt.subplots(figsize=(14, 4))

            for event in events:
                date = datetime.fromisoformat(event.get("date", ""))
                label = event.get("label", "")
                ax.scatter(date, 0, s=100, zorder=5)
                ax.annotate(label, (date, 0), textcoords="offset points",
                           xytext=(0, 10), ha="center", rotation=45, fontsize=8)

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.set_yticks([])
            ax.set_title("Timeline")
            plt.tight_layout()

            out = self.output_dir / f"timeline_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Timeline saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_multi_line(self, series: list, labels: list, title: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(12, 6))
            for i, s in enumerate(series):
                label = labels[i] if i < len(labels) else f"Series {i+1}"
                ax.plot(s, label=label, marker="o", markersize=3)
            ax.legend()
            ax.set_title(title or "Multi-Line Chart")
            plt.tight_layout()

            out = self.output_dir / f"multiline_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Multi-line chart saved: {out}"
        except Exception as e:
            return f"Error: {e}"

    def create_box(self, data: list, labels: list, title: str = "") -> str:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.boxplot(data, labels=labels)
            ax.set_title(title or "Box Plot")
            plt.tight_layout()

            out = self.output_dir / f"box_{int(time.time())}.png"
            plt.savefig(str(out), dpi=150)
            plt.close()
            return f"Box plot saved: {out}"
        except Exception as e:
            return f"Error: {e}"
