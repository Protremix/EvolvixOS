#!/usr/bin/env python3
"""RSS Feed Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import xml.etree.ElementTree as ET
        rss_xml = args.get("rss", "<rss><channel><item><title>News 1</title></item></channel></rss>")
        try:
            root = ET.fromstring(rss_xml)
            titles = [elem.text for elem in root.findall(".//item/title")]
            return {"titles": titles, "count": len(titles)}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
