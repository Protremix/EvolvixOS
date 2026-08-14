#!/usr/bin/env python3
"""Timezone Offset Difference - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        tz1_offset = int(args.get("tz1_offset_hours", -5))
        tz2_offset = int(args.get("tz2_offset_hours", 1))
        diff = tz2_offset - tz1_offset
        return {"tz1_offset": tz1_offset, "tz2_offset": tz2_offset, "hour_difference": diff}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
