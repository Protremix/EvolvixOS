#!/usr/bin/env python3
"""Data Decompressor — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import gzip, bz2, lzma, base64
        text = args.get("text", "")
        algo = args.get("algorithm", "gzip")
        if not text:
            return {"error": "text required"}
        data = base64.b64decode(text)
        if algo == "gzip":
            decompressed = gzip.decompress(data)
        elif algo == "bz2":
            decompressed = bz2.decompress(data)
        elif algo == "lzma":
            decompressed = lzma.decompress(data)
        else:
            return {"error": f"unknown: {algo}"}
        return {"text": decompressed.decode(), "size": len(decompressed)}
