#!/usr/bin/env python3
"""Package Version Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        v1 = args.get("v1", "1.2.3")
        v2 = args.get("v2", "1.3.0")
        t1 = tuple(map(int, v1.split(".")))
        t2 = tuple(map(int, v2.split(".")))
        return {"v1": v1, "v2": v2, "v1_older_than_v2": t1 < t2, "equal": t1 == t2}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
