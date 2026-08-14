#!/usr/bin/env python3
"""Outlier Detector - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        data = sorted(args.get("data", [10, 12, 11, 15, 100, 11, 13]))
        q1 = data[len(data) // 4]
        q3 = data[(3 * len(data)) // 4]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = [x for x in data if x < lower or x > upper]
        return {"outliers": outliers, "lower_bound": lower, "upper_bound": upper}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
