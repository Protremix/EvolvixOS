#!/usr/bin/env python3
"""Simple Linear Regression - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        x = args.get("x", [1, 2, 3, 4, 5])
        y = args.get("y", [2, 4, 5, 4, 5])
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den = sum((xi - mean_x)**2 for xi in x)
        m = num / den if den else 0
        b = mean_y - m * mean_x
        return {"slope_m": round(m, 4), "intercept_b": round(b, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
