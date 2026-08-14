#!/usr/bin/env python3
"""One-Hot Encoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        labels = args.get("labels", ["cat", "dog", "cat", "bird"])
        vocab = sorted(list(set(labels)))
        encoded = [[1 if l == v else 0 for v in vocab] for l in labels]
        return {"vocabulary": vocab, "one_hot_matrix": encoded}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
