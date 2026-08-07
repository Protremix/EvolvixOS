"""
Tests for the Dependency Graph Tracker.
"""

import os
import tempfile
import pytest

from app.services.dependency_graph import (
    DependencyGraph, DependencyNode, DependencyGraphBuilder,
)


@pytest.fixture
def sample_project():
    """Create a temporary sample project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create structure:
        #   main.py (imports app.utils)
        #   app/__init__.py
        #   app/utils.py (imports app.helpers)
        #   app/helpers.py
        #   app/models.py (imports app.helpers — circular with helpers if helpers imports models)

        os.makedirs(os.path.join(tmpdir, "app"))

        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("from app.utils import helper\n\n\ndef main():\n    helper()\n")

        with open(os.path.join(tmpdir, "app", "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(tmpdir, "app", "utils.py"), "w") as f:
            f.write("from app.helpers import format_data\n\n\ndef helper():\n    return format_data()\n")

        with open(os.path.join(tmpdir, "app", "helpers.py"), "w") as f:
            f.write("def format_data():\n    return 'formatted'\n")

        with open(os.path.join(tmpdir, "app", "models.py"), "w") as f:
            f.write("from app.helpers import format_data\n\n\nclass User:\n    pass\n")

        # Circular dependency: models -> helpers, helpers -> models
        with open(os.path.join(tmpdir, "app", "circular_a.py"), "w") as f:
            f.write("from app.circular_b import do_b\n\n\ndef do_a():\n    do_b()\n")

        with open(os.path.join(tmpdir, "app", "circular_b.py"), "w") as f:
            f.write("from app.circular_a import do_a\n\n\ndef do_b():\n    do_a()\n")

        yield tmpdir


class TestDependencyGraph:
    """Test the DependencyGraph data structure."""

    def test_add_node(self):
        graph = DependencyGraph()
        node = DependencyNode("test.py", "test", "python")
        graph.add_node(node)
        assert "test.py" in graph.nodes
        assert graph.module_to_file["test"] == "test.py"

    def test_add_edge(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python"))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        assert "b.py" in graph.edges["a.py"]
        assert "a.py" in graph.reverse_edges["b.py"]

    def test_get_dependencies(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python"))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        deps = graph.get_dependencies("a.py")
        assert "b.py" in deps

    def test_get_dependents(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python"))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        dependents = graph.get_dependents("b.py")
        assert "a.py" in dependents

    def test_get_impact(self):
        graph = DependencyGraph()
        for f in ["a.py", "b.py", "c.py", "d.py"]:
            graph.add_node(DependencyNode(f, f.replace(".py", ""), "python"))
        # a -> b -> c, a -> d (a depends on b, b depends on c)
        graph.add_edge("a.py", "b.py")
        graph.add_edge("b.py", "c.py")
        graph.add_edge("a.py", "d.py")
        
        # If c.py changes, b.py is affected (depends on c), then a.py (depends on b)
        impact = graph.get_impact("c.py")
        assert "c.py" not in impact["affected_files"]  # the changed file itself
        assert "b.py" in impact["affected_files"]
        assert "a.py" in impact["affected_files"]
        assert impact["affected_count"] == 2
        
        # d.py is depended on by a.py, so 1 affected
        impact_d = graph.get_impact("d.py")
        assert impact_d["affected_count"] == 1
        assert "a.py" in impact_d["affected_files"]

    def test_get_impact_chain(self):
        graph = DependencyGraph()
        for f in ["a.py", "b.py", "c.py"]:
            graph.add_node(DependencyNode(f, f.replace(".py", ""), "python"))
        # a -> b -> c (a depends on b, b depends on c)
        graph.add_edge("a.py", "b.py")
        graph.add_edge("b.py", "c.py")
        
        impact = graph.get_impact("c.py")
        # If c changes, b is affected (b depends on c), and a is affected (a depends on b)
        assert "b.py" in impact["affected_files"]
        assert "a.py" in impact["affected_files"]
        assert impact["affected_count"] == 2

    def test_detect_cycles_simple(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python"))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        graph.add_edge("b.py", "a.py")
        
        cycles = graph.detect_cycles()
        assert len(cycles) >= 1
        assert cycles[0].severity == "critical"  # 2-node cycle

    def test_detect_cycles_none(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python"))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        
        cycles = graph.detect_cycles()
        assert len(cycles) == 0

    def test_get_stats(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("main.py", "main", "python", is_entry_point=True))
        graph.add_node(DependencyNode("utils.py", "utils", "python"))
        graph.add_edge("main.py", "utils.py")
        
        stats = graph.get_stats()
        assert stats["total_files"] == 2
        assert stats["total_dependencies"] == 1
        assert "main.py" in stats["entry_points"]

    def test_to_dict(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("a.py", "a", "python", imports=["b"]))
        graph.add_node(DependencyNode("b.py", "b", "python"))
        graph.add_edge("a.py", "b.py")
        
        result = graph.to_dict()
        assert "nodes" in result
        assert "stats" in result
        assert "cycles" in result
        assert len(result["nodes"]) == 2


class TestDependencyGraphBuilder:
    """Test the graph builder that parses files."""

    def test_find_source_files(self, sample_project):
        builder = DependencyGraphBuilder(sample_project)
        files = builder._find_source_files()
        assert len(files) > 0
        # Should find .py files
        py_files = [f for f, lang in files if lang == "python"]
        assert any("main.py" in f for f in py_files)
        assert any("utils.py" in f for f in py_files)

    def test_parse_python_imports(self, sample_project):
        builder = DependencyGraphBuilder(sample_project)
        imports = builder._parse_python_imports("from os import path\nimport sys\nfrom app.utils import helper")
        assert "os" in imports
        assert "sys" in imports
        assert "app.utils" in imports

    def test_parse_js_imports(self):
        builder = DependencyGraphBuilder(".")
        imports = builder._parse_js_imports('import foo from "./bar"\nconst x = require("express")')
        assert "./bar" in imports
        assert "express" in imports

    def test_build_graph(self, sample_project):
        builder = DependencyGraphBuilder(sample_project)
        graph = builder.build()
        
        assert len(graph.nodes) > 0
        stats = graph.get_stats()
        assert stats["total_files"] >= 5  # main, __init__, utils, helpers, models, circular_a, circular_b

    def test_build_detects_cycles(self, sample_project):
        builder = DependencyGraphBuilder(sample_project)
        graph = builder.build()
        
        cycles = graph.detect_cycles()
        assert len(cycles) >= 1
        # Should detect the circular_a -> circular_b -> circular_a cycle
        cycle_files = [f for c in cycles for f in c.cycle]
        assert any("circular_a" in f for f in cycle_files)
        assert any("circular_b" in f for f in cycle_files)

    def test_build_entry_points(self, sample_project):
        builder = DependencyGraphBuilder(sample_project)
        graph = builder.build()
        
        entry_points = [f for f, n in graph.nodes.items() if n.is_entry_point]
        assert any("main.py" in f for f in entry_points)

    def test_ignore_dirs(self, sample_project):
        # Create a node_modules dir that should be ignored
        nm_dir = os.path.join(sample_project, "node_modules", "express")
        os.makedirs(nm_dir)
        with open(os.path.join(nm_dir, "index.js"), "w") as f:
            f.write('module.exports = {}')
        
        builder = DependencyGraphBuilder(sample_project)
        files = builder._find_source_files()
        # node_modules files should NOT be included
        assert not any("node_modules" in f for f, _ in files)


class TestDependencyGraphAPI:
    """Test the dependency graph API endpoints."""

    def test_build_unauthorized(self, client):
        response = client.post("/api/v1/dep-graph/build", json={"project_path": "."})
        assert response.status_code == 401

    def test_stats_unauthorized(self, client):
        response = client.get("/api/v1/dep-graph/stats?project_path=some_path")
        assert response.status_code == 401

    def test_cycles_unauthorized(self, client):
        response = client.get("/api/v1/dep-graph/cycles?project_path=some_path")
        assert response.status_code == 401

    def test_build_not_found(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/dep-graph/build",
                              json={"project_path": "/nonexistent/path"},
                              headers=headers)
        assert response.status_code == 400

    def test_build_and_query(self, client, test_user, sample_project):
        headers = test_user["headers"]
        
        # Build graph
        response = client.post("/api/v1/dep-graph/build",
                              json={"project_path": sample_project},
                              headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "stats" in data
        assert "cycles" in data
        assert data["stats"]["total_files"] >= 5

        # Get stats
        response = client.get(f"/api/v1/dep-graph/stats?project_path={sample_project}",
                             headers=headers)
        assert response.status_code == 200

        # Get cycles
        response = client.get(f"/api/v1/dep-graph/cycles?project_path={sample_project}",
                             headers=headers)
        assert response.status_code == 200
        assert len(response.json()["cycles"]) >= 1

    def test_dependencies_query(self, client, test_user, sample_project):
        headers = test_user["headers"]
        
        # Build first
        client.post("/api/v1/dep-graph/build",
                   json={"project_path": sample_project},
                   headers=headers)

        # Get all dependencies
        response = client.get(f"/api/v1/dep-graph/dependencies?project_path={sample_project}",
                            headers=headers)
        assert response.status_code == 200
        assert "dependencies" in response.json()
        assert len(response.json()["dependencies"]) >= 5

    def test_clear_cache(self, client, test_user, sample_project):
        headers = test_user["headers"]
        
        # Build first
        client.post("/api/v1/dep-graph/build",
                   json={"project_path": sample_project},
                   headers=headers)
        
        # Clear cache
        response = client.delete(f"/api/v1/dep-graph/cache?project_path={sample_project}",
                                headers=headers)
        assert response.status_code == 200
        assert response.json()["cleared"] is True

    def test_clear_cache_not_found(self, client, test_user):
        headers = test_user["headers"]
        response = client.delete("/api/v1/dep-graph/cache?project_path=nonexistent",
                                headers=headers)
        assert response.status_code == 404
