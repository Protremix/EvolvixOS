#!/usr/bin/env python3
"""Password Risk Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        pwd = args.get("password", "")
        common = {"password", "123456", "qwerty", "admin", "welcome", "12345678"}
        is_common = pwd.lower() in common
        return {"password": pwd, "is_commonly_breached": is_common, "length": len(pwd)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
