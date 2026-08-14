#!/usr/bin/env python3
"""HTML to Markdown - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        html = args.get("html", "")
        if not html:
            return {"markdown": ""}
        md = html
        md = re.sub(r'<h1>(.*?)</h1>', r'# \1\n', md)
        md = re.sub(r'<h2>(.*?)</h2>', r'## \1\n', md)
        md = re.sub(r'<h3>(.*?)</h3>', r'### \1\n', md)
        md = re.sub(r'<strong>(.*?)</strong>|<b>(.*?)</b>', r'**\1\2**', md)
        md = re.sub(r'<em>(.*?)</em>|<i>(.*?)</i>', r'*\1\2*', md)
        md = re.sub(r'<code>(.*?)</code>', r'`\1`', md)
        md = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', md)
        md = re.sub(r'<li>(.*?)</li>', r'- \1\n', md)
        md = re.sub(r'<p>(.*?)</p>', r'\1\n\n', md)
        md = re.sub(r'<br\s*/?>', r'\n', md)
        md = re.sub(r'<[^>]+>', '', md)
        return {"markdown": md.strip()}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
