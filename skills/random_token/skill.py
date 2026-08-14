#!/usr/bin/env python3
"""Random Token Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import secrets
        nbytes = int(args.get("nbytes", 32))
        fmt = args.get("format", "hex")
        if fmt == "url": tok = secrets.token_urlsafe(nbytes)
        else: tok = secrets.token_hex(nbytes)
        return {"token": tok, "bytes": nbytes, "format": fmt}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
