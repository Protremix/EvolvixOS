#!/usr/bin/env python3
"""Port Scanner - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import socket
        host = args.get("host", "127.0.0.1")
        ports = args.get("ports", [80, 443, 22, 8080])
        open_ports = []
        for p in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((host, p)) == 0:
                open_ports.append(p)
            s.close()
        return {"host": host, "open_ports": open_ports}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
