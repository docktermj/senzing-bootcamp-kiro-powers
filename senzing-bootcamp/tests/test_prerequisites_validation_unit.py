"""Unit tests for validate_prerequisites.py.

Feature: module-prerequisites-validation
Tests: error/warning message formats, file-not-found, parse errors,
       --warnings-as-errors flag, smoke test, and performance.
"""

import sys
import time
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_prerequisites import (  # noqa: E402
    parse_gate_key,
    extract_keywords,
    Finding,
    ModuleInfo,
    GateInfo,
    count_checkpoints,
    has_success_criteria,
    _validate_module_references,
    _validate_keyword_presence,
    _validate_checkpoint_coverage,
    validate_prerequisites,
    main,
    load_dependency_graph,
    load_steering_index,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GRAPH_PATH = _REPO_ROOT / "config" / "module-dependencies.yaml"
_STEERING_INDEX_PATH = _REPO_ROOT / "steering" / "steering-index.yaml"
_STEERING_DIR = _REPO_ROOT / "steering"


# ---------------------------------------------------------------------------
# 7.1 Message Format Tests
# ---------------------------------------------------------------------------


class TestMessageFormats:
    """Tests for error/warning message format strings."""

    def test_finding_format_error(self):
        """Finding.format() produces 'ERROR: description' for errors."""
        f = Finding("ERROR", "something went wrong")
        assert f.format() == "ERROR: something went wrong"

    def test_finding_format_warning(self):
        """Finding.format() produces 'WARNING: description' for warnings."""
        f = Finding("WARNING", "minor issue detected")
        assert f.format() == "WARNING: minor issue detected"

    def test_module_reference_error_mentions_module_numbers(self):
        """Module reference errors mention the module numbers involved."""
        modules = {
            1: ModuleInfo(name="First", requires=[99]),
        }
        gates: dict[str, GateInfo] = {}
        steering_index: dict[int, list[str]] = {1: ["mod-01.md"]}

        findings = _validate_module_references(modules, gates, steering_index)
        assert len(findings) == 1
        assert findings[0].level == "ERROR"
        assert "1" in findings[0].description
        assert "99" in findings[0].description

    def test_gate_reference_error_mentions_module_numbers(self):
        """Gate reference errors mention the gate key and module numbers."""
        modules: dict[int, ModuleInfo] = {}
        gates = {
            "5->6": GateInfo(source=5, destination=6, requires=["test"]),
        }
        steering_index: dict[int, list[str]] = {}

        findings = _validate_module_references(modules, gates, steering_index)
        assert len(findings) >= 1
        descriptions = " ".join(f.description for f in findings)
        assert "5" in descriptions
        assert "6" in descriptions

    def test_keyword_warning_mentions_gate_and_keyword(self, tmp_path):
        """Keyword warnings mention the gate key and the missing keyword."""
        steering_file = tmp_path / "mod-01.md"
        steering_file.write_text("# Module 1\nSome unrelated content.\n")

        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=["SDK installed"]),
        }
        steering_index = {1: ["mod-01.md"]}

        findings = _validate_keyword_presence(gates, steering_index, tmp_path)
        assert len(findings) >= 1
        assert findings[0].level == "WARNING"
        assert "1->2" in findings[0].description
        assert "sdk installed" in findings[0].description

    def test_checkpoint_error_mentions_module_number(self, tmp_path):
        """Checkpoint errors mention the module number."""
        steering_file = tmp_path / "mod-01.md"
        steering_file.write_text("# Module 1\nNo checkpoints here.\n")

        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=["test"]),
        }
        steering_index = {1: ["mod-01.md"]}

        findings = _validate_checkpoint_coverage(gates, steering_index, tmp_path)
        # Should have an error about zero checkpoints
        error_findings = [f for f in findings if f.level == "ERROR"]
        assert len(error_findings) >= 1
        assert "1" in error_findings[0].description


# ---------------------------------------------------------------------------
# 7.2 File Not Found and Parse Error Tests
# ---------------------------------------------------------------------------


class TestFileNotFound:
    """Tests for missing file handling."""

    def test_load_dependency_graph_exits_on_missing_file(self, tmp_path):
        """load_dependency_graph exits with code 1 when file doesn't exist."""
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(SystemExit) as exc_info:
            load_dependency_graph(missing)
        assert exc_info.value.code == 1

    def test_load_dependency_graph_error_contains_path(self, tmp_path, capsys):
        """Error message contains the file path."""
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(SystemExit):
            load_dependency_graph(missing)
        captured = capsys.readouterr()
        assert str(missing) in captured.out

    def test_load_steering_index_exits_on_missing_file(self, tmp_path):
        """load_steering_index exits with code 1 when file doesn't exist."""
        missing = tmp_path / "nonexistent-index.yaml"
        with pytest.raises(SystemExit) as exc_info:
            load_steering_index(missing)
        assert exc_info.value.code == 1

    def test_load_steering_index_error_contains_path(self, tmp_path, capsys):
        """Error message contains the file path."""
        missing = tmp_path / "missing-steering-index.yaml"
        with pytest.raises(SystemExit):
            load_steering_index(missing)
        captured = capsys.readouterr()
        assert str(missing) in captured.out


