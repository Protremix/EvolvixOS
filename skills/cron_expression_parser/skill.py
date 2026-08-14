#!/usr/bin/env python3
"""Cron Expression Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        expr = args.get("cron", "*/5 * * * *")
        parts = expr.split()
        if len(parts) != 5: return {"error": "Invalid cron expression"}
        return {"minute": parts[0], "hour": parts[1], "day_of_month": parts[2], "month": parts[3], "day_of_week": parts[4]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
