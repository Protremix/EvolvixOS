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
    
def sync_openclaw_repo():
    """Sync the OpenClaw and API Mega List repos to keep the API directory up to date."""
    import subprocess
    import hashlib
    import re as re_mod
    import json as json_mod
    from datetime import datetime, timezone

    repos = [
        ("https://github.com/cporter202/openclaw-api-list.git", "/opt/evolvixos/openclaw-api-list", "openclaw-api-list"),
        ("https://github.com/cporter202/API-mega-list.git", "/opt/evolvixos/API-mega-list", "api-mega-list"),
        ("https://github.com/cporter202/ai-agent-tools.git", "/opt/evolvixos/ai-agent-tools", "ai-agent-tools"),
        ("https://github.com/cporter202/lovable-for-beginners.git", "/opt/evolvixos/lovable-for-beginners", "lovable-for-beginners"),
        ("https://github.com/open-free-llm-api/awesome-freellm-apis.git", "/opt/evolvixos/awesome-freellm-apis", "awesome-freellm-apis"),
        ("https://github.com/ShaikhWarsi/free-ai-tools.git", "/opt/evolvixos/free-ai-tools", "free-ai-tools"),
        ("https://github.com/saurav-z/free-image-generation-api.git", "/opt/evolvixos/free-image-generation-api", "free-image-generation-api"),
    ]

    CATEGORY_MAP = {
        "agents-apis": "Agent APIs",
        "ai-apis": "AI APIs",
        "automation-apis": "Automation APIs",
        "business-apis": "Business APIs",
        "developer-tools-apis": "Developer Tools APIs",
        "ecommerce-apis": "E-commerce APIs",
        "education-apis": "Education APIs",
        "for-creators-apis": "Creator APIs",
        "games-apis": "Games APIs",
        "integrations-apis": "Integration APIs",
        "jobs-apis": "Jobs APIs",
        "lead-generation-apis": "Lead Generation APIs",
        "marketing-apis": "Marketing APIs",
        "mcp-servers-apis": "MCP Servers",
        "news-apis": "News APIs",
        "open-source-apis": "Open Source APIs",
        "other-apis": "Other APIs",
        "real-estate-apis": "Real Estate APIs",
        "seo-tools-apis": "SEO Tools APIs",
        "social-media-apis": "Social Media APIs",
        "sports-apis": "Sports APIs",
        "travel-apis": "Travel APIs",
        "videos-apis": "Video APIs",
        "00-featured-apis": "Featured APIs",
    }

    # Section mapping for repos with single README format (ai-agent-tools)
    SECTION_MAP = {
        "Editor's Choice": "AI Editor's Choice",
        "AI Text": "AI Text Tools",
        "Code with AI": "AI Code Tools",
        "Generative AI Images": "AI Image Tools",
        "Generative AI Video": "AI Video Tools",
        "Generative AI Audio": "AI Audio Tools",
        "AI Tools for Marketing": "AI Marketing Tools",
        "AI Phone Call Agents": "AI Phone Agents",
        "Other AI Tools": "Other AI Tools",
        "Learning Resources": "AI Learning Resources",
    }
    SKIP_SECTIONS = ["Contents", "Featured Monthly", "Feature Set", "Perfect For",
                      "Additional Features", "Contributing", "License", "Acknowledgments",
                      "Follow Me on Facebook"]

    ROW_PATTERN = re_mod.compile(
        r'\\|\\s*\\[([^\\]]+)\\]\\(([^)]+)\\)\\s*\\|\\s*([^|]+)\\s*\\|'
    )

    try:
        # Pull/clone both repos
        for repo_url, repo_dir, repo_name in repos:
            if os.path.exists(repo_dir):
                result = subprocess.run(
                    ["git", "-C", repo_dir, "pull", "--quiet"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    print(f"  {repo_name} sync: git pull failed - {result.stderr}")
            else:
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, repo_dir],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    print(f"  {repo_name} sync: git clone failed - {result.stderr}")

        # Parse all repos
        import re as re_mod
        all_apis = []
        seen_keys = set()

        # For repos with folder-per-category format (openclaw, mega-list)
        ROW_PATTERN_MOD = re_mod.compile(
            r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\s*\|'
        )
        # For repos with single README format (ai-agent-tools)
        TOOL_PATTERN = re_mod.compile(r"\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*-?\s*(.*)")

        for repo_url, repo_dir, repo_name in repos:
            if not os.path.exists(repo_dir):
                continue
            for folder in sorted(os.listdir(repo_dir)):
                folder_path = os.path.join(repo_dir, folder)
                if not os.path.isdir(folder_path) or folder in ("settings", "assets", ".git"):
                    continue
                category = None
                for prefix, cat_name in CATEGORY_MAP.items():
                    if folder.startswith(prefix):
                        category = cat_name
                        break
                if not category:
                    continue
                readme_path = os.path.join(folder_path, "README.md")
                if not os.path.exists(readme_path):
                    continue

                with open(readme_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        m = ROW_PATTERN_MOD.match(line)
                        if m:
                            name = m.group(1).strip()
                            url = m.group(2).strip()
                            desc = m.group(3).strip()
                            key = (name.lower(), url)
                            if key in seen_keys:
                                continue
                            seen_keys.add(key)
                            api_id = hashlib.md5(f"{name}_{url}".encode()).hexdigest()[:12]
                            all_apis.append({
                                "id": api_id,
                                "name": name,
                                "url": url,
                                "description": desc,
                                "category": category,
                                "source": repo_name,
                                "discovered_date": datetime.now(timezone.utc).isoformat(),
                                "type": "api"
                            })

        # Parse ai-agent-tools (single README format)
        ai_tools_path = "/opt/evolvixos/ai-agent-tools/README.md"
        if os.path.exists(ai_tools_path):
            with open(ai_tools_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
            sections = re_mod.split(r"\n## ", readme_content)
            for section in sections[1:]:
                title_line = section.split("\n")[0].strip()
                if any(s in title_line for s in SKIP_SECTIONS):
                    continue
                category = None
                for key, cat_name in SECTION_MAP.items():
                    if key.lower() in title_line.lower():
                        category = cat_name
                        break
                if not category:
                    continue
                tools = TOOL_PATTERN.findall(section)
                for name, url, desc in tools:
                    if "Follow on Facebook" in name:
                        continue
                    key = (name.lower(), url)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    api_id = hashlib.md5(f"{name}_{url}".encode()).hexdigest()[:12]
                    all_apis.append({
                        "id": api_id,
                        "name": name.strip(),
                        "url": url.strip(),
                        "description": desc.strip() if desc else "AI tool from ai-agent-tools",
                        "category": category,
                        "source": "ai-agent-tools",
                        "discovered_date": datetime.now(timezone.utc).isoformat(),
                        "type": "tool"
                    })

        category_counts = {}
        for a in all_apis:
            category_counts[a["category"]] = category_counts.get(a["category"], 0) + 1

        registry = {
            "sources": ["openclaw-api-list", "api-mega-list", "ai-agent-tools"],
            "source_urls": [
                "https://github.com/cporter202/openclaw-api-list",
                "https://github.com/cporter202/API-mega-list",
                "https://github.com/cporter202/ai-agent-tools"
            ],
            "total_apis": len(all_apis),
            "categories": category_counts,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "apis": all_apis
        }

        with open("/opt/evolvixos/models/openclaw_apis.json", "w") as f:
            json_mod.dump(registry, f, indent=2)

        # Rebuild course index
        course_dir = "/opt/evolvixos/lovable-for-beginners"
        if os.path.exists(course_dir):
            import re as re_c
            course_modules = []
            for fname in sorted(os.listdir(course_dir)):
                if not fname.endswith(".md") or fname == "README.md":
                    continue
                fpath = os.path.join(course_dir, fname)
                with open(fpath, "r") as cf:
                    ccontent = cf.read()
                title_m = re_c.match(r"#\s+(.+)", ccontent)
                title = title_m.group(1) if title_m else fname
                num_m = re_c.search(r"module-(\d+)", fname)
                mod_num = int(num_m.group(1)) if num_m else 0
                words = len(ccontent.split())
                goals_m = re_c.search(r"## Learning goals.*?\n(.*?)(?=\n##|\Z)", ccontent, re_c.DOTALL)
                goals = re_c.findall(r"-\s+(.+)", goals_m.group(1)) if goals_m else []
                sections = re_c.findall(r"^##\s+(.+)", ccontent, re_c.MULTILINE)
                summary = ""
                for line in ccontent.split("\n")[1:]:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith(">") and not line.startswith("|") and not line.startswith("-"):
                        summary = line[:200]
                        break
                if mod_num <= 5:
                    phase = "Phase 1: Foundations"
                elif mod_num <= 10:
                    phase = "Phase 2: Full-Stack Delivery"
                elif mod_num <= 15:
                    phase = "Phase 3: Advanced Practice"
                else:
                    phase = "Supplement"
                is_supp = fname.startswith("supplement")
                course_modules.append({
                    "filename": fname, "title": title, "module_num": mod_num,
                    "phase": phase, "is_supplement": is_supp, "summary": summary,
                    "goals": goals, "sections": sections, "word_count": words,
                    "read_time": max(1, words // 200),
                    "url": "/api/learn/" + fname.replace(".md", "")
                })
            
            phases = []
            phase_defs = [
                ("Phase 1: Foundations", "Build a strong product foundation before adding backend complexity."),
                ("Phase 2: Full-Stack Delivery", "Turn the interface into a secure, tested, published application."),
                ("Phase 3: Advanced Practice", "Scale your workflow, integrations, collaboration, and infrastructure choices.")
            ]
            for pname, pdesc in phase_defs:
                pmods = [m for m in course_modules if m["phase"] == pname and not m["is_supplement"]]
                phases.append({"name": pname, "description": pdesc, "modules": pmods})
            
            course_index = {
                "title": "Lovable for Beginners",
                "subtitle": "Your complete beginner's course to mastering Lovable Vibe Coding",
                "source": "https://github.com/cporter202/lovable-for-beginners",
                "total_modules": len([m for m in course_modules if not m["is_supplement"]]),
                "total_supplements": len([m for m in course_modules if m["is_supplement"]]),
                "phases": phases,
                "supplements": [m for m in course_modules if m["is_supplement"]],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open("/opt/evolvixos/models/lovable_course.json", "w") as cf:
                json.dump(course_index, cf, indent=2)
            print("  Course index rebuilt: " + str(course_index["total_modules"]) + " modules")

        # Rebuild freellm registry
        freellm_dir = "/opt/evolvixos/awesome-freellm-apis"
        if os.path.exists(freellm_dir):
            import re as re_f
            readme_path = os.path.join(freellm_dir, "README.md")
            with open(readme_path, "r") as rf:
                rf_content = rf.read()
            
            def extract_link_f(text):
                m = re_f.search(r'href="([^"]+)"', text)
                return m.group(1) if m else ""
            
            def extract_name_f(text):
                clean = re_f.sub(r'<[^>]+>', '', text)
                clean = re_f.sub(r'\[([^\]]+)\]\([^)]+\)', r'', clean)
                return clean.strip()
            
            perm_providers = []
            perm_m = re_f.search(r'<!-- BEGIN_PERMANENT_FREE -->(.*?)<!-- END_PERMANENT_FREE -->', rf_content, re_f.DOTALL)
            if perm_m:
                for line in perm_m.group(1).split("\n"):
                    line = line.strip()
                    if not line.startswith("|") or "---" in line or "Provider" in line:
                        continue
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cells) < 6:
                        continue
                    perm_providers.append({
                        "name": extract_name_f(cells[0]),
                        "free_models": int(cells[1]) if cells[1].isdigit() else cells[1],
                        "credit_card": cells[2],
                        "max_context": cells[3],
                        "modalities": [m2.strip() for m2 in cells[4].split(",")],
                        "key_url": extract_link_f(cells[5]),
                        "tier": "permanent_free"
                    })
            
            renew_providers = []
            renew_m = re_f.search(r'<!-- BEGIN_RENEWABLE -->(.*?)<!-- END_RENEWABLE -->', rf_content, re_f.DOTALL)
            if renew_m:
                for line in renew_m.group(1).split("\n"):
                    line = line.strip()
                    if not line.startswith("|") or "---" in line or "Provider" in line:
                        continue
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cells) < 6:
                        continue
                    renew_providers.append({
                        "name": extract_name_f(cells[0]),
                        "free_models": int(cells[1]) if cells[1].isdigit() else cells[1],
                        "credit_model": cells[2],
                        "max_context": cells[3],
                        "modalities": [m2.strip() for m2 in cells[4].split(",")],
                        "key_url": extract_link_f(cells[5]),
                        "tier": "renewable_credits"
                    })
            
            provider_urls = {}
            quick_m = re_f.search(r'<!-- BEGIN_QUICK_REF -->(.*?)<!-- END_QUICK_REF -->', rf_content, re_f.DOTALL)
            if quick_m:
                for line in quick_m.group(1).split("\n"):
                    line = line.strip()
                    if not line.startswith("|") or "---" in line or "Provider" in line:
                        continue
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cells) < 4:
                        continue
                    name = extract_name_f(cells[0])
                    provider_urls[name] = {"base_url": cells[1].strip("`"), "key_url": extract_link_f(cells[2])}
            
            all_providers = perm_providers + renew_providers
            for p in all_providers:
                if p["name"] in provider_urls:
                    p["base_url"] = provider_urls[p["name"]]["base_url"]
                    p["key_url"] = provider_urls[p["name"]]["key_url"] or p.get("key_url", "")
                else:
                    p["base_url"] = ""
                p["models"] = []
            
            freellm_reg = {
                "title": "Awesome Free LLM APIs",
                "subtitle": "442+ free LLM APIs from 31+ providers",
                "source": "https://github.com/open-free-llm-api/awesome-freellm-apis",
                "website": "https://freellm.net",
                "total_providers": len(all_providers),
                "total_free_models": sum(p["free_models"] for p in all_providers if isinstance(p["free_models"], int)),
                "providers": all_providers,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open("/opt/evolvixos/models/freellm_registry.json", "w") as ff:
                json.dump(freellm_reg, ff, indent=2)
            print("  FreeLLM registry rebuilt: " + str(freellm_reg["total_providers"]) + " providers")

        # Rebuild free-ai-tools registry
        aitools_dir = "/opt/evolvixos/free-ai-tools/website/src/data"
        if os.path.exists(aitools_dir):
            import re as re_at
            tools_path = os.path.join(aitools_dir, "tools.ts")
            cats_path = os.path.join(aitools_dir, "categories.ts")
            stacks_path = os.path.join(aitools_dir, "stacks.ts")
            
            with open(tools_path, "r") as tf:
                tools_ts = tf.read()
            with open(cats_path, "r") as cf:
                cats_ts = cf.read()
            with open(stacks_path, "r") as sf:
                stacks_ts = sf.read()
            
            # Simple extraction
            def extract_str_at(field, text):
                m = re_at.search(field + r':\s*"([^"]*)"', text)
                return m.group(1) if m else ""
            
            def extract_list_at(field, text):
                m = re_at.search(field + r':\s*\[([^\]]*)\]', text)
                if m:
                    return re_at.findall(r'"([^"]*)"', m.group(1))
                return []
            
            # Parse tools
            tools = []
            tool_section = re_at.search(r'export const tools.*?=\s*\[(.*)\];', tools_ts, re_at.DOTALL)
            if tool_section:
                text = tool_section.group(1)
                i = 0
                while i < len(text):
                    start = text.find("{", i)
                    if start == -1:
                        break
                    depth = 0
                    j = start
                    in_str = False
                    sc = None
                    while j < len(text):
                        c = text[j]
                        if in_str:
                            if c == sc and text[j-1] != "\\":
                                in_str = False
                        elif c in ('"', "'", "`"):
                            in_str = True
                            sc = c
                        elif c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        j += 1
                    if depth != 0:
                        break
                    bt = text[start:j+1]
                    i = j + 1
                    
                    tool = {
                        "id": extract_str_at("id", bt),
                        "name": extract_str_at("name", bt),
                        "category": extract_str_at("category", bt),
                        "shortDescription": extract_str_at("shortDescription", bt),
                        "description": extract_str_at("description", bt),
                        "website": extract_str_at("website", bt),
                        "github": extract_str_at("github", bt),
                        "models": extract_list_at("models", bt),
                        "tags": extract_list_at("tags", bt),
                        "features": extract_list_at("features", bt),
                        "pros": extract_list_at("pros", bt),
                        "cons": extract_list_at("cons", bt),
                        "openSource": bool(re_at.search(r"openSource:\s*true", bt)),
                        "featured": bool(re_at.search(r"featured:\s*true", bt)),
                        "deployment": extract_str_at("deployment", bt),
                    }
                    pricing_m = re_at.search(r'pricing:\s*\{([^}]+)\}', bt)
                    if pricing_m:
                        pt = pricing_m.group(1)
                        tool["pricing"] = {
                            "type": extract_str_at("type", pt),
                            "freeTier": extract_str_at("freeTier", pt),
                            "creditCardRequired": bool(re_at.search(r"creditCardRequired:\s*false", pt))
                        }
                    if tool["id"]:
                        tools.append(tool)
            
            # Parse categories
            categories = []
            cat_section = re_at.search(r'export const categories.*?=\s*\[(.*?)\];', cats_ts, re_at.DOTALL)
            if cat_section:
                for block in re_at.finditer(r'\{([^}]+)\}', cat_section.group(1)):
                    bt = block.group(1)
                    categories.append({
                        "id": extract_str_at("id", bt),
                        "name": extract_str_at("name", bt),
                        "slug": extract_str_at("slug", bt),
                        "description": extract_str_at("description", bt),
                        "icon": extract_str_at("icon", bt),
                        "color": extract_str_at("color", bt),
                    })
            
            aitools_reg = {
                "title": "Free AI Tools",
                "subtitle": "Curated list of free and low-cost AI tools for building real AI apps",
                "source": "https://github.com/ShaikhWarsi/free-ai-tools",
                "total_tools": len(tools),
                "total_categories": len(categories),
                "categories": categories,
                "tools": tools,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open("/opt/evolvixos/models/free_ai_tools_registry.json", "w") as af:
                json.dump(aitools_reg, af, indent=2)
            print("  AI Tools registry rebuilt: " + str(len(tools)) + " tools, " + str(len(categories)) + " categories")

        print(f"  API directory sync: {len(all_apis)} APIs across {len(category_counts)} categories")
        return True

    except Exception as e:
        print(f"  API directory sync error: {e}")
        return False



if __name__ == "__main__":
    print("EvolvixOS GitHub Discovery Engine started")
    print(f"Scan interval: {SCAN_INTERVAL}s ({SCAN_INTERVAL//60} min)")
    print(f"GitHub token: {'configured' if GITHUB_TOKEN else 'NOT SET (rate limited)'}")
    while True:
        try:
            run_scan()
        except Exception as e:
            print(f"Scan error: {e}")
        sync_openclaw_repo()
        print(f"\nNext scan in {SCAN_INTERVAL//60} minutes...")
        time.sleep(SCAN_INTERVAL)

