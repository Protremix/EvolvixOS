#!/usr/bin/env python3
"""TCP Ping Tool - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import socket, time
        host = args.get("host", "8.8.8.8")
        port = int(args.get("port", 53))
        start = time.perf_counter()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((host, port))
            s.close()
            latency = (time.perf_counter() - start) * 1000
            return {"host": host, "port": port, "latency_ms": round(latency, 2), "status": "UP"}
        except Exception as e:
            return {"host": host, "port": port, "status": "DOWN", "error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
