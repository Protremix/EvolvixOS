#!/usr/bin/env python3
"""SSL/TLS Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import ssl, socket
        domain = args.get("domain", "google.com")
        ctx = ssl.create_default_context()
        try:
            with socket.create_connection((domain, 443), timeout=3) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {"domain": domain, "subject": dict(x[0] for x in cert['subject']), "notAfter": cert['notAfter']}
        except Exception as e:
            return {"domain": domain, "error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
