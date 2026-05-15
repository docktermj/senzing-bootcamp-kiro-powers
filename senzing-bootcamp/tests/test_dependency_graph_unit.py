"""Unit and integration tests for the module dependency graph.

Feature: module-dependency-graph
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_dependencies import (
    Violation,
    load_dependency_graph,
    validate_schema,
    validate_no_cycles,
    validate_references,
    validate_topological_order,
    validate_steering_files,
    validate_prerequisites_file,
    validate_onboarding_flow,
    run_all_checks,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GRAPH_PATH = _REPO_ROOT / "config" / "module-dependencies.yaml"
_STEERING_DIR = _REPO_ROOT / "steering"
_PREREQS_PATH = _STEERING_DIR / "module-prerequisites.md"
_ONBOARDING_PATH = _STEERING_DIR / "onboarding-flow.md"
_ONBOARDING_PHASE2_PATH = _STEERING_DIR / "onboarding-phase2-track-setup.md"


# ---------------------------------------------------------------------------
# Unit tests — real graph
# ---------------------------------------------------------------------------


class TestRealGraphParsing:
    """Tests against the actual dependency graph file."""

    def test_graph_parses_without_error(self):
        """(a) Real graph parses without error."""
        graph = load_dependency_graph(_GRAPH_PATH)
        assert isinstance(graph, dict)

    def test_graph_has_11_modules(self):
        """(b) Real graph has 11 modules."""
        graph = load_dependency_graph(_GRAPH_PATH)
        assert len(graph["modules"]) == 11

    def test_graph_has_2_tracks(self):
        """(c) Real graph has exactly 2 tracks."""
        graph = load_dependency_graph(_GRAPH_PATH)
        assert len(graph["tracks"]) == 2

    def test_quick_demo_absent_from_tracks(self):
        """quick_demo track is not present in the dependency graph."""
        graph = load_dependency_graph(_GRAPH_PATH)
        assert "quick_demo" not in graph["tracks"]

    def test_core_bootcamp_properties_preserved(self):
        """Core Bootcamp track retains expected name, modules, and recommendation."""
        graph = load_dependency_graph(_GRAPH_PATH)
        core = graph["tracks"]["core_bootcamp"]
        assert core["name"] == "Core Bootcamp"
        assert core["modules"] == [1, 2, 3, 4, 5, 6, 7]
        assert core["recommendation"] == "recommended"

    def test_graph_has_10_gates(self):
        """(d) Real graph has 10 gates."""
        graph = load_dependency_graph(_GRAPH_PATH)
        assert len(graph["gates"]) == 10

    def test_graph_has_no_cycles(self):
        """(e) Real graph has no cycles."""
        graph = load_dependency_graph(_GRAPH_PATH)
        violations = validate_no_cycles(graph)
        assert len(violations) == 0, f"Unexpected cycles: {[v.format() for v in violations]}"

    def test_graph_has_no_dangling_references(self):
        """(f) Real graph has no dangling references."""
        graph = load_dependency_graph(_GRAPH_PATH)
        violations = validate_references(graph)
        assert len(violations) == 0, f"Dangling refs: {[v.format() for v in violations]}"

    def test_graph_schema_is_valid(self):
        """Real graph passes schema validation."""
        graph = load_dependency_graph(_GRAPH_PATH)
        violations = validate_schema(graph)
        assert len(violations) == 0, f"Schema errors: {[v.format() for v in violations]}"

    def test_graph_tracks_in_topological_order(self):
        """Real graph tracks are in valid topological order."""
        graph = load_dependency_graph(_GRAPH_PATH)
        violations = validate_topological_order(graph)
        assert len(violations) == 0, f"Order violations: {[v.format() for v in violations]}"


class TestReferenceNotes:
    """(g) Reference notes exist in steering files."""

    def test_prerequisites_file_has_authoritative_note(self):
        """module-prerequisites.md contains the authoritative source note."""
        content = _PREREQS_PATH.read_text(encoding="utf-8")
        assert "config/module-dependencies.yaml" in content
        assert "authoritative" in content.lower() or "Authoritative" in content

    def test_onboarding_flow_has_track_note(self):
        """Onboarding files contain the track authoritative source note."""
        # After the split, track content is in Phase 2 file
        content = _ONBOARDING_PHASE2_PATH.read_text(encoding="utf-8")
        # Check in the Track Selection section area
        assert "config/module-dependencies.yaml" in content

    def test_onboarding_flow_has_gates_note(self):
        """Onboarding files contain the gates authoritative source note."""
        # After the split, Validation Gates is in Phase 2 file
        content = _ONBOARDING_PHASE2_PATH.read_text(encoding="utf-8")
        # Find the Validation Gates section and check for the note
        gates_idx = content.find("## Validation Gates")
        assert gates_idx != -1, "Validation Gates section not found"
        gates_section = content[gates_idx:gates_idx + 500]
        assert "config/module-dependencies.yaml" in gates_section


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_validation_exits_zero(self):
        """Full validation run on real graph + steering files exits with code 0."""
        violations, exit_code = run_all_checks(_GRAPH_PATH, _STEERING_DIR)
        error_violations = [v for v in violations if v.level == "ERROR"]
        assert exit_code == 0, (
            f"Expected exit code 0, got {exit_code}. "
            f"Errors: {[v.format() for v in error_violations]}"
        )

    def test_script_runs_with_stdlib_and_pyyaml(self):
        """Script runs with only stdlib + PyYAML (no other imports)."""
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "scripts" / "validate_dependencies.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stdout}\n{result.stderr}"

    def test_summary_line_format(self):
        """Summary line shows correct format."""
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "scripts" / "validate_dependencies.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = result.stdout.strip().split("\n")
        summary_line = lines[-1]
        assert "Summary:" in summary_line
        assert "error(s)" in summary_line
        assert "warning(s)" in summary_line


class TestViolationDataclass:
    """Tests for the Violation dataclass."""

    def test_format_error(self):
        v = Violation("ERROR", "something went wrong")
        assert v.format() == "ERROR: something went wrong"

    def test_format_warning(self):
        v = Violation("WARNING", "minor issue")
        assert v.format() == "WARNING: minor issue"
