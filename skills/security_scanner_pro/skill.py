#!/usr/bin/env python3
"""Security Scanner Pro - Semgrep + Bandit (LGPL/Apache 2.0) - 100% Free"""
import json, sys, subprocess, os, tempfile


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        path = args.get("path", "")
        code = args.get("code", "")
        scanner = args.get("scanner", "bandit")
        try:
            if code and not path:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                    f.write(code); path = f.name
            if scanner == "bandit":
                r = subprocess.run([sys.executable, "-m", "bandit", "-r", path, "-f", "json"], capture_output=True, text=True)
                data = json.loads(r.stdout) if r.stdout.strip() else {}
                return {"issues": data.get("results", []), "count": len(data.get("results", []))}
            elif scanner == "semgrep":
                r = subprocess.run(["semgrep", "--json", path], capture_output=True, text=True)
                data = json.loads(r.stdout) if r.stdout.strip() else {}
                return {"issues": data.get("results", []), "count": len(data.get("results", []))}
            return {"error": f"unknown scanner: {scanner}"}
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
