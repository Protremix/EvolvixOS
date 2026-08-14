#!/usr/bin/env python3
"""Universal Adapter — Wrap ANY pip package as an EvolvixOS skill. 100% Free."""
import json, sys, subprocess, importlib


class Skill:
    """Execute any pip package function dynamically."""
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        package = args.get("package", "")
        function = args.get("function", "")
        func_args = args.get("args", [])
        func_kwargs = args.get("kwargs", {})
        if not package or not function:
            return {"error": "package and function required"}
        try:
            mod = importlib.import_module(package)
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], capture_output=True)
            mod = importlib.import_module(package)
        func = getattr(mod, function, None)
        if func is None:
            members = [m for m in dir(mod) if not m.startswith("_")]
            return {"error": f"Function '{function}' not found. Available: {members[:20]}"}
        result = func(*func_args, **func_kwargs)
        try:
            json.dumps(result)
            return {"result": result, "package": package, "function": function}
        except TypeError:
            return {"result": str(result), "package": package, "function": function}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
