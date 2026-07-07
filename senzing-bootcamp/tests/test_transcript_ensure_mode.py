"""Tests for the transcript renderer's ``--ensure`` mode.

Feature: guaranteed-graduation-artifacts

Covers the "ensure" mode added to ``generate_transcript.py`` (task 2.1): when
``--ensure`` is set and there are no Q&A events, ``main`` writes a Non_Empty
placeholder transcript containing an explicit "no Q&A history was available"
record (Req 1.8) rather than writing nothing. The default mode (no ``--ensure``)
preserves the pre-existing backward-compatible behavior of writing nothing when
there are no Q&A events. The pure ``render_empty_transcript`` helper is exercised
directly so the placeholder is verified without touching the filesystem.

All fixtures use synthetic, PII-free content; no secret-looking strings are
placed in the generated data.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_transcript  # noqa: E402

# Event types the renderer treats as Q&A events.
_QA_EVENT_TYPES = {"question", "answer"}

# The heading + phrasing that identify the "no Q&A history" record (Req 1.8).
_NO_HISTORY_HEADING = "## No Q&A History Available"
_NO_HISTORY_PHRASE = "no q&a history was available"

# A fixed generation timestamp used by the helper-level tests (no clock use).
_GENERATED_AT = "2024-01-01T12:00:00+00:00"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_generated_at(draw) -> str:
    """Generate an ISO-like generation timestamp string.

    Produces deterministic, PII-free ``2024-01-01T{hh}:{mm}:{ss}+00:00`` values
    so the placeholder header can be checked for the exact timestamp.
    """
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return f"2024-01-01T{hour:02d}:{minute:02d}:{second:02d}+00:00"


@st.composite
def st_non_qa_line(draw) -> str:
    """Generate a single log line that is never a valid Q&A event.

    Covers blank lines, invalid JSON, and JSON objects whose ``event_type`` is
    not a Q&A event, so ``read_events`` yields nothing for the generated log.
    """
    kind = draw(st.sampled_from(["blank", "invalid", "non_qa"]))
    if kind == "blank":
        return draw(st.sampled_from(["", "   ", "\t"]))
    if kind == "invalid":
        return draw(
            st.sampled_from(["not valid json", "{broken: ", "][", "<<<>>>"])
        )
    # A well-formed JSON object with a non-Q&A event_type.
    event_type = draw(
        st.sampled_from(["turn", "action", "module_start", "artifact", "correction"])
    )
    return (
        '{"event_type": "' + event_type + '", "module": '
        + str(draw(st.integers(min_value=0, max_value=11)))
        + "}"
    )


@st.composite
def st_empty_of_qa_log(draw) -> str:
    """Generate full log text containing ZERO Q&A events.

    Produces either an entirely empty file or an interleaving of non-Q&A lines.
    By construction ``read_events`` yields nothing for the result.
    """
    if draw(st.booleans()):
        return ""
    lines = draw(st.lists(st_non_qa_line(), max_size=10))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _is_qa_event_line(line: str) -> bool:
    """Return True if *line* would parse to a Q&A event dict."""
    import json

    stripped = line.strip()
    if not stripped:
        return False
    try:
        obj = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return False
    return isinstance(obj, dict) and obj.get("event_type") in _QA_EVENT_TYPES


# ---------------------------------------------------------------------------
# render_empty_transcript: the pure placeholder helper (Req 1.7, 1.8)
# ---------------------------------------------------------------------------


class TestRenderEmptyTranscript:
    """Validates ``render_empty_transcript`` output for the no-history case.

    The helper returns a Non_Empty Markdown document that always contains the
    metadata header (with zero totals) and an explicit record stating that no
    Q&A history was available -- verifiable without any filesystem access.

    Validates: Requirements 1.7, 1.8
    """

    def test_output_is_non_empty(self) -> None:
        document = generate_transcript.render_empty_transcript(_GENERATED_AT)

        # Non_Empty: at least one non-whitespace character.
        assert document.strip() != ""

    def test_contains_no_qa_history_record(self) -> None:
        document = generate_transcript.render_empty_transcript(_GENERATED_AT)

        # The explicit "no Q&A history" record is present (Req 1.8).
        assert _NO_HISTORY_HEADING in document
        assert _NO_HISTORY_PHRASE in document.lower()

    def test_contains_metadata_header_with_zero_totals(self) -> None:
        document = generate_transcript.render_empty_transcript(_GENERATED_AT)

        # The metadata header is present with the supplied timestamp and zero
        # question/answer totals.
        assert "# Bootcamp Q&A Transcript" in document
        assert f"- **Generated at:** {_GENERATED_AT}" in document
        assert "- **Total questions:** 0" in document
        assert "- **Answered questions:** 0" in document

    @given(generated_at=st_generated_at())
    def test_always_non_empty_with_history_record(self, generated_at: str) -> None:
        # For any generation timestamp, the placeholder is Non_Empty and carries
        # the no-history record and the supplied timestamp.
        document = generate_transcript.render_empty_transcript(generated_at)

        assert document.strip() != ""
        assert _NO_HISTORY_HEADING in document
        assert _NO_HISTORY_PHRASE in document.lower()
        assert f"- **Generated at:** {generated_at}" in document


# ---------------------------------------------------------------------------
# --ensure mode: guarantees a Non_Empty transcript when no Q&A events exist
# ---------------------------------------------------------------------------


class TestEnsureModeWritesPlaceholder:
    """Validates that ``--ensure`` guarantees a Non_Empty transcript.

    When ``--ensure`` is set and the log has no Q&A events (empty, non-Q&A only,
    or absent), ``main`` writes a Non_Empty transcript containing the "no Q&A
    history" record and returns 0.

    Validates: Requirements 1.7, 1.8
    """

    def test_ensure_with_empty_log_writes_placeholder(self, tmp_path, capsys) -> None:
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")
        out_path = tmp_path / "bootcamp_transcript.md"

        exit_code = generate_transcript.main(
            ["--log", str(log_path), "--output", str(out_path), "--ensure"]
        )

        assert exit_code == 0
        # A Non_Empty transcript exists on disk.
        assert out_path.exists()
        rendered = out_path.read_text(encoding="utf-8")
        assert rendered.strip() != ""
        # It carries the explicit "no Q&A history" record (Req 1.8).
        assert _NO_HISTORY_HEADING in rendered
        assert _NO_HISTORY_PHRASE in rendered.lower()

        captured = capsys.readouterr()
        assert "transcript" in captured.out.lower()

    def test_ensure_with_absent_log_writes_placeholder(self, tmp_path) -> None:
        missing_log = tmp_path / "does_not_exist.jsonl"
        out_path = tmp_path / "bootcamp_transcript.md"
        assert not missing_log.exists()

        exit_code = generate_transcript.main(
            ["--log", str(missing_log), "--output", str(out_path), "--ensure"]
        )

        assert exit_code == 0
        assert out_path.exists()
        rendered = out_path.read_text(encoding="utf-8")
        assert rendered.strip() != ""
        assert _NO_HISTORY_HEADING in rendered
        assert _NO_HISTORY_PHRASE in rendered.lower()

    @given(content=st_empty_of_qa_log())
    def test_ensure_always_writes_non_empty_transcript(self, content: str) -> None:
        # Guard: the generated content must truly contain zero Q&A events.
        for line in content.splitlines():
            assert not _is_qa_event_line(line)

        import tempfile

        log_dir = Path(tempfile.mkdtemp())
        out_dir = Path(tempfile.mkdtemp())
        log_path = log_dir / "session_log.jsonl"
        out_path = out_dir / "bootcamp_transcript.md"
        try:
            log_path.write_text(content, encoding="utf-8")
            assert not out_path.exists()

            exit_code = generate_transcript.main(
                ["--log", str(log_path), "--output", str(out_path), "--ensure"]
            )

            # Ensure mode always produces a Non_Empty transcript (Req 1.7, 1.8).
            assert exit_code == 0
            assert out_path.exists()
            rendered = out_path.read_text(encoding="utf-8")
            assert rendered.strip() != ""
            assert _NO_HISTORY_HEADING in rendered
            assert _NO_HISTORY_PHRASE in rendered.lower()
        finally:
            log_path.unlink(missing_ok=True)
            out_path.unlink(missing_ok=True)
            for directory in (log_dir, out_dir):
                try:
                    directory.rmdir()
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Default mode: unchanged backward-compatible behavior (writes nothing)
# ---------------------------------------------------------------------------


class TestDefaultModeBackwardCompat:
    """Validates default mode still writes nothing when there are no events.

    Without ``--ensure``, ``main`` preserves its pre-existing behavior: on a log
    with no Q&A events (empty or absent) it warns to stderr, writes no transcript
    file, and returns 0. This guards backward compatibility of the transcript
    renderer's existing contract.

    Validates: Requirements 1.7, 1.8
    """

    def test_default_with_empty_log_writes_nothing(self, tmp_path, capsys) -> None:
        log_path = tmp_path / "session_log.jsonl"
        log_path.write_text("", encoding="utf-8")
        out_path = tmp_path / "bootcamp_transcript.md"
        assert not out_path.exists()

        exit_code = generate_transcript.main(
            ["--log", str(log_path), "--output", str(out_path)]
        )

        # Backward compatible: returns 0, warns, and creates no output file.
        assert exit_code == 0
        assert not out_path.exists()
        captured = capsys.readouterr()
        assert "no transcript written" in captured.err.lower()

    def test_default_with_absent_log_writes_nothing(self, tmp_path, capsys) -> None:
        missing_log = tmp_path / "does_not_exist.jsonl"
        out_path = tmp_path / "bootcamp_transcript.md"
        assert not missing_log.exists()
        assert not out_path.exists()

        exit_code = generate_transcript.main(
            ["--log", str(missing_log), "--output", str(out_path)]
        )

        assert exit_code == 0
        assert not out_path.exists()
        captured = capsys.readouterr()
        assert "no transcript written" in captured.err.lower()

    @given(content=st_empty_of_qa_log())
    def test_default_never_writes_when_no_qa_events(self, content: str) -> None:
        # Guard: the generated content must truly contain zero Q&A events.
        for line in content.splitlines():
            assert not _is_qa_event_line(line)

        import tempfile

        log_dir = Path(tempfile.mkdtemp())
        out_dir = Path(tempfile.mkdtemp())
        log_path = log_dir / "session_log.jsonl"
        out_path = out_dir / "bootcamp_transcript.md"
        try:
            log_path.write_text(content, encoding="utf-8")
            assert not out_path.exists()

            exit_code = generate_transcript.main(
                ["--log", str(log_path), "--output", str(out_path)]
            )

            # Default mode writes nothing regardless of the (non-Q&A) content.
            assert exit_code == 0
            assert not out_path.exists()
        finally:
            log_path.unlink(missing_ok=True)
            out_path.unlink(missing_ok=True)
            for directory in (log_dir, out_dir):
                try:
                    directory.rmdir()
                except OSError:
                    pass
