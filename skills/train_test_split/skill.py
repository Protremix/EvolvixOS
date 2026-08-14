#!/usr/bin/env python3
"""Train/Test Splitter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import random
        data = args.get("data", [])
        test_size = args.get("test_size", 0.2)
        shuffle = args.get("shuffle", True)
        seed = args.get("seed", 42)
        if not data:
            return {"error": "data required"}
        n = len(data)
        indices = list(range(n))
        if shuffle:
            random.seed(seed)
            random.shuffle(indices)
        split = int(n * (1 - test_size))
        train_idx = indices[:split]
        test_idx = indices[split:]
        return {"train": [data[i] for i in train_idx], "test": [data[i] for i in test_idx], "train_size": len(train_idx), "test_size": len(test_idx), "split_ratio": test_size}
