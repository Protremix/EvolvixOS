"""
Tests for the AST-Aware Diff Engine.
"""

import pytest
from app.services.ast_diff import ASTDiffEngine, DiffChange, ASTNode


class TestASTDiffEngine:
    """Test the AST diff engine."""

    def test_no_changes(self):
        engine = ASTDiffEngine()
        code = "def hello():\n    return 'world'\n"
        result = engine.diff(code, code)
        assert result["summary"]["total_changes"] == 0
        assert not result["summary"]["breaking"]

    def test_added_function(self):
        engine = ASTDiffEngine()
        old = "def foo():\n    pass\n"
        new = "def foo():\n    pass\n\ndef bar():\n    return True\n"
        result = engine.diff(old, new)
        assert result["summary"]["added"] == 1
        assert any(c["name"] == "bar" and c["change_type"] == "added" for c in result["changes"])

    def test_removed_function(self):
        engine = ASTDiffEngine()
        old = "def foo():\n    pass\n\ndef bar():\n    return True\n"
        new = "def foo():\n    pass\n"
        result = engine.diff(old, new)
        assert result["summary"]["removed"] == 1
        assert any(c["name"] == "bar" and c["change_type"] == "removed" for c in result["changes"])
        # Removing a function is breaking
        assert result["summary"]["breaking"]

    def test_modified_function_body(self):
        engine = ASTDiffEngine()
        old = "def foo():\n    return 1\n"
        new = "def foo():\n    return 2\n"
        result = engine.diff(old, new)
        assert result["summary"]["modified"] == 1
        assert any(c["name"] == "foo" and c["change_type"] == "modified" for c in result["changes"])
        assert not result["summary"]["breaking"]

    def test_signature_changed(self):
        engine = ASTDiffEngine()
        old = "def foo(a, b):\n    return a + b\n"
        new = "def foo(a, b, c):\n    return a + b + c\n"
        result = engine.diff(old, new)
        assert result["summary"]["signature_changed"] == 1
        assert any(c["change_type"] == "signature_changed" for c in result["changes"])

    def test_class_added(self):
        engine = ASTDiffEngine()
        old = ""
        new = "class MyClass:\n    def __init__(self):\n        self.x = 1\n"
        result = engine.diff(old, new)
        assert result["summary"]["added"] == 1
        assert any(c["node_type"] == "class" for c in result["changes"])

    def test_class_method_modified(self):
        engine = ASTDiffEngine()
        old = "class MyClass:\n    def method(self):\n        return 1\n"
        new = "class MyClass:\n    def method(self):\n        return 2\n"
        result = engine.diff(old, new)
        assert result["summary"]["modified"] >= 1
        # Should detect the method change at the class level
        assert any("method" in c["name"] for c in result["changes"])

    def test_import_added(self):
        engine = ASTDiffEngine()
        old = "def foo():\n    pass\n"
        new = "import os\n\ndef foo():\n    pass\n"
        result = engine.diff(old, new)
        assert any(c["node_type"] == "import" and c["change_type"] == "added" for c in result["changes"])

    def test_import_removed(self):
        engine = ASTDiffEngine()
        old = "import os\n\ndef foo():\n    pass\n"
        new = "def foo():\n    pass\n"
        result = engine.diff(old, new)
        assert any(c["node_type"] == "import" and c["change_type"] == "removed" for c in result["changes"])

    def test_rename_detection(self):
        engine = ASTDiffEngine()
        old = "def calculate_sum(a, b):\n    return a + b\n"
        new = "def calculate_total(a, b):\n    return a + b\n"
        result = engine.diff(old, new)
        assert result["summary"]["renamed"] >= 1
        assert any(c["change_type"] == "renamed" and "calculate_sum" in c["name"] for c in result["changes"])

    def test_assign_change(self):
        engine = ASTDiffEngine()
        old = "x = 1\n"
        new = "x = 2\n"
        result = engine.diff(old, new)
        assert any(c["node_type"] == "assign" for c in result["changes"])

    def test_line_diff_fallback(self):
        engine = ASTDiffEngine()
        old = "const x = 1;"
        new = "const x = 2;"
        result = engine.diff(old, new, language="javascript")
        assert result["summary"]["language"] == "javascript"
        assert result["summary"]["total_changes"] >= 0

    def test_syntax_error_handling(self):
        engine = ASTDiffEngine()
        old = "def foo(:\n    pass\n"  # Syntax error
        new = "def foo():\n    pass\n"
        result = engine.diff(old, new)
        # Should not crash, should still produce some result
        assert "summary" in result

    def test_empty_code(self):
        engine = ASTDiffEngine()
        result = engine.diff("", "")
        assert result["summary"]["total_changes"] == 0

    def test_empty_to_code(self):
        engine = ASTDiffEngine()
        result = engine.diff("", "def foo():\n    pass\n")
        assert result["summary"]["added"] == 1

    def test_code_to_empty(self):
        engine = ASTDiffEngine()
        result = engine.diff("def foo():\n    pass\n", "")
        assert result["summary"]["removed"] == 1
        assert result["summary"]["breaking"]

    def test_multiple_changes(self):
        engine = ASTDiffEngine()
        old = """def foo():
    return 1

def bar(a):
    return a

import os
"""
        new = """def foo():
    return 2  # changed body

def baz(a):  # renamed from bar
    return a

import sys  # changed import
"""
        result = engine.diff(old, new)
        assert result["summary"]["total_changes"] >= 3

    def test_change_to_dict(self):
        change = DiffChange(
            change_type="added",
            node_type="function",
            name="test_func",
            new_value="def test_func():",
            new_lines=(1, 2),
            description="Added function 'test_func'",
        )
        engine = ASTDiffEngine()
        d = engine._change_to_dict(change)
        assert d["change_type"] == "added"
        assert d["name"] == "test_func"
        assert d["new_lines"] == [1, 2]


