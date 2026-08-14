#!/usr/bin/env python3
"""Text Hasher — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import hashlib
        text = args.get("text", "")
        algo = args.get("algorithm", "sha256")
        if not text:
            return {"error": "text required"}
        try:
            h = hashlib.new(algo)
            h.update(text.encode())
            return {"hash": h.hexdigest(), "algorithm": algo, "input": text[:50]}
        except Exception as e:
            return {"error": str(e)}
