"""Unit tests for the completion summary feature.

Validates hook file structure, steering file content, and integration
points for the completion-summary feature.

Feature: completion-summary
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HOOKS_DIR: Path = Path(__file__).resolve().parent.parent / "hooks"
_HOOK_FILE: Path = _HOOKS_DIR / "session-log-events.kiro.hook"


# ---------------------------------------------------------------------------
# Tests: Hook File Structure (Task 7.2)
# ---------------------------------------------------------------------------


class TestHookFileStructure:
    """Validate the session-log-events.kiro.hook file structure.

    Requirements: 1.3, 1.4
    """

    def test_hook_file_exists(self) -> None:
        """Hook file exists at the expected path."""
        assert _HOOK_FILE.exists(), f"Hook file not found at {_HOOK_FILE}"

    def test_hook_file_is_valid_json(self) -> None:
        """Hook file contains valid JSON."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_hook_has_required_top_level_fields(self) -> None:
        """Hook JSON has required top-level fields: name, version, when, then."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        required_fields = {"name", "version", "when", "then"}
        missing = required_fields - set(hook.keys())
        assert not missing, f"Missing required fields: {missing}"

    def test_when_type_is_post_tool_use(self) -> None:
        """when.type is 'postToolUse'."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        assert hook["when"]["type"] == "postToolUse"

    def test_when_tool_types_contains_write(self) -> None:
        """when.toolTypes is a list containing 'write'."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        tool_types = hook["when"]["toolTypes"]
        assert isinstance(tool_types, list), "toolTypes must be a list"
        assert "write" in tool_types, "toolTypes must contain 'write'"

    def test_then_type_is_ask_agent(self) -> None:
        """then.type is 'askAgent'."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        assert hook["then"]["type"] == "askAgent"

    def test_then_prompt_is_non_empty_string(self) -> None:
        """then.prompt is a non-empty string."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        prompt = hook["then"]["prompt"]
        assert isinstance(prompt, str), "prompt must be a string"
        assert len(prompt) > 0, "prompt must not be empty"

    def test_name_is_non_empty_string(self) -> None:
        """name field is a non-empty string."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        name = hook["name"]
        assert isinstance(name, str), "name must be a string"
        assert len(name) > 0, "name must not be empty"

    def test_version_matches_semver_pattern(self) -> None:
        """version field matches semver pattern (MAJOR.MINOR.PATCH)."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook = json.loads(content)
        version = hook["version"]
        assert isinstance(version, str), "version must be a string"
        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(semver_pattern, version), (
            f"version '{version}' does not match semver pattern MAJOR.MINOR.PATCH"
        )


# ---------------------------------------------------------------------------
# Paths for PDF generator tests
# ---------------------------------------------------------------------------

import sys
import tempfile

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_completion_summary import (  # noqa: E402
    DEFAULT_PDF_OUTPUT_PATH,
    CompletionNarrative,
    NarrativeSection,
    ensure_fpdf2,
    generate_pdf_with_fallback,
    render_completion_pdf,
    render_markdown,
    write_narrative,
)
from session_logger import (  # noqa: E402
    CompletionLogEntry,
    append_completion_entry,
    build_completion_entry,
    serialize_completion_entry,
)


# ---------------------------------------------------------------------------
# Tests: PDF Generator (Task 4.2)
# ---------------------------------------------------------------------------


class TestPDFGenerator:
    """Validate PDF generator functions.

    Requirements: 5.5, 5.6, 5.7, 5.8, 5.9, 7.4
    """

    def test_ensure_fpdf2_returns_true_when_available(self) -> None:
        """fpdf2 is installed in this environment, so ensure_fpdf2() returns True."""
        result = ensure_fpdf2()
        assert result is True

    def test_generate_pdf_with_fallback_missing_markdown(self) -> None:
        """When md_path doesn't exist, returns message about missing markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = str(Path(tmpdir) / "nonexistent.md")
            pdf_path = str(Path(tmpdir) / "output.pdf")
            result = generate_pdf_with_fallback(md_path, pdf_path)
            assert "No completion summary markdown found" in result
            assert md_path in result

    def test_generate_pdf_with_fallback_empty_markdown(self) -> None:
        """When md_path exists but is empty, returns message about insufficient data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = str(Path(tmpdir) / "empty.md")
            pdf_path = str(Path(tmpdir) / "output.pdf")
            Path(md_path).write_text("", encoding="utf-8")
            result = generate_pdf_with_fallback(md_path, pdf_path)
            assert "empty" in result.lower() or "insufficient" in result.lower()
            assert md_path in result

    def test_generate_pdf_with_fallback_no_module_sections(self) -> None:
        """When md_path has content but no '## Module' sections, returns insufficient data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = str(Path(tmpdir) / "no_modules.md")
            pdf_path = str(Path(tmpdir) / "output.pdf")
            Path(md_path).write_text(
                "# Summary\n\nSome content without module sections.\n",
                encoding="utf-8",
            )
            result = generate_pdf_with_fallback(md_path, pdf_path)
            assert "insufficient data" in result.lower()
            assert md_path in result

    def test_output_path_separate_from_recap_pdf(self) -> None:
        """DEFAULT_PDF_OUTPUT_PATH is 'docs/completion_summary.pdf' (not recap)."""
        assert DEFAULT_PDF_OUTPUT_PATH == "docs/completion_summary.pdf"
        assert DEFAULT_PDF_OUTPUT_PATH != "docs/bootcamp_recap.pdf"

    def test_render_completion_pdf_creates_file(self) -> None:
        """Create a simple CompletionNarrative, call render_completion_pdf, verify PDF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = str(Path(tmpdir) / "test_output.pdf")
            narrative = CompletionNarrative(
                bootcamper_name="Test User",
                start_date="2025-01-10",
                completion_date="2025-01-15",
                total_duration="5 days, 12 hours",
                track="Core Bootcamp",
                modules_completed=3,
                total_artifacts=5,
                er_stats=None,
                sections=[
                    NarrativeSection(
                        module_number=1,
                        module_name="Business Problem",
                        questions=[("What problem are you solving?", "Deduplication")],
                        actions=["file_create: `docs/problem.md` — Created problem doc"],
                        artifacts=[("docs/problem.md", "report", "Business problem doc")],
                    ),
                ],
            )
            render_completion_pdf(narrative, pdf_path)
            assert Path(pdf_path).exists()
            assert Path(pdf_path).stat().st_size > 0

    def test_generate_pdf_with_fallback_success(self) -> None:
        """Full end-to-end: create session log, progress, preferences, generate md, then PDF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up paths
            log_path = str(Path(tmpdir) / "session_log.jsonl")
            progress_path = str(Path(tmpdir) / "progress.json")
            preferences_path = str(Path(tmpdir) / "preferences.yaml")
            md_path = str(Path(tmpdir) / "completion_summary.md")
            pdf_path = str(Path(tmpdir) / "completion_summary.pdf")

            # Create session log with events
            entries = [
                build_completion_entry(
                    "question", 1,
                    {"text": "What problem are you solving?", "question_id": "q001"},
                ),
                build_completion_entry(
                    "answer", 1,
                    {"text": "Customer deduplication", "question_id": "q001"},
                ),
                build_completion_entry(
                    "action", 1,
                    {
                        "action_type": "file_create",
                        "description": "Created business problem doc",
                        "file_path": "docs/business_problem.md",
                    },
                ),
                build_completion_entry(
                    "artifact", 1,
                    {
                        "file_path": "docs/business_problem.md",
                        "artifact_type": "report",
                        "description": "Business problem documentation",
                    },
                ),
            ]
            for entry in entries:
                append_completion_entry(log_path, entry)

            # Create progress file
            Path(progress_path).write_text(
                json.dumps({
                    "current_module": 2,
                    "modules_completed": [1],
                    "track": "core_bootcamp",
                }),
                encoding="utf-8",
            )

            # Create preferences file
            Path(preferences_path).write_text(
                "name: Test Bootcamper\ntrack: Core Bootcamp\nlanguage: python\n",
                encoding="utf-8",
            )

            # Generate markdown first (needed by generate_pdf_with_fallback)
            from generate_completion_summary import (  # noqa: PLC0415
                build_narrative,
                parse_session_log,
            )

            parsed_entries = parse_session_log(log_path)
            narrative = build_narrative(parsed_entries, progress_path, preferences_path)
            md_content = render_markdown(narrative)
            write_narrative(md_path, md_content)

            # Now generate PDF with fallback
            result = generate_pdf_with_fallback(
                md_path, pdf_path,
                log_path=log_path,
                progress_path=progress_path,
                preferences_path=preferences_path,
            )
            assert "generated" in result.lower() or pdf_path in result
            assert Path(pdf_path).exists()
            assert Path(pdf_path).stat().st_size > 0
