#!/usr/bin/env python3
"""Config File Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cfg = args.get("config", {"host": "localhost", "port": 80})
        req = args.get("required_keys", ["host", "port"])
        missing = [k for k in req if k not in cfg]
        return {"is_valid": len(missing) == 0, "missing_keys": missing}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
