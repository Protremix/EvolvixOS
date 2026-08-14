#!/usr/bin/env python3
"""Bash Script Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        script = args.get("script", "#!/bin/bash\necho 'hello'")
        has_shebang = script.startswith("#!/bin/bash") or script.startswith("#!/bin/sh")
        return {"has_shebang": has_shebang, "is_valid": has_shebang}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
