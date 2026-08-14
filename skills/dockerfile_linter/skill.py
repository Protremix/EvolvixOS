#!/usr/bin/env python3
"""Dockerfile Linter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        content = args.get("dockerfile", "FROM ubuntu:latest\nRUN apt-get update")
        issues = []
        if ":latest" in content: issues.append("Avoid using 'latest' tag for base image.")
        if "apt-get install" in content and "-y" not in content: issues.append("Use -y flag with apt-get install.")
        return {"is_valid": len(issues) == 0, "issues": issues}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
