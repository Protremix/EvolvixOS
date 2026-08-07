"""
AST-Aware Diff Engine.

Provides semantic code diffs by comparing Abstract Syntax Trees
rather than line-by-line text. Understands function renames, parameter
changes, body modifications, import additions, and structural reordering.
"""

import ast
import difflib
import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("evolvixos")


@dataclass
class ASTNode:
    """A node in the AST diff tree."""
    node_type: str  # function, class, method, import, assign, etc.
    name: str  # function/class name or import module
    signature: str  # function signature or import statement
    start_line: int
    end_line: int
    hash: str  # content hash for change detection
    children: list = field(default_factory=list)


@dataclass
class DiffChange:
    """A single semantic change."""
    change_type: str  # added, removed, modified, renamed, signature_changed
    node_type: str  # function, class, method, import, etc.
    name: str
    old_value: str = ""
    new_value: str = ""
    old_lines: tuple = (0, 0)
    new_lines: tuple = (0, 0)
    description: str = ""
    severity: str = "info"  # info, warning, critical


class ASTDiffEngine:
    """Compares two versions of Python source code using AST analysis."""

    def __init__(self):
        self.old_ast: dict[str, ASTNode] = {}
        self.new_ast: dict[str, ASTNode] = {}

    def diff(self, old_code: str, new_code: str, language: str = "python") -> dict:
        """Generate a semantic diff between two code versions.

        Returns:
            {
                "changes": [DiffChange...],
                "summary": {...},
                "line_diff": [...],
            }
        """
        if language != "python":
            # Fall back to line diff for non-Python
            return self._line_diff(old_code, new_code, language)

        old_nodes = self._parse_to_nodes(old_code)
        new_nodes = self._parse_to_nodes(new_code)

        changes = self._compare_nodes(old_nodes, new_nodes)

        # Also get line-level diff for context
        line_diff = self._unified_diff(old_code, new_code)

        # Categorize changes
        added = [c for c in changes if c.change_type == "added"]
        removed = [c for c in changes if c.change_type == "removed"]
        modified = [c for c in changes if c.change_type == "modified"]
        renamed = [c for c in changes if c.change_type == "renamed"]
        sig_changed = [c for c in changes if c.change_type == "signature_changed"]

        # Determine if change is breaking
        breaking = any(c.severity == "critical" for c in changes)

        return {
            "changes": [self._change_to_dict(c) for c in changes],
            "summary": {
                "total_changes": len(changes),
                "added": len(added),
                "removed": len(removed),
                "modified": len(modified),
                "renamed": len(renamed),
                "signature_changed": len(sig_changed),
                "breaking": breaking,
                "language": language,
            },
            "line_diff": line_diff,
        }

    def _parse_to_nodes(self, code: str) -> dict[str, ASTNode]:
        """Parse Python code into a dict of top-level AST nodes."""
        nodes = {}
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse code: {e}")
            return nodes

        for node in ast.iter_child_nodes(tree):
            ast_node = self._ast_to_node(node, code)
            if ast_node:
                nodes[ast_node.name] = ast_node

        return nodes

    def _ast_to_node(self, node: ast.AST, code: str) -> ASTNode | None:
        """Convert an AST node to our ASTNode."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            defaults_count = len(node.args.defaults)
            if defaults_count > 0:
                args_str = ", ".join(args[:-defaults_count] + [f"{a}=..." for a in args[-defaults_count:]])
            else:
                args_str = ", ".join(args)
            signature = f"def {node.name}({args_str})"
            body_hash = self._hash_body(node)
            return ASTNode(
                node_type="function",
                name=node.name,
                signature=signature,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                hash=body_hash,
                children=self._parse_children(node, code),
            )
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_node = self._ast_to_node(child, code)
                    if method_node:
                        methods.append(method_node)
            body_hash = self._hash_body(node)
            return ASTNode(
                node_type="class",
                name=node.name,
                signature=f"class {node.name}",
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                hash=body_hash,
                children=methods,
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                name = f"from {node.module} import ..."
            else:
                name = ", ".join(a.name for a in node.names)
            source_line = code.splitlines()[node.lineno - 1].strip() if node.lineno <= len(code.splitlines()) else ""
            return ASTNode(
                node_type="import",
                name=name,
                signature=source_line,
                start_line=node.lineno,
                end_line=node.lineno,
                hash=source_line,
            )
        elif isinstance(node, ast.Assign):
            targets = []
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                elif isinstance(t, ast.Attribute):
                    targets.append(self._unparse_attr(t))
            name = ", ".join(targets) if targets else "assign"
            return ASTNode(
                node_type="assign",
                name=name,
                signature=f"{name} = ...",
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                hash=self._hash_body(node),
            )
        return None

    def _parse_children(self, node: ast.AST, code: str) -> list:
        """Parse child nodes (methods of a class, etc.)."""
        children = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                child_node = self._ast_to_node(child, code)
                if child_node:
                    children.append(child_node)
        return children

    def _compare_nodes(self, old: dict[str, ASTNode], new: dict[str, ASTNode]) -> list[DiffChange]:
        """Compare two sets of AST nodes and return changes."""
        changes = []

        old_names = set(old.keys())
        new_names = set(new.keys())

        # Added nodes
        for name in sorted(new_names - old_names):
            node = new[name]
            changes.append(DiffChange(
                change_type="added",
                node_type=node.node_type,
                name=name,
                new_value=node.signature,
                new_lines=(node.start_line, node.end_line),
                description=f"Added {node.node_type} '{name}'",
            ))

        # Removed nodes
        for name in sorted(old_names - new_names):
            node = old[name]
            severity = "critical" if node.node_type in ("function", "class") else "warning"
            changes.append(DiffChange(
                change_type="removed",
                node_type=node.node_type,
                name=name,
                old_value=node.signature,
                old_lines=(node.start_line, node.end_line),
                description=f"Removed {node.node_type} '{name}'",
                severity=severity,
            ))

        # Modified or renamed
        for name in sorted(old_names & new_names):
            old_node = old[name]
            new_node = new[name]

            if old_node.node_type != new_node.node_type:
                changes.append(DiffChange(
                    change_type="modified",
                    node_type=new_node.node_type,
                    name=name,
                    old_value=old_node.signature,
                    new_value=new_node.signature,
                    old_lines=(old_node.start_line, old_node.end_line),
                    new_lines=(new_node.start_line, new_node.end_line),
                    description=f"Changed type of '{name}' from {old_node.node_type} to {new_node.node_type}",
                    severity="warning",
                ))
            elif old_node.hash != new_node.hash:
                # Body changed — check if signature changed too
                if old_node.signature != new_node.signature:
                    changes.append(DiffChange(
                        change_type="signature_changed",
                        node_type=new_node.node_type,
                        name=name,
                        old_value=old_node.signature,
                        new_value=new_node.signature,
                        old_lines=(old_node.start_line, old_node.end_line),
                        new_lines=(new_node.start_line, new_node.end_line),
                        description=f"Signature changed: {old_node.signature} → {new_node.signature}",
                        severity="warning" if new_node.node_type == "function" else "info",
                    ))
                else:
                    changes.append(DiffChange(
                        change_type="modified",
                        node_type=new_node.node_type,
                        name=name,
                        old_value=old_node.signature,
                        new_value=new_node.signature,
                        old_lines=(old_node.start_line, old_node.end_line),
                        new_lines=(new_node.start_line, new_node.end_line),
                        description=f"Modified {new_node.node_type} '{name}' body",
                        severity="info",
                    ))

                # Compare children (methods within classes)
                if old_node.children and new_node.children:
                    old_children = {c.name: c for c in old_node.children}
                    new_children = {c.name: c for c in new_node.children}
                    child_changes = self._compare_nodes(old_children, new_children)
                    for cc in child_changes:
                        cc.name = f"{name}.{cc.name}"
                        changes.append(cc)

        # Detect potential renames (similar names that were added/removed)
        removed_names = old_names - new_names
        added_names = new_names - old_names
        for r_name in list(removed_names):
            for a_name in list(added_names):
                ratio = difflib.SequenceMatcher(None, r_name, a_name).ratio()
                if ratio > 0.6 and old[r_name].node_type == new[a_name].node_type:
                    changes.append(DiffChange(
                        change_type="renamed",
                        node_type=old[r_name].node_type,
                        name=f"{r_name} → {a_name}",
                        old_value=old[r_name].signature,
                        new_value=new[a_name].signature,
                        old_lines=(old[r_name].start_line, old[r_name].end_line),
                        new_lines=(new[a_name].start_line, new[a_name].end_line),
                        description=f"Renamed {old[r_name].node_type} '{r_name}' to '{a_name}'",
                        severity="warning",
                    ))
                    removed_names.discard(r_name)
                    added_names.discard(a_name)
                    break

        return changes

    def _hash_body(self, node: ast.AST) -> str:
        """Generate a hash for the body of an AST node."""
        try:
            body_str = ast.dump(node)
            return hashlib.md5(body_str.encode()).hexdigest()[:12]
        except Exception:
            return ""

    def _unparse_attr(self, node: ast.Attribute) -> str:
        """Unparse an attribute access chain."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._unparse_attr(node.value)}.{node.attr}"
        return node.attr

    def _unified_diff(self, old_code: str, new_code: str) -> list[str]:
        """Generate a unified line-level diff."""
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        return list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile="old", tofile="new",
            lineterm=""
        ))

    def _line_diff(self, old_code: str, new_code: str, language: str) -> dict:
        """Fallback line-level diff for non-Python languages."""
        changes = []
        line_diff = self._unified_diff(old_code, new_code)

        # Parse line diff for simple add/remove detection
        for line in line_diff:
            if line.startswith("+") and not line.startswith("+++"):
                changes.append({
                    "change_type": "added",
                    "node_type": "line",
                    "name": "",
                    "description": line[1:].strip()[:100],
                    "severity": "info",
                })
            elif line.startswith("-") and not line.startswith("---"):
                changes.append({
                    "change_type": "removed",
                    "node_type": "line",
                    "name": "",
                    "description": line[1:].strip()[:100],
                    "severity": "info",
                })

        return {
            "changes": changes,
            "summary": {
                "total_changes": len(changes),
                "added": sum(1 for c in changes if c["change_type"] == "added"),
                "removed": sum(1 for c in changes if c["change_type"] == "removed"),
                "modified": 0,
                "renamed": 0,
                "signature_changed": 0,
                "breaking": False,
                "language": language,
            },
            "line_diff": line_diff,
        }

    def _change_to_dict(self, change: DiffChange) -> dict:
        """Convert a DiffChange to a dict for API response."""
        return {
            "change_type": change.change_type,
            "node_type": change.node_type,
            "name": change.name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "old_lines": list(change.old_lines),
            "new_lines": list(change.new_lines),
            "description": change.description,
            "severity": change.severity,
        }
