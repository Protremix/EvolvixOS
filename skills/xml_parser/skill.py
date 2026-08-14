#!/usr/bin/env python3
"""XML Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import xml.etree.ElementTree as ET
        xml_text = args.get("xml", "")
        try:
            root = ET.fromstring(xml_text)
            def elem_to_dict(elem):
                d = {elem.tag: {} if elem.attrib else None}
                children = list(elem)
                if children:
                    dd = {}
                    for child in children:
                        cd = elem_to_dict(child)
                        for k, v in cd.items():
                            if k in dd:
                                if not isinstance(dd[k], list): dd[k] = [dd[k]]
                                dd[k].append(v)
                            else: dd[k] = v
                    d[elem.tag] = dd
                elif elem.text and elem.text.strip():
                    d[elem.tag] = elem.text.strip()
                return d
            return {"result": elem_to_dict(root)}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
