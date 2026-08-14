#!/usr/bin/env python3
"""Data Analyzer - Pandas + DuckDB (BSD/MIT) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "stats")
        try:
            import pandas as pd
            import duckdb
            if action == "load_csv":
                df = pd.read_csv(args["file"])
                return {"rows": len(df), "columns": list(df.columns), "head": df.head(10).to_dict("records")}
            elif action == "sql":
                df = pd.read_csv(args.get("file", "")) if args.get("file") else pd.DataFrame(args.get("data", []))
                result = duckdb.query(args["query"]).df()
                return {"rows": len(result), "data": result.to_dict("records")}
            elif action == "stats":
                df = pd.read_csv(args["file"]) if args.get("file") else pd.DataFrame(args.get("data", []))
                return {"describe": df.describe().to_dict(), "rows": len(df), "cols": len(df.columns)}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pandas", "duckdb"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
