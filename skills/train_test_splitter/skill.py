#!/usr/bin/env python3
"""Train/Test Splitter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        data = args.get("data", list(range(10)))
        test_ratio = float(args.get("test_ratio", 0.2))
        split_idx = int(len(data) * (1 - test_ratio))
        return {"train": data[:split_idx], "test": data[split_idx:]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
