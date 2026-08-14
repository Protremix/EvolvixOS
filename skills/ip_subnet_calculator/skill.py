#!/usr/bin/env python3
"""IP Subnet Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import ipaddress
        cidr = args.get("cidr", "192.168.1.0/24")
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            return {
                "network": str(net.network_address),
                "netmask": str(net.netmask),
                "broadcast": str(net.broadcast_address),
                "num_hosts": net.num_addresses
            }
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
