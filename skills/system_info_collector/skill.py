#!/usr/bin/env python3
"""System Info Collector - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import platform, sys
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version.split()[0],
            "architecture": platform.machine()
        }

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
