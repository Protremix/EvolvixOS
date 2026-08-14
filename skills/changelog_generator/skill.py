#!/usr/bin/env python3
"""Changelog Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        commits = args.get("commits", ["feat: add oauth support", "fix: resolve memory leak in worker"])
        added = [c for c in commits if c.startswith("feat:")]
        fixed = [c for c in commits if c.startswith("fix:")]
        return {"markdown": f"## [Unreleased]\n### Added\n- {added}\n### Fixed\n- {fixed}"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
