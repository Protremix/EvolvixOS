#!/usr/bin/env python3
"""Systemd Service Unit Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        name = args.get("name", "myapp")
        cmd = args.get("exec", "/usr/bin/python3 main.py")
        unit = f"[Unit]\nDescription={name}\nAfter=network.target\n\n[Service]\nExecStart={cmd}\nRestart=always\n\n[Install]\nWantedBy=multi-user.target"
        return {"service_file": unit}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
