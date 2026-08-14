"""
EvolvixOS — Research Skill
Deep web research using self-hosted SearXNG + local web scraping.
Zero tokens, zero external APIs.
"""

import requests
import re
import time
import hashlib
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from rich.console import Console
from trafilatura import extract as extract_article

console = Console()


class Skill:
    """Research skill — local web search and scraping, no API tokens."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.searxng_url = self.config.get("searxng_url", "http://localhost:8888")
        self.max_results = self.config.get("max_results", 10)
        self.depth = self.config.get("depth", 5)
        self.max_report_words = self.config.get("max_report_words", 5000)
        self.output_dir = Path(self.config.get("output_dir", "./output/research"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str) -> list:
        """Search via local SearXNG instance. No API tokens needed."""
        try:
            response = requests.get(
                f"{self.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "engines": "duckduckgo,google,bing,wikipedia",
                    "safesearch": 1,
                    "pageno": 1,
                },
                timeout=15,
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                return results[:self.max_results]
        except requests.ConnectionError:
            console.print("[yellow]⚠ SearXNG not running. Using DuckDuckGo HTML directly.[/yellow]")
            return self._search_ddg_fallback(query)
        except Exception as e:
            console.print(f"[yellow]⚠ Search error: {e}. Using fallback.[/yellow]")
            return self._search_ddg_fallback(query)

    def _search_ddg_fallback(self, query: str) -> list:
        """Fallback: scrape DuckDuckGo HTML. No API tokens."""
        try:
            response = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                timeout=15,
            )
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for item in soup.select(".result"):
                title_tag = item.select_one(".result__title a")
                snippet_tag = item.select_one(".result__snippet")
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": title_tag.get("href", ""),
                        "content": snippet_tag.get_text(strip=True) if snippet_tag else "",
                    })
            return results[:self.max_results]
        except Exception as e:
            console.print(f"[red]Search fallback failed: {e}[/red]")
            return []

    def scrape_page(self, url: str) -> Optional[str]:
        """Extract article text from a URL. Local processing."""
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                timeout=15,
            )
            text = extract_article(response.text)
            return text if text else None
        except Exception as e:
            console.print(f"[yellow]⚠ Scrape error for {url}: {e}[/yellow]")
            return None

    def research(self, query: str) -> str:
        """Full research: search → scrape → summarize → report."""
        console.print(f"[cyan]🔍 Researching: {query}[/cyan]")

        # Step 1: Search
        results = self.search(query)
        if not results:
            return "No results found. Is SearXNG running? Start it: docker run -p 8888:8080 searxng/searxng"

        console.print(f"[green]Found {len(results)} results[/green]")

        # Step 2: Scrape top results
        scraped = []
        for i, result in enumerate(results[:self.depth]):
            console.print(f"  [{i+1}/{min(self.depth, len(results))}] {result.get('title', 'No title')[:60]}")
            content = self.scrape_page(result.get("url", ""))
            if content:
                scraped.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": content[:5000],
                })
            time.sleep(0.5)  # Be polite

        if not scraped:
            # Use snippets from search results
            scraped = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]

        # Step 3: Build report
        report = self._build_report(query, scraped)

        # Save report
        report_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        report_file = self.output_dir / f"research_{report_hash}.md"
        report_file.write_text(report, encoding="utf-8")

        console.print(f"[green]✅ Report saved: {report_file}[/green]")
        return report

    def _build_report(self, query: str, sources: list) -> str:
        """Build a research report from sources."""
        lines = [
            f"# Research Report: {query}",
            f"\n_Generated by EvolvixOS — 100% local research, no API tokens_\n",
            f"## Summary\n",
        ]

        # Combine key findings
        for source in sources:
            lines.append(f"### {source['title']}")
            lines.append(f"**Source:** {source['url']}\n")
            content = source.get("content", "")
            # Take first ~1000 chars per source
            lines.append(content[:1000])
            if len(content) > 1000:
                lines.append("...")
            lines.append("\n---\n")

        lines.append(f"\n## Sources ({len(sources)})\n")
        for s in sources:
            lines.append(f"- [{s['title']}]({s['url']})")

        return "\n".join(lines)

    def run(self, args: dict) -> str:
        """Execute the research skill."""
        action = args.get("action", "search")
        query = args.get("query", args.get("args", {}).get("query", ""))

        if not query:
            return "Error: no query provided for research."

        if action == "search":
            results = self.search(query)
            return json.dumps(results, indent=2)
        elif action == "research":
            return self.research(query)
        else:
            return self.research(query)
