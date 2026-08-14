"""
EvolvixOS — Auto Auditor Skill
Automatic code/file/directory auditing system for security, code quality, performance, best practices, and dependencies.
"""

import os
import re
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Known CVE Database for popular Python/JS packages
KNOWN_CVES: Dict[str, List[Dict[str, str]]] = {
    "requests": [
        {"max_version": "2.20.0", "cve": "CVE-2018-18074", "severity": "high", "summary": "Redirect credentials leak across hosts"}
    ],
    "flask": [
        {"max_version": "2.0.0", "cve": "CVE-2019-1010083", "severity": "medium", "summary": "Unexpected memory usage in request handling"}
    ],
    "django": [
        {"max_version": "3.2.14", "cve": "CVE-2022-34265", "severity": "critical", "summary": "SQL Injection vulnerability in Trunc/Extract database functions"}
    ],
    "pyyaml": [
        {"max_version": "5.4.0", "cve": "CVE-2020-14343", "severity": "critical", "summary": "Arbitrary code execution via full_load / load without Loader"}
    ],
    "urllib3": [
        {"max_version": "1.26.5", "cve": "CVE-2021-33503", "severity": "high", "summary": "ReDoS vulnerability in URL authority parsing"}
    ],
    "jinja2": [
        {"max_version": "2.11.3", "cve": "CVE-2020-28493", "severity": "medium", "summary": "ReDoS in urlize filter"}
    ],
    "pillow": [
        {"max_version": "9.0.0", "cve": "CVE-2022-22817", "severity": "high", "summary": "Arbitrary code execution in ImageMath.eval"}
    ],
    "lodash": [
        {"max_version": "4.17.21", "cve": "CVE-2021-23337", "severity": "high", "summary": "Command injection via template function"}
    ],
    "express": [
        {"max_version": "4.16.0", "cve": "CVE-2019-10777", "severity": "high", "summary": "Open redirect vulnerability"}
    ],
    "axios": [
        {"max_version": "0.21.1", "cve": "CVE-2020-28168", "severity": "medium", "summary": "SSRF vulnerability"}
    ],
    "cryptography": [
        {"max_version": "3.3.2", "cve": "CVE-2020-36242", "severity": "high", "summary": "Buffer overflow in PKCS12 parsing"}
    ]
}


def _parse_version(ver_str: str) -> Tuple[int, ...]:
    """Parse version string into tuple of integers for comparison."""
    clean = re.sub(r"[^\d.]", "", ver_str.split("-")[0].split("+")[0])
    parts = [int(p) for p in clean.split(".") if p.isdigit()]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


