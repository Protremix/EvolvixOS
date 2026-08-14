#!/usr/bin/env python3
"""Confusion Matrix - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        y_true = args.get("y_true", [1, 0, 1, 1, 0])
        y_pred = args.get("y_pred", [1, 0, 1, 0, 0])
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
        return {"TP": tp, "FP": fp, "TN": tn, "FN": fn}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
