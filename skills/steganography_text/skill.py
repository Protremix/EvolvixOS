#!/usr/bin/env python3
"""Text Steganography - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cover = args.get("cover", "Hello World")
        secret = args.get("secret", "hi")
        # Encode secret using zero-width spaces
        bits = "".join(f"{ord(c):08b}" for c in secret)
        zw = "".join("\u200b" if b == "0" else "\u200c" for b in bits)
        return {"stego_text": cover + zw, "bits_hidden": len(bits)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
