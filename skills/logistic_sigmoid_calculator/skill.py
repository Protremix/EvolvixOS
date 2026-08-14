#!/usr/bin/env python3
"""Sigmoid & Softmax Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        z = float(args.get("z", 0.0))
        sigmoid = 1.0 / (1.0 + math.exp(-z))
        return {"z": z, "sigmoid": round(sigmoid, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
