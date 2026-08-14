#!/usr/bin/env python3
"""CPU Load Analyzer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os
        try: load = os.getloadavg()
        except Exception: load = (0.5, 0.5, 0.5)
        return {"load_1min": load[0], "load_5min": load[1], "load_15min": load[2], "cores": os.cpu_count()}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
