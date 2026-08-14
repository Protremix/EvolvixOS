#!/usr/bin/env python3
"""JSON Schema Validator Light - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        obj = args.get("json", {})
        schema = args.get("schema", {"required": []})
        missing = [f for f in schema.get("required", []) if f not in obj]
        return {"valid": len(missing) == 0, "missing_required_fields": missing}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
