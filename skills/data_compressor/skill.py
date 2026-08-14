#!/usr/bin/env python3
"""Data Compressor - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import gzip, bz2, lzma, base64
        algo = args.get("algo", "gzip")
        action = args.get("action", "compress")
        data = args.get("data", "")
        if action == "compress":
            raw = data.encode('utf-8')
            if algo == "bz2": comp = bz2.compress(raw)
            elif algo == "lzma": comp = lzma.compress(raw)
            else: comp = gzip.compress(raw)
            return {"compressed_b64": base64.b64encode(comp).decode('utf-8'), "original_size": len(raw), "compressed_size": len(comp)}
        else:
            raw = base64.b64decode(data.encode('utf-8'))
            if algo == "bz2": decomp = bz2.decompress(raw)
            elif algo == "lzma": decomp = lzma.decompress(raw)
            else: decomp = gzip.decompress(raw)
            return {"decompressed": decomp.decode('utf-8')}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
