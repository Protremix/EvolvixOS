"""EvolvixOS Plugin System — connect agents and builder to external services.

Plugins available:
- web_search: Search the internet via DuckDuckGo
- web_fetch: Fetch and parse any URL
- email_send: Send emails via Brevo API
- http_request: Make HTTP calls to any API
- database_query: Query entities directly
- code_exec: Execute Python code safely
- file_ops: Read/write files on server
- github: GitHub repo operations (commit, issue, PR)
- image_gen: Generate images via available providers
- crypto: Get crypto prices and blockchain data
- weather: Get weather for any city
- time_tools: Get current time, date, timezone
- translate: Translate text between languages
- summarize: Summarize long text
- sentiment: Analyze sentiment of text
"""
import json
import os
import urllib.request
import urllib.parse
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional


class PluginRegistry:
    """Registry of all available plugins."""
    
    _plugins = {}
    _initialized = False
    
    @classmethod
    def _ensure_init(cls):
        if cls._initialized:
            return
        cls._plugins = {
            "web_search": {
                "name": "Web Search",
                "description": "Search the internet for current information",
                "category": "information",
                "icon": "🔍",
                "params": {"query": "string", "max_results": "int (optional, default 5)"},
                "handler": cls.web_search,
            },
            "web_fetch": {
                "name": "Web Fetch",
                "description": "Fetch and parse content from any URL",
                "category": "information",
                "icon": "🌐",
                "params": {"url": "string"},
                "handler": cls.web_fetch,
            },
            "email_send": {
                "name": "Send Email",
                "description": "Send an email via Brevo SMTP API",
                "category": "communication",
                "icon": "📧",
                "params": {"to": "string", "subject": "string", "body": "string"},
                "handler": cls.email_send,
            },
            "http_request": {
                "name": "HTTP Request",
                "description": "Make an HTTP call to any external API",
                "category": "integration",
                "icon": "🔗",
                "params": {"url": "string", "method": "string (GET/POST/PUT/DELETE)", "headers": "object (optional)", "body": "object (optional)"},
                "handler": cls.http_request,
            },
            "database_query": {
                "name": "Database Query",
                "description": "Query platform entities directly",
                "category": "data",
                "icon": "🗄️",
                "params": {"entity": "string", "action": "string (list/get/filter)", "filters": "object (optional)"},
                "handler": cls.database_query,
            },
            "code_exec": {
                "name": "Code Execution",
                "description": "Execute Python code in a sandboxed environment",
                "category": "compute",
                "icon": "🐍",
                "params": {"code": "string (Python code to execute)"},
                "handler": cls.code_exec,
            },
            "file_ops": {
                "name": "File Operations",
                "description": "Read or write files on the server",
                "category": "system",
                "icon": "📄",
                "params": {"action": "string (read/write/list)", "path": "string", "content": "string (for write)"},
                "handler": cls.file_ops,
            },
            "github": {
                "name": "GitHub",
                "description": "GitHub repository operations",
                "category": "integration",
                "icon": "🐙",
                "params": {"action": "string (repos/issues/commits)", "repo": "string (optional)"},
                "handler": cls.github,
            },
            "image_gen": {
                "name": "Image Generation",
                "description": "Generate images from text prompts",
                "category": "media",
                "icon": "🎨",
                "params": {"prompt": "string", "width": "int (optional)", "height": "int (optional)"},
                "handler": cls.image_gen,
            },
            "crypto": {
                "name": "Crypto Prices",
                "description": "Get cryptocurrency prices and market data",
                "category": "finance",
                "icon": "₿",
                "params": {"coin": "string (e.g. bitcoin, ethereum)", "vs_currency": "string (default usd)"},
                "handler": cls.crypto,
            },
            "weather": {
                "name": "Weather",
                "description": "Get current weather for any city",
                "category": "information",
                "icon": "🌤️",
                "params": {"city": "string", "units": "string (metric/imperial, default metric)"},
                "handler": cls.weather,
            },
            "time_tools": {
                "name": "Time & Date",
                "description": "Get current time, date, and timezone info",
                "category": "utility",
                "icon": "🕐",
                "params": {"timezone": "string (optional, default UTC)"},
                "handler": cls.time_tools,
            },
            "translate": {
                "name": "Translate",
                "description": "Translate text between languages",
                "category": "utility",
                "icon": "🌍",
                "params": {"text": "string", "from_lang": "string (optional)", "to_lang": "string"},
                "handler": cls.translate,
            },
            "summarize": {
                "name": "Summarize",
                "description": "Summarize long text into key points",
                "category": "utility",
                "icon": "📝",
                "params": {"text": "string", "max_sentences": "int (optional, default 5)"},
                "handler": cls.summarize,
            },
            "sentiment": {
                "name": "Sentiment Analysis",
                "description": "Analyze sentiment of text (positive/negative/neutral)",
                "category": "utility",
                "icon": "📊",
                "params": {"text": "string"},
                "handler": cls.sentiment,
            },
        }
        cls._initialized = True
    
    @classmethod
    def list_plugins(cls) -> List[Dict]:
        """List all available plugins."""
        cls._ensure_init()
        return [
            {
                "id": pid,
                "name": p["name"],
                "description": p["description"],
                "category": p["category"],
                "icon": p["icon"],
                "params": p["params"],
            }
            for pid, p in cls._plugins.items()
        ]
    
    @classmethod
    def get_plugin(cls, plugin_id: str) -> Optional[Dict]:
        """Get a single plugin by ID."""
        cls._ensure_init()
        return cls._plugins.get(plugin_id)
    
    @classmethod
    async def execute_plugin(cls, plugin_id: str, params: Dict[str, Any], db=None) -> Dict:
        """Execute a plugin by ID with given parameters."""
        cls._ensure_init()
        plugin = cls._plugins.get(plugin_id)
        if not plugin:
            return {"error": f"Plugin '{plugin_id}' not found", "available": list(cls._plugins.keys())}
        
        try:
            handler = plugin["handler"]
            # Pass db to database_query handler
            if plugin_id == "database_query" and db:
                return await handler(params, db)
            result = await handler(params)
            return {"success": True, "plugin": plugin_id, "result": result}
        except Exception as e:
            return {"success": False, "plugin": plugin_id, "error": str(e)}
    
    # ═══════════════════════════════════════════════
    # PLUGIN IMPLEMENTATIONS
    # ═══════════════════════════════════════════════
    
    @staticmethod
    async def web_search(params: Dict) -> Dict:
        """Search the internet using DuckDuckGo Instant Answer API."""
        query = params.get("query", "")
        if not query:
            return {"error": "query is required"}
        
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "EvolvixOS/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        results = []
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "snippet": data.get("AbstractText", ""),
                "source": data.get("AbstractURL", ""),
            })
        for topic in data.get("RelatedTopics", [])[:10]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "source": topic.get("FirstURL", ""),
                })
        
        # Also try HTML scrape of DuckDuckGo as fallback
        if not results:
            html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req2 = urllib.request.Request(html_url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                resp2 = urllib.request.urlopen(req2, timeout=10)
                html = resp2.read().decode("utf-8", errors="ignore")
                import re
                snippets = re.findall(r'class="result__snippet">(.*?)</a>', html, re.DOTALL)[:5]
                for s in snippets:
                    clean = re.sub(r'<[^>]+>', '', s).strip()
                    if clean:
                        results.append({"title": clean[:80], "snippet": clean, "source": "DuckDuckGo"})
            except:
                pass
        
        return {"query": query, "results": results[:int(params.get("max_results", 5))], "count": len(results)}
    
    @staticmethod
    async def web_fetch(params: Dict) -> Dict:
        """Fetch content from a URL."""
        url = params.get("url", "")
        if not url:
            return {"error": "url is required"}
        if not url.startswith("http"):
            url = "https://" + url
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (EvolvixOS)"})
        resp = urllib.request.urlopen(req, timeout=30)
        content = resp.read().decode("utf-8", errors="ignore")
        
        # Strip HTML tags for readable text
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return {
            "url": url,
            "status": resp.status,
            "content": text[:5000],
            "content_length": len(text),
            "truncated": len(text) > 5000,
        }
    
    @staticmethod
    async def email_send(params: Dict) -> Dict:
        """Send email via Brevo API."""
        brevo_key = os.environ.get("BREVO_API_KEY", "")
        to_email = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        
        if not to_email or not subject:
            return {"error": "to and subject are required"}
        
        if not brevo_key:
            return {"error": "BREVO_API_KEY not configured"}
        
        payload = json.dumps({
            "sender": {"email": "support@evolvixos.com", "name": "EvolvixOS"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": f"<html><body><p>{body}</p></body></html>",
            "textContent": body,
        }).encode()
        
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "api-key": brevo_key,
            },
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        return {"sent": True, "to": to_email, "subject": subject, "message_id": data.get("messageId", "")}
    
    @staticmethod
    async def http_request(params: Dict) -> Dict:
        """Make an HTTP request to any URL."""
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        body = params.get("body")
        
        if not url:
            return {"error": "url is required"}
        
        data = None
        if body and method in ("POST", "PUT", "PATCH"):
            data = json.dumps(body).encode() if isinstance(body, (dict, list)) else str(body).encode()
            headers["Content-Type"] = headers.get("Content-Type", "application/json")
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=30)
        content = resp.read().decode("utf-8", errors="ignore")
        
        try:
            parsed = json.loads(content)
            return {"status": resp.status, "data": parsed}
        except:
            return {"status": resp.status, "data": content[:2000]}
    
    @staticmethod
    async def database_query(params: Dict, db=None) -> Dict:
        """Query platform entities."""
        entity = params.get("entity", "")
        action = params.get("action", "list")
        filters = params.get("filters", {})
        
        if not entity:
            return {"error": "entity is required"}
        if not db:
            return {"error": "database not available in this context"}
        
        from sqlalchemy import text as sql_text
        
        table = f"entity_{entity.lower()}"
        if action == "list":
            result = await db.execute(sql_text(f"SELECT * FROM {table} ORDER BY created_date DESC LIMIT 50"))
            rows = result.fetchall()
            cols = result.keys()
            return {"entity": entity, "count": len(rows), "records": [dict(zip(cols, r)) for r in rows]}
        elif action == "get":
            record_id = params.get("id")
            result = await db.execute(sql_text(f"SELECT * FROM {table} WHERE id = :id"), {"id": record_id})
            row = result.fetchone()
            if row:
                return {"entity": entity, "record": dict(zip(result.keys(), row))}
            return {"error": "Record not found"}
        
        return {"error": f"Unknown action: {action}"}
    
    @staticmethod
    async def code_exec(params: Dict) -> Dict:
        """Execute Python code safely."""
        code = params.get("code", "")
        if not code:
            return {"error": "code is required"}
        
        # Block dangerous operations
        blocked = ["import os", "import subprocess", "import sys", "os.system", "os.popen", "subprocess", "eval(", "exec(", "__import__", "open('/", "rm -rf"]
        for b in blocked:
            if b in code:
                return {"error": f"Blocked operation: {b}"}
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            tmpfile = f.name
        
        try:
            result = subprocess.run(
                ["python3", tmpfile],
                capture_output=True, text=True, timeout=10,
                env={"PATH": "/usr/bin:/usr/local/bin", "HOME": "/tmp", "PYTHONPATH": "/opt/evolvixos/platform"}
            )
            return {
                "stdout": result.stdout[:3000],
                "stderr": result.stderr[:1000],
                "exit_code": result.returncode,
            }
        finally:
            os.unlink(tmpfile)
    
    @staticmethod
    async def file_ops(params: Dict) -> Dict:
        """Read, write, or list files."""
        action = params.get("action", "list")
        path = params.get("path", "/opt/evolvixos")
        content = params.get("content", "")
        
        # Safety: restrict to /opt/evolvixos and /tmp
        safe_paths = ["/opt/evolvixos", "/tmp", "/var/log/evolvixos"]
        if not any(path.startswith(p) for p in safe_paths):
            return {"error": f"Path not allowed. Must start with: {safe_paths}"}
        
        if action == "read":
            with open(path) as f:
                return {"path": path, "content": f.read()[:5000], "size": os.path.getsize(path)}
        elif action == "write":
            with open(path, "w") as f:
                f.write(content)
            return {"path": path, "written": True, "size": len(content)}
        elif action == "list":
            entries = os.listdir(path)
            return {"path": path, "entries": entries}
        
        return {"error": f"Unknown action: {action}"}
    
    @staticmethod
    async def github(params: Dict) -> Dict:
        """GitHub operations via API."""
        action = params.get("action", "repos")
        repo = params.get("repo", "Protremix/EvolvixOS")
        token = os.environ.get("GITHUB_TOKEN", "")
        
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "EvolvixOS"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        if action == "repos":
            url = f"https://api.github.com/users/{repo.split('/')[0]}/repos?per_page=20"
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            return {"repos": [{"name": r["name"], "stars": r["stargazers_count"], "desc": r.get("description", "")} for r in data]}
        elif action == "issues":
            url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=10"
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            return {"issues": [{"number": i["number"], "title": i["title"], "labels": [l["name"] for l in i.get("labels", [])]} for i in data]}
        elif action == "commits":
            url = f"https://api.github.com/repos/{repo}/commits?per_page=10"
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            return {"commits": [{"sha": c["sha"][:7], "message": c["commit"]["message"][:80], "author": c["commit"]["author"]["name"]} for c in data]}
        
        return {"error": f"Unknown action: {action}"}
    
    @staticmethod
    async def image_gen(params: Dict) -> Dict:
        """Generate images via Pollinations or other providers."""
        prompt = params.get("prompt", "")
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        
        if not prompt:
            return {"error": "prompt is required"}
        
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={width}&height={height}&nologo=true"
        
        return {
            "prompt": prompt,
            "url": url,
            "width": width,
            "height": height,
            "provider": "pollinations",
        }
    
    @staticmethod
    async def crypto(params: Dict) -> Dict:
        """Get crypto prices from CoinGecko."""
        coin = params.get("coin", "bitcoin")
        vs = params.get("vs_currency", "usd")
        
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies={vs}&include_24hr_change=true&include_market_cap=true"
        req = urllib.request.Request(url, headers={"User-Agent": "EvolvixOS/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        return {"coin": coin, "data": data}
    
    @staticmethod
    async def weather(params: Dict) -> Dict:
        """Get weather via wttr.in."""
        city = params.get("city", "")
        units = params.get("units", "metric")
        
        if not city:
            return {"error": "city is required"}
        
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        current = data.get("current_condition", [{}])[0]
        return {
            "city": city,
            "temp": current.get("temp_C", "?") + "°C" if units == "metric" else current.get("temp_F", "?") + "°F",
            "desc": current.get("weatherDesc", [{}])[0].get("value", ""),
            "humidity": current.get("humidity", "?") + "%",
            "wind": current.get("windspeedKmph", "?") + " km/h",
        }
    
    @staticmethod
    async def time_tools(params: Dict) -> Dict:
        """Get current time and date."""
        tz = params.get("timezone", "UTC")
        now = datetime.utcnow()
        return {
            "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "iso": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": tz,
        }
    
    @staticmethod
    async def translate(params: Dict) -> Dict:
        """Translate text using MyMemory API (free)."""
        text = params.get("text", "")
        to_lang = params.get("to_lang", "en")
        from_lang = params.get("from_lang", "")
        
        if not text:
            return {"error": "text is required"}
        
        lang_pair = f"{from_lang}|{to_lang}" if from_lang else to_lang
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={lang_pair}"
        req = urllib.request.Request(url, headers={"User-Agent": "EvolvixOS/1.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        return {
            "original": text,
            "translated": data.get("responseData", {}).get("translatedText", ""),
            "from": from_lang or "auto",
            "to": to_lang,
        }
    
    @staticmethod
    async def summarize(params: Dict) -> Dict:
        """Summarize text using extractive summarization."""
        text = params.get("text", "")
        max_sentences = int(params.get("max_sentences", 5))
        
        if not text:
            return {"error": "text is required"}
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= max_sentences:
            return {"summary": text, "sentences": len(sentences)}
        
        # Score sentences by word frequency
        words = re.findall(r'\w+', text.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        
        scored = []
        for i, s in enumerate(sentences):
            s_words = re.findall(r'\w+', s.lower())
            score = sum(word_freq.get(w, 0) for w in s_words) / max(len(s_words), 1)
            scored.append((i, s, score))
        
        top = sorted(scored, key=lambda x: x[2], reverse=True)[:max_sentences]
        top.sort(key=lambda x: x[0])
        
        return {
            "summary": " ".join(s[1] for s in top),
            "original_sentences": len(sentences),
            "summary_sentences": len(top),
            "compression": f"{len(top)}/{len(sentences)}",
        }
    
    @staticmethod
    async def sentiment(params: Dict) -> Dict:
        """Analyze sentiment of text."""
        text = params.get("text", "")
        if not text:
            return {"error": "text is required"}
        
        # Simple word-based sentiment analysis
        positive_words = {"good", "great", "excellent", "amazing", "love", "happy", "positive", "best", "awesome", "perfect", "wonderful", "fantastic", "nice", "brilliant", "success", "win", "beautiful", "outstanding", "superb"}
        negative_words = {"bad", "terrible", "awful", "hate", "sad", "negative", "worst", "horrible", "fail", "broken", "ugly", "poor", "disappointing", "angry", "wrong", "error", "problem", "issue", "crash"}
        
        words = set(text.lower().split())
        pos = len(words & positive_words)
        neg = len(words & negative_words)
        
        if pos > neg:
            sentiment = "positive"
            score = pos / max(pos + neg, 1)
        elif neg > pos:
            sentiment = "negative"
            score = -neg / max(pos + neg, 1)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_words": pos,
            "negative_words": neg,
        }
