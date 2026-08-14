"""
EvolvixOS — Model Registry Skill
Version, compare, and deploy AI models. All local, zero tokens.

Manages:
  - Model versions (semver)
  - Model metadata (type, size, format, performance metrics)
  - A/B comparisons
  - Deployment status (which model is live)
  - Model lineage (which experiment produced this model)

Storage: data/registry/models.json
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

console = Console()

REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "registry" / "models.json"


class Skill:
    """Model Registry — version and manage AI models."""

    def __init__(self, config=None):
        self.config = config or {}
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if REGISTRY_PATH.exists():
            self.registry = json.loads(REGISTRY_PATH.read_text())
        else:
            self.registry = {"models": {}, "deployed": {}}

    def _save(self):
        REGISTRY_PATH.write_text(json.dumps(self.registry, indent=2))

    def _model_id(self, name: str, version: str) -> str:
        return f"{name}:{version}"

    def register(self, name: str, version: str, model_type: str = "llm",
                 path: str = "", format: str = "gguf", size_mb: float = 0,
                 metrics: dict = None, description: str = "",
                 experiment_id: str = "", tags: list = None) -> str:
        """Register a new model version."""
        mid = self._model_id(name, version)
        if mid in self.registry["models"]:
            return f"⚠ Model {mid} already registered. Use action='update' to modify."

        model = {
            "id": mid,
            "name": name,
            "version": version,
            "type": model_type,
            "path": path,
            "format": format,
            "size_mb": size_mb,
            "metrics": metrics or {},
            "description": description,
            "experiment_id": experiment_id,
            "tags": tags or [],
            "status": "registered",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "deployed": False,
        }
        self.registry["models"][mid] = model
        self._save()
        return f"✅ Registered {mid} — {model_type} model, {size_mb}MB"

    def list_models(self, name: str = None, model_type: str = None) -> str:
        """List all registered models, optionally filtered."""
        models = list(self.registry["models"].values())
        if name:
            models = [m for m in models if m["name"] == name]
        if model_type:
            models = [m for m in models if m["type"] == model_type]

        if not models:
            return "No models registered."

        table = Table(title="🧠 Model Registry", show_lines=True)
        table.add_column("Model", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Size", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Deployed", style="blue")

        for m in models:
            deployed = "🟢 LIVE" if m.get("deployed") else "—"
            table.add_row(
                m["id"], m["type"], f"{m['size_mb']}MB",
                m["status"], deployed
            )
        console.print(table)
        return f"\n{len(models)} models registered."

    def get_model(self, name: str, version: str = None) -> str:
        """Get details for a specific model."""
        if version:
            mid = self._model_id(name, version)
            m = self.registry["models"].get(mid)
            if not m:
                return f"❌ Model {mid} not found."
        else:
            # Get latest version
            versions = [v for k, v in self.registry["models"].items() if v["name"] == name]
            if not versions:
                return f"❌ No models named '{name}'."
            m = max(versions, key=lambda x: x["version"])
        return json.dumps(m, indent=2)

    def compare(self, name1: str, version1: str, name2: str, version2: str) -> str:
        """Compare two model versions."""
        m1 = self.registry["models"].get(self._model_id(name1, version1))
        m2 = self.registry["models"].get(self._model_id(name2, version2))
        if not m1 or not m2:
            return f"❌ One or both models not found."

        lines = [f"📊 Model Comparison: {name1}:{version1} vs {name2}:{version2}\n"]
        all_keys = set(list(m1.get("metrics", {}).keys()) + list(m2.get("metrics", {}).keys()))
        for k in sorted(all_keys):
            v1 = m1.get("metrics", {}).get(k, "—")
            v2 = m2.get("metrics", {}).get(k, "—")
            diff = ""
            try:
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    diff = f" ({'+' if v2 > v1 else ''}{v2 - v1:.2f})"
            except:
                pass
            lines.append(f"  {k:25s}  {str(v1):>15s}  →  {str(v2):>15s}{diff}")
        lines.append(f"\n  Size:     {m1['size_mb']}MB  vs  {m2['size_mb']}MB")
        lines.append(f"  Format:   {m1['format']}  vs  {m2['format']}")
        return "\n".join(lines)

    def deploy(self, name: str, version: str, endpoint: str = "") -> str:
        """Mark a model as deployed (live)."""
        mid = self._model_id(name, version)
        m = self.registry["models"].get(mid)
        if not m:
            return f"❌ Model {mid} not found."

        # Undeploy previous version of same name
        for k, v in self.registry["models"].items():
            if v["name"] == name and v.get("deployed"):
                v["deployed"] = False
                v["status"] = "registered"

        m["deployed"] = True
        m["status"] = "deployed"
        m["endpoint"] = endpoint or f"/api/v1/models/{name}/predict"
        self.registry["deployed"][name] = mid
        self._save()
        return f"🚀 Deployed {mid} as {name} → {m['endpoint']}"

    def undeploy(self, name: str) -> str:
        """Undeploy a model."""
        mid = self.registry["deployed"].get(name)
        if not mid:
            return f"⚠ {name} is not deployed."
        self.registry["models"][mid]["deployed"] = False
        self.registry["models"][mid]["status"] = "registered"
        del self.registry["deployed"][name]
        self._save()
        return f"✅ Undeployed {name}"

    def delete(self, name: str, version: str) -> str:
        """Delete a model version."""
        mid = self._model_id(name, version)
        if mid not in self.registry["models"]:
            return f"❌ Model {mid} not found."
        if self.registry["models"][mid].get("deployed"):
            return f"⚠ Cannot delete deployed model. Undeploy first."
        del self.registry["models"][mid]
        self._save()
        return f"✅ Deleted {mid}"

    def get_deployed(self) -> str:
        """List all deployed models."""
        deployed = self.registry.get("deployed", {})
        if not deployed:
            return "No models currently deployed."
        lines = ["🟢 Deployed Models:"]
        for name, mid in deployed.items():
            m = self.registry["models"].get(mid, {})
            lines.append(f"  {name} → {mid} ({m.get('endpoint', '?')})")
        return "\n".join(lines)

    def run(self, args: dict) -> str:
        action = args.get("action", "list")

        if action == "register":
            return self.register(
                name=args.get("name", ""),
                version=args.get("version", "1.0.0"),
                model_type=args.get("type", "llm"),
                path=args.get("path", ""),
                format=args.get("format", "gguf"),
                size_mb=args.get("size_mb", 0),
                metrics=args.get("metrics", {}),
                description=args.get("description", ""),
                experiment_id=args.get("experiment_id", ""),
                tags=args.get("tags", []),
            )
        elif action == "list":
            return self.list_models(args.get("name"), args.get("type"))
        elif action == "get":
            return self.get_model(args.get("name", ""), args.get("version"))
        elif action == "compare":
            return self.compare(args.get("name1", ""), args.get("version1", ""),
                                args.get("name2", ""), args.get("version2", ""))
        elif action == "deploy":
            return self.deploy(args.get("name", ""), args.get("version", ""),
                               args.get("endpoint", ""))
        elif action == "undeploy":
            return self.undeploy(args.get("name", ""))
        elif action == "delete":
            return self.delete(args.get("name", ""), args.get("version", ""))
        elif action == "deployed":
            return self.get_deployed()
        else:
            return f"Unknown action: {action}\nAvailable: register, list, get, compare, deploy, undeploy, delete, deployed"