class AuditVisitor(ast.NodeVisitor):
    """AST Visitor for Python source code auditing."""

    def __init__(self, filename: str, code_lines: List[str]):
        self.filename = filename
        self.code_lines = code_lines
        self.findings: List[Dict[str, Any]] = []
        self.imported_names: Dict[str, int] = {}  # name -> line
        self.used_names: Set[str] = set()
        self.in_loop = False
        self.loop_depth = 0

    def add_finding(
        self,
        category: str,
        rule: str,
        severity: str,
        title: str,
        message: str,
        line: int,
        snippet: str = "",
        recommendation: str = ""
    ):
        if not snippet and 1 <= line <= len(self.code_lines):
            snippet = self.code_lines[line - 1].strip()

        finding_id = f"{category.upper()[:3]}-{len(self.findings) + 1:03d}"
        self.findings.append({
            "id": finding_id,
            "category": category,
            "rule": rule,
            "severity": severity,
            "title": title,
            "message": message,
            "file": self.filename,
            "line": line,
            "code_snippet": snippet,
            "recommendation": recommendation
        })

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name != "*":
                name = alias.asname or alias.name
                self.imported_names[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        was_loop = self.in_loop
        self.in_loop = True
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        self.in_loop = was_loop

    def visit_While(self, node: ast.While):
        was_loop = self.in_loop
        self.in_loop = True
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
        self.in_loop = was_loop

    def visit_Call(self, node: ast.Call):
        # 1. SQL Injection check in DB query execution calls
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        if func_name in ("execute", "executemany", "query", "raw", "raw_query"):
            if node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.JoinedStr):  # f-string
                    self.add_finding(
                        category="security",
                        rule="sql_injection",
                        severity="high",
                        title="SQL Injection Vulnerability",
                        message="Dynamic f-string used in database query execution.",
                        line=node.lineno,
                        recommendation="Use parameterized queries with placeholder bindings (e.g. cursor.execute('SELECT * FROM t WHERE id = %s', (val,)))"
                    )
                elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, (ast.Mod, ast.Add)):
                    self.add_finding(
                        category="security",
                        rule="sql_injection",
                        severity="high",
                        title="SQL Injection Vulnerability",
                        message="String formatting or concatenation used in database query execution.",
                        line=node.lineno,
                        recommendation="Parameterize SQL queries instead of string concatenation/formatting."
                    )

        # 2. Insecure Deserialization
        if func_name in ("loads", "load") and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id in ("pickle", "marshal", "cPickle"):
                self.add_finding(
                    category="security",
                    rule="insecure_deserialization",
                    severity="critical",
                    title="Insecure Deserialization (pickle/marshal)",
                    message=f"Use of {node.func.value.id}.{func_name} can execute arbitrary code on untrusted input.",
                    line=node.lineno,
                    recommendation="Avoid pickle for untrusted data. Use JSON, Protocol Buffers, or safe serialization formats."
                )
            elif isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
                loader_spec = any(kw.arg == "Loader" for kw in node.keywords)
                if not loader_spec:
                    self.add_finding(
                        category="security",
                        rule="insecure_deserialization",
                        severity="critical",
                        title="Insecure YAML Loading",
                        message="yaml.load called without specifying Loader=yaml.SafeLoader",
                        line=node.lineno,
                        recommendation="Use yaml.safe_load(data) or yaml.load(data, Loader=yaml.SafeLoader)"
                    )

        # 3. Command Execution
        if func_name in ("system", "popen") and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                self.add_finding(
                    category="security",
                    rule="command_injection",
                    severity="critical",
                    title="Potential Command Injection",
                    message="os.system or os.popen executes command strings through shell.",
                    line=node.lineno,
                    recommendation="Use subprocess.run(['cmd', 'arg1'], shell=False) with array arguments."
                )

        if func_name in ("call", "Popen", "run", "check_output") and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.add_finding(
                            category="security",
                            rule="command_injection",
                            severity="critical",
                            title="Command Injection via shell=True",
                            message="subprocess call executed with shell=True",
                            line=node.lineno,
                            recommendation="Set shell=False and pass arguments as a list."
                        )

        # 4. Dangerous eval/exec
        if func_name in ("eval", "exec") and isinstance(node.func, ast.Name):
            self.add_finding(
                category="security",
                rule="command_injection",
                severity="critical",
                title="Use of Dynamic Code Execution (eval/exec)",
                message=f"Use of {func_name}() allows arbitrary code execution.",
                line=node.lineno,
                recommendation="Avoid eval/exec; use ast.literal_eval or structured logic instead."
            )

        # 5. Performance: N+1 queries in loops
        if self.in_loop and func_name in ("execute", "query", "filter", "filter_by", "get", "fetch", "all"):
            self.add_finding(
                category="performance",
                rule="n_plus_one_query",
                severity="medium",
                title="Possible N+1 Query in Loop",
                message=f"Database query operation '{func_name}' executed inside loop body.",
                line=node.lineno,
                recommendation="Batch database queries outside loops or use JOIN / eager loading."
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check authorization checks in endpoint / handler functions
        is_route = False
        for dec in node.decorator_list:
            dec_name = ""
            if isinstance(dec, ast.Name):
                dec_name = dec.id
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    dec_name = dec.func.id
                elif isinstance(dec.func, ast.Attribute):
                    dec_name = dec.func.attr
            if "route" in dec_name or "get" in dec_name or "post" in dec_name:
                is_route = True

        if is_route:
            # check input validation
            if node.args.args and len(node.body) > 0:
                has_check = any(isinstance(stmt, (ast.If, ast.Assert)) for stmt in node.body[:3])
                if not has_check:
                    self.add_finding(
                        category="best_practices",
                        rule="input_validation",
                        severity="medium",
                        title="Missing Input Validation on Endpoint",
                        message=f"Route function '{node.name}' receives parameters without explicit validation check.",
                        line=node.lineno,
                        recommendation="Validate parameters (types, required fields, formats) at the start of the request handler."
                    )

            # check auth decorator
            has_auth = any(
                "auth" in ast.dump(dec).lower() or "login" in ast.dump(dec).lower() or "jwt" in ast.dump(dec).lower()
                for dec in node.decorator_list
            )
            if not has_auth and "public" not in node.name.lower():
                self.add_finding(
                    category="best_practices",
                    rule="authentication",
                    severity="low",
                    title="Unauthenticated Endpoint Handler",
                    message=f"Route handler '{node.name}' has no login_required or auth decorator.",
                    line=node.lineno,
                    recommendation="Add authentication middleware or auth decorators to sensitive endpoints."
                )

        # Check variable naming in function arguments
        for arg in node.args.args:
            if len(arg.arg) == 1 and arg.arg not in ("i", "j", "k", "x", "y", "z", "e", "f", "_"):
                self.add_finding(
                    category="quality",
                    rule="poor_naming",
                    severity="low",
                    title="Non-descriptive Parameter Name",
                    message=f"Parameter name '{arg.arg}' is too short/non-descriptive.",
                    line=node.lineno,
                    recommendation="Use clear, descriptive parameter names."
                )

        # Check dead code after return / raise
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                if i < len(node.body) - 1:
                    dead_stmt = node.body[i + 1]
                    self.add_finding(
                        category="quality",
                        rule="dead_code",
                        severity="medium",
                        title="Unreachable Code Detected",
                        message=f"Code following line {stmt.lineno} is unreachable due to return/raise/break.",
                        line=dead_stmt.lineno,
                        recommendation="Remove unreachable dead code statements."
                    )
                break

        # Check missing error handling in functions performing I/O or network requests
        has_io = False
        has_try = False
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Try):
                has_try = True
            if isinstance(stmt, ast.Call):
                fn = ""
                if isinstance(stmt.func, ast.Name):
                    fn = stmt.func.id
                elif isinstance(stmt.func, ast.Attribute):
                    fn = stmt.func.attr
                if fn in ("open", "get", "post", "loads", "dumps", "read", "connect"):
                    has_io = True

        if has_io and not has_try and len(node.body) > 3:
            self.add_finding(
                category="quality",
                rule="missing_error_handling",
                severity="medium",
                title="Missing Error Handling",
                message=f"Function '{node.name}' performs I/O or network calls without try/except error handling.",
                line=node.lineno,
                recommendation="Wrap I/O, network, or parsing operations in try-except blocks."
            )

        self.generic_visit(node)


