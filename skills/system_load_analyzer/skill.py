#!/usr/bin/env python3
"""System Load Analyzer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os
        try: load = os.getloadavg()[0]
        except Exception: load = 1.2
        cores = os.cpu_count() or 4
        return {"load_average": load, "cores": cores, "overloaded": load > cores}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
