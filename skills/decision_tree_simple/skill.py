#!/usr/bin/env python3
"""Decision Tree Evaluator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        labels = args.get("labels", [1, 1, 0, 0])
        p1 = labels.count(1) / len(labels) if labels else 0
        p0 = labels.count(0) / len(labels) if labels else 0
        gini = 1.0 - (p1**2 + p0**2)
        entropy = - (p1 * math.log2(p1) if p1 else 0) - (p0 * math.log2(p0) if p0 else 0)
        return {"gini_impurity": round(gini, 4), "entropy": round(entropy, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
