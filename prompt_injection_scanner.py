"""
EvolvixOS Prompt Injection Scanner v1.0
Adapted from ECC Security Guide & AgentShield — MIT licensed (affaan-m/ECC)

Security scanning for agent inputs, skills, and MCP configs.
Based on real CVE research (Check Point, Snyk ToxicSkills, OWASP MCP Top 10).

Key threats addressed:
  1. Direct prompt injection via user/external input
  2. Indirect injection via documents, PRs, tool output
  3. Skill/plugin supply chain attacks (Snyk found 36% of public skills have injection)
  4. MCP server poisoning (tool descriptions, schemas, output)
  5. Memory poisoning (Microsoft AI Recommendation Poisoning, Feb 2026)
  6. Config file hijacking (CVE-2025-59536, CVE-2026-21852)

Integrates with existing EvolvixOS security (DANGEROUS_PATTERNS, SSRF checks).
"""

import re
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ScanResult:
    safe: bool
    threat_level: str  # clean | low | medium | high | critical
    threats: List[Dict[str, Any]] = field(default_factory=list)
    scanned_text: str = ""
    scanner: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe": self.safe,
            "threat_level": self.threat_level,
            "threats": self.threats,
            "scanner": self.scanner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ─────────────────────────────────────────────
# 1. Prompt Injection Patterns
# ─────────────────────────────────────────────