class Skill:
    """Auto Auditor Skill for EvolvixOS."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def _detect_language(self, target: str, code_content: str, explicit_lang: Optional[str] = None) -> str:
        if explicit_lang:
            return explicit_lang.lower()

        ext = os.path.splitext(target)[1].lower()
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".htm": "html",
            ".php": "php",
            ".sql": "sql",
            ".json": "json",
            ".sh": "bash",
            ".bash": "bash"
        }
        if ext in ext_map:
            return ext_map[ext]

        if "def " in code_content or "import " in code_content or "class " in code_content:
            return "python"
        elif "function " in code_content or "const " in code_content or "let " in code_content:
            return "javascript"
        elif "<html" in code_content.lower() or "<!doctype html>" in code_content.lower():
            return "html"
        elif "SELECT " in code_content.upper() or "CREATE TABLE" in code_content.upper():
            return "sql"

        return "python"

    def _scan_regex_patterns(self, content: str, filename: str, lang: str) -> List[Dict[str, Any]]:
        findings = []
        lines = content.splitlines()

        def add_regex_finding(category, rule, severity, title, message, line_num, snippet, recommendation):
            findings.append({
                "id": f"{category.upper()[:3]}-{len(findings) + 1:03d}",
                "category": category,
                "rule": rule,
                "severity": severity,
                "title": title,
                "message": message,
                "file": filename,
                "line": line_num,
                "code_snippet": snippet.strip(),
                "recommendation": recommendation
            })

        # 1. SQL Injection regex check (e.g. f"SELECT ... {x}")
        sql_pattern = r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?\b(?:WHERE|SET|VALUES|INTO)\b.*?f['\"].*?\{"
        sql_pattern_2 = r"(?i)\w+\s*=\s*f['\"][^'\"]*(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?\{"
        for idx, line in enumerate(lines, 1):
            if re.search(sql_pattern, line) or re.search(sql_pattern_2, line):
                add_regex_finding(
                    category="security",
                    rule="sql_injection",
                    severity="high",
                    title="SQL Injection Risk",
                    message="Formatted SQL query string using dynamic string interpolation.",
                    line_num=idx,
                    snippet=line,
                    recommendation="Parameterize SQL queries using database placeholder bindings."
                )

        # 2. Hardcoded Secrets (API keys, AWS tokens, passwords, private keys)
        secret_patterns = [
            (r"(?i)(?:api_key|apikey|secret_key|private_key|auth_token|password|passwd)\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded API/Secret Key"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
            (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "Hardcoded Private Key"),
            (r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+", "Hardcoded JWT Token"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token")
        ]

        for idx, line in enumerate(lines, 1):
            for pattern, name in secret_patterns:
                if re.search(pattern, line):
                    if "os.getenv" in line or "os.environ" in line or "ENV" in line or "YOUR_" in line or "example" in line.lower():
                        continue
                    add_regex_finding(
                        category="security",
                        rule="hardcoded_secret",
                        severity="critical",
                        title=f"Hardcoded Secret Detected ({name})",
                        message=f"Sensitive secret/credential found in source code: {name}.",
                        line_num=idx,
                        snippet=line,
                        recommendation="Store secrets in environment variables or external secret managers (e.g. os.getenv('API_KEY'))."
                    )

        # 3. XSS Vulnerabilities
        xss_patterns = [
            (r"innerHTML\s*=", "Direct innerHTML assignment"),
            (r"document\.write\(", "document.write usage"),
            (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML"),
            (r"v-html\s*=", "Vue v-html directive"),
            (r"\|\s*safe\b", "Jinja2 safe filter disabling HTML escaping")
        ]

        for idx, line in enumerate(lines, 1):
            for pattern, name in xss_patterns:
                if re.search(pattern, line):
                    add_regex_finding(
                        category="security",
                        rule="xss_vulnerability",
                        severity="high",
                        title="Potential XSS Vulnerability",
                        message=f"Disabling output encoding or direct DOM HTML insertion: {name}.",
                        line_num=idx,
                        snippet=line,
                        recommendation="Sanitize user input and use textContent or auto-escaping templates instead of raw HTML insertion."
                    )

        # 4. Path Traversal
        path_traversal_patterns = [
            (r"open\s*\(\s*(?:request\.|args\.|params\.|user_input|input_path|file_path)[^)]*\)", "Direct open on unsanitized file path"),
            (r"send_file\s*\(\s*(?:request\.|args\.|user_input)[^)]*\)", "Flask send_file with unsanitized path")
        ]

        for idx, line in enumerate(lines, 1):
            for pattern, name in path_traversal_patterns:
                if re.search(pattern, line):
                    if "abspath" not in line and "secure_filename" not in line and "resolve" not in line:
                        add_regex_finding(
                            category="security",
                            rule="path_traversal",
                            severity="high",
                            title="Path Traversal Risk",
                            message=f"{name} without directory verification or filename sanitization.",
                            line_num=idx,
                            snippet=line,
                            recommendation="Sanitize file names using werkzeug.utils.secure_filename or verify path lies inside allowed base directory."
                        )

        # 5. Performance: Inefficient loop string concatenation / Memory leak
        in_loop = False
        for idx, line in enumerate(lines, 1):
            if re.search(r"\b(for|while)\b.*:", line):
                in_loop = True
            elif in_loop and re.search(r"^\s*\w+\s*\+=\s*['\"]", line):
                add_regex_finding(
                    category="performance",
                    rule="inefficient_loop",
                    severity="low",
                    title="Inefficient String Concatenation in Loop",
                    message="Repeated string concatenation '+=' inside loop allocates new memory each iteration.",
                    line_num=idx,
                    snippet=line,
                    recommendation="Append strings to a list and join them with ''.join(list) after loop."
                )
                in_loop = False
            elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_loop = False

        # Memory Leak: unclosed file without 'with'
        for idx, line in enumerate(lines, 1):
            if re.search(r"^\s*\w+\s*=\s*open\([^)]+\)", line) and "with open" not in line:
                add_regex_finding(
                    category="performance",
                    rule="memory_leak",
                    severity="medium",
                    title="Unclosed File Descriptor Risk",
                    message="File opened without 'with' context manager or explicit close call.",
                    line_num=idx,
                    snippet=line,
                    recommendation="Use 'with open(...) as f:' context manager to ensure file handles are properly closed."
                )

        # Performance / Schema: Missing indexes
        if lang == "sql" or "CREATE TABLE" in content.upper():
            if "PRIMARY KEY" not in content.upper() and "INDEX" not in content.upper():
                add_regex_finding(
                    category="performance",
                    rule="missing_index",
                    severity="medium",
                    title="Missing Index on Table Schema",
                    message="Table definition lacks PRIMARY KEY or INDEX specifications.",
                    line_num=1,
                    snippet=lines[0] if lines else "",
                    recommendation="Add PRIMARY KEY and INDEX declarations on frequently queried columns."
                )

        # 6. Best Practices: CSRF checks
        if lang in ("html", "python", "javascript"):
            for idx, line in enumerate(lines, 1):
                if "<form" in line.lower() and "method=\"post\"" in line.lower():
                    sub_lines = lines[idx:idx + 10]
                    has_csrf = any("csrf" in sl.lower() for sl in sub_lines)
                    if not has_csrf:
                        add_regex_finding(
                            category="best_practices",
                            rule="csrf_protection",
                            severity="medium",
                            title="Missing CSRF Token in Form",
                            message="HTML form with POST method missing anti-CSRF token input.",
                            line_num=idx,
                            snippet=line,
                            recommendation="Include an anti-CSRF hidden field in all state-changing HTML forms."
                        )

        return findings

    def _scan_dependencies(self, content: str, filename: str) -> List[Dict[str, Any]]:
        findings = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("//"):
                continue

            m = re.match(r"^([a-zA-Z0-9_\-]+)\s*==\s*([0-9a-zA-Z\.\-]+)", line_str)
            if not m:
                m = re.match(r"^\s*\"([a-zA-Z0-9_\-]+)\"\s*:\s*\"[~^]?([0-9\.]+)\"", line_str)

            if m:
                pkg_name = m.group(1).lower()
                pkg_ver = m.group(2)

                if pkg_name in KNOWN_CVES:
                    for cve_info in KNOWN_CVES[pkg_name]:
                        max_v = _parse_version(cve_info["max_version"])
                        curr_v = _parse_version(pkg_ver)
                        if curr_v <= max_v:
                            findings.append({
                                "id": f"DEP-{len(findings) + 1:03d}",
                                "category": "dependencies",
                                "rule": "known_cve",
                                "severity": cve_info["severity"],
                                "title": f"Known CVE in Dependency '{pkg_name}'",
                                "message": f"Package {pkg_name}@{pkg_ver} is vulnerable to {cve_info['cve']}: {cve_info['summary']}",
                                "file": filename,
                                "line": idx,
                                "code_snippet": line_str,
                                "recommendation": f"Upgrade {pkg_name} to a version greater than {cve_info['max_version']}."
                            })

        return findings

    def audit_single_code(self, code_content: str, filename: str = "source_code", lang: Optional[str] = None) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        detected_lang = self._detect_language(filename, code_content, lang)

        # 1. AST Analysis for Python
        if detected_lang == "python":
            try:
                tree = ast.parse(code_content, filename=filename)
                visitor = AuditVisitor(filename, code_content.splitlines())
                visitor.visit(tree)
                findings.extend(visitor.findings)

                # Check unused imports
                for name, line_no in visitor.imported_names.items():
                    if name not in visitor.used_names:
                        findings.append({
                            "id": f"QUA-{len(findings) + 1:03d}",
                            "category": "quality",
                            "rule": "unused_import",
                            "severity": "low",
                            "title": "Unused Import Statement",
                            "message": f"Imported module/name '{name}' is never used in code.",
                            "file": filename,
                            "line": line_no,
                            "code_snippet": code_content.splitlines()[line_no - 1].strip() if line_no <= len(code_content.splitlines()) else "",
                            "recommendation": f"Remove unused import '{name}'."
                        })
            except SyntaxError as se:
                findings.append({
                    "id": f"SYN-{len(findings) + 1:03d}",
                    "category": "quality",
                    "rule": "syntax_error",
                    "severity": "high",
                    "title": "Python Syntax Error",
                    "message": f"Syntax error during parsing: {se.msg}",
                    "file": filename,
                    "line": se.lineno or 1,
                    "code_snippet": se.text.strip() if se.text else "",
                    "recommendation": "Fix syntax error to allow full compilation and static analysis."
                })

        # 2. Regex Pattern Analysis (all languages)
        regex_findings = self._scan_regex_patterns(code_content, filename, detected_lang)
        findings.extend(regex_findings)

        # 3. Dependency scan if file looks like requirements / package manifest
        if "requirements" in filename or "package.json" in filename or "Pipfile" in filename:
            dep_findings = self._scan_dependencies(code_content, filename)
            findings.extend(dep_findings)

        return findings

    def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run automatic audit on given target.
        args: {'target': 'path to file/dir/code', 'type': 'file/dir/code', 'lang': 'optional language'}
        """
        target = args.get("target", "")
        target_type = args.get("type", "").lower()
        lang = args.get("lang")

        if not target:
            return {
                "status": "error",
                "message": "Missing required argument 'target'",
                "score": 0,
                "findings": []
            }

        if not target_type:
            if os.path.isfile(target):
                target_type = "file"
            elif os.path.isdir(target):
                target_type = "dir"
            else:
                target_type = "code"

        all_findings: List[Dict[str, Any]] = []
        scanned_files: List[str] = []

        if target_type == "code":
            scanned_files.append("snippet.py")
            all_findings = self.audit_single_code(target, filename="snippet.py", lang=lang)

        elif target_type == "file":
            if not os.path.exists(target):
                return {"status": "error", "message": f"File not found: {target}"}
            scanned_files.append(target)
            try:
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                all_findings = self.audit_single_code(content, filename=target, lang=lang)
            except Exception as e:
                return {"status": "error", "message": f"Failed to read file {target}: {str(e)}"}

        elif target_type == "dir":
            if not os.path.exists(target):
                return {"status": "error", "message": f"Directory not found: {target}"}

            valid_exts = {".py", ".js", ".ts", ".html", ".htm", ".php", ".sql", ".sh", ".json", ".txt"}
            for root, _, files in os.walk(target):
                if any(ignored in root for ignored in [".git", "__pycache__", "node_modules", ".venv", "venv"]):
                    continue
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_exts or file in ("requirements.txt", "package.json", "Pipfile"):
                        filepath = os.path.join(root, file)
                        scanned_files.append(filepath)
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            file_findings = self.audit_single_code(content, filename=filepath, lang=lang)
                            all_findings.extend(file_findings)
                        except Exception:
                            continue

        # Calculate Score
        sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        cat_counts = {"security": 0, "quality": 0, "performance": 0, "best_practices": 0, "dependencies": 0}

        deductions = 0
        for f in all_findings:
            sev = f.get("severity", "medium").lower()
            cat = f.get("category", "quality").lower()

            if sev in sev_counts:
                sev_counts[sev] += 1
            if cat in cat_counts:
                cat_counts[cat] += 1

            if sev == "critical":
                deductions += 15
            elif sev == "high":
                deductions += 10
            elif sev == "medium":
                deductions += 5
            elif sev == "low":
                deductions += 2

        score = max(0, 100 - deductions)

        if score >= 95:
            grade = "A+"
        elif score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        recommendations: List[str] = []
        for f in all_findings:
            rec = f.get("recommendation")
            if rec and rec not in recommendations:
                recommendations.append(rec)

        return {
            "status": "success",
            "score": score,
            "grade": grade,
            "scanned_files": scanned_files,
            "scanned_files_count": len(scanned_files),
            "summary": {
                "total_issues": len(all_findings),
                "by_severity": sev_counts,
                "by_category": cat_counts
            },
            "findings": all_findings,
            "recommendations": recommendations[:10]
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_args = json.loads(sys.argv[1])
        res = Skill().run(raw_args)
        print(json.dumps(res, indent=2))
