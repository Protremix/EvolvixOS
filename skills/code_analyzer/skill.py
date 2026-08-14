"""
EvolvixOS — Code Analyzer Skill
Analyze code: complexity, quality, security, dependencies, structure.
100% local using AST, radon, bandit. Zero tokens.

Pip: pip install radon bandit
License: MIT (radon), Apache-2.0 (bandit)
"""

import os
import ast
import json
import time
from pathlib import Path
from typing import Optional, List
from collections import Counter
from rich.console import Console

console = Console()


class Skill:
    """Code analyzer — quality, complexity, security. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/analysis"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "analyze")

        if action == "analyze":
            return self.analyze(args.get("path", ""), args.get("recursive", True))
        elif action == "complexity":
            return self.complexity(args.get("path", ""))
        elif action == "security":
            return self.security_scan(args.get("path", ""))
        elif action == "structure":
            return self.file_structure(args.get("path", ""))
        elif action == "imports":
            return self.imports_map(args.get("path", ""))
        elif action == "duplicates":
            return self.find_duplicates(args.get("path", ""))
        elif action == "dead_code":
            return self.find_dead_code(args.get("path", ""))
        elif action == "todo":
            return self.find_todos(args.get("path", ""))
        else:
            return (f"Unknown action: {action}. Use: analyze, complexity, security, "
                    "structure, imports, duplicates, dead_code, todo")

    def analyze(self, path: str, recursive: bool = True) -> str:
        if not path or not os.path.exists(path):
            return "Error: Path not found."

        if os.path.isfile(path):
            return self._analyze_file(path)
        return self._analyze_directory(path, recursive)

    def _analyze_file(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            tree = ast.parse(source)
            result = {
                "file": file_path,
                "lines": len(source.splitlines()),
                "chars": len(source),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
            }

            # Count docstrings
            docstrings = sum(1 for n in ast.walk(tree)
                           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                           and ast.get_docstring(n))
            result["docstrings"] = docstrings
            result["docstring_coverage"] = round(docstrings / max(1, result["functions"] + result["classes"]) * 100, 1)

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error analyzing {file_path}: {e}"

    def _analyze_directory(self, path: str, recursive: bool = True) -> str:
        results = {"directory": path, "files": {}, "summary": {}}
        py_files = list(Path(path).rglob("*.py")) if recursive else list(Path(path).glob("*.py"))

        total_lines = 0
        total_functions = 0
        total_classes = 0

        for py_file in py_files[:100]:
            analysis = self._analyze_file(str(py_file))
            if not analysis.startswith("Error"):
                data = json.loads(analysis)
                results["files"][str(py_file)] = data
                total_lines += data.get("lines", 0)
                total_functions += data.get("functions", 0)
                total_classes += data.get("classes", 0)

        results["summary"] = {
            "total_files": len(results["files"]),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
        }

        return json.dumps(results, indent=2)[:15000]

    def complexity(self, path: str) -> str:
        try:
            from radon.complexity import cc_visit, cc_rank
            from radon.metrics import h_visit

            if os.path.isfile(path):
                return self._cc_file(path, cc_visit, cc_rank)
            results = {}
            for py_file in Path(path).rglob("*.py"):
                r = self._cc_file(str(py_file), cc_visit, cc_rank)
                results[str(py_file)] = json.loads(r) if not r.startswith("Error") else r
            return json.dumps(results, indent=2)[:10000]
        except ImportError:
            return "Error: pip install radon"
        except Exception as e:
            return f"Error: {e}"

    def _cc_file(self, path, cc_visit, cc_rank):
        try:
            with open(path) as f:
                source = f.read()
            results = cc_visit(source)
            functions = []
            for r in results:
                functions.append({
                    "name": r.name,
                    "complexity": r.complexity,
                    "rank": cc_rank(r.complexity),
                    "lineno": r.lineno,
                })
            functions.sort(key=lambda x: -x["complexity"])
            return json.dumps(functions[:20], indent=2)
        except Exception as e:
            return f"Error: {e}"

    def security_scan(self, path: str) -> str:
        try:
            import bandit
            from bandit.core.manager import BanditManager
            from bandit.core.config import BanditConfig

            b_conf = BanditConfig()
            mgr = BanditManager(b_conf, "file")
            mgr.discover_files([path])
            mgr.run_tests()
            results = mgr.get_issue_list()

            issues = []
            for issue in results:
                issues.append({
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "text": issue.text,
                    "file": issue.fname,
                    "line": issue.lineno,
                    "test_id": issue.test_id,
                })

            return json.dumps({
                "total_issues": len(issues),
                "high": sum(1 for i in issues if i["severity"] == "HIGH"),
                "medium": sum(1 for i in issues if i["severity"] == "MEDIUM"),
                "low": sum(1 for i in issues if i["severity"] == "LOW"),
                "issues": issues[:50],
            }, indent=2)
        except ImportError:
            return "Error: pip install bandit"
        except Exception as e:
            return f"Error: {e}"

    def file_structure(self, path: str) -> str:
        if not os.path.exists(path):
            return "Error: Path not found."

        tree = {"name": Path(path).name, "type": "dir", "children": []}

        def build_tree(dir_path, node, depth=0):
            if depth > 5:
                return
            for item in sorted(Path(dir_path).iterdir()):
                if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", ".git"):
                    continue
                child = {"name": item.name, "type": "dir" if item.is_dir() else "file"}
                if child["type"] == "dir":
                    child["children"] = []
                    build_tree(item, child, depth + 1)
                else:
                    child["size"] = f"{item.stat().st_size} bytes"
                node["children"].append(child)

        build_tree(path, tree)
        return json.dumps(tree, indent=2)[:15000]

    def imports_map(self, path: str) -> str:
        import_map = {}
        for py_file in Path(path).rglob("*.py"):
            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        imports.append(node.module or "")
                if imports:
                    import_map[str(py_file)] = imports
            except Exception:
                pass
        return json.dumps(import_map, indent=2)[:10000]

    def find_duplicates(self, path: str) -> str:
        hashes = {}
        duplicates = []
        for py_file in Path(path).rglob("*.py"):
            try:
                content = Path(py_file).read_text()
                h = hash(content)
                if h in hashes:
                    duplicates.append({"file1": hashes[h], "file2": str(py_file)})
                else:
                    hashes[h] = str(py_file)
            except Exception:
                pass
        return json.dumps({"duplicates": duplicates}, indent=2)

    def find_dead_code(self, path: str) -> str:
        """Find potentially unused functions/classes (heuristic)."""
        all_defs = []
        all_refs = set()

        for py_file in Path(path).rglob("*.py"):
            try:
                source = Path(py_file).read_text()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        all_defs.append({"name": node.name, "file": str(py_file), "line": node.lineno})
                    if isinstance(node, ast.Name):
                        all_refs.add(node.id)
                    if isinstance(node, ast.Attribute):
                        all_refs.add(node.attr)
            except Exception:
                pass

        unused = [d for d in all_defs if d["name"] not in all_refs and not d["name"].startswith("_")]
        return json.dumps({"potentially_unused": unused[:50]}, indent=2)

    def find_todos(self, path: str) -> str:
        todos = []
        for py_file in Path(path).rglob("*.py"):
            try:
                for i, line in enumerate(Path(py_file).read_text().splitlines(), 1):
                    if "TODO" in line or "FIXME" in line or "HACK" in line or "XXX" in line:
                        todos.append({"file": str(py_file), "line": i, "text": line.strip()})
            except Exception:
                pass
        return json.dumps({"todos": todos[:50]}, indent=2)
