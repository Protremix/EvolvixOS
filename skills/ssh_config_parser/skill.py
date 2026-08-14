#!/usr/bin/env python3
"""SSH Config Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        content = args.get("config", "Host server1\n  HostName 10.0.0.1\n  User admin")
        hosts = []
        curr = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("Host "):
                if curr: hosts.append(curr)
                curr = {"host": line.split()[1]}
            elif curr and " " in line:
                k, v = line.split(None, 1)
                curr[k.lower()] = v
        if curr: hosts.append(curr)
        return {"hosts": hosts}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
