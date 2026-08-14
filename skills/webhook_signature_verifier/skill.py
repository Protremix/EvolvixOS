#!/usr/bin/env python3
"""Webhook Signature Verifier - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import hmac, hashlib
        secret = args.get("secret", "whsec_123").encode('utf-8')
        payload = args.get("payload", "{}").encode('utf-8')
        signature = args.get("signature", "")
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return {"valid": hmac.compare_digest(expected, signature), "expected": expected}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
