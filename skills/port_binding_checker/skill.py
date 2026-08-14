#!/usr/bin/env python3
"""Port Binding Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import socket
        port = int(args.get("port", 80))
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
            bound = False
        except Exception:
            bound = True
        finally:
            s.close()
        return {"port": port, "is_bound": bound}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
