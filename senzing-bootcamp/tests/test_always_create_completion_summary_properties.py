"""Always-create completion summary — fix + preservation property suite.

Bugfix: always-create-completion-summary

These properties exercise the *script contract* that the steering fix relies on.
Governing rule 16 requires the completion-summary document (``docs/completion_summary.md``)
to ALWAYS be created at graduation/stopping points; the fix re-scopes the yes/no answer
so it governs only the shareable PDF. Because the script ``generate_completion_summary.py``
already writes the markdown unconditionally and gates only the PDF behind ``--pdf``, these
properties PASS on the current (unfixed) script and pin the behavior the fix depends on
(confirming "no script change needed").

Properties (see design.md "Correctness Properties"):
- Property 3 (design Property 1): Markdown always created regardless of answer.
- Property 4 (design Property 2): The answer governs only the PDF.
- Property 5 (design Property 3): Graceful degradation on empty/whitespace log.
- Property 6 (design Property 4): Script invariants unchanged (ordering, four
  subsections per module, metadata completeness).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts are not packages — sys.path manipulation).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_completion_summary import (  # noqa: E402
    build_narrative,
    ensure_fpdf2,
    main,
    render_markdown,
)
from session_logger import (  # noqa: E402
    COMPLETION_EVENT_TYPES,
    CompletionLogEntry,
    build_completion_entry,
    serialize_completion_entry,
)

# Resolve fpdf2 availability once (the script's helper) so the PDF property can
# skip gracefully where fpdf2 is unavailable, consistent with the integration test.
_FPDF_AVAILABLE: bool = ensure_fpdf2()


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_-prefixed) — replicate the patterns from
# test_completion_summary_properties.py for a self-contained suite.
# ---------------------------------------------------------------------------

_VALID_ACTION_TYPES = [
    "file_create", "file_modify", "file_delete", "command_run", "mcp_tool_call",
]
_FILE_ACTION_TYPES = {"file_create", "file_modify", "file_delete"}
_VALID_ARTIFACT_TYPES = ["script", "config", "data", "report", "visualization"]


@st.composite
def st_question_data(draw) -> dict[str, str]:
    """Generate a valid data dict for a question event."""
    text = draw(st.text(min_size=1, max_size=100))
    question_id = draw(st.text(min_size=1, max_size=8, alphabet="abcdef0123456789"))
    return {"text": text, "question_id": question_id}


@st.composite
def st_answer_data(draw) -> dict[str, str]:
    """Generate a valid data dict for an answer event."""
    text = draw(st.text(min_size=1, max_size=100))
    question_id = draw(st.text(min_size=1, max_size=8, alphabet="abcdef0123456789"))
    return {"text": text, "question_id": question_id}


@st.composite
def st_action_data(draw) -> dict[str, str]:
    """Generate a valid data dict for an action event."""
    action_type = draw(st.sampled_from(_VALID_ACTION_TYPES))
    description = draw(st.text(min_size=1, max_size=100))
    data: dict[str, str] = {"action_type": action_type, "description": description}
    if action_type in _FILE_ACTION_TYPES:
        data["file_path"] = draw(
            st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz/._")
        )
    return data


@st.composite
def st_artifact_data(draw) -> dict[str, str]:
    """Generate a valid data dict for an artifact event."""
    file_path = draw(
        st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz/._")
    )
    artifact_type = draw(st.sampled_from(_VALID_ARTIFACT_TYPES))
    description = draw(st.text(min_size=1, max_size=100))
    return {"file_path": file_path, "artifact_type": artifact_type, "description": description}


@st.composite
def st_completion_entry(draw) -> CompletionLogEntry:
    """Generate any valid CompletionLogEntry via build_completion_entry."""
    event_type = draw(st.sampled_from(sorted(COMPLETION_EVENT_TYPES)))
    module = draw(st.integers(min_value=0, max_value=11))

    if event_type == "question":
        data = draw(st_question_data())
    elif event_type == "answer":
        data = draw(st_answer_data())
    elif event_type == "action":
        data = draw(st_action_data())
    else:
        data = draw(st_artifact_data())

    return build_completion_entry(event_type, module, data)


@st.composite
def st_content_entry(draw) -> CompletionLogEntry:
    """Generate a content-producing entry (question/action/artifact only).

    Answer-only modules render as "Session log was unavailable"; restricting to
    these event types guarantees at least one populated narrative section so the
    PDF branch has content to render.
    """
    event_type = draw(st.sampled_from(["question", "action", "artifact"]))
    module = draw(st.integers(min_value=0, max_value=11))
    if event_type == "question":
        data = draw(st_question_data())
    elif event_type == "action":
        data = draw(st_action_data())
    else:
        data = draw(st_artifact_data())
    return build_completion_entry(event_type, module, data)


@st.composite
def st_session_log(draw) -> list[CompletionLogEntry]:
    """Generate a varied multi-module session log with guaranteed content.

    Draws a list of arbitrary completion entries and appends one guaranteed
    content-producing entry, so the log always yields at least one populated
    per-module section.
    """
    entries: list[CompletionLogEntry] = draw(
        st.lists(st_completion_entry(), min_size=0, max_size=10)
    )
    entries.append(draw(st_content_entry()))
    return entries


def st_whitespace_log() -> st.SearchStrategy[str]:
    """Draw empty or whitespace-only session-log file content."""
    return st.sampled_from(
        ["", " ", "   ", "\n", "\n\n", "  \n  \n", "\t\n", "   \n\t  \n"]
    )


@st.composite
def st_bootcamper_name(draw) -> str:
    """Generate a non-empty bootcamper name (stripped, since YAML strips values)."""
    name = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("L", "Nd", "Zs")),
    ))
    stripped = name.strip()
    assume(len(stripped) > 0)
    return stripped


def st_track_name() -> st.SearchStrategy[str]:
    """Draw a valid track name."""
    return st.sampled_from(
        ["core_bootcamp", "advanced_bootcamp", "data_engineering", "full_stack"]
    )


@st.composite
def st_modules_completed_list(draw) -> list[int]:
    """Generate a non-empty, sorted list of completed module numbers (1-11)."""
    modules = draw(st.lists(
        st.integers(min_value=1, max_value=11),
        min_size=1,
        max_size=11,
        unique=True,
    ))
    return sorted(modules)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_log_and_config(
    tmpdir: str,
    *,
    log_content: str,
    modules_completed: list[int] | None = None,
    track: str = "core_bootcamp",
    name: str = "Test Bootcamper",
) -> tuple[str, str, str]:
    """Write session_log.jsonl, progress JSON, and preferences YAML into tmpdir.

    Args:
        tmpdir: Temporary directory path.
        log_content: Raw text to write into session_log.jsonl.
        modules_completed: Completed module numbers for the progress file.
        track: Track name for the progress/preferences files.
        name: Bootcamper name for the preferences file.

    Returns:
        Tuple of (log_path, progress_path, preferences_path).
    """
    base = Path(tmpdir)
    log_path = base / "session_log.jsonl"
    progress_path = base / "bootcamp_progress.json"
    preferences_path = base / "bootcamp_preferences.yaml"

    log_path.write_text(log_content, encoding="utf-8")
    progress_path.write_text(
        json.dumps({"modules_completed": modules_completed or [], "track": track}),
        encoding="utf-8",
    )
    preferences_path.write_text(f"name: {name}\ntrack: {track}\n", encoding="utf-8")

    return str(log_path), str(progress_path), str(preferences_path)


def _serialize_log(entries: list[CompletionLogEntry]) -> str:
    """Render a list of completion entries as JSONL text."""
    return "".join(serialize_completion_entry(e) + "\n" for e in entries)


# ---------------------------------------------------------------------------
# Property 3 (design Property 1): Markdown always created regardless of answer.
# ---------------------------------------------------------------------------


class TestMarkdownAlwaysCreatedProperty:
    """Property 3: Fix — Markdown always created regardless of answer.

    For any varied session log, running ``main([...])`` with no ``--pdf`` always
    writes ``completion_summary.md`` containing the per-module ``## Module N:``
    sections. The script takes no yes/no answer, so the markdown's existence is
    independent of any offer answer — pinning the always-create contract.

    Validates: Requirements 2.1, 2.2, 2.4
    """

    @given(entries=st_session_log())
    @settings(max_examples=20)
    def test_markdown_created_with_per_module_sections(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """main() without --pdf always creates the markdown with per-module sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=_serialize_log(entries)
            )
            output_path = Path(tmpdir) / "completion_summary.md"
            pdf_path = Path(tmpdir) / "completion_summary.pdf"

            exit_code = main([
                "--log", log_path,
                "--output", str(output_path),
                "--progress", progress_path,
                "--preferences", prefs_path,
            ])

            assert exit_code == 0, "main() should succeed for a valid session log"
            assert output_path.exists(), "completion_summary.md must always be created"

            content = output_path.read_text(encoding="utf-8")

            # Every module appearing in the log gets a `## Module N:` section,
            # independent of any yes/no answer.
            modules_in_log = {e.module for e in entries}
            for mod_num in modules_in_log:
                assert f"## Module {mod_num}:" in content, (
                    f"Expected '## Module {mod_num}:' section in the markdown"
                )

            # No --pdf means only the markdown is produced.
            assert not pdf_path.exists(), "PDF must not be created without --pdf"


