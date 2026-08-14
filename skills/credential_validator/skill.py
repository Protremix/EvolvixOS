#!/usr/bin/env python3
"""Credential Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        username = args.get("username", "")
        valid_user = bool(re.match(r'^[a-zA-Z0-9_-]{3,20}$', username))
        return {"username": username, "valid_username": valid_user}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