class TestParseErrors:
    """Tests for unparseable content."""

    def test_dependency_graph_no_modules_exits(self, tmp_path):
        """Dependency graph with no modules section exits with code 1."""
        bad_file = tmp_path / "bad-graph.yaml"
        bad_file.write_text("metadata:\n  version: 1.0\n")
        with pytest.raises(SystemExit) as exc_info:
            load_dependency_graph(bad_file)
        assert exc_info.value.code == 1

    def test_dependency_graph_no_modules_error_message(self, tmp_path, capsys):
        """Parse error message mentions 'no modules found'."""
        bad_file = tmp_path / "bad-graph.yaml"
        bad_file.write_text("metadata:\n  version: 1.0\n")
        with pytest.raises(SystemExit):
            load_dependency_graph(bad_file)
        captured = capsys.readouterr()
        assert "no modules found" in captured.out

    def test_steering_index_no_modules_exits(self, tmp_path):
        """Steering index with no modules section exits with code 1."""
        bad_file = tmp_path / "bad-index.yaml"
        bad_file.write_text("keywords:\n  error: common-pitfalls.md\n")
        with pytest.raises(SystemExit) as exc_info:
            load_steering_index(bad_file)
        assert exc_info.value.code == 1

    def test_steering_index_no_modules_error_message(self, tmp_path, capsys):
        """Parse error message mentions 'no modules found'."""
        bad_file = tmp_path / "bad-index.yaml"
        bad_file.write_text("keywords:\n  error: common-pitfalls.md\n")
        with pytest.raises(SystemExit):
            load_steering_index(bad_file)
        captured = capsys.readouterr()
        assert "no modules found" in captured.out


# ---------------------------------------------------------------------------
# 7.3 Warnings As Errors Tests
# ---------------------------------------------------------------------------


class TestWarningsAsErrors:
    """Tests for --warnings-as-errors flag behavior."""

    def test_main_exits_0_with_warnings_only(self, tmp_path):
        """main() exits 0 with warnings only (no --warnings-as-errors)."""
        # Create a graph with a module that has an outgoing gate but no
        # success criteria — produces a WARNING but not an ERROR
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text(
            "modules:\n"
            "  1:\n"
            "    name: First\n"
            "    requires: []\n"
            "  2:\n"
            "    name: Second\n"
            "    requires: [1]\n"
            "gates:\n"
            '  "1->2":\n'
            "    requires:\n"
            '      - "test keyword present"\n'
        )

        index_file = tmp_path / "index.yaml"
        index_file.write_text(
            "modules:\n"
            "  1: mod-01.md\n"
            "  2: mod-02.md\n"
        )

        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        # Include the keyword and a checkpoint but no success criteria
        (steering_dir / "mod-01.md").write_text(
            "# Module 1\ntest keyword present\n**Checkpoint:** done\n"
        )
        (steering_dir / "mod-02.md").write_text("# Module 2\n")

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--graph", str(graph_file),
                "--steering-index", str(index_file),
                "--steering-dir", str(steering_dir),
            ])
        assert exc_info.value.code == 0

    def test_main_exits_1_with_warnings_as_errors(self, tmp_path):
        """main() exits 1 with warnings when --warnings-as-errors is set."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text(
            "modules:\n"
            "  1:\n"
            "    name: First\n"
            "    requires: []\n"
            "  2:\n"
            "    name: Second\n"
            "    requires: [1]\n"
            "gates:\n"
            '  "1->2":\n'
            "    requires:\n"
            '      - "test keyword present"\n'
        )

        index_file = tmp_path / "index.yaml"
        index_file.write_text(
            "modules:\n"
            "  1: mod-01.md\n"
            "  2: mod-02.md\n"
        )

        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        # Include keyword and checkpoint but no success criteria → WARNING
        (steering_dir / "mod-01.md").write_text(
            "# Module 1\ntest keyword present\n**Checkpoint:** done\n"
        )
        (steering_dir / "mod-02.md").write_text("# Module 2\n")

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--warnings-as-errors",
                "--graph", str(graph_file),
                "--steering-index", str(index_file),
                "--steering-dir", str(steering_dir),
            ])
        assert exc_info.value.code == 1

    def test_main_exits_1_with_errors_regardless(self, tmp_path):
        """main() exits 1 with errors regardless of --warnings-as-errors."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text(
            "modules:\n"
            "  1:\n"
            "    name: First\n"
            "    requires: [99]\n"
            "gates:\n"
        )

        index_file = tmp_path / "index.yaml"
        index_file.write_text(
            "modules:\n"
            "  1: mod-01.md\n"
        )

        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        (steering_dir / "mod-01.md").write_text("# Module 1\n")

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--graph", str(graph_file),
                "--steering-index", str(index_file),
                "--steering-dir", str(steering_dir),
            ])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 7.4 Smoke Test
# ---------------------------------------------------------------------------


class TestSmokeTest:
    """Integration test against real project files."""

    def test_validate_prerequisites_returns_findings_list(self):
        """validate_prerequisites() returns a list of Finding objects."""
        findings = validate_prerequisites(
            _GRAPH_PATH,
            _STEERING_INDEX_PATH,
            _STEERING_DIR,
        )
        assert isinstance(findings, list)
        for f in findings:
            assert isinstance(f, Finding)

    def test_no_errors_on_real_project(self):
        """No ERRORs are found on the real project files."""
        findings = validate_prerequisites(
            _GRAPH_PATH,
            _STEERING_INDEX_PATH,
            _STEERING_DIR,
        )
        errors = [f for f in findings if f.level == "ERROR"]
        assert len(errors) == 0, (
            "Unexpected errors:\n"
            + "\n".join(f.format() for f in errors)
        )


# ---------------------------------------------------------------------------
# 7.5 Performance Test
# ---------------------------------------------------------------------------


class TestPerformance:
    """Performance assertion: validator completes in < 10 seconds."""

    def test_validation_completes_under_10_seconds(self):
        """validate_prerequisites() completes in < 10 seconds for 11 modules."""
        start = time.perf_counter()
        validate_prerequisites(
            _GRAPH_PATH,
            _STEERING_INDEX_PATH,
            _STEERING_DIR,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 10.0, (
            f"Validation took {elapsed:.2f}s, exceeds 10s threshold"
        )