class TestASTDiffAPI:
    """Test the AST diff API endpoints."""

    def test_compare_unauthorized(self, client):
        response = client.post("/api/v1/ast-diff/compare", json={"old_code": "", "new_code": ""})
        assert response.status_code == 401

    def test_info_unauthorized(self, client):
        response = client.get("/api/v1/ast-diff/info")
        assert response.status_code == 401

    def test_compare_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/ast-diff/compare", json={
            "old_code": "def foo():\n    return 1\n",
            "new_code": "def foo():\n    return 2\n",
            "language": "python",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "changes" in data
        assert data["summary"]["total_changes"] >= 1

    def test_compare_added_function(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/ast-diff/compare", json={
            "old_code": "pass\n",
            "new_code": "def new_func():\n    pass\n",
            "language": "python",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["summary"]["added"] == 1

    def test_compare_javascript(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/ast-diff/compare", json={
            "old_code": "const x = 1;",
            "new_code": "const x = 2;",
            "language": "javascript",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["summary"]["language"] == "javascript"

    def test_info_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.get("/api/v1/ast-diff/info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "python" in data["supported_languages"][0]
        assert "signature_changed" in data["change_types"]

    def test_compare_files_not_found(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/ast-diff/compare-files", json={
            "old_file": "/nonexistent/old.py",
            "new_file": "/nonexistent/new.py",
        }, headers=headers)
        assert response.status_code == 400

    def test_compare_files_authorized(self, client, test_user, tmp_path):
        headers = test_user["headers"]
        old_file = tmp_path / "old.py"
        new_file = tmp_path / "new.py"
        old_file.write_text("def foo():\n    return 1\n")
        new_file.write_text("def foo():\n    return 2\n")

        response = client.post("/api/v1/ast-diff/compare-files", json={
            "old_file": str(old_file),
            "new_file": str(new_file),
            "language": "python",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["summary"]["modified"] >= 1
