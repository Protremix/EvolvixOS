#!/usr/bin/env python3
"""Service Status Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import socket
        host = args.get("host", "localhost")
        port = int(args.get("port", 80))
        s = socket.socket()
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            s.close()
            return {"service": f"{host}:{port}", "status": "UP"}
        except Exception:
            return {"service": f"{host}:{port}", "status": "DOWN"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
