#!/usr/bin/env python3
"""IP Range Expander - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import ipaddress
        cidr = args.get("cidr", "192.168.1.0/29")
        net = ipaddress.ip_network(cidr, strict=False)
        ips = [str(ip) for ip in net.hosts()]
        return {"ips": ips, "count": len(ips)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
