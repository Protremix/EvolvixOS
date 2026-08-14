"""
EvolvixOS — Data Analyst Skill
Analyze data with pandas, generate statistics, create charts.
100% local. Zero tokens. Zero cloud.

Pip: pip install pandas matplotlib seaborn numpy
License: BSD-3 (pandas), matplotlib (PSF), seaborn (BSD)
"""

import os
import json
import time
import tempfile
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """Data analyst — pandas-based data analysis. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/analysis"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "analyze")

        if action == "analyze":
            return self.analyze(args.get("file", ""), args.get("format", "csv"))
        elif action == "stats":
            return self.statistics(args.get("file", ""), args.get("format", "csv"))
        elif action == "chart":
            return self.create_chart(args.get("file", ""), args.get("chart_type", "bar"),
                                     args.get("x", ""), args.get("y", ""),
                                     args.get("title", ""), args.get("format", "csv"))
        elif action == "query":
            return self.query_data(args.get("file", ""), args.get("query", ""),
                                   args.get("format", "csv"))
        elif action == "merge":
            return self.merge_files(args.get("files", []), args.get("output", ""))
        elif action == "convert":
            return self.convert_format(args.get("file", ""), args.get("to_format", "json"))
        else:
            return f"Unknown action: {action}. Use: analyze, stats, chart, query, merge, convert"

    def analyze(self, file_path: str, fmt: str = "csv") -> str:
        if not file_path or not os.path.exists(file_path):
            return "Error: File not found."

        try:
            import pandas as pd
        except ImportError:
            return "Error: pip install pandas matplotlib seaborn numpy"

        try:
            df = self._load(file_path, fmt)

            result = {
                "file": file_path,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "null_counts": df.isnull().sum().to_dict(),
                "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
            }

            # Numeric column stats
            numeric = df.select_dtypes(include="number")
            if not numeric.empty:
                result["statistics"] = numeric.describe().to_dict()

            # First 5 rows
            result["head"] = df.head().to_dict(orient="records")
            result["tail"] = df.tail().to_dict(orient="records")

            return json.dumps(result, indent=2, default=str)[:10000]
        except Exception as e:
            return f"Error analyzing: {e}"

    def statistics(self, file_path: str, fmt: str = "csv") -> str:
        try:
            import pandas as pd
            df = self._load(file_path, fmt)
            stats = df.describe(include="all").to_dict()
            return json.dumps(stats, indent=2, default=str)[:10000]
        except Exception as e:
            return f"Error: {e}"

    def create_chart(self, file_path: str, chart_type: str = "bar",
                     x: str = "", y: str = "", title: str = "", fmt: str = "csv") -> str:
        try:
            import pandas as pd
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            df = self._load(file_path, fmt)

            if not x:
                x = df.columns[0]
            if not y:
                y = df.columns[1] if len(df.columns) > 1 else df.columns[0]

            fig, ax = plt.subplots(figsize=(10, 6))

            if chart_type == "bar":
                df.plot.bar(x=x, y=y, ax=ax)
            elif chart_type == "line":
                df.plot.line(x=x, y=y, ax=ax)
            elif chart_type == "scatter":
                df.plot.scatter(x=x, y=y, ax=ax)
            elif chart_type == "hist":
                df[y].plot.hist(ax=ax, bins=30)
            elif chart_type == "pie":
                df.plot.pie(y=y, labels=df[x], ax=ax)
            elif chart_type == "box":
                df.plot.box(ax=ax)
            else:
                df.plot(x=x, y=y, ax=ax)

            ax.set_title(title or f"{chart_type} chart: {y} vs {x}")
            plt.tight_layout()

            output_file = self.output_dir / f"chart_{int(time.time())}.png"
            plt.savefig(str(output_file), dpi=150)
            plt.close()

            return f"Chart saved: {output_file}"
        except Exception as e:
            return f"Error creating chart: {e}"

    def query_data(self, file_path: str, query: str, fmt: str = "csv") -> str:
        try:
            import pandas as pd
            df = self._load(file_path, fmt)
            result = df.query(query)
            return result.to_string()[:10000]
        except Exception as e:
            return f"Error querying: {e}"

    def merge_files(self, files: list, output: str = "") -> str:
        try:
            import pandas as pd
            dfs = [pd.read_csv(f) for f in files if os.path.exists(f)]
            merged = pd.concat(dfs, ignore_index=True)
            if not output:
                output = str(self.output_dir / f"merged_{int(time.time())}.csv")
            merged.to_csv(output, index=False)
            return f"Merged {len(files)} files → {output} ({len(merged)} rows)"
        except Exception as e:
            return f"Error merging: {e}"

    def convert_format(self, file_path: str, to_format: str = "json") -> str:
        try:
            import pandas as pd
            df = self._load_auto(file_path)
            output = file_path.rsplit(".", 1)[0] + f".{to_format}"

            if to_format == "json":
                df.to_json(output, orient="records", indent=2)
            elif to_format == "csv":
                df.to_csv(output, index=False)
            elif to_format == "xlsx":
                df.to_excel(output, index=False)
            elif to_format == "parquet":
                df.to_parquet(output, index=False)
            elif to_format == "html":
                df.to_html(output, index=False)
            else:
                return f"Unsupported format: {to_format}"

            return f"Converted: {file_path} → {output}"
        except Exception as e:
            return f"Error converting: {e}"

    def _load(self, file_path: str, fmt: str = "csv"):
        import pandas as pd
        if fmt == "csv":
            return pd.read_csv(file_path)
        elif fmt == "json":
            return pd.read_json(file_path)
        elif fmt == "xlsx" or fmt == "excel":
            return pd.read_excel(file_path)
        elif fmt == "parquet":
            return pd.read_parquet(file_path)
        elif fmt == "tsv":
            return pd.read_csv(file_path, sep="\t")
        elif fmt == "html":
            return pd.read_html(file_path)[0]
        return pd.read_csv(file_path)

    def _load_auto(self, file_path: str):
        import pandas as pd
        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext in ("csv", "tsv"):
            return pd.read_csv(file_path)
        elif ext == "json":
            return pd.read_json(file_path)
        elif ext in ("xlsx", "xls"):
            return pd.read_excel(file_path)
        elif ext == "parquet":
            return pd.read_parquet(file_path)
        elif ext == "html":
            return pd.read_html(file_path)[0]
        return pd.read_csv(file_path)
