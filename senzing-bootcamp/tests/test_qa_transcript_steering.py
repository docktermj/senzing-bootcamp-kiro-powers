"""Steering presence tests for ``qa-transcript.md``.

Feature: bootcamp-qa-transcript

This module hosts example-based (non-property) tests that assert the Q&A
transcript steering file exists, is well-formed, references the
``session_logger`` event types and helper functions, states the event-driven
(not per-write) constraint, and is registered in ``steering-index.yaml``.

The index is read as plain text and checked with substring assertions
(consistent with the project's "custom minimal parsers" convention); PyYAML is
not required.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve steering paths relative to this test file so the suite is
# location-independent: <repo>/senzing-bootcamp/tests/ -> ../steering/.
# ---------------------------------------------------------------------------
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_QA_TRANSCRIPT = _STEERING_DIR / "qa-transcript.md"
_STEERING_INDEX = _STEERING_DIR / "steering-index.yaml"


class TestQATranscriptSteering:
    """Validates Requirements 6.1, 6.2, 6.4, 6.5, 3.1.

    Confirms the ``qa-transcript.md`` steering file is present, carries YAML
    frontmatter, documents the ``session_logger`` event types and helper
    functions, encodes the event-driven (never per-write) constraint, and is
    registered in ``steering-index.yaml``.
    """

    def test_steering_file_exists(self) -> None:
        """The ``qa-transcript.md`` steering file is present (Req 6.1)."""
        assert _QA_TRANSCRIPT.exists(), f"missing steering file: {_QA_TRANSCRIPT}"
        assert _QA_TRANSCRIPT.is_file(), f"not a file: {_QA_TRANSCRIPT}"

    def test_has_yaml_frontmatter(self) -> None:
        """The file opens with a YAML frontmatter fence (Req 6.1)."""
        content = _QA_TRANSCRIPT.read_text(encoding="utf-8")
        assert content.lstrip().startswith("---"), "steering file lacks YAML frontmatter"

    def test_references_session_logger_event_types_and_functions(self) -> None:
        """References the event types and ``session_logger`` helpers (Req 6.2, 6.5)."""
        content = _QA_TRANSCRIPT.read_text(encoding="utf-8")
        required_substrings = [
            "session_logger",
            "question",
            "answer",
            "build_completion_entry",
            "append_completion_entry",
            "generate_question_id",
        ]
        missing = [s for s in required_substrings if s not in content]
        assert not missing, f"steering file missing required references: {missing}"

    def test_states_event_driven_not_per_write_constraint(self) -> None:
        """States the event-driven / not-per-write constraint (Req 6.4, 3.1)."""
        content = _QA_TRANSCRIPT.read_text(encoding="utf-8")
        # The constraint is encoded both as a heading phrase and via explicit
        # mention of the write tools that must NOT trigger Q&A logging.
        assert "event-driven" in content, "missing 'event-driven' framing"
        assert "never" in content.lower(), "missing 'never' constraint wording"
        # Names at least one write tool that is explicitly not a trigger.
        write_tools = ["fs_write", "fs_append", "str_replace"]
        named = [tool for tool in write_tools if tool in content]
        assert named, f"expected a write-tool reference from {write_tools}"
        # Explicitly disclaims coupling to file writes.
        assert "file writes" in content or "file-write" in content, (
            "missing explicit decoupling-from-file-writes statement"
        )

    def test_registered_in_steering_index(self) -> None:
        """The file is registered in ``steering-index.yaml`` (registration)."""
        index_text = _STEERING_INDEX.read_text(encoding="utf-8")
        assert "qa-transcript.md:" in index_text, (
            "qa-transcript.md is not registered under file_metadata in steering-index.yaml"
        )
