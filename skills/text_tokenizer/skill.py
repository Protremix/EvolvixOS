#!/usr/bin/env python3
"""Text Tokenizer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        method = args.get("method", "word")
        if not text:
            return {"error": "text required"}
        if method == "word":
            tokens = re.findall(r'\b\w+\b', text.lower())
        elif method == "char":
            tokens = list(text)
        elif method == "sentence":
            tokens = re.split(r'(?<=[.!?])\s+', text)
        elif method == "subword":
            tokens = re.findall(r'\b\w+\b|\W+', text)
        else:
            tokens = text.split()
        return {"tokens": tokens, "count": len(tokens), "method": method}
