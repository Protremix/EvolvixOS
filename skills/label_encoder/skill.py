#!/usr/bin/env python3
"""Label Encoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        labels = args.get("labels", ["red", "blue", "green", "red"])
        vocab = sorted(list(set(labels)))
        mapping = {v: i for i, v in enumerate(vocab)}
        encoded = [mapping[l] for l in labels]
        return {"vocabulary": vocab, "encoded_indices": encoded}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
