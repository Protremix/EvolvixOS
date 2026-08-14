#!/usr/bin/env python3
"""GeoJSON Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import json
        geojson = args.get("geojson", {})
        if isinstance(geojson, str):
            try: geojson = json.loads(geojson)
            except Exception: return {"is_valid": False, "error": "Invalid JSON"}
        valid = "type" in geojson and ("coordinates" in geojson or "features" in geojson or "geometry" in geojson)
        return {"is_valid": valid, "type": geojson.get("type")}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
