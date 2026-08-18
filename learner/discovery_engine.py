#!/usr/bin/env python3
"""
EvolvixOS GitHub Discovery Engine
Automatically discovers new AI tools, libraries, and frameworks from GitHub.
Adds discovered tools to the EvolvixOS model registry.
"""
import json, os, time, sqlite3, hashlib
from datetime import datetime
import urllib.request, urllib.parse

# ─── Config ───
DISCOVERY_DB = "/opt/evolvixos/learner/discovery.db"
REGISTRY_DB = "/opt/evolvixos/models/registry.db"
SCAN_INTERVAL = 3600  # 1 hour between scans
MAX_TOOLS_PER_SCAN = 5
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN_6", "")

DISCOVERY_CATEGORIES = {
    "llm_text": ["llm", "language-model", "text-generation", "inference", "transformer"],
    "image_generation": ["stable-diffusion", "image-generation", "diffusion", "gan"],
    "video_generation": ["video-generation", "text-to-video", "video-model"],
    "speech_voice": ["tts", "speech-synthesis", "voice-cloning"],
    "music_audio": ["music-generation", "audio-model", "musicgen"],
    "vision_multimodal": ["vision-language", "multimodal", "vlm"],
    "ai_coding": ["code-generation", "code-model", "copilot"],
    "rag_agents": ["rag", "agent-framework", "autonomous-agent"],
    "frameworks": ["ai-framework", "ml-framework", "inference-engine"],
    "local_engines": ["local-llm", "ollama", "llama.cpp", "onnx"],
}

def init_db():
    os.makedirs(os.path.dirname(DISCOVERY_DB), exist_ok=True)
    conn = sqlite3.connect(DISCOVERY_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS discovered_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, full_name TEXT, description TEXT,
        category TEXT, url TEXT, stars INTEGER DEFAULT 0,
        language TEXT, topics TEXT, first_seen TEXT, last_seen TEXT,
        status TEXT DEFAULT 'new', sha256 TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS scan_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, category TEXT, found INTEGER, added INTEGER, status TEXT
    )""")
    conn.commit()
    conn.close()

def github_search(query, sort="stars", per_page=10):
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}&sort={sort}&order=desc&per_page={per_page}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  GitHub API error: {e}")
        return {"items": []}

def is_already_known(name, full_name):
    conn = sqlite3.connect(DISCOVERY_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM discovered_tools WHERE name=? OR full_name=?", (name.lower(), full_name.lower()))
    found = c.fetchone() is not None
    conn.close()
    return found

def categorize_tool(name, description, topics):
    text = f"{name} {description} {' '.join(topics)}".lower()
    best_cat, best_score = None, 0
    for cat, keywords in DISCOVERY_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score, best_cat = score, cat
    return best_cat or "frameworks"

def add_to_registry(name, full_name, description, category, url, stars, language, topics):
    try:
        conn = sqlite3.connect(REGISTRY_DB)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS model_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, category TEXT, description TEXT, source TEXT,
            engine TEXT DEFAULT 'github-discovered', status TEXT DEFAULT 'discovered',
            stars INTEGER DEFAULT 0, language TEXT, topics TEXT, url TEXT, created_date TEXT
        )""")
        c.execute("SELECT id FROM model_registry WHERE name=? AND category=?", (name, category))
        if c.fetchone():
            conn.close()
            return False
        c.execute("""INSERT INTO model_registry
            (name, category, description, source, engine, status, stars, language, topics, url, created_date)
            VALUES (?, ?, ?, 'github-discovery', 'github-discovered', 'discovered', ?, ?, ?, ?, ?)""",
            (name, category, description, stars, language, json.dumps(topics), url, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  Registry error: {e}")
        return False

def scan_category(category, keywords):
    query = " ".join(keywords[:3]) + " stars:>100 pushed:>2024-01-01"
    results = github_search(query, per_page=15)
    found, added = 0, 0
    for item in results.get("items", []):
        name = item["name"]
        full_name = item["full_name"]
        desc = (item.get("description") or "")[:500]
        url = item["html_url"]
        stars = item.get("stargazers_count", 0)
        lang = item.get("language", "Unknown")
        topics = item.get("topics", [])
        if is_already_known(name, full_name):
            continue
        found += 1
        cat = categorize_tool(name, desc, topics)
        conn = sqlite3.connect(DISCOVERY_DB)
        c = conn.cursor()
        sha = hashlib.sha256(f"{full_name}{datetime.now()}".encode()).hexdigest()[:16]
        try:
            c.execute("""INSERT INTO discovered_tools
                (name, full_name, description, category, url, stars, language, topics, first_seen, last_seen, status, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
                (name.lower(), full_name.lower(), desc, cat, url, stars, lang,
                 json.dumps(topics), datetime.now().isoformat(), datetime.now().isoformat(), sha))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
        if add_to_registry(name, full_name, desc, cat, url, stars, lang, topics):
            added += 1
            print(f"  + {name} ({cat}, {stars} stars) -> registry")
        if added >= MAX_TOOLS_PER_SCAN:
            break
    conn = sqlite3.connect(DISCOVERY_DB)
    c = conn.cursor()
    c.execute("INSERT INTO scan_log (timestamp, category, found, added, status) VALUES (?, ?, ?, ?, 'ok')",
              (datetime.now().isoformat(), category, found, added))
    conn.commit()
    conn.close()
    return found, added

def run_scan():
    print(f"\n{'='*60}")
    print(f"EvolvixOS GitHub Discovery Engine - Scan {datetime.now()}")
    print(f"{'='*60}")
    total_found, total_added = 0, 0
    for cat, keywords in DISCOVERY_CATEGORIES.items():
        print(f"\nScanning [{cat}]...")
        found, added = scan_category(cat, keywords)
        total_found += found
        total_added += added
        time.sleep(2)
    print(f"\n{'='*60}")
    print(f"Scan complete: {total_found} found, {total_added} added to registry")
    print(f"{'='*60}")
    return total_found, total_added

if __name__ == "__main__":
    init_db()
    print("EvolvixOS GitHub Discovery Engine started")
    print(f"Scan interval: {SCAN_INTERVAL}s ({SCAN_INTERVAL//60} min)")
    print(f"GitHub token: {'configured' if GITHUB_TOKEN else 'NOT SET (rate limited)'}")
    while True:
        try:
            run_scan()
        except Exception as e:
            print(f"Scan error: {e}")
        print(f"\nNext scan in {SCAN_INTERVAL//60} minutes...")
        time.sleep(SCAN_INTERVAL)