# ---------------------------------------------------------------------------
# Property 4 (design Property 2): The answer governs only the PDF.
# ---------------------------------------------------------------------------


class TestAnswerGovernsOnlyPdfProperty:
    """Property 4: Fix — Answer governs only the PDF.

    For the same logs, ``main([..., "--pdf"])`` creates both the markdown and the
    PDF, while ``main([...])`` creates only the markdown. This models that the
    secondary concern (PDF/share) is the only thing the yes/no answer toggles —
    the always-created markdown is unaffected.

    Validates: Requirements 2.2, 2.3, 2.6
    """

    @given(entries=st_session_log())
    @settings(max_examples=20)
    def test_pdf_only_added_when_requested(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """Without --pdf: markdown only. With --pdf: markdown + PDF."""
        log_content = _serialize_log(entries)

        # Run 1 — no --pdf: only the markdown is created ("no" answer analogue).
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=log_content
            )
            md_only = Path(tmpdir) / "completion_summary.md"
            pdf_only = Path(tmpdir) / "completion_summary.pdf"

            exit_code = main([
                "--log", log_path,
                "--output", str(md_only),
                "--progress", progress_path,
                "--preferences", prefs_path,
            ])
            assert exit_code == 0
            assert md_only.exists(), "markdown must be created without --pdf"
            assert not pdf_only.exists(), "PDF must not exist without --pdf"

        # Run 2 — with --pdf: both the markdown and the PDF are created ("yes").
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=log_content
            )
            md_path = Path(tmpdir) / "completion_summary.md"
            pdf_path = Path(tmpdir) / "completion_summary.pdf"

            exit_code = main([
                "--log", log_path,
                "--output", str(md_path),
                "--progress", progress_path,
                "--preferences", prefs_path,
                "--pdf",
                "--pdf-output", str(pdf_path),
            ])
            assert exit_code == 0
            assert md_path.exists(), "markdown must be created with --pdf"

            if not _FPDF_AVAILABLE:
                pytest.skip("fpdf2 not available — skipping PDF assertion")

            assert pdf_path.exists(), "PDF must be created when --pdf is supplied"


