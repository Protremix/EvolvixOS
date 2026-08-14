#!/usr/bin/env python3
"""Pip Package Info — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import subprocess
        action = args.get("action", "list")
        if action == "list":
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], capture_output=True, text=True)
            import json
            packages = json.loads(result.stdout)
            return {"packages": packages, "count": len(packages)}
        elif action == "info":
            name = args.get("package", "")
            if not name:
                return {"error": "package required"}
            result = subprocess.run([sys.executable, "-m", "pip", "show", name], capture_output=True, text=True)
            info = {}
            for line in result.stdout.split("\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    info[k.strip()] = v.strip()
            return {"info": info}
        elif action == "outdated":
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated", "--format=json"], capture_output=True, text=True)
            import json
            outdated = json.loads(result.stdout) if result.stdout.strip() else []
            return {"outdated": outdated, "count": len(outdated)}
        return {"error": f"unknown: {action}"}
