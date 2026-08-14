#!/usr/bin/env python3
"""Timezone Lookup - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        city = args.get("city", "London").lower()
        TZS = {"london": "UTC+0", "paris": "UTC+1", "new york": "UTC-5", "tokyo": "UTC+9", "sydney": "UTC+10"}
        return {"city": city.capitalize(), "timezone": TZS.get(city, "UTC+0")}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
