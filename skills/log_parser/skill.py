#!/usr/bin/env python3
"""Nginx/Apache Log Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        line = args.get("line", '127.0.0.1 - - [14/Aug/2026:12:00:00 +0000] "GET /index.html HTTP/1.1" 200 1024')
        pattern = r'^(\S+) \S+ \S+ \[(.*?)\] "(\S+) (\S+) \S+" (\d+) (\d+|-)'
        m = re.match(pattern, line)
        if m:
            return {
                "ip": m.group(1),
                "timestamp": m.group(2),
                "method": m.group(3),
                "path": m.group(4),
                "status": int(m.group(5)),
                "size_bytes": int(m.group(6)) if m.group(6) != "-" else 0
            }
        return {"error": "log line format unmatched"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
