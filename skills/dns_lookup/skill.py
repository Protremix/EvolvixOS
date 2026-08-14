#!/usr/bin/env python3
"""DNS Lookup - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import socket
        domain = args.get("domain", "google.com")
        try:
            info = socket.gethostbyname_ex(domain)
            return {"domain": domain, "canonical_name": info[0], "aliases": info[1], "ips": info[2]}
        except Exception as e:
            return {"domain": domain, "error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
