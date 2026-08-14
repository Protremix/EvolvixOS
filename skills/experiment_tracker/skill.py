"""
EvolvixOS — Experiment Tracker Skill
Track ML/AI experiments, log metrics, compare runs, reproduce results.

Features:
  - Log experiments with parameters, metrics, artifacts
  - Compare experiments side-by-side
  - Track experiment lineage (which produced which model)
  - Search and filter experiments
  - Export experiment reports

Storage: data/experiments/experiments.json
"""

import os
import json
import time
import uuid
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

EXPERIMENTS_PATH = Path(__file__).parent.parent.parent / "data" / "experiments" / "experiments.json"


class Skill:
    """Experiment Tracker — log and compare AI experiments."""

    def __init__(self, config=None):
        self.config = config or {}
        EXPERIMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if EXPERIMENTS_PATH.exists():
            self.data = json.loads(EXPERIMENTS_PATH.read_text())
        else:
            self.data = {"experiments": {}}

    def _save(self):
        EXPERIMENTS_PATH.write_text(json.dumps(self.data, indent=2))

    def log(self, name: str, parameters: dict = None, metrics: dict = None,
            model: str = "", dataset: str = "", status: str = "running",
            notes: str = "", tags: list = None) -> str:
        """Log a new experiment."""
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        experiment = {
            "id": exp_id,
            "name": name,
            "parameters": parameters or {},
            "metrics": metrics or {},
            "model": model,
            "dataset": dataset,
            "status": status,
            "notes": notes,
            "tags": tags or [],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.data["experiments"][exp_id] = experiment
        self._save()
        return f"📝 Logged experiment '{name}' → {exp_id}"

    def update(self, exp_id: str, metrics: dict = None, status: str = None,
               notes: str = None) -> str:
        """Update an experiment (add metrics, change status)."""
        exp = self.data["experiments"].get(exp_id)
        if not exp:
            return f"❌ Experiment {exp_id} not found."
        if metrics:
            exp["metrics"].update(metrics)
        if status:
            exp["status"] = status
        if notes:
            exp["notes"] = (exp.get("notes", "") + "\n" + notes).strip()
        exp["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return f"✅ Updated {exp_id} — status: {exp['status']}"

    def list_experiments(self, status: str = None, tag: str = None,
                         model: str = None, limit: int = 20) -> str:
        """List experiments, optionally filtered."""
        exps = list(self.data["experiments"].values())
        if status:
            exps = [e for e in exps if e["status"] == status]
        if tag:
            exps = [e for e in exps if tag in e.get("tags", [])]
        if model:
            exps = [e for e in exps if e.get("model") == model]
        exps = sorted(exps, key=lambda x: x["created_at"], reverse=True)[:limit]

        if not exps:
            return "No experiments found."

        table = Table(title="🧪 Experiments", show_lines=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Status", style="green")
        table.add_column("Model", style="magenta")
        table.add_column("Created", style="yellow")

        for e in exps:
            status_icon = {"running": "🔄", "completed": "✅", "failed": "❌"}.get(e["status"], "❓")
            table.add_row(e["id"], e["name"], f"{status_icon} {e['status']}",
                          e.get("model", "—"), e["created_at"][:10])
        console.print(table)
        return f"\n{len(exps)} experiments shown."

    def get(self, exp_id: str) -> str:
        """Get full details of an experiment."""
        exp = self.data["experiments"].get(exp_id)
        if not exp:
            return f"❌ Experiment {exp_id} not found."
        return json.dumps(exp, indent=2)

    def compare(self, exp_id1: str, exp_id2: str) -> str:
        """Compare two experiments side-by-side."""
        e1 = self.data["experiments"].get(exp_id1)
        e2 = self.data["experiments"].get(exp_id2)
        if not e1 or not e2:
            return f"❌ One or both experiments not found."

        lines = [f"📊 Experiment Comparison\n"]

        # Compare parameters
        lines.append("Parameters:")
        all_params = set(list(e1.get("parameters", {}).keys()) + list(e2.get("parameters", {}).keys()))
        for p in sorted(all_params):
            v1 = e1.get("parameters", {}).get(p, "—")
            v2 = e2.get("parameters", {}).get(p, "—")
            same = "✓" if v1 == v2 else "≠"
            lines.append(f"  {p:25s}  {str(v1):>20s}  {same}  {str(v2):>20s}")

        # Compare metrics
        lines.append("\nMetrics:")
        all_metrics = set(list(e1.get("metrics", {}).keys()) + list(e2.get("metrics", {}).keys()))
        for m in sorted(all_metrics):
            v1 = e1.get("metrics", {}).get(m, "—")
            v2 = e2.get("metrics", {}).get(m, "—")
            better = ""
            try:
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    if v2 > v1:
                        better = " ⬆️"
                    elif v2 < v1:
                        better = " ⬇️"
            except:
                pass
            lines.append(f"  {m:25s}  {str(v1):>20s}  →  {str(v2):>20s}{better}")

        return "\n".join(lines)

    def search(self, query: str) -> str:
        """Search experiments by name, notes, or tags."""
        query_lower = query.lower()
        results = []
        for exp in self.data["experiments"].values():
            if (query_lower in exp["name"].lower() or
                query_lower in exp.get("notes", "").lower() or
                any(query_lower in t.lower() for t in exp.get("tags", []))):
                results.append(exp)
        if not results:
            return f"No experiments matching '{query}'."
        lines = [f"🔍 Found {len(results)} experiments matching '{query}':"]
        for e in results:
            lines.append(f"  {e['id']} — {e['name']} ({e['status']})")
        return "\n".join(lines)

    def delete(self, exp_id: str) -> str:
        """Delete an experiment."""
        if exp_id not in self.data["experiments"]:
            return f"❌ Experiment {exp_id} not found."
        del self.data["experiments"][exp_id]
        self._save()
        return f"✅ Deleted {exp_id}"

    def summary(self) -> str:
        """Get a summary of all experiments."""
        exps = list(self.data["experiments"].values())
        total = len(exps)
        running = sum(1 for e in exps if e["status"] == "running")
        completed = sum(1 for e in exps if e["status"] == "completed")
        failed = sum(1 for e in exps if e["status"] == "failed")
        models = len(set(e.get("model", "") for e in exps if e.get("model")))

        return (
            f"📊 Experiment Summary\n"
            f"  Total:      {total}\n"
            f"  Running:    {running}\n"
            f"  Completed:  {completed}\n"
            f"  Failed:     {failed}\n"
            f"  Models:     {models} unique models tested"
        )

    def run(self, args: dict) -> str:
        action = args.get("action", "list")

        if action == "log":
            return self.log(
                name=args.get("name", "unnamed"),
                parameters=args.get("parameters", {}),
                metrics=args.get("metrics", {}),
                model=args.get("model", ""),
                dataset=args.get("dataset", ""),
                status=args.get("status", "running"),
                notes=args.get("notes", ""),
                tags=args.get("tags", []),
            )
        elif action == "update":
            return self.update(args.get("exp_id", ""), args.get("metrics"),
                               args.get("status"), args.get("notes"))
        elif action == "list":
            return self.list_experiments(args.get("status"), args.get("tag"),
                                          args.get("model"))
        elif action == "get":
            return self.get(args.get("exp_id", ""))
        elif action == "compare":
            return self.compare(args.get("exp_id1", ""), args.get("exp_id2", ""))
        elif action == "search":
            return self.search(args.get("query", ""))
        elif action == "delete":
            return self.delete(args.get("exp_id", ""))
        elif action == "summary":
            return self.summary()
        else:
            return f"Unknown action: {action}\nAvailable: log, update, list, get, compare, search, delete, summary"
