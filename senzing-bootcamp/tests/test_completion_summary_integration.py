"""Integration tests for the completion summary feature.

Tests the full pipeline from session log events through narrative formatting
to markdown/PDF output, plus validation of steering and hook file content.

Feature: completion-summary
Requirements: 3.2, 5.1, 7.3, 7.4
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup for importing scripts
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_completion_summary import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PDF_OUTPUT_PATH,
    build_narrative,
    parse_session_log,
    render_markdown,
    write_narrative,
)

# ---------------------------------------------------------------------------
# Paths to real files
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _POWER_ROOT / "steering"
_HOOKS_DIR: Path = _POWER_ROOT / "hooks"
_STEERING_FILE: Path = _STEERING_DIR / "completion-summary-offer.md"
_HOOK_FILE: Path = _HOOKS_DIR / "session-log-events.kiro.hook"


# ---------------------------------------------------------------------------
# Helper: create a sample session log
# ---------------------------------------------------------------------------


def _create_sample_session_log(log_path: Path) -> None:
    """Write a multi-module session log with various event types."""
    entries = [
        {
            "event_type": "question",
            "module": 1,
            "timestamp": "2025-01-10T09:00:00Z",
            "data": {
                "text": "What business problem are you solving?",
                "question_id": "q001",
            },
        },
        {
            "event_type": "answer",
            "module": 1,
            "timestamp": "2025-01-10T09:05:00Z",
            "data": {
                "text": "We need to deduplicate customer records.",
                "question_id": "q001",
            },
        },
        {
            "event_type": "action",
            "module": 2,
            "timestamp": "2025-01-11T10:00:00Z",
            "data": {
                "action_type": "file_create",
                "description": "Created SDK setup script",
                "file_path": "scripts/setup_sdk.py",
            },
        },
        {
            "event_type": "artifact",
            "module": 2,
            "timestamp": "2025-01-11T10:30:00Z",
            "data": {
                "file_path": "scripts/setup_sdk.py",
                "artifact_type": "script",
                "description": "SDK initialization script",
            },
        },
        {
            "event_type": "question",
            "module": 3,
            "timestamp": "2025-01-12T08:00:00Z",
            "data": {
                "text": "Which data sources do you want to profile?",
                "question_id": "q002",
            },
        },
        {
            "event_type": "answer",
            "module": 3,
            "timestamp": "2025-01-12T08:10:00Z",
            "data": {
                "text": "The CRM export and the vendor list CSV.",
                "question_id": "q002",
            },
        },
        {
            "event_type": "action",
            "module": 3,
            "timestamp": "2025-01-12T09:00:00Z",
            "data": {
                "action_type": "command_run",
                "description": "Ran data profiling analysis",
            },
        },
        {
            "event_type": "artifact",
            "module": 3,
            "timestamp": "2025-01-12T09:30:00Z",
            "data": {
                "file_path": "docs/data_profile_report.md",
                "artifact_type": "report",
                "description": "Data profiling report",
            },
        },
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Tests: End-to-End Pipeline
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """Test the full pipeline: log events → parse → build narrative → render → write.

    Requirements: 3.2, 5.1
    """

    def test_full_pipeline_log_to_markdown(self) -> None:
        """Full pipeline produces valid markdown with expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "config" / "session_log.jsonl"
            progress_path = tmp / "config" / "bootcamp_progress.json"
            prefs_path = tmp / "config" / "bootcamp_preferences.yaml"
            output_path = tmp / "docs" / "completion_summary.md"

            # Create session log
            _create_sample_session_log(log_path)

            # Create progress file
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(json.dumps({
                "current_module": 3,
                "modules_completed": [1, 2, 3],
                "track": "core_bootcamp",
            }), encoding="utf-8")

            # Create preferences file
            prefs_path.write_text(
                "name: Jane Smith\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            # Run pipeline
            entries = parse_session_log(str(log_path))
            narrative = build_narrative(
                entries, str(progress_path), str(prefs_path)
            )
            md_content = render_markdown(narrative)
            write_narrative(str(output_path), md_content)

            # Verify output file exists
            assert output_path.exists(), "Output markdown file should exist"

            content = output_path.read_text(encoding="utf-8")

            # Verify module headings present
            assert "## Module 1:" in content, "Should contain Module 1 heading"
            assert "## Module 2:" in content, "Should contain Module 2 heading"
            assert "## Module 3:" in content, "Should contain Module 3 heading"

            # Verify question/answer content
            assert "What business problem are you solving?" in content
            assert "We need to deduplicate customer records." in content

            # Verify artifact entries
            assert "scripts/setup_sdk.py" in content
            assert "SDK initialization script" in content

            # Verify file size within limit
            file_size = output_path.stat().st_size
            assert file_size <= 512000, (
                f"File size {file_size} exceeds 512000 byte limit"
            )

    def test_full_pipeline_log_to_pdf(self) -> None:
        """Full pipeline can generate a PDF file (if fpdf2 available)."""
        try:
            import fpdf  # noqa: F401
        except ImportError:
            import pytest
            pytest.skip("fpdf2 not installed — skipping PDF test")

        from generate_completion_summary import render_completion_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "config" / "session_log.jsonl"
            progress_path = tmp / "config" / "bootcamp_progress.json"
            prefs_path = tmp / "config" / "bootcamp_preferences.yaml"
            pdf_path = tmp / "docs" / "completion_summary.pdf"

            # Create session log
            _create_sample_session_log(log_path)

            # Create progress file
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(json.dumps({
                "current_module": 3,
                "modules_completed": [1, 2, 3],
                "track": "core_bootcamp",
            }), encoding="utf-8")

            # Create preferences file
            prefs_path.write_text(
                "name: Jane Smith\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            # Run pipeline
            entries = parse_session_log(str(log_path))
            narrative = build_narrative(
                entries, str(progress_path), str(prefs_path)
            )
            render_completion_pdf(narrative, str(pdf_path))

            # Verify PDF file exists and is non-empty
            assert pdf_path.exists(), "PDF file should exist"
            assert pdf_path.stat().st_size > 0, "PDF file should be non-empty"


# ---------------------------------------------------------------------------
# Tests: Steering File Content
# ---------------------------------------------------------------------------


class TestSteeringFileContent:
    """Validate steering file content matches requirements.

    Requirements: 3.2, 7.3
    """

    def test_steering_file_exists(self) -> None:
        """Steering file exists at expected path."""
        assert _STEERING_FILE.exists(), (
            f"Steering file not found at {_STEERING_FILE}"
        )

    def test_steering_file_has_yaml_frontmatter(self) -> None:
        """Steering file starts with YAML frontmatter delimiters."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Steering file must start with '---' YAML frontmatter delimiter"
        )
        # Must have closing delimiter
        parts = content.split("---", 2)
        assert len(parts) >= 3, (
            "Steering file must have opening and closing '---' delimiters"
        )

    def test_steering_file_mentions_four_categories(self) -> None:
        """Steering file mentions all four content categories."""
        content = _STEERING_FILE.read_text(encoding="utf-8").lower()
        assert "questions asked" in content, (
            "Steering file must mention 'questions asked'"
        )
        assert "answers given" in content, (
            "Steering file must mention 'answers given'"
        )
        assert "actions taken" in content, (
            "Steering file must mention 'actions taken'"
        )
        assert "artifacts created" in content, (
            "Steering file must mention 'artifacts created'"
        )

    def test_steering_file_names_deliverable(self) -> None:
        """Steering file mentions 'Completion Summary PDF' as deliverable name."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert "Completion Summary PDF" in content, (
            "Steering file must name the deliverable as 'Completion Summary PDF'"
        )

    def test_steering_file_binary_prompt(self) -> None:
        """Steering file specifies a yes/no binary prompt."""
        content = _STEERING_FILE.read_text(encoding="utf-8").lower()
        assert "yes/no" in content, (
            "Steering file must mention 'yes/no' binary prompt requirement"
        )

    def test_steering_file_ordering_rules(self) -> None:
        """Steering file specifies ordering (after celebration, before export)."""
        content = _STEERING_FILE.read_text(encoding="utf-8").lower()
        # Check for ordering-related content
        assert "celebration" in content or "🎉" in content, (
            "Steering file must mention ordering relative to celebration message"
        )
        assert "export" in content, (
            "Steering file must mention ordering relative to export results offer"
        )


# ---------------------------------------------------------------------------
# Tests: Hook File Integration
# ---------------------------------------------------------------------------


class TestHookFileIntegration:
    """Validate hook file structure for integration.

    Requirements: 7.3
    """

    def test_hook_file_valid_json(self) -> None:
        """Hook file is valid JSON."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_hook_file_has_required_fields(self) -> None:
        """Hook file has required fields: name, version, when, then."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        required = {"name", "version", "when", "then"}
        missing = required - set(hook.keys())
        assert not missing, f"Missing required hook fields: {missing}"

    def test_hook_captures_write_operations(self) -> None:
        """Hook toolTypes includes 'write' to capture write operations."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        tool_types = hook.get("when", {}).get("toolTypes", [])
        assert "write" in tool_types, (
            "Hook must capture write operations via toolTypes"
        )


# ---------------------------------------------------------------------------
# Tests: Output Path Separation
# ---------------------------------------------------------------------------


class TestOutputPathSeparation:
    """Verify completion summary paths do not collide with recap paths.

    Requirements: 7.4
    """

    def test_pdf_output_path_not_recap(self) -> None:
        """DEFAULT_PDF_OUTPUT_PATH is not the recap PDF path."""
        assert DEFAULT_PDF_OUTPUT_PATH != "docs/bootcamp_recap.pdf", (
            "Completion summary PDF must not collide with bootcamp_recap.pdf"
        )

    def test_markdown_output_path_not_recap(self) -> None:
        """DEFAULT_OUTPUT_PATH is not the recap markdown path."""
        assert DEFAULT_OUTPUT_PATH != "docs/bootcamp_recap.md", (
            "Completion summary markdown must not collide with bootcamp_recap.md"
        )
