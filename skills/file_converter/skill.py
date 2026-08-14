"""
EvolvixOS — File Converter Skill
Convert between formats: PDF, DOCX, TXT, MD, HTML, JSON, CSV, YAML, XML, etc.
100% local. Zero tokens. Zero cloud.

Pip: pip install pypandoc (also requires pandoc binary) OR use built-in converters
License: GPL (pandoc), MIT (pypandoc)
"""

import os
import json
import time
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """File converter — convert between any formats. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/converted"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "convert")

        if action == "convert":
            return self.convert(args.get("file", ""), args.get("to_format", "md"))
        elif action == "convert_text":
            return self.convert_text(args.get("text", ""), args.get("from_format", "txt"),
                                     args.get("to_format", "md"))
        elif action == "batch_convert":
            return self.batch_convert(args.get("files", []), args.get("to_format", "md"))
        elif action == "supported":
            return self.supported_formats()
        else:
            return f"Unknown action: {action}. Use: convert, convert_text, batch_convert, supported"

    def convert(self, file_path: str, to_format: str = "md") -> str:
        if not file_path or not os.path.exists(file_path):
            return "Error: File not found."

        from_format = Path(file_path).suffix.lstrip(".").lower()

        # Try pandoc first (most powerful)
        try:
            return self._convert_pandoc(file_path, to_format)
        except Exception:
            pass

        # Fallback to built-in converters
        return self._convert_builtin(file_path, from_format, to_format)

    def _convert_pandoc(self, file_path: str, to_format: str) -> str:
        base = Path(file_path).stem
        out = self.output_dir / f"{base}.{to_format}"

        result = subprocess.run(
            ["pandoc", file_path, "-o", str(out), "-t", to_format],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return f"Converted: {file_path} → {out}"
        else:
            raise Exception(f"pandoc error: {result.stderr}")

    def _convert_builtin(self, file_path: str, from_fmt: str, to_fmt: str) -> str:
        base = Path(file_path).stem
        out = self.output_dir / f"{base}.{to_fmt}"

        # Read source
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")

        # Parse to intermediate dict
        data = None
        if from_fmt in ("json",):
            data = json.loads(content)
        elif from_fmt in ("yaml", "yml"):
            import yaml
            data = yaml.safe_load(content)
        elif from_fmt in ("csv",):
            import csv
            data = list(csv.DictReader(content.splitlines()))
        elif from_fmt in ("txt", "md", "html", "xml"):
            data = content
        else:
            data = content

        # Write target format
        if to_fmt in ("json",):
            if isinstance(data, str):
                data = {"content": data}
            out.write_text(json.dumps(data, indent=2, default=str))
        elif to_fmt in ("yaml", "yml"):
            import yaml
            if isinstance(data, str):
                data = {"content": data}
            out.write_text(yaml.dump(data, default_flow_style=False))
        elif to_fmt in ("csv",):
            import csv
            if isinstance(data, list) and data and isinstance(data[0], dict):
                with open(out, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                out.write_text(str(data))
        elif to_fmt in ("txt",):
            out.write_text(str(data))
        elif to_fmt in ("md",):
            if isinstance(data, dict):
                out.write_text(self._dict_to_markdown(data))
            elif isinstance(data, list):
                out.write_text(self._list_to_markdown(data))
            else:
                out.write_text(str(data))
        elif to_fmt in ("html",):
            out.write_text(f"<!DOCTYPE html>\n<html><body><pre>{str(data)}</pre></body></html>")
        else:
            out.write_text(str(data))

        return f"Converted: {file_path} → {out}"

    def _dict_to_markdown(self, data: dict, level: int = 1) -> str:
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{'#' * level} {key}\n")
                lines.append(self._dict_to_markdown(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{'#' * level} {key}\n")
                lines.append(self._list_to_markdown(value))
            else:
                lines.append(f"**{key}**: {value}\n")
        return "\n".join(lines)

    def _list_to_markdown(self, data: list) -> str:
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(f"- {json.dumps(item, default=str)}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    def convert_text(self, text: str, from_format: str = "txt",
                     to_format: str = "md") -> str:
        temp = self.output_dir / f"temp_{int(time.time())}.{from_format}"
        temp.write_text(text)
        result = self.convert(str(temp), to_format)
        temp.unlink()
        return result

    def batch_convert(self, files: list, to_format: str = "md") -> str:
        results = []
        for f in files:
            results.append(self.convert(f, to_format))
        return "\n".join(results)

    def supported_formats(self) -> str:
        formats = {
            "document": ["md", "html", "txt", "rst", "docx", "pdf", "epub", "latex"],
            "data": ["json", "yaml", "yml", "csv", "tsv", "xml", "toml"],
            "code": ["py", "js", "ts", "sh", "sql", "rb", "go", "rs"],
            "config": ["ini", "cfg", "env", "properties"],
        }
        return json.dumps(formats, indent=2)
