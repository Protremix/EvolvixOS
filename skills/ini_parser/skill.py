#!/usr/bin/env python3
"""INI Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import configparser
        ini_text = args.get("ini", "")
        cp = configparser.ConfigParser()
        try:
            cp.read_string(ini_text)
            res = {sec: dict(cp[sec]) for sec in cp.sections()}
            return {"sections": res}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
