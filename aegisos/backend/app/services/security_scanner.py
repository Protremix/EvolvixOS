"""
Automated Security Scanner — Phase 27

Scans codebase for common security vulnerabilities.
"""

import os
import re
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.security_scanner")

# Vulnerability patterns
PATTERNS = {
    "hardcoded_secret": {
        "regex": r"(?:password|secret|api_key|private_key|token)\s*[:=]\s*['\"]([a-zA-Z0-9]{16,})['\"]",
        "severity": "high",
        "description": "Hardcoded secret/credential detected",
    },
    "sql_injection": {
        "regex": r"(?:execute|query|cursor\.execute)\s*\(\s*f['\"]|\.format\s*\(.*\+",
        "severity": "high",
        "description": "Potential SQL injection (string formatting in query)",
    },
    "xss_vulnerability": {
        "regex": r"innerHTML\s*=|document\.write\s*\(|eval\s*\(",
        "severity": "high",
        "description": "Potential XSS vulnerability",
    },
    "weak_crypto": {
        "regex": r"(?:md5|sha1)\s*\(",
        "severity": "medium",
        "description": "Weak hash algorithm (MD5/SHA1)",
    },
    "debug_mode": {
        "regex": r"DEBUG\s*=\s*True|debug\s*=\s*True",
        "severity": "medium",
        "description": "Debug mode enabled",
    },
    "unsafe_eval": {
        "regex": r"\beval\s*\(|exec\s*\(",
        "severity": "high",
        "description": "Unsafe eval/exec usage",
    },
    "insecure_random": {
        "regex": r"random\.random\(\)|random\.randint\(",
        "severity": "low",
        "description": "Insecure random number generator for security contexts",
    },
}


@dataclass
class SecurityFinding:
    id: str
    file: str
    line: int
    pattern: str
    severity: str
    description: str
    code_snippet: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class SecurityScanner:
    """Scans codebase for security vulnerabilities."""

    def __init__(self):
        self._findings: list[SecurityFinding] = []
        self._lock = threading.Lock()
        self._scan_count = 0

    def scan_file(self, file_path: str) -> list[SecurityFinding]:
        """Scan a single file for vulnerabilities."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return findings

        for i, line in enumerate(lines, 1):
            for pattern_name, pattern_info in PATTERNS.items():
                # Skip test files for debug_mode pattern
                if pattern_name == "debug_mode" and "test" in file_path.lower():
                    continue
                if pattern_name == "insecure_random" and "test" in file_path.lower():
                    continue

                match = re.search(pattern_info["regex"], line, re.IGNORECASE)
                if match:
                    finding = SecurityFinding(
                        id=f"sec-{self._scan_count}-{len(findings)}",
                        file=file_path,
                        line=i,
                        pattern=pattern_name,
                        severity=pattern_info["severity"],
                        description=pattern_info["description"],
                        code_snippet=line.strip()[:100],
                    )
                    findings.append(finding)

        return findings

    def scan_directory(self, directory: str, extensions: list[str] = None) -> list[SecurityFinding]:
        """Scan a directory recursively for vulnerabilities."""
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".sol", ".kt"]

        all_findings = []
        for root, dirs, files in os.walk(directory):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}]

            for filename in files:
                filepath = os.path.join(root, filename)
                if any(skip in filepath for skip in {"node_modules", "__pycache__", ".git/"}):
                    continue
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, filename)
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)

        with self._lock:
            self._findings.extend(all_findings)
            self._scan_count += 1

        logger.info("security_scan_complete", directory=directory, findings=len(all_findings))
        return all_findings

    def get_findings(self, severity: str = None, limit: int = 100) -> list[SecurityFinding]:
        """Get findings, optionally filtered by severity."""
        findings = self._findings
        if severity:
            findings = [f for f in findings if f.severity == severity]
        return findings[:limit]

    def get_summary(self) -> dict:
        """Get scan summary statistics."""
        by_severity = defaultdict(int)
        by_pattern = defaultdict(int)
        by_file = defaultdict(int)

        for f in self._findings:
            by_severity[f.severity] += 1
            by_pattern[f.pattern] += 1
            by_file[f.file] += 1

        return {
            "total_findings": len(self._findings),
            "scans_run": self._scan_count,
            "by_severity": dict(by_severity),
            "by_pattern": dict(by_pattern),
            "top_files": sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10],
            "last_scan": datetime.utcnow().isoformat() if self._findings else None,
        }

    def clear(self):
        with self._lock:
            self._findings.clear()
            self._scan_count = 0


_service: Optional[SecurityScanner] = None

def get_security_scanner() -> SecurityScanner:
    global _service
    if _service is None:
        _service = SecurityScanner()
    return _service
