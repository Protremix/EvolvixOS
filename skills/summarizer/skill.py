"""
EvolvixOS — Summarizer Skill
Summarize text, articles, documents, PDFs using local LLM.
100% local via Ollama. Zero tokens. Zero cloud.

Uses: deepseek-r1 or llama3.2 via Ollama (already installed)
License: MIT
"""

import os
import json
import time
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """Summarizer — condense any text using local LLM. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/summaries"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = self.config.get("model", "llama3.2:3b")
        self.host = self.config.get("host", "http://localhost:11434")

    def run(self, args: dict) -> str:
        action = args.get("action", "summarize")

        if action == "summarize":
            return self.summarize(args.get("text", ""), args.get("ratio", 0.3),
                                  args.get("style", "concise"))
        elif action == "summarize_file":
            return self.summarize_file(args.get("file", ""), args.get("ratio", 0.3))
        elif action == "key_points":
            return self.key_points(args.get("text", ""), args.get("n", 5))
        elif action == "abstract":
            return self.abstract(args.get("text", ""))
        elif action == "bullet_points":
            return self.bullet_points(args.get("text", ""))
        elif action == "tldr":
            return self.tldr(args.get("text", ""))
        elif action == "summarize_pdf":
            return self.summarize_pdf(args.get("file", ""))
        else:
            return (f"Unknown action: {action}. Use: summarize, summarize_file, "
                    "key_points, abstract, bullet_points, tldr, summarize_pdf")

    def summarize(self, text: str, ratio: float = 0.3, style: str = "concise") -> str:
        if not text:
            return "Error: No text provided."

        if len(text) < 200:
            return text

        try:
            import ollama
            client = ollama.Client(host=self.host)

            prompt = f"""Summarize the following text in a {style} manner.
Keep the most important information. Target length: {int(len(text) * ratio)} characters.

TEXT:
{text[:10000}

SUMMARY:"""

            response = client.generate(model=self.model, prompt=prompt, stream=False)
            summary = response.get("response", "").strip()

            out = self.output_dir / f"summary_{int(time.time())}.md"
            out.write_text(f"# Summary\n\n{summary}\n\n---\n*Original: {len(text)} chars → Summary: {len(summary)} chars*")

            return summary
        except Exception as e:
            return f"Error: {e}\n(Requires Ollama running: ollama serve)"

    def summarize_file(self, file_path: str, ratio: float = 0.3) -> str:
        if not file_path or not os.path.exists(file_path):
            return "Error: File not found."

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        return self.summarize(text, ratio)

    def summarize_pdf(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = "\n\n".join([page.extract_text() for page in reader.pages])
            return self.summarize(text[:20000], ratio=0.2, style="detailed")
        except ImportError:
            return "Error: pip install PyPDF2"
        except Exception as e:
            return f"Error: {e}"

    def key_points(self, text: str, n: int = 5) -> str:
        if not text:
            return "Error: No text provided."

        try:
            import ollama
            client = ollama.Client(host=self.host)
            prompt = f"""Extract the {n} most important key points from this text.
Format as a numbered list.

TEXT:
{text[:10000}

KEY POINTS:"""

            response = client.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"

    def abstract(self, text: str) -> str:
        try:
            import ollama
            client = ollama.Client(host=self.host)
            prompt = f"""Write a single-paragraph abstract (max 200 words) for this text:

{text[:10000}

ABSTRACT:"""
            response = client.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"

    def bullet_points(self, text: str) -> str:
        try:
            import ollama
            client = ollama.Client(host=self.host)
            prompt = f"""Summarize this text as bullet points. One key idea per bullet.

{text[:10000}

SUMMARY (bullet points):"""
            response = client.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"

    def tldr(self, text: str) -> str:
        try:
            import ollama
            client = ollama.Client(host=self.host)
            prompt = f"""TL;DR this text in one sentence:

{text[:10000}

TL;DR:"""
            response = client.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"
