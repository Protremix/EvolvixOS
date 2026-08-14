#!/usr/bin/env python3
"""Service Status Checker — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import subprocess
        service = args.get("service", "")
        if not service:
            return {"error": "service required"}
        try:
            result = subprocess.run(["systemctl", "status", service], capture_output=True, text=True, timeout=10)
            active = "active (running)" in result.stdout
            return {"service": service, "active": active, "status": "running" if active else "stopped", "output": result.stdout[:1000]}
        except Exception as e:
            return {"error": str(e)}
