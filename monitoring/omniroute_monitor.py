#!/usr/bin/env python3
"""
OmniRoute Inference Monitor — alerts when inference fails >3 times in a row.

Checks: Groq API, Ollama local, Gemini API
Alert: Sends notification via AgentMessage entity + logs to file
Runs as systemd timer every 60 seconds.
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime

STATE_FILE = "/opt/evolvixos/monitoring/omniroute_state.json"
LOG_FILE = "/opt/evolvixos/monitoring/omniroute_alerts.log"
ALERT_URL = "https://evolvixos.com/platform/api/fn/sendAlert"

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"consecutive_failures": 0, "last_success": None, "alerts_sent": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log(msg):
    ts = datetime.utcnow().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_groq():
    try:
        payload = json.dumps({
            "model": "openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_KEY}",
                "User-Agent": "EvolvixOS-Monitor/1.0"
            }
        )
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status == 200
    except Exception as e:
        log(f"Groq check failed: {e}")
        return False

def check_ollama():
    try:
        payload = json.dumps({
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
            "keep_alive": "30m",
            "options": {"num_predict": 1}
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status == 200
    except Exception as e:
        log(f"Ollama check failed: {e}")
        return False

def check_gemini():
    try:
        payload = json.dumps({"contents": [{"parts": [{"text": "ping"}]}]}).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_KEY}",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return "candidates" in data
    except Exception as e:
        log(f"Gemini check failed: {e}")
        return False

def send_alert(failures, details):
    """Send alert via multiple channels."""
    msg = f"⚠️ OmniRoute ALERT: {failures} consecutive inference failures! Details: {details}"
    log(f"ALERT: {msg}")
    
    # Try platform API
    try:
        payload = json.dumps({
            "message": msg,
            "severity": "critical",
            "source": "omniroute-monitor"
        }).encode()
        req = urllib.request.Request(ALERT_URL, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

def main():
    state = load_state()
    
    # Run health checks
    groq_ok = check_groq()
    ollama_ok = check_ollama()
    gemini_ok = check_gemini()
    
    all_ok = groq_ok or ollama_ok  # At least one inference path must work
    # Gemini is bonus
    
    results = f"groq={'✅' if groq_ok else '❌'} ollama={'✅' if ollama_ok else '❌'} gemini={'✅' if gemini_ok else '❌'}"
    
    if all_ok:
        if state["consecutive_failures"] > 0:
            log(f"RECOVERED after {state['consecutive_failures']} failures. {results}")
        state["consecutive_failures"] = 0
        state["last_success"] = datetime.utcnow().isoformat()
        log(f"OK: {results}")
    else:
        state["consecutive_failures"] += 1
        log(f"FAIL #{state['consecutive_failures']}: {results}")
        
        if state["consecutive_failures"] >= 3:
            send_alert(state["consecutive_failures"], results)
            state["alerts_sent"] += 1
    
    save_state(state)

if __name__ == "__main__":
    main()
