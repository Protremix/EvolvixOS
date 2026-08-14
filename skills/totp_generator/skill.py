#!/usr/bin/env python3
"""TOTP Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import time, hmac, hashlib, base64, struct
        secret = args.get("secret", "EvolvixOS")
        if not secret:
            return {"error": "secret required"}
        key = base64.b32encode(secret.encode()).rstrip(b"=")
        period = args.get("period", 30)
        digits = args.get("digits", 6)
        t = int(time.time() // period)
        msg = struct.pack(">Q", t)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = (struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF) % (10 ** digits)
        return {"code": str(code).zfill(digits), "period": period, "remaining": int(period - (time.time() % period)), "digits": digits}
