"""
EvolvixOS — Security Scanner Skill
Scan code for vulnerabilities, secrets, dependencies with known CVEs.
100% local using bandit + safety. Zero tokens.

Pip: pip install bandit safety
License: Apache-2.0 (bandit), MIT (safety)
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Security scanner — find vulnerabilities in code. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/security"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "scan")

        if action == "scan":
            return self.scan(args.get("path", ""))
        elif action == "check_deps":
            return self.check_dependencies(args.get("requirements_file", "requirements.txt"))
        elif action == "find_secrets":
            return self.find_secrets(args.get("path", ""))
        elif action == "check_permissions":
            return self.check_permissions(args.get("path", ""))
        else:
            return f"Unknown action: {action}. Use: scan, check_deps, find_secrets, check_permissions"

    def scan(self, path: str) -> str:
        if not path or not os.path.exists(path):
            return "Error: Path not found."

        try:
            from bandit.core.manager import BanditManager
            from bandit.core.config import BanditConfig

            b_conf = BanditConfig()
            mgr = BanditManager(b_conf, "file")
            mgr.discover_files([path])
            mgr.run_tests()

            issues = []
            for issue in mgr.get_issue_list():
                issues.append({
                    "severity": str(issue.severity),
                    "confidence": str(issue.confidence),
                    "description": issue.text,
                    "file": issue.fname,
                    "line": issue.lineno,
                    "test_id": issue.test_id,
                    "cwe": issue.cwe,
                })

            result = {
                "path": path,
                "total_issues": len(issues),
                "by_severity": {
                    "HIGH": sum(1 for i in issues if i["severity"] == "HIGH"),
                    "MEDIUM": sum(1 for i in issues if i["severity"] == "MEDIUM"),
                    "LOW": sum(1 for i in issues if i["severity"] == "LOW"),
                },
                "issues": issues[:100],
            }

            out = self.output_dir / f"security_report_{int(__import__('time').time())}.json"
            out.write_text(json.dumps(result, indent=2))

            return json.dumps(result, indent=2)[:10000]
        except ImportError:
            return "Error: pip install bandit"
        except Exception as e:
            return f"Error: {e}"

    def check_dependencies(self, req_file: str = "requirements.txt") -> str:
        if not os.path.exists(req_file):
            return f"Error: {req_file} not found."

        try:
            result = subprocess.run(
                ["safety", "check", "--file", req_file, "--json"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return json.dumps({"vulnerable": False, "message": "No known vulnerabilities found."}, indent=2)
            try:
                vulns = json.loads(result.stdout)
                return json.dumps({"vulnerable": True, "vulnerabilities": vulns}, indent=2)
            except json.JSONDecodeError:
                return result.stdout[:5000]
        except FileNotFoundError:
            return "Error: pip install safety"
        except Exception as e:
            return f"Error: {e}"

    def find_secrets(self, path: str) -> str:
        """Scan for hardcoded secrets (API keys, passwords, tokens)."""
        import re

        patterns = [
            (r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]", "API Key"),
            (r"password\s*[:=]\s*['\"][^'\"]+['\"]", "Password"),
            (r"secret\s*[:=]\s*['\"][^'\"]+['\"]", "Secret"),
            (r"token\s*[:=]\s*['\"][^'\"]+['\"]", "Token"),
            (r"BEGIN.*PRIVATE KEY", "Private Key"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
            (r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "JWT Token"),
        ]

        findings = []
        scan_path = Path(path)
        files = scan_path.rglob("*") if scan_path.is_dir() else [scan_path]

        for f in files:
            if not f.is_file() or f.suffix in (".pyc", ".so", ".dll", ".exe"):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    for pattern, name in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                "file": str(f),
                                "line": i,
                                "type": name,
                                "preview": line.strip()[:100],
                            })
            except Exception:
                pass

        return json.dumps({
            "total_secrets_found": len(findings),
            "findings": findings[:50],
        }, indent=2)

    def check_permissions(self, path: str) -> str:
        """Check for insecure file permissions."""
        insecure = []
        scan_path = Path(path)
        files = scan_path.rglob("*") if scan_path.is_dir() else [scan_path]

        for f in files:
            if not f.is_file():
                continue
            try:
                perms = oct(f.stat().st_mode)[-3:]
                if f.suffix in (".sh", ".py", ".js") and "7" in perms:
                    insecure.append({
                        "file": str(f),
                        "permissions": perms,
                        "issue": "World-writable executable" if perms[-1] == "7" else "Executable by others",
                    })
                # Check for readable private files
                if f.name in (".env", "config.json", "secrets.json", ".npmrc", ".pypirc"):
                    if perms[-1] != "0":
                        insecure.append({
                            "file": str(f),
                            "permissions": perms,
                            "issue": "Sensitive file readable by others",
                        })
            except Exception:
                pass

        return json.dumps({"insecure_files": insecure[:50]}, indent=2)
