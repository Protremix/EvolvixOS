#!/usr/bin/env python3
"""K-Nearest Neighbors (KNN) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        point = args.get("point", [1, 1])
        dataset = args.get("dataset", [([0, 0], "A"), ([2, 2], "B")])
        dists = [(math.sqrt(sum((a - b)**2 for a, b in zip(point, p))), label) for p, label in dataset]
        dists.sort()
        k = int(args.get("k", 1))
        top_k_labels = [label for _, label in dists[:k]]
        return {"predicted_label": top_k_labels[0]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
