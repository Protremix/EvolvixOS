"""
EvolvixOS — Web Scraper Skill
Scrape any website. Extract text, links, images, tables, forms.
100% local using BeautifulSoup + requests. Zero tokens.

Pip: pip install beautifulsoup4 requests lxml
License: MIT (BeautifulSoup), Apache-2.0 (requests), BSD (lxml)
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console

console = Console()


class Skill:
    """Web scraper — extract content from any website. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/scraped"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = self.config.get("timeout", 30)
        self.user_agent = self.config.get("user_agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 EvolvixOS/1.0")

    def run(self, args: dict) -> str:
        action = args.get("action", "scrape")

        if action == "scrape":
            return self.scrape(args.get("url", ""), args.get("extract", "all"))
        elif action == "scrape_multi":
            return self.scrape_multiple(args.get("urls", []), args.get("extract", "all"))
        elif action == "extract_links":
            return self.extract_links(args.get("url", ""))
        elif action == "extract_text":
            return self.extract_text(args.get("url", ""))
        elif action == "extract_tables":
            return self.extract_tables(args.get("url", ""))
        elif action == "extract_images":
            return self.extract_images(args.get("url", ""))
        elif action == "download":
            return self.download_file(args.get("url", ""), args.get("filename", ""))
        else:
            return f"Unknown action: {action}. Use: scrape, scrape_multi, extract_links, extract_text, extract_tables, extract_images, download"

    def scrape(self, url: str, extract: str = "all") -> str:
        if not url:
            return "Error: No URL provided."

        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return "Error: Install dependencies: pip install beautifulsoup4 requests lxml"

        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")
            result = {"url": url, "scraped_at": time.time()}

            if extract in ("all", "title"):
                result["title"] = soup.title.string.strip() if soup.title else ""

            if extract in ("all", "text"):
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                result["text"] = soup.get_text(separator="\n", strip=True)[:50000]

            if extract in ("all", "links"):
                result["links"] = [{"text": a.get_text(strip=True), "href": a.get("href", "")}
                                    for a in soup.find_all("a", href=True)][:100]

            if extract in ("all", "images"):
                result["images"] = [img.get("src", "") for img in soup.find_all("img", src=True)][:50]

            if extract in ("all", "tables"):
                tables = []
                for table in soup.find_all("table"):
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        tables.append(rows)
                result["tables"] = tables

            if extract in ("all", "meta"):
                result["meta"] = {m.get("name", m.get("property", "")): m.get("content", "")
                                  for m in soup.find_all("meta")}

            # Save result
            filename = f"scrape_{int(time.time())}.json"
            filepath = self.output_dir / filename
            with open(filepath, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            return json.dumps(result, indent=2, ensure_ascii=False)[:10000]

        except Exception as e:
            return f"Error scraping {url}: {e}"

    def scrape_multiple(self, urls: List[str], extract: str = "all") -> str:
        results = []
        for url in urls:
            r = self.scrape(url, extract)
            results.append(r)
        return json.dumps(results, indent=2, ensure_ascii=False)[:20000]

    def extract_links(self, url: str) -> str:
        return self.scrape(url, "links")

    def extract_text(self, url: str) -> str:
        return self.scrape(url, "text")

    def extract_tables(self, url: str) -> str:
        return self.scrape(url, "tables")

    def extract_images(self, url: str) -> str:
        return self.scrape(url, "images")

    def download_file(self, url: str, filename: str = "") -> str:
        try:
            import requests
            if not filename:
                filename = url.split("/")[-1] or f"download_{int(time.time())}"
            filepath = self.output_dir / filename
            response = requests.get(url, headers={"User-Agent": self.user_agent},
                                     timeout=self.timeout, stream=True)
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            return f"Downloaded: {filepath}"
        except Exception as e:
            return f"Error downloading: {e}"
