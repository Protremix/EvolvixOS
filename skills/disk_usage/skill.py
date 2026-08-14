#!/usr/bin/env python3
"""Disk Usage Analyzer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import os, shutil
        path = args.get("path", "/")
        try:
            total, used, free = shutil.disk_usage(path)
            return {
                "path": path,
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "total_gb": round(total / 1073741824, 2),
                "used_gb": round(used / 1073741824, 2),
                "free_gb": round(free / 1073741824, 2),
                "percent_used": round(used / total * 100, 1) if total > 0 else 0,
            }
        except Exception as e:
            return {"error": str(e)}
