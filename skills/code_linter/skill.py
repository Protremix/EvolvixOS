#!/usr/bin/env python3
"""Code Linter - Ruff (MIT) - 100% Free"""
import json, sys, subprocess, os, tempfile


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "check")
        path = args.get("file", "")
        code = args.get("code", "")
        try:
            if code and not path:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(code); path = f.name
            if action == "check":
                r = subprocess.run([sys.executable, "-m", "ruff", "check", path, "--output-format", "json"], capture_output=True, text=True)
                issues = json.loads(r.stdout) if r.stdout.strip() else []
                return {"issues": issues, "count": len(issues)}
            elif action == "fix":
                r = subprocess.run([sys.executable, "-m", "ruff", "check", path, "--fix"], capture_output=True, text=True)
                return {"output": r.stdout, "fixed": r.returncode == 0}
            elif action == "format":
                r = subprocess.run([sys.executable, "-m", "ruff", "format", path], capture_output=True, text=True)
                return {"output": r.stdout, "formatted": r.returncode == 0}
            return {"error": f"unknown: {action}"}
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
