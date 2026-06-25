"""Unit / example tests for the example-coverage report script.

These plain pytest tests exercise specific examples and error paths of the
`language-example-coverage` loader, complementing the property-based tests in
`test_example_coverage_report_properties.py`.

Scripts under `senzing-bootcamp/scripts/` are not packages, so the script is
imported via `sys.path` manipulation (per python-conventions.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from example_coverage_report import (  # noqa: E402
    CoverageError,
    CoverageRecord,
    Snapshot,
    load_coverage_record,
    main,
)

# ---------------------------------------------------------------------------
# Shared fixture text
# ---------------------------------------------------------------------------

#: A minimal but complete, schema-valid Coverage_Record YAML document used by
#: the successful-load test.
VALID_RECORD_YAML = """\
metadata:
  snapshot:
    last_observed: "2026-06-09"
    senzing_version: "4.0.0"
languages:
  - python
  - java
topics:
  add_records:
    label: "Add records to the repository"
  query:
    label: "Query and search for entities"
coverage:
  python:
    add_records: available
    query: available
  java:
    add_records: available
    query: unknown
"""


class TestLoadCoverageRecord:
    """Example and error-path tests for :func:`load_coverage_record`."""

    def test_loads_valid_record(self, tmp_path: Path) -> None:
        """A well-formed record parses into the expected CoverageRecord."""
        record_path = tmp_path / "example-coverage.yaml"
        record_path.write_text(VALID_RECORD_YAML, encoding="utf-8")

        record = load_coverage_record(record_path)

        assert isinstance(record, CoverageRecord)
        assert record.languages == ("python", "java")
        assert record.topics == {
            "add_records": "Add records to the repository",
            "query": "Query and search for entities",
        }
        assert record.coverage == {
            "python": {"add_records": "available", "query": "available"},
            "java": {"add_records": "available", "query": "unknown"},
        }
        assert isinstance(record.snapshot, Snapshot)
        assert record.snapshot.last_observed == "2026-06-09"
        assert record.snapshot.senzing_version == "4.0.0"

    def test_missing_file_raises_coverage_error(self, tmp_path: Path) -> None:
        """A non-existent record path raises CoverageError mentioning not found."""
        missing_path = tmp_path / "does-not-exist.yaml"

        with pytest.raises(CoverageError, match="not found"):
            load_coverage_record(missing_path)

    def test_invalid_yaml_raises_coverage_error(self, tmp_path: Path) -> None:
        """Malformed YAML content raises CoverageError instead of leaking YAMLError."""
        record_path = tmp_path / "example-coverage.yaml"
        # Unbalanced flow-mapping bracket is rejected by yaml.safe_load.
        record_path.write_text("metadata: {unterminated: [1, 2, 3\n", encoding="utf-8")

        with pytest.raises(CoverageError):
            load_coverage_record(record_path)

    def test_non_mapping_top_level_list_raises(self, tmp_path: Path) -> None:
        """A top-level YAML sequence raises CoverageError (must be a mapping)."""
        record_path = tmp_path / "example-coverage.yaml"
        record_path.write_text("- a\n- b\n", encoding="utf-8")

        with pytest.raises(CoverageError, match="mapping"):
            load_coverage_record(record_path)

    def test_non_mapping_top_level_scalar_raises(self, tmp_path: Path) -> None:
        """A top-level YAML scalar raises CoverageError (must be a mapping)."""
        record_path = tmp_path / "example-coverage.yaml"
        record_path.write_text("just a string\n", encoding="utf-8")

        with pytest.raises(CoverageError, match="mapping"):
            load_coverage_record(record_path)


# Assembled from parts so the literal MCP server URL never appears verbatim in
# this tracked file (the URL belongs only in mcp.json).
_MCP_URL_FRAGMENT = "mcp." + "senzing" + ".com"


class TestSmokePlacement:
    """Smoke/placement tests asserting the feature's files are committed in the
    right places, follow naming conventions, and stay free of MCP/network calls.

    These read the real committed files (not fixtures), so they double as the
    placement guard for Requirement 7.6 (tests live under ``senzing-bootcamp/tests/``).
    """

    #: Power root: ``senzing-bootcamp/`` (parent of ``tests/``).
    POWER_ROOT = Path(__file__).resolve().parent.parent
    #: Repository root (parent of the power root).
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent

    #: Top-level imports allowed in the script: Python stdlib only. PyYAML must
    #: be imported lazily inside the loader, never at module top level.
    _ALLOWED_TOP_LEVEL_IMPORTS = {
        "__future__",
        "argparse",
        "dataclasses",
        "json",
        "os",
        "pathlib",
        "re",
        "sys",
        "tempfile",
    }

    def _script_path(self) -> Path:
        return self.POWER_ROOT / "scripts" / "example_coverage_report.py"

    def _record_path(self) -> Path:
        return self.POWER_ROOT / "config" / "example-coverage.yaml"

    def _top_level_import_names(self, source: str) -> set[str]:
        """Collect the top-level (module-scoped) imported module roots.

        Walks only the module body (not nested function/class bodies) so lazily
        imported dependencies inside functions are excluded.
        """
        import ast

        tree = ast.parse(source)
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    names.add(node.module.split(".")[0])
        return names

    def test_record_exists_at_config_path(self) -> None:
        """The Coverage_Record is committed at config/example-coverage.yaml (Req 1.1)."""
        assert self._record_path().is_file()

    def test_record_filename_naming(self) -> None:
        """The record uses a .yaml extension with kebab/snake_case naming (Req 1.7)."""
        import re

        name = self._record_path().name
        assert name == "example-coverage.yaml"
        assert name.endswith(".yaml")
        assert re.fullmatch(r"[a-z0-9_-]+\.yaml", name) is not None

    def test_script_exists_at_scripts_path(self) -> None:
        """The report script is committed at scripts/example_coverage_report.py (Req 3.1)."""
        assert self._script_path().is_file()

    def test_top_level_imports_are_stdlib_and_pyyaml_is_lazy(self) -> None:
        """Module top-level imports are stdlib only; PyYAML is imported lazily (Req 3.2)."""
        source = self._script_path().read_text(encoding="utf-8")
        top_level = self._top_level_import_names(source)

        assert "yaml" not in top_level, "PyYAML must be imported lazily, not at module top level"
        unexpected = top_level - self._ALLOWED_TOP_LEVEL_IMPORTS
        assert not unexpected, f"unexpected non-stdlib top-level imports: {sorted(unexpected)}"

    def test_script_makes_no_mcp_or_network_calls(self) -> None:
        """The script contains no MCP URL and imports no networking modules (Req 5.2)."""
        import ast

        source = self._script_path().read_text(encoding="utf-8")
        assert _MCP_URL_FRAGMENT not in source

        # No networking modules imported anywhere (top level or nested).
        network_roots = {"requests", "urllib", "http", "socket", "httplib", "ftplib"}
        imported_roots: set[str] = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".")[0])
        offending = imported_roots & network_roots
        assert not offending, (
            f"script must make no network calls; found imports: {sorted(offending)}"
        )

    def test_record_contains_no_mcp_url(self) -> None:
        """The committed record contains no MCP URL substring (Req 5.3)."""
        text = self._record_path().read_text(encoding="utf-8")
        assert _MCP_URL_FRAGMENT not in text

    def test_workflow_runs_check_mode(self) -> None:
        """CI runs the Coverage_Validator via example_coverage_report.py --check (Req 7.5)."""
        workflow = self.REPO_ROOT / ".github" / "workflows" / "validate-power.yml"
        assert workflow.is_file()
        assert "example_coverage_report.py --check" in workflow.read_text(encoding="utf-8")

    def test_power_md_has_disclosure_markers(self) -> None:
        """POWER.md carries the example-coverage generated-region markers (Req 4.3)."""
        power_md = (self.POWER_ROOT / "POWER.md").read_text(encoding="utf-8")
        assert "<!-- BEGIN GENERATED: example-coverage -->" in power_md
        assert "<!-- END GENERATED: example-coverage -->" in power_md


class TestExampleEdge:
    """Example/edge tests asserting the committed Coverage_Record's content and
    the script's CLI contract (explicit argv and ``--help``).

    These read the real committed record at ``config/example-coverage.yaml`` and
    drive ``main()`` against it, so they double as a guard that the shipped record
    stays schema-valid and self-describing.
    """

    #: Power root: ``senzing-bootcamp/`` (parent of ``tests/``).
    POWER_ROOT = Path(__file__).resolve().parent.parent

    def _record_path(self) -> Path:
        return self.POWER_ROOT / "config" / "example-coverage.yaml"

    def _raw_metadata(self) -> dict:
        """Parse the committed record's raw ``metadata`` mapping with PyYAML."""
        import yaml

        data = yaml.safe_load(self._record_path().read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        metadata = data["metadata"]
        assert isinstance(metadata, dict)
        return metadata

    def test_committed_record_lists_expected_languages(self) -> None:
        """The committed record lists the five expected Supported_Languages (Req 1.2)."""
        record = load_coverage_record(self._record_path())
        assert set(record.languages) == {"python", "java", "csharp", "rust", "typescript"}

    def test_committed_record_has_non_empty_topics(self) -> None:
        """The committed record declares a non-empty topic set (Req 1.3)."""
        record = load_coverage_record(self._record_path())
        assert len(record.topics) >= 1

    def test_signal_definition_references_find_examples(self) -> None:
        """metadata.signal_definition references the find_examples tool (Req 2.1)."""
        signal_definition = self._raw_metadata()["signal_definition"]
        assert isinstance(signal_definition, str)
        assert "find_examples" in signal_definition

    def test_status_meanings_available_present_and_non_empty(self) -> None:
        """metadata.status_meanings.available is present and non-empty (Req 2.2)."""
        status_meanings = self._raw_metadata()["status_meanings"]
        assert isinstance(status_meanings, dict)
        available = status_meanings["available"]
        assert isinstance(available, str)
        assert available.strip()

    def test_status_meanings_unknown_present_and_non_empty(self) -> None:
        """metadata.status_meanings.unknown is present and non-empty (Req 2.3)."""
        status_meanings = self._raw_metadata()["status_meanings"]
        assert isinstance(status_meanings, dict)
        unknown = status_meanings["unknown"]
        assert isinstance(unknown, str)
        assert unknown.strip()

    def test_maintenance_present_and_non_empty(self) -> None:
        """metadata.maintenance is present and non-empty (Req 5.4)."""
        maintenance = self._raw_metadata()["maintenance"]
        assert isinstance(maintenance, str)
        assert maintenance.strip()

    def test_main_accepts_explicit_argv_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """main() accepts an explicit argv and emits JSON for --format json (Req 3.3)."""
        import json

        exit_code = main(["--format", "json"])
        assert exit_code == 0

        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, dict)

    def test_main_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        """main(["--help"]) triggers argparse help and exits with code 0 (Req 3.3)."""
        with pytest.raises(SystemExit) as excinfo:
            main(["--help"])
        assert excinfo.value.code == 0

    def test_snapshot_is_single_current_object(self) -> None:
        """The snapshot is a single current object with populated fields (Req 8.3)."""
        record = load_coverage_record(self._record_path())
        assert record.snapshot.last_observed.strip()
        assert record.snapshot.senzing_version.strip()

        # The raw metadata.snapshot is a single mapping, not a list of snapshots.
        snapshot = self._raw_metadata()["snapshot"]
        assert isinstance(snapshot, dict)
        assert not isinstance(snapshot, list)
