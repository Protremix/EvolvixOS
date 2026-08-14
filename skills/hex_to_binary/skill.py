#!/usr/bin/env python3
"""Hex to Binary Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        hex_str = args.get("hex", "48656c6c6f")
        try:
            b = bytes.fromhex(hex_str)
            bits = bin(int.from_bytes(b, 'big'))[2:]
            return {"binary_bits": bits, "text": b.decode('utf-8', errors='ignore')}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