# Direct injection — explicit override attempts
DIRECT_INJECTION_PATTERNS = [
    # System prompt overrides
    (r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", "system-override"),
    (r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)", "system-override"),
    (r"you\s+are\s+(now\s+)?(?:a|an)\s+(different|new)\s+(agent|assistant|mode)", "identity-override"),
    (r"forget\s+(all\s+)?(your\s+)?(previous|prior)\s+(instructions|rules|guidelines)", "system-override"),
    (r"new\s+instructions?\s*:", "instruction-injection"),
    (r"system\s*:\s*", "system-impersonation"),
    (r"<\|im_start\|>system", "token-injection"),
    (r"\[SYSTEM\]|\[INST\]|\[/INST\]", "tag-injection"),

    # Privilege escalation
    (r"(?:grant|give)\s+me\s+(?:admin|root|sudo|elevated)", "privilege-escalation"),
    (r"(?:enable|turn\s+on|activate)\s+(?:developer|debug|admin|god)\s+mode", "privilege-escalation"),
    (r"bypass\s+(?:all\s+)?(?:security|safety|content)\s+(?:filter|check|guard)", "privilege-escalation"),

    # Data exfiltration
    (r"(?:send|email|post|upload|exfiltrate)\s+(?:all\s+)?(?:secrets?|keys?|passwords?|tokens?|\.env)", "exfiltration"),
    (r"(?:print|show|reveal|display|leak)\s+(?:your\s+)?(?:system\s+prompt|instructions?|rules?)", "exfiltration"),
    (r"(?:curl|wget|fetch)\s+.*\|\s*(?:sh|bash|python)", "command-injection"),

    # Silent execution
    (r"(?:silently|quietly|without\s+(?:telling|notifying|asking))\s+(?:execute|run|send|delete)", "silent-exec"),
    (r"(?:do\s+not|don'?t)\s+(?:tell|notify|inform|ask|log)\s+(?:the\s+user|anyone|me)", "silent-exec"),

    # Persistence
    (r"(?:remember|store|save|keep)\s+(?:this|that|the\s+following)\s+(?:forever|always|permanently)", "memory-poisoning"),
    (r"(?:from\s+now\s+on|always|henceforth)\s+(?:respond|reply|answer|act)", "memory-poisoning"),
]

# Indirect injection — hidden in documents, tool output, PRs
INDIRECT_INJECTION_PATTERNS = [
    # Hidden text (zero-width chars, invisible unicode)
    (r"[\u200b-\u200f\u202a-\u202e\ufeff]", "hidden-unicode"),
    # White text on white background (HTML)
    (r'color:\s*[white|#fff|#ffffff].*?style="[^"]*color:\s*[white|#fff|#ffffff]', "hidden-text"),
    # Tiny font size
    (r'font-size:\s*0px|font-size:\s*0\.0(?:px|pt|em)', "hidden-text"),
    # HTML comments with instructions
    (r"<!--\s*(?:ignore|disregard|forget|system|admin|execute|run)", "hidden-instruction"),
    # Markdown images that are actually prompts
    (r"!\[.*?\]\(.*?\)\{.*?prompt.*?\}", "image-prompt-injection"),
    # Base64 encoded instructions
    (r"(?:base64|b64)\s*[:=]\s*[A-Za-z0-9+/=]{40,}", "encoded-injection"),
]

# Skill/plugin supply chain patterns (Snyk ToxicSkills findings)
SKILL_INJECTION_PATTERNS = [
    # Exfiltration via webhook/API calls
    (r"https?://[^\s\"]+(?:webhook|ngrok|hook|catch|request\.bin|pipedream)", "skill-exfil"),
    (r"(?:fetch|axios|requests?|urllib)\s*\(\s*['\"]https?://(?!localhost|127\.0\.0\.1)", "skill-exfil"),
    # Dynamic code execution
    (r"eval\s*\(|new\s+Function\s*\(|exec\s*\(|child_process\.exec", "skill-rce"),
    (r"import\s*\(\s*['\"]https?://", "dynamic-import"),
    # Environment variable harvesting
    (r"process\.env|os\.environ|getenv\s*\(", "env-harvest"),
    # File system access beyond skill scope
    (r"\.\./\.\./\.\./|/etc/passwd|/etc/shadow|~/.ssh", "fs-traversal"),
]


# ─────────────────────────────────────────────
# 2. Scanner Functions
# ─────────────────────────────────────────────

def scan_input(text: str, source: str = "user") -> ScanResult:
    """
    Scan user/external input for prompt injection.

    Args:
        text: Input text to scan
        source: Where the input came from (user, document, pr, tool_output, email)

    Returns:
        ScanResult with threat assessment
    """
    threats = []
    text_lower = text.lower()

    # Check direct injection patterns
    for pattern, threat_type in DIRECT_INJECTION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            threats.append({
                "type": threat_type,
                "category": "direct-injection",
                "match": m.group()[:100],
                "position": m.start(),
                "source": source,
                "severity": "high" if "override" in threat_type or "exfiltration" in threat_type else "medium",
            })

    # Check indirect injection patterns
    for pattern, threat_type in INDIRECT_INJECTION_PATTERNS:
        matches = re.finditer(pattern, text)
        for m in matches:
            threats.append({
                "type": threat_type,
                "category": "indirect-injection",
                "match": f"[hidden chars at pos {m.start()}]" if "unicode" in threat_type else m.group()[:100],
                "position": m.start(),
                "source": source,
                "severity": "critical" if "hidden" in threat_type else "medium",
            })

    # Determine threat level
    if not threats:
        return ScanResult(safe=True, threat_level="clean", threats=[], scanner="prompt-injection")

    critical = sum(1 for t in threats if t["severity"] == "critical")
    high = sum(1 for t in threats if t["severity"] == "high")

    if critical > 0 or high > 1:
        level = "critical"
    elif high > 0:
        level = "high"
    elif len(threats) > 3:
        level = "medium"
    else:
        level = "low"

    return ScanResult(
        safe=level not in ("high", "critical"),
        threat_level=level,
        threats=threats,
        scanned_text=text[:200],
        scanner="prompt-injection",
    )


def scan_skill(skill_content: str, skill_name: str = "") -> ScanResult:
    """
    Scan an imported skill/plugin for supply chain attacks.
    Based on Snyk ToxicSkills findings (36% of public skills had injection).
    """
    threats = []

    # Check skill injection patterns
    for pattern, threat_type in SKILL_INJECTION_PATTERNS:
        matches = re.finditer(pattern, skill_content, re.IGNORECASE)
        for m in matches:
            threats.append({
                "type": threat_type,
                "category": "skill-supply-chain",
                "match": m.group()[:100],
                "position": m.start(),
                "skill": skill_name,
                "severity": "critical" if "rce" in threat_type or "exfil" in threat_type else "high",
            })

    # Also run direct injection scan on skill content
    direct_result = scan_input(skill_content, source=f"skill:{skill_name}")
    threats.extend(direct_result.threats)

    if not threats:
        return ScanResult(safe=True, threat_level="clean", threats=[], scanner="skill-supply-chain")

    critical = sum(1 for t in threats if t["severity"] == "critical")
    if critical > 0:
        level = "critical"
    elif len(threats) > 2:
        level = "high"
    else:
        level = "medium"

    return ScanResult(
        safe=level not in ("high", "critical"),
        threat_level=level,
        threats=threats,
        scanned_text=f"skill:{skill_name}",
        scanner="skill-supply-chain",
    )


def scan_mcp_config(config: Dict[str, Any]) -> ScanResult:
    """
    Scan MCP server configuration for poisoning.
    Based on OWASP MCP Top 10.
    """
    threats = []

    servers = config.get("mcpServers", config.get("servers", {}))

    for name, server_config in servers.items():
        # Check for suspicious endpoints
        url = server_config.get("url", server_config.get("command", ""))
        if isinstance(url, str):
            # Non-local endpoints
            if re.search(r"https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)", url):
                threats.append({
                    "type": "external-mcp-endpoint",
                    "category": "mcp-poisoning",
                    "server": name,
                    "url": url[:200],
                    "severity": "high",
                })

            # Webhook-like URLs
            if re.search(r"webhook|ngrok|request\.bin|pipedream|hook\.", url, re.IGNORECASE):
                threats.append({
                    "type": "exfiltration-endpoint",
                    "category": "mcp-poisoning",
                    "server": name,
                    "url": url[:200],
                    "severity": "critical",
                })

        # Check for auto-approve (bypasses trust dialog)
        if server_config.get("autoApprove") or server_config.get("auto_approve"):
            threats.append({
                "type": "auto-approve-enabled",
                "category": "mcp-consent-abuse",
                "server": name,
                "severity": "high",
            })

        # Check for excessive permissions
        permissions = server_config.get("permissions", [])
        if "*" in permissions or "root" in permissions:
            threats.append({
                "type": "excessive-permissions",
                "category": "mcp-over-trust",
                "server": name,
                "permissions": permissions,
                "severity": "high",
            })

    if not threats:
        return ScanResult(safe=True, threat_level="clean", threats=[], scanner="mcp-config")

    critical = sum(1 for t in threats if t["severity"] == "critical")
    if critical > 0:
        level = "critical"
    elif len(threats) > 2:
        level = "high"
    else:
        level = "medium"

    return ScanResult(
        safe=level not in ("high", "critical"),
        threat_level=level,
        threats=threats,
        scanned_text=json.dumps(config)[:200],
        scanner="mcp-config",
    )


def scan_env_config(env_content: str) -> ScanResult:
    """
    Scan .env / config files for hijacking vectors.
    Based on CVE-2026-21852 (ANTHROPIC_BASE_URL override).
    """
    threats = []

    # Check for API URL overrides
    url_overrides = [
        r"ANTHROPIC_BASE_URL\s*=\s*https?://(?!api\.anthropic\.com)",
        r"OPENAI_BASE_URL\s*=\s*https?://(?!api\.openai\.com)",
        r"GROQ_BASE_URL\s*=\s*https?://(?!api\.groq\.com)",
        r"GOOGLE_BASE_URL\s*=\s*https?://(?!generativelanguage\.googleapis\.com)",
        r"OPENROUTER_BASE_URL\s*=\s*https?://(?!openrouter\.ai)",
    ]
    for pattern in url_overrides:
        matches = re.finditer(pattern, env_content)
        for m in matches:
            threats.append({
                "type": "api-url-override",
                "category": "config-hijack",
                "match": m.group()[:100],
                "severity": "critical",
                "cve_reference": "CVE-2026-21852",
            })

    # Check for trust bypass settings
    trust_bypass = [
        r"TRUST_ALL\s*=\s*true",
        r"SKIP_TRUST\s*=\s*true",
        r"AUTO_APPROVE\s*=\s*true",
        r"DISABLE_SECURITY\s*=\s*true",
    ]
    for pattern in trust_bypass:
        matches = re.finditer(pattern, env_content, re.IGNORECASE)
        for m in matches:
            threats.append({
                "type": "trust-bypass",
                "category": "config-hijack",
                "match": m.group()[:100],
                "severity": "high",
            })

    if not threats:
        return ScanResult(safe=True, threat_level="clean", threats=[], scanner="env-config")

    critical = sum(1 for t in threats if t["severity"] == "critical")
    level = "critical" if critical > 0 else "high"

    return ScanResult(
        safe=False,
        threat_level=level,
        threats=threats,
        scanned_text="[env content]",
        scanner="env-config",
    )


# ─────────────────────────────────────────────
# 3. Lethal Trifecta Check
# ─────────────────────────────────────────────

def check_lethal_trifecta(
    has_private_data: bool,
    has_untrusted_content: bool,
    has_external_communication: bool,
) -> Dict[str, Any]:
    """
    Simon Willison's lethal trifecta: when private data, untrusted content,
    and external communication all exist in the same runtime, prompt injection
    becomes data exfiltration.

    Returns risk assessment and mitigation recommendations.
    """
    score = sum([has_private_data, has_untrusted_content, has_external_communication])
    is_dangerous = score == 3

    mitigations = []
    if is_dangerous:
        mitigations = [
            "Isolate untrusted content processing in a separate context",
            "Use structured output parsing (not free-form text) for tool results",
            "Strip instructions from document content before feeding to the model",
            "Rate-limit outbound requests from the agent runtime",
            "Log all external communications for audit",
            "Use allowlists for outbound domains/IPs",
        ]

    return {
        "dangerous": is_dangerous,
        "score": f"{score}/3",
        "factors": {
            "private_data": has_private_data,
            "untrusted_content": has_untrusted_content,
            "external_communication": has_external_communication,
        },
        "mitigations": mitigations if is_dangerous else [],
        "reference": "https://simonwillison.net/2025/Apr/9/dual-llm-pattern/",
    }
