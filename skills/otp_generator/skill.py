#!/usr/bin/env python3
"""OTP Generator (TOTP) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import hmac, hashlib, time, base64, struct
        secret = args.get("secret", "JBSWY3DPEHPK3PXP")
        interval = int(args.get("interval", 30))
        try:
            key = base64.b32decode(secret.upper() + '=' * (-len(secret) % 8))
            t = int(time.time()) // interval
            msg = struct.pack(">Q", t)
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0f
            code = (struct.unpack(">I", h[offset:offset+4])[0] & 0x7fffffff) % 1000000
            return {"totp": f"{code:06d}", "time_remaining": interval - (int(time.time()) % interval)}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
