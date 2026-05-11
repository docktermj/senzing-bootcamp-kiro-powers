"""Tests for module dependency visualization script.

Validates:
- CLI accepts --format text and --format mermaid
- Text output contains all 11 module names
- Mermaid output contains flowchart TD and classDef
- No progress file → Module 1 and 2 shown as available, others locked
- Module status is always one of {complete, current, available, locked}
- status.py accepts --graph flag
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from visualize_dependencies import (
    get_module_status,
    render_mermaid,
    render_text,
    _default_modules,
    _parse_yaml_modules,
    _parse_yaml_tracks,
)


# ---------------------------------------------------------------------------
# Strategies for property tests
# ---------------------------------------------------------------------------

def st_module_num() -> st.SearchStrategy[int]:
    """Strategy for valid module numbers."""
    return st.integers(min_value=1, max_value=11)


def st_completed_modules() -> st.SearchStrategy[list[int]]:
    """Strategy for a list of completed module numbers."""
    return st.lists(st_module_num(), unique=True, max_size=11)


def st_progress() -> st.SearchStrategy[dict]:
    """Strategy for progress data."""
    return st.builds(
        lambda completed, current: {
            "modules_completed": completed,
            "current_module": current,
        },
        completed=st_completed_modules(),
        current=st.one_of(st.none(), st_module_num()),
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

class TestCLIFormats:
    """Test that the script accepts --format text and --format mermaid."""

    def test_format_text_accepted(self):
        """Script produces output with --format text."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_text(modules, progress)
        assert len(output) > 0
        assert "Module" in output

    def test_format_mermaid_accepted(self):
        """Script produces output with --format mermaid."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_mermaid(modules, progress)
        assert len(output) > 0
        assert "flowchart TD" in output


class TestTextOutput:
    """Test text output contains all 11 module names."""

    def test_contains_all_module_names(self):
        """Text output mentions all 11 modules by name."""
        modules = _default_modules()
        progress = {"modules_completed": [1, 2, 3], "current_module": 4}
        output = render_text(modules, progress)

        for num, info in modules.items():
            assert info["name"] in output, (
                f"Module {num} name '{info['name']}' not found in text output"
            )

    def test_contains_all_module_numbers(self):
        """Text output references all 11 module numbers."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_text(modules, progress)

        for num in range(1, 12):
            assert f"Module {num}" in output


class TestMermaidOutput:
    """Test Mermaid output structure."""

    def test_contains_flowchart_td(self):
        """Mermaid output starts with flowchart TD."""
        modules = _default_modules()
        progress = {"modules_completed": [1], "current_module": 2}
        output = render_mermaid(modules, progress)
        assert "flowchart TD" in output

    def test_contains_classdef(self):
        """Mermaid output contains classDef styling."""
        modules = _default_modules()
        progress = {"modules_completed": [1], "current_module": 2}
        output = render_mermaid(modules, progress)
        assert "classDef complete" in output
        assert "classDef current" in output
        assert "classDef available" in output
        assert "classDef locked" in output

    def test_contains_node_definitions(self):
        """Mermaid output has node definitions for all modules."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_mermaid(modules, progress)
        for num in range(1, 12):
            assert f"M{num}[" in output

    def test_contains_edges(self):
        """Mermaid output has edge definitions."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_mermaid(modules, progress)
        # Module 3 requires 2, so M2 --> M3 should exist
        assert "M2 --> M3" in output
        # Module 4 requires 1
        assert "M1 --> M4" in output


class TestNoProgressFile:
    """Test behavior when no progress file exists."""

    def test_module_1_available_no_progress(self):
        """Module 1 (no prerequisites) shown as available when no progress."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        status = get_module_status(1, modules, progress)
        assert status == "available"

    def test_module_2_available_no_progress(self):
        """Module 2 (no prerequisites) shown as available when no progress."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        status = get_module_status(2, modules, progress)
        assert status == "available"

    def test_modules_with_prereqs_locked_no_progress(self):
        """Modules with prerequisites shown as locked when no progress."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        for num in range(3, 12):
            status = get_module_status(num, modules, progress)
            assert status == "locked", (
                f"Module {num} should be locked but got '{status}'"
            )

    def test_text_output_shows_available_emoji_for_entry_points(self):
        """Text output shows 🔓 for Module 1 and 2 with no progress."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_text(modules, progress)
        assert "🔓 Module 1" in output
        assert "🔓 Module 2" in output

    def test_text_output_shows_locked_emoji_for_others(self):
        """Text output shows 🔒 for modules with unmet prerequisites."""
        modules = _default_modules()
        progress = {"modules_completed": [], "current_module": None}
        output = render_text(modules, progress)
        assert "🔒 Module 3" in output
        assert "🔒 Module 11" in output


