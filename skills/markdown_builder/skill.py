"""
EvolvixOS — Markdown Builder Skill
Generate markdown documents, READMEs, reports, documentation.
100% local. Zero tokens. No dependencies needed.

License: MIT
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Markdown builder — generate docs, READMEs, reports. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/markdown"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "generate")

        if action == "generate":
            return self.generate(args.get("sections", []), args.get("title", ""),
                                 args.get("filename", ""))
        elif action == "readme":
            return self.generate_readme(args.get("project_name", ""),
                                         args.get("description", ""),
                                         args.get("features", []),
                                         args.get("install_cmd", ""),
                                         args.get("usage", ""))
        elif action == "report":
            return self.generate_report(args.get("title", ""), args.get("data", {}),
                                         args.get("sections", []))
        elif action == "table":
            return self.generate_table(args.get("headers", []), args.get("rows", []))
        elif action == "toc":
            return self.generate_toc(args.get("markdown", ""))
        elif action == "changelog":
            return self.generate_changelog(args.get("versions", []))
        elif action == "api_doc":
            return self.generate_api_docs(args.get("endpoints", []))
        else:
            return (f"Unknown action: {action}. Use: generate, readme, report, table, "
                    "toc, changelog, api_doc")

    def generate(self, sections: list, title: str = "", filename: str = "") -> str:
        lines = []
        if title:
            lines.append(f"# {title}\n")

        for section in sections:
            if isinstance(section, str):
                lines.append(f"## {section}\n")
            elif isinstance(section, dict):
                heading = section.get("heading", section.get("title", ""))
                content = section.get("content", section.get("body", ""))
                level = section.get("level", 2)
                lines.append(f"{'#' * level} {heading}\n")
                if content:
                    lines.append(f"{content}\n")

        result = "\n".join(lines)
        if filename:
            out = self.output_dir / filename
            out.write_text(result)
            return f"Markdown written: {out}\n\n{result}"
        return result

    def generate_readme(self, project_name: str, description: str = "",
                        features: list = None, install_cmd: str = "",
                        usage: str = "") -> str:
        lines = [
            f"# {project_name}\n",
            f"{description}\n",
            "## Features\n",
        ]

        for feat in (features or []):
            if isinstance(feat, str):
                lines.append(f"- {feat}")
            elif isinstance(feat, dict):
                lines.append(f"- **{feat.get('name', '')}**: {feat.get('description', '')}")

        lines.append("\n## Installation\n")
        if install_cmd:
            lines.append(f"```bash\n{install_cmd}\n```\n")
        else:
            lines.append("```bash\npip install " + project_name.lower().replace(" ", "-") + "\n```\n")

        lines.append("## Usage\n")
        if usage:
            lines.append(f"```python\n{usage}\n```\n")
        else:
            lines.append(f"```python\nimport {project_name.lower().replace(' ', '_')}\n```\n")

        lines.append("## License\n")
        lines.append("MIT\n")

        result = "\n".join(lines)
        out = self.output_dir / "README.md"
        out.write_text(result)
        return f"README generated: {out}"

    def generate_report(self, title: str, data: dict, sections: list = None) -> str:
        lines = [f"# {title}\n", f"**Generated:** {time.strftime('%Y-%m-%d %H:%M')}\n"]

        if data:
            lines.append("## Summary\n")
            for key, value in data.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        for section in (sections or []):
            if isinstance(section, dict):
                lines.append(f"## {section.get('title', '')}\n")
                lines.append(f"{section.get('content', '')}\n")
                if section.get("table"):
                    lines.append(self.generate_table(
                        section["table"].get("headers", []),
                        section["table"].get("rows", [])
                    ))

        result = "\n".join(lines)
        out = self.output_dir / f"report_{int(time.time())}.md"
        out.write_text(result)
        return f"Report generated: {out}"

    def generate_table(self, headers: list, rows: list) -> str:
        if not headers:
            return ""

        lines = [
            f"| {' | '.join(headers)} |",
            f"| {' | '.join(['---'] * len(headers))} |",
        ]

        for row in rows:
            if isinstance(row, dict):
                row = [str(row.get(h, "")) for h in headers]
            elif isinstance(row, list):
                row = [str(c) for c in row]
            lines.append(f"| {' | '.join(row)} |")

        return "\n".join(lines)

    def generate_toc(self, markdown: str) -> str:
        lines = markdown.splitlines()
        toc_lines = ["## Table of Contents\n"]

        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ").strip()
                anchor = title.lower().replace(" ", "-").replace(".", "")
                indent = "  " * (level - 1)
                toc_lines.append(f"{indent}- [{title}](#{anchor})")

        return "\n".join(toc_lines)

    def generate_changelog(self, versions: list) -> str:
        lines = ["# Changelog\n"]

        for version in versions:
            lines.append(f"## [{version.get('version', '')}] - {version.get('date', '')}\n")
            for change_type in ["added", "changed", "deprecated", "removed", "fixed", "security"]:
                if version.get(change_type):
                    lines.append(f"### {change_type.title()}\n")
                    for item in version[change_type]:
                        lines.append(f"- {item}")
                    lines.append("")

        result = "\n".join(lines)
        out = self.output_dir / "CHANGELOG.md"
        out.write_text(result)
        return f"Changelog generated: {out}"

    def generate_api_docs(self, endpoints: list) -> str:
        lines = ["# API Documentation\n"]

        for ep in endpoints:
            method = ep.get("method", "GET")
            path = ep.get("path", "")
            summary = ep.get("summary", "")
            params = ep.get("parameters", [])
            response = ep.get("response", "")

            lines.append(f"## {method} `{path}`\n")
            lines.append(f"{summary}\n")

            if params:
                lines.append("### Parameters\n")
                lines.append(self.generate_table(
                    ["Name", "Type", "Required", "Description"],
                    [[p.get("name", ""), p.get("type", ""), str(p.get("required", False)),
                      p.get("description", "")] for p in params]
                ))
                lines.append("")

            if response:
                lines.append("### Response\n")
                lines.append(f"```json\n{json.dumps(response, indent=2)}\n```\n")

        result = "\n".join(lines)
        out = self.output_dir / "API_DOCS.md"
        out.write_text(result)
        return f"API docs generated: {out}"