# ---------------------------------------------------------------------------
# Property 5 (design Property 3): Graceful degradation on empty/whitespace log.
# ---------------------------------------------------------------------------


class TestGracefulDegradationProperty:
    """Property 5: Fix — Graceful degradation on empty/whitespace log.

    With an empty or whitespace-only ``session_log.jsonl``, ``main([...])`` still
    produces the markdown with the "Session log was unavailable" rendering and does
    not crash — the always-create contract degrades gracefully, not into an error.

    Validates: Requirements 2.5, 3.9
    """

    @given(
        log_content=st_whitespace_log(),
        modules_completed=st_modules_completed_list(),
    )
    @settings(max_examples=20)
    def test_empty_log_still_produces_markdown(
        self, log_content: str, modules_completed: list[int]
    ) -> None:
        """An empty/whitespace log yields markdown with the unavailable rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path, progress_path, prefs_path = _write_log_and_config(
                tmpdir,
                log_content=log_content,
                modules_completed=modules_completed,
            )
            output_path = Path(tmpdir) / "completion_summary.md"

            exit_code = main([
                "--log", log_path,
                "--output", str(output_path),
                "--progress", progress_path,
                "--preferences", prefs_path,
            ])

            assert exit_code == 0, "main() must not crash on an empty/whitespace log"
            assert output_path.exists(), "markdown must be produced even with no events"

            content = output_path.read_text(encoding="utf-8")
            assert "Session log was unavailable for this module." in content, (
                "Empty log should render the graceful 'unavailable' fallback"
            )


# ---------------------------------------------------------------------------
# Property 6 (design Property 4): Script invariants unchanged (preservation).
# ---------------------------------------------------------------------------


class TestScriptInvariantsPreservedProperty:
    """Property 6: Preservation — Script invariants unchanged.

    Reusing the completion-entry strategies, re-assert the script's preserved
    behavior: module-ascending section ordering, the four-subsection presence per
    populated module, and metadata completeness via build_narrative /
    render_markdown.

    Validates: Requirements 3.8
    """

    @given(entries=st.lists(st_completion_entry(), min_size=2, max_size=15))
    @settings(max_examples=20)
    def test_sections_ordered_by_module_ascending(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """build_narrative sections are strictly ascending by module_number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=_serialize_log(entries)
            )
            narrative = build_narrative(entries, progress_path, prefs_path)

            module_numbers = [s.module_number for s in narrative.sections]
            assert module_numbers == sorted(module_numbers), (
                f"Sections not in ascending module_number order: {module_numbers}"
            )
            assert len(module_numbers) == len(set(module_numbers)), (
                f"Duplicate module_numbers found: {module_numbers}"
            )

    @given(entries=st.lists(st_completion_entry(), min_size=1, max_size=15))
    @settings(max_examples=20)
    def test_each_module_has_four_subsection_lists(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """Each module with events exposes the four content categories as lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=_serialize_log(entries)
            )
            narrative = build_narrative(entries, progress_path, prefs_path)

            modules_with_entries = {e.module for e in entries}
            for mod_num in modules_with_entries:
                matching = [s for s in narrative.sections if s.module_number == mod_num]
                assert len(matching) == 1, (
                    f"Expected exactly 1 section for module {mod_num}, got {len(matching)}"
                )
                section = matching[0]
                assert isinstance(section.questions, list), "questions must be a list"
                assert isinstance(section.actions, list), "actions must be a list"
                assert isinstance(section.artifacts, list), "artifacts must be a list"

    @given(entries=st_session_log())
    @settings(max_examples=20)
    def test_populated_modules_render_four_subsections(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """Each populated module renders all four markdown subsection headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, progress_path, prefs_path = _write_log_and_config(
                tmpdir, log_content=_serialize_log(entries)
            )
            narrative = build_narrative(entries, progress_path, prefs_path)
            content = render_markdown(narrative)

            blocks = content.split("\n## Module ")
            for section in narrative.sections:
                has_content = (
                    section.questions or section.actions or section.artifacts
                )
                if not has_content:
                    continue
                marker = f"{section.module_number}: {section.module_name}"
                block = next((b for b in blocks if b.startswith(marker)), None)
                assert block is not None, f"Missing rendered block for module {marker}"
                for header in (
                    "### Questions Asked",
                    "### Answers Given",
                    "### Actions Taken",
                    "### Artifacts Created",
                ):
                    assert header in block, (
                        f"Module {section.module_number} block missing '{header}'"
                    )

    @given(
        entries=st.lists(st_completion_entry(), min_size=1, max_size=10),
        bootcamper_name=st_bootcamper_name(),
        track=st_track_name(),
        modules_completed=st_modules_completed_list(),
    )
    @settings(max_examples=20)
    def test_metadata_completeness(
        self,
        entries: list[CompletionLogEntry],
        bootcamper_name: str,
        track: str,
        modules_completed: list[int],
    ) -> None:
        """Rendered markdown carries the cover metadata and summary statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, progress_path, prefs_path = _write_log_and_config(
                tmpdir,
                log_content=_serialize_log(entries),
                modules_completed=modules_completed,
                track=track,
                name=bootcamper_name,
            )
            narrative = build_narrative(entries, progress_path, prefs_path)
            content = render_markdown(narrative)

            assert f"**Bootcamper:** {bootcamper_name}" in content
            assert "**Started:**" in content
            assert "**Completed:**" in content
            assert "**Duration:**" in content
            assert f"**Track:** {track}" in content
            assert f"| Modules Completed | {len(modules_completed)} |" in content
            assert "| Artifacts Produced |" in content
