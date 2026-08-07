"""
Dependency Graph Tracker.

Parses source files to extract import/dependency relationships,
builds a directed graph, detects circular dependencies, and
provides impact analysis for change propagation.
"""

import os
import re
import json
import logging
from typing import Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("evolvixos")


@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    file_path: str
    module_name: str
    language: str  # python, javascript, typescript
    imports: list[str] = field(default_factory=list)  # imported module names
    imported_by: list[str] = field(default_factory=list)  # who imports this
    line_count: int = 0
    is_entry_point: bool = False  # main.py, index.ts, etc.


@dataclass
class CircularDependency:
    """A detected circular dependency."""
    cycle: list[str]  # file paths in cycle order
    severity: str  # "critical" if <3 files, "warning" otherwise


class DependencyGraph:
    """Directed graph of file/module dependencies."""

    def __init__(self):
        self.nodes: dict[str, DependencyNode] = {}  # file_path -> node
        self.edges: dict[str, set[str]] = defaultdict(set)  # file -> set of files it depends on
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)  # file -> set of files that depend on it
        self.module_to_file: dict[str, str] = {}  # module name -> file path

    def add_node(self, node: DependencyNode):
        """Add a node to the graph."""
        self.nodes[node.file_path] = node
        if node.module_name:
            self.module_to_file[node.module_name] = node.file_path

    def add_edge(self, from_file: str, to_file: str):
        """Add a dependency edge: from_file depends on to_file."""
        self.edges[from_file].add(to_file)
        self.reverse_edges[to_file].add(from_file)

    def get_dependencies(self, file_path: str) -> list[str]:
        """Get all files that this file depends on."""
        return sorted(self.edges.get(file_path, set()))

    def get_dependents(self, file_path: str) -> list[str]:
        """Get all files that depend on this file (reverse deps)."""
        return sorted(self.reverse_edges.get(file_path, set()))

    def get_impact(self, file_path: str, max_depth: int = 10) -> dict:
        """Impact analysis: what files are affected if this file changes."""
        affected = set()
        queue = deque([(file_path, 0)])
        visited = {file_path}

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for dependent in self.reverse_edges.get(current, set()):
                if dependent not in visited:
                    visited.add(dependent)
                    affected.add(dependent)
                    queue.append((dependent, depth + 1))

        return {
            "changed_file": file_path,
            "affected_files": sorted(affected),
            "affected_count": len(affected),
            "max_depth_reached": max(d for _, d in [(f, 0) for f in affected]) if affected else 0,
        }

    def detect_cycles(self) -> list[CircularDependency]:
        """Detect all circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str):
            if node in rec_stack:
                # Found a cycle — extract it
                cycle_start = path.index(node) if node in path else 0
                cycle = path[cycle_start:] + [node]
                severity = "critical" if len(cycle) <= 3 else "warning"
                cycles.append(CircularDependency(cycle=cycle, severity=severity))
                return
            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.edges.get(node, set()):
                dfs(neighbor)

            path.pop()
            rec_stack.discard(node)

        for node_file in self.nodes:
            if node_file not in visited:
                dfs(node_file)

        return cycles

    def get_stats(self) -> dict:
        """Get graph statistics."""
        total_deps = sum(len(deps) for deps in self.edges.values())
        avg_deps = total_deps / len(self.nodes) if self.nodes else 0
        most_depended = sorted(
            [(f, len(deps)) for f, deps in self.reverse_edges.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        most_dependencies = sorted(
            [(f, len(deps)) for f, deps in self.edges.items()],
            key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_files": len(self.nodes),
            "total_dependencies": total_deps,
            "avg_dependencies_per_file": round(avg_deps, 2),
            "entry_points": [f for f, n in self.nodes.items() if n.is_entry_point],
            "most_depended_on": [{"file": f, "dependents": c} for f, c in most_depended],
            "most_dependencies": [{"file": f, "imports": c} for f, c in most_dependencies],
        }

    def get_topological_order(self) -> list[str]:
        """Get topological sort of the dependency graph."""
        in_degree = {node: 0 for node in self.nodes}
        for deps in self.edges.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 0  # dep is depended upon

        # Calculate in-degree (number of files that depend on this one)
        for node in self.nodes:
            in_degree[node] = len(self.reverse_edges.get(node, set()))

        queue = deque([n for n, d in in_degree.items() if d == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for dep in self.edges.get(node, set()):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        return result

    def to_dict(self) -> dict:
        """Serialize graph to dict for API response."""
        return {
            "nodes": [
                {
                    "file_path": n.file_path,
                    "module_name": n.module_name,
                    "language": n.language,
                    "imports": n.imports,
                    "imported_by": n.imported_by,
                    "line_count": n.line_count,
                    "is_entry_point": n.is_entry_point,
                }
                for n in self.nodes.values()
            ],
            "stats": self.get_stats(),
            "cycles": [
                {"cycle": c.cycle, "severity": c.severity}
                for c in self.detect_cycles()
            ],
        }


class DependencyGraphBuilder:
    """Builds a dependency graph from source code files."""

    # Python import patterns
    PY_IMPORT_RE = re.compile(r'^\s*(?:from\s+(\S+)\s+import\s+(.+)|import\s+(\S+))', re.MULTILINE)
    
    # JS/TS import patterns
    JS_IMPORT_RE = re.compile(
        r'(?:import\s+.*\s+from\s+["\']([^"\']+)["\']|require\(\s*["\']([^"\']+)["\']\s*\))',
        re.MULTILINE
    )

    # Entry point patterns
    ENTRY_POINTS = {"main.py", "app.py", "index.ts", "index.js", "index.tsx", "index.jsx", "main.ts", "main.js"}

    def __init__(self, root_path: str, ignore_dirs: set[str] = None):
        self.root_path = root_path
        self.ignore_dirs = ignore_dirs or {"node_modules", ".git", "__pycache__", "dist", "build", ".venv", "venv", "env"}
        self.graph = DependencyGraph()

    def build(self) -> DependencyGraph:
        """Scan the project and build the dependency graph."""
        files = self._find_source_files()

        # First pass: create all nodes
        for file_path, language in files:
            node = self._parse_file(file_path, language)
            if node:
                self.graph.add_node(node)

        # Second pass: resolve edges
        for node in self.graph.nodes.values():
            for imp in node.imports:
                # Try to resolve the import to a file
                target_file = self._resolve_import(imp, node.file_path, node.language)
                if target_file:
                    self.graph.add_edge(node.file_path, target_file)
                    # Update reverse deps
                    if node.file_path not in self.graph.nodes[target_file].imported_by:
                        self.graph.nodes[target_file].imported_by.append(node.file_path)

        logger.info(f"Built dependency graph: {len(self.graph.nodes)} files, "
                    f"{sum(len(d) for d in self.graph.edges.values())} edges")
        return self.graph

    def _find_source_files(self) -> list[tuple[str, str]]:
        """Find all source files in the project."""
        result = []
        extensions = {".py": "python", ".ts": "typescript", ".js": "javascript", ".tsx": "typescript", ".jsx": "javascript"}

        for root, dirs, files in os.walk(self.root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext in extensions:
                    full_path = os.path.join(root, fname)
                    result.append((full_path, extensions[ext]))

        return result

    def _parse_file(self, file_path: str, language: str) -> DependencyNode | None:
        """Parse a file to extract imports and metadata."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except IOError:
            return None

        lines = content.splitlines()
        line_count = len(lines)
        imports = []
        fname = os.path.basename(file_path)
        is_entry = fname in self.ENTRY_POINTS

        if language == "python":
            imports = self._parse_python_imports(content)
            module_name = self._file_to_module(file_path)
        else:
            imports = self._parse_js_imports(content)
            module_name = fname

        return DependencyNode(
            file_path=file_path,
            module_name=module_name,
            language=language,
            imports=imports,
            line_count=line_count,
            is_entry_point=is_entry,
        )

    def _parse_python_imports(self, content: str) -> list[str]:
        """Extract Python import statements."""
        imports = []
        for match in self.PY_IMPORT_RE.finditer(content):
            if match.group(1):  # from X import Y
                imports.append(match.group(1))
            elif match.group(3):  # import X
                imports.append(match.group(3))
        return list(set(imports))

    def _parse_js_imports(self, content: str) -> list[str]:
        """Extract JS/TS import statements."""
        imports = []
        for match in self.JS_IMPORT_RE.finditer(content):
            imp = match.group(1) or match.group(2)
            if imp:
                imports.append(imp)
        return list(set(imports))

    def _file_to_module(self, file_path: str) -> str:
        """Convert a file path to a Python module name."""
        rel_path = os.path.relpath(file_path, self.root_path)
        if rel_path.endswith("__init__.py"):
            return os.path.dirname(rel_path).replace(os.sep, ".")
        module = rel_path.replace(os.sep, ".").replace(".py", "")
        return module

    def _resolve_import(self, import_path: str, from_file: str, language: str) -> str | None:
        """Resolve an import to a file path."""
        if language == "python":
            # Try module.name → module/name.py or module/name/__init__.py
            parts = import_path.replace(".", os.sep)
            candidates = [
                os.path.join(self.root_path, parts + ".py"),
                os.path.join(self.root_path, parts, "__init__.py"),
                # Relative to the importing file's directory
                os.path.join(os.path.dirname(from_file), parts + ".py"),
                os.path.join(os.path.dirname(from_file), parts, "__init__.py"),
            ]
            for cand in candidates:
                if os.path.exists(cand):
                    return os.path.normpath(cand)
        else:
            # JS/TS: resolve relative imports
            if import_path.startswith("."):
                base_dir = os.path.dirname(from_file)
                resolved = os.path.normpath(os.path.join(base_dir, import_path))
                for ext in [".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"]:
                    if os.path.exists(resolved + ext):
                        return os.path.normpath(resolved + ext)
            # Also try as a file in the project
            else:
                candidates = [
                    os.path.join(self.root_path, import_path + ".ts"),
                    os.path.join(self.root_path, import_path + ".js"),
                    os.path.join(self.root_path, "src", import_path + ".ts"),
                    os.path.join(self.root_path, "src", import_path + ".js"),
                ]
                for cand in candidates:
                    if os.path.exists(cand):
                        return os.path.normpath(cand)

        return None
