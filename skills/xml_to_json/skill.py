#!/usr/bin/env python3
"""XML to JSON - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import xml.etree.ElementTree as ET, json
        xml_text = args.get("xml", "")
        try:
            root = ET.fromstring(xml_text)
            d = {root.tag: {child.tag: child.text for child in root}}
            return {"json": json.dumps(d)}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
