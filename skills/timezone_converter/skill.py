#!/usr/bin/env python3
"""Timezone Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import datetime
        dt_str = args.get("datetime", "2026-08-14 12:00:00")
        from_offset = int(args.get("from_utc_offset_hours", 0))
        to_offset = int(args.get("to_utc_offset_hours", 2))
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        converted = dt + datetime.timedelta(hours=(to_offset - from_offset))
        return {"original": dt_str, "converted": converted.strftime("%Y-%m-%d %H:%M:%S")}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
