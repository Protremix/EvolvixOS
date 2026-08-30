#!/usr/bin/env python3
"""Paddle webhook adapter tests for EvolvixOS.

Covers signature verification (the security-critical part) and event->fulfilment
mapping. Runs against a throwaway copy of users.db; never touches live data.

Usage:  python3 test_paddle_webhook.py [/path/to/auth_api.py]
"""
import hashlib
import hmac
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import time

AUTH_API = sys.argv[1] if len(sys.argv) > 1 else "/opt/evolvixos/auth/auth_api.py"
LIVE_DB = "/opt/evolvixos/auth/users.db"
TEST_DB = "/tmp/test_paddle_users.db"
SECRET = "pdl_ntfset_01testsecretvalue"

spec = importlib.util.spec_from_file_location("authmod", AUTH_API)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

shutil.copy(LIVE_DB, TEST_DB)
m.DB_PATH = TEST_DB
m.PADDLE_WEBHOOK_SECRET = SECRET

PASS = FAIL = 0


def chk(label, got, want):
    global PASS, FAIL
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + label + (
        "" if ok else f"\n          got={got!r}\n         want={want!r}"))
    if ok:
        PASS += 1
    else:
        FAIL += 1


def sign(body_bytes, secret=SECRET, ts=None):
    ts = str(int(time.time())) if ts is None else str(ts)
    sig = hmac.new(secret.encode(), ts.encode() + b":" + body_bytes,
                   hashlib.sha256).hexdigest()
    return f"ts={ts};h1={sig}"


# -- fixtures ---------------------------------------------------------------
conn = sqlite3.connect(TEST_DB)
c = conn.cursor()
c.execute("INSERT INTO users (email, password_hash, created_date) VALUES (?,?,?)",
          ("paddletest@x.dev", "x", m._now()))
UID = c.lastrowid
free = c.execute("SELECT id FROM plans WHERE name='Free'").fetchone()[0]
c.execute("INSERT INTO subscriptions (user_id, plan_id, status, billing_cycle, "
          "credits_remaining, credits_used, created_date, updated_date) "
          "VALUES (?,?,?,?,?,0,?,?)",
          (UID, free, "active", "monthly", 100, m._now(), m._now()))
conn.commit()
conn.close()


def state():
    cn = sqlite3.connect(TEST_DB)
    r = cn.execute("SELECT p.name, s.credits_remaining, s.billing_cycle "
                   "FROM subscriptions s JOIN plans p ON s.plan_id=p.id "
                   "WHERE s.user_id=? AND s.status='active'", (UID,)).fetchone()
    cn.close()
    return r


print("\n-- signature verification --")
body = json.dumps({"event_type": "transaction.completed", "data": {}}).encode()

chk("valid signature accepted",
    m.verify_paddle_signature(body, sign(body)), (True, "ok"))
chk("tampered body rejected",
    m.verify_paddle_signature(body + b" ", sign(body))[1], "signature_mismatch")
chk("wrong secret rejected",
    m.verify_paddle_signature(body, sign(body, secret="pdl_ntfset_wrong"))[1],
    "signature_mismatch")
chk("stale timestamp rejected (replay)",
    m.verify_paddle_signature(body, sign(body, ts=int(time.time()) - 600))[1],
    "timestamp_out_of_tolerance")
chk("future timestamp rejected",
    m.verify_paddle_signature(body, sign(body, ts=int(time.time()) + 600))[1],
    "timestamp_out_of_tolerance")
chk("malformed header rejected",
    m.verify_paddle_signature(body, "garbage")[1], "malformed_header")
chk("missing h1 rejected",
    m.verify_paddle_signature(body, "ts=1700000000")[1], "malformed_header")
chk("non-numeric ts rejected",
    m.verify_paddle_signature(body, "ts=abc;h1=deadbeef")[1], "bad_timestamp")
chk("empty header rejected",
    m.verify_paddle_signature(body, "")[1], "missing_signature_or_body")
chk("unconfigured secret fails closed",
    m.verify_paddle_signature(body, sign(body), secret="")[1],
    "no_secret_configured")
other = json.dumps({"event_type": "transaction.completed", "data": {"x": 1}}).encode()
chk("cross-body signature reuse rejected",
    m.verify_paddle_signature(body, sign(other))[1], "signature_mismatch")

print("\n-- event mapping --")
sub_evt = {"event_type": "transaction.completed",
           "data": {"id": "txn_001", "custom_data": {
               "user_id": str(UID), "type": "subscription",
               "plan": "Pro", "cycle": "monthly"}}}
chk("subscription event maps",
    m.paddle_event_to_fulfilment(sub_evt),
    {"kind": "subscription", "user_id": UID, "charge_id": "txn_001",
     "plan": "Pro", "cycle": "monthly", "credits": 0, "provider": "paddle"})

chk("cancel event maps",
    m.paddle_event_to_fulfilment({"event_type": "subscription.canceled",
                                  "data": {"custom_data": {"user_id": str(UID)}}}),
    {"kind": "cancel", "user_id": UID, "provider": "paddle"})

chk("unrelated event ignored",
    m.paddle_event_to_fulfilment({"event_type": "product.updated", "data": {}}), None)
chk("transaction without type ignored",
    m.paddle_event_to_fulfilment({"event_type": "transaction.completed",
                                  "data": {"custom_data": {"user_id": "1"}}}), None)
chk("missing custom_data ignored",
    m.paddle_event_to_fulfilment({"event_type": "transaction.completed",
                                  "data": {"id": "txn_x"}}), None)
chk("non-numeric user_id degrades to 0",
    m.paddle_event_to_fulfilment({"event_type": "subscription.canceled",
                                  "data": {"custom_data": {"user_id": "abc"}}})["user_id"], 0)

print("\n-- end-to-end fulfilment --")
chk("baseline Free/100", state(), ("Free", 100, "monthly"))

m.apply_payment_event(**m.paddle_event_to_fulfilment(sub_evt))
chk("Pro subscription applied", state(), ("Pro", 10000, "monthly"))

credits_evt = {"event_type": "transaction.completed",
               "data": {"id": "txn_002", "custom_data": {
                   "user_id": str(UID), "type": "credits", "credits": "5000"}}}
m.apply_payment_event(**m.paddle_event_to_fulfilment(credits_evt))
chk("5000-credit pack applied", state(), ("Pro", 15000, "monthly"))

cn = sqlite3.connect(TEST_DB)
desc = cn.execute("SELECT description FROM credit_transactions WHERE user_id=? "
                  "ORDER BY id DESC LIMIT 1", (UID,)).fetchone()[0]
cn.close()
chk("ledger credits Paddle", desc, "Purchased 5000 credits via Paddle")

yearly = {"event_type": "transaction.completed",
          "data": {"id": "txn_003", "custom_data": {
              "user_id": str(UID), "type": "subscription",
              "plan": "Team", "cycle": "yearly"}}}
m.apply_payment_event(**m.paddle_event_to_fulfilment(yearly))
chk("yearly Team applied", state(), ("Team", 50000, "yearly"))

m.apply_payment_event(**m.paddle_event_to_fulfilment(
    {"event_type": "subscription.canceled",
     "data": {"custom_data": {"user_id": str(UID)}}}))
chk("cancel downgrades to Free", state(), ("Free", 100, "yearly"))

os.remove(TEST_DB)
print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
