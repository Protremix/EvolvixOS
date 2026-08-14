#!/usr/bin/env python3
"""Precision & Recall Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        tp = int(args.get("TP", 10))
        fp = int(args.get("FP", 2))
        fn = int(args.get("FN", 3))
        tn = int(args.get("TN", 85))
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        acc = (tp + tn) / (tp + tn + fp + fn)
        return {"precision": round(prec, 4), "recall": round(rec, 4), "accuracy": round(acc, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