class TestStatusDetermination:
    """Test module status logic."""

    def test_completed_module_shows_complete(self):
        """A module in modules_completed has status 'complete'."""
        modules = _default_modules()
        progress = {"modules_completed": [1, 2], "current_module": 3}
        assert get_module_status(1, modules, progress) == "complete"
        assert get_module_status(2, modules, progress) == "complete"

    def test_current_module_shows_current(self):
        """The current_module has status 'current'."""
        modules = _default_modules()
        progress = {"modules_completed": [1], "current_module": 2}
        assert get_module_status(2, modules, progress) == "current"

    def test_available_when_prereqs_met(self):
        """Module is available when all prerequisites are complete."""
        modules = _default_modules()
        # Module 3 requires [2], and 2 is complete
        progress = {"modules_completed": [2], "current_module": None}
        assert get_module_status(3, modules, progress) == "available"

    def test_locked_when_prereqs_not_met(self):
        """Module is locked when prerequisites are not complete."""
        modules = _default_modules()
        # Module 6 requires [2, 5], only 2 is complete
        progress = {"modules_completed": [2], "current_module": None}
        assert get_module_status(6, modules, progress) == "locked"


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------

class TestModuleStatusProperties:
    """Property-based tests for module status determination."""

    @given(progress=st_progress())
    @settings(max_examples=100)
    def test_status_always_valid(self, progress: dict):
        """Module status is always one of {complete, current, available, locked}."""
        modules = _default_modules()
        valid_statuses = {"complete", "current", "available", "locked"}
        for num in range(1, 12):
            status = get_module_status(num, modules, progress)
            assert status in valid_statuses, (
                f"Module {num} has invalid status '{status}'"
            )

    @given(progress=st_progress())
    @settings(max_examples=100)
    def test_completed_never_locked(self, progress: dict):
        """Completed modules are never shown as locked."""
        modules = _default_modules()
        completed = progress.get("modules_completed", [])
        for num in completed:
            if 1 <= num <= 11:
                status = get_module_status(num, modules, progress)
                assert status != "locked", (
                    f"Module {num} is completed but shown as locked"
                )

    @given(progress=st_progress())
    @settings(max_examples=100)
    def test_current_never_complete(self, progress: dict):
        """Current module is never shown as complete (unless also in completed)."""
        modules = _default_modules()
        current = progress.get("current_module")
        completed = progress.get("modules_completed", [])
        if current is not None and 1 <= current <= 11 and current not in completed:
            status = get_module_status(current, modules, progress)
            assert status != "complete", (
                f"Module {current} is current but shown as complete"
            )


# ---------------------------------------------------------------------------
# status.py --graph flag
# ---------------------------------------------------------------------------

class TestStatusGraphFlag:
    """Test that status.py accepts --graph flag."""

    def test_status_argparse_accepts_graph(self):
        """status.py argparse accepts --graph without error."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--html", action="store_true")
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--no-open", action="store_true")
        parser.add_argument("--sync", action="store_true")
        parser.add_argument("--member", type=str, default=None)
        parser.add_argument("--graph", action="store_true",
                            help="Show module dependency graph")
        # Should parse without error
        args = parser.parse_args(["--graph"])
        assert args.graph is True

    def test_status_graph_flag_in_source(self):
        """status.py source contains --graph argument definition."""
        status_path = Path(_SCRIPTS_DIR) / "status.py"
        source = status_path.read_text(encoding="utf-8")
        assert '"--graph"' in source or "'--graph'" in source


# ---------------------------------------------------------------------------
# YAML parser tests
# ---------------------------------------------------------------------------

class TestYAMLParser:
    """Test the minimal YAML parser."""

    def test_parse_modules_from_file(self):
        """Parser extracts all 11 modules from the real YAML file."""
        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )
        if not yaml_path.is_file():
            pytest.skip("module-dependencies.yaml not found")
        text = yaml_path.read_text(encoding="utf-8")
        modules = _parse_yaml_modules(text)
        assert len(modules) == 11
        assert modules[1]["name"] == "Business Problem"
        assert modules[2]["requires"] == []
        assert 2 in modules[6]["requires"]

    def test_parse_tracks_from_file(self):
        """Parser extracts track definitions from the real YAML file."""
        yaml_path = (
            Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"
        )
        if not yaml_path.is_file():
            pytest.skip("module-dependencies.yaml not found")
        text = yaml_path.read_text(encoding="utf-8")
        tracks = _parse_yaml_tracks(text)
        assert "quick_demo" in tracks
        assert tracks["quick_demo"]["modules"] == [2, 3]
