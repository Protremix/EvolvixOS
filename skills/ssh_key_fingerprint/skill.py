#!/usr/bin/env python3
"""SSH Key Fingerprint - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64, hashlib
        key_str = args.get("key", "")
        parts = key_str.split()
        if len(parts) >= 2:
            raw = base64.b64decode(parts[1])
            sha256_fp = base64.b64encode(hashlib.sha256(raw).digest()).decode('utf-8')
            return {"fingerprint_sha256": f"SHA256:{sha256_fp}"}
        return {"error": "invalid ssh key string"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
