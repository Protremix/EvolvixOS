"""
EvolvixOS — Browser Automation Skill
Automate web browsing: navigate, click, type, screenshot, extract data.
100% local using Playwright. Zero tokens.

Pip: pip install playwright && playwright install chromium
License: Apache-2.0 (Playwright)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Browser automation — Playwright-powered. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/browser"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._browser = None
        self._page = None

    def run(self, args: dict) -> str:
        action = args.get("action", "navigate")

        if action == "navigate":
            return self.navigate(args.get("url", ""))
        elif action == "click":
            return self.click(args.get("selector", ""))
        elif action == "type":
            return self.type_text(args.get("selector", ""), args.get("text", ""))
        elif action == "screenshot":
            return self.screenshot(args.get("filename", ""))
        elif action == "get_text":
            return self.get_text(args.get("selector", ""))
        elif action == "get_html":
            return self.get_html(args.get("selector", ""))
        elif action == "extract":
            return self.extract(args.get("selector", ""), args.get("attributes", []))
        elif action == "fill_form":
            return self.fill_form(args.get("fields", {}))
        elif action == "wait":
            return self.wait(args.get("selector", ""), args.get("timeout", 10000))
        elif action == "scroll":
            return self.scroll(args.get("direction", "down"))
        elif action == "close":
            return self.close()
        else:
            return (f"Unknown action: {action}. Use: navigate, click, type, screenshot, "
                    "get_text, get_html, extract, fill_form, wait, scroll, close")

    def _ensure_browser(self):
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
                self._pw = sync_playwright().start()
                self._browser = self._pw.chromium.launch(headless=True)
                self._page = self._browser.new_page()
            except ImportError:
                return False
        return True

    def navigate(self, url: str) -> str:
        if not url:
            return "Error: No URL provided."
        if not self._ensure_browser():
            return "Error: pip install playwright && playwright install chromium"

        try:
            self._page.goto(url, timeout=30000)
            title = self._page.title()
            return f"Navigated to: {url}\nTitle: {title}"
        except Exception as e:
            return f"Error: {e}"

    def click(self, selector: str) -> str:
        try:
            self._page.click(selector, timeout=10000)
            return f"Clicked: {selector}"
        except Exception as e:
            return f"Error: {e}"

    def type_text(self, selector: str, text: str) -> str:
        try:
            self._page.fill(selector, text)
            return f"Typed into {selector}: {text[:50]}"
        except Exception as e:
            return f"Error: {e}"

    def screenshot(self, filename: str = "") -> str:
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        try:
            filepath = self.output_dir / filename
            self._page.screenshot(path=str(filepath), full_page=True)
            return f"Screenshot saved: {filepath}"
        except Exception as e:
            return f"Error: {e}"

    def get_text(self, selector: str = "") -> str:
        try:
            if selector:
                return self._page.inner_text(selector)[:10000]
            return self._page.inner_text("body")[:10000]
        except Exception as e:
            return f"Error: {e}"

    def get_html(self, selector: str = "") -> str:
        try:
            if selector:
                return self._page.inner_html(selector)[:10000]
            return self._page.content()[:10000]
        except Exception as e:
            return f"Error: {e}"

    def extract(self, selector: str, attributes: list = None) -> str:
        try:
            elements = self._page.query_selector_all(selector)
            results = []
            for el in elements[:100]:
                if attributes:
                    data = {attr: el.get_attribute(attr) for attr in attributes}
                    data["text"] = el.inner_text()
                else:
                    data = {"text": el.inner_text()}
                results.append(data)
            return json.dumps(results, indent=2, default=str)[:10000]
        except Exception as e:
            return f"Error: {e}"

    def fill_form(self, fields: dict) -> str:
        try:
            for selector, value in fields.items():
                self._page.fill(selector, str(value))
            return f"Filled {len(fields)} form fields"
        except Exception as e:
            return f"Error: {e}"

    def wait(self, selector: str, timeout: int = 10000) -> str:
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
            return f"Element appeared: {selector}"
        except Exception as e:
            return f"Error: {e}"

    def scroll(self, direction: str = "down") -> str:
        try:
            if direction == "down":
                self._page.evaluate("window.scrollBy(0, 500)")
            elif direction == "up":
                self._page.evaluate("window.scrollBy(0, -500)")
            elif direction == "bottom":
                self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            elif direction == "top":
                self._page.evaluate("window.scrollTo(0, 0)")
            return f"Scrolled {direction}"
        except Exception as e:
            return f"Error: {e}"

    def close(self) -> str:
        try:
            if self._browser:
                self._browser.close()
                self._pw.stop()
                self._browser = None
                self._page = None
            return "Browser closed."
        except Exception as e:
            return f"Error: {e}"
