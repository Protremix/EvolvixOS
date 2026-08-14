#!/usr/bin/env python3
"""Random Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import random
        action = args.get("action", "number")
        min_val = args.get("min", 0)
        max_val = args.get("max", 100)
        count = args.get("count", 1)
        seed = args.get("seed", None)
        if seed is not None:
            random.seed(seed)
        if action == "number":
            result = random.randint(min_val, max_val)
        elif action == "float":
            result = random.uniform(min_val, max_val)
        elif action == "list":
            result = [random.randint(min_val, max_val) for _ in range(count)]
        elif action == "choice":
            items = args.get("items", [])
            result = random.choice(items) if items else None
        elif action == "shuffle":
            items = args.get("items", [])
            result = items[:]
            random.shuffle(result)
        elif action == "sample":
            items = args.get("items", [])
            result = random.sample(items, min(count, len(items))) if items else []
        else:
            result = random.randint(min_val, max_val)
        return {"result": result, "action": action}
