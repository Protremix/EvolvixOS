#!/usr/bin/env python3
"""HTTP Status Code Lookup - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        code = int(args.get("code", 200))
        CODES = {200: "OK", 201: "Created", 301: "Moved Permanently", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 500: "Internal Server Error"}
        return {"code": code, "description": CODES.get(code, "Unknown Status Code")}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
