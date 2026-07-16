"""Focused schema-validation tests for the ``capture-qa-events.json`` hook.

Feature: durable-qa-capture
Validates the new Q&A capture hook file against the Kiro 1.0 ``v1`` hook JSON
schema and asserts the specific structure the durable-Q&A-capture cadence
relies on: a ``Stop`` entry that records the pending question and a
``UserPromptSubmit`` entry that records the bootcamper's answer, both invoking
``log_qa_event.py`` via a ``command`` action.

Reuses the repo's hook-schema conformance helpers
(``load_wrapper`` / ``validate_hook_schema``) rather than reinventing
validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from test_hook_schema_conformance import (
    HOOKS_DIR,
    V1_TRIGGERS,
    load_wrapper,
    validate_hook_schema,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CAPTURE_QA_HOOK_PATH = HOOKS_DIR / "capture-qa-events.json"

ALLOWED_TRIGGERS = {"Stop", "UserPromptSubmit"}


# ===========================================================================
# Feature: durable-qa-capture
# Requirement 2.1: the capture hook is a valid v1 hook file with a Stop entry
# (record-question) and a UserPromptSubmit entry (record-answer).
# ===========================================================================


class TestCaptureQaEventsHookSchema:
    """Schema-validation tests for ``senzing-bootcamp/hooks/capture-qa-events.json``.

    Feature: durable-qa-capture
    Validates: Requirements 2.1
    """

    @pytest.fixture(scope="class")
    def wrapper(self) -> dict:
        """Load and return the full ``capture-qa-events.json`` wrapper object."""
        assert CAPTURE_QA_HOOK_PATH.is_file(), (
            f"capture hook not found at {CAPTURE_QA_HOOK_PATH}"
        )
        return load_wrapper(CAPTURE_QA_HOOK_PATH)

    @pytest.fixture(scope="class")
    def entries(self, wrapper: dict) -> list[dict]:
        """Return the hook entries from the wrapper's ``hooks`` array."""
        hooks = wrapper.get("hooks")
        assert isinstance(hooks, list), '"hooks" must be a JSON array'
        return hooks

    def test_declares_version_v1(self, wrapper: dict) -> None:
        """The wrapper declares top-level ``version`` of ``"v1"``.

        Validates: Requirements 2.1
        """
        assert wrapper.get("version") == "v1", 'capture hook must declare version "v1"'

    def test_has_two_entries(self, entries: list[dict]) -> None:
        """The hook file contains exactly two entries (question + answer).

        Validates: Requirements 2.1
        """
        assert len(entries) == 2, (
            f"capture hook must contain exactly 2 entries, got {len(entries)}"
        )

    def test_every_entry_conforms_to_v1_schema(self, entries: list[dict]) -> None:
        """Each entry conforms to the shared v1 hook schema (reused helper).

        Validates: Requirements 2.1
        """
        for index, entry in enumerate(entries):
            errors = validate_hook_schema(entry)
            assert not errors, (
                f"capture hook entry {index} schema violations: {'; '.join(errors)}"
            )

    def test_every_entry_has_non_empty_name(self, entries: list[dict]) -> None:
        """Each entry carries a present, non-empty ``name``.

        Validates: Requirements 2.1
        """
        for index, entry in enumerate(entries):
            name = entry.get("name")
            assert isinstance(name, str) and name.strip(), (
                f"capture hook entry {index} must have a non-empty name"
            )

    def test_every_trigger_is_in_allowed_set(self, entries: list[dict]) -> None:
        """Each ``trigger`` is one of the allowed triggers ``{Stop, UserPromptSubmit}``.

        The allowed set is also a subset of the repo-wide ``V1_TRIGGERS``.

        Validates: Requirements 2.1
        """
        assert ALLOWED_TRIGGERS <= V1_TRIGGERS, (
            "allowed triggers must be valid v1 triggers"
        )
        for index, entry in enumerate(entries):
            trigger = entry.get("trigger")
            assert trigger in ALLOWED_TRIGGERS, (
                f"capture hook entry {index} trigger {trigger!r} "
                f"not in {sorted(ALLOWED_TRIGGERS)}"
            )

    def test_every_action_is_a_non_empty_command(self, entries: list[dict]) -> None:
        """Each entry uses a ``command`` action with a present, non-empty command.

        Validates: Requirements 2.1
        """
        for index, entry in enumerate(entries):
            action = entry.get("action")
            assert isinstance(action, dict), (
                f"capture hook entry {index} action must be an object"
            )
            assert action.get("type") == "command", (
                f"capture hook entry {index} action.type must be 'command'"
            )
            command = action.get("command")
            assert isinstance(command, str) and command.strip(), (
                f"capture hook entry {index} action.command must be non-empty"
            )

    def test_first_entry_is_stop_record_question(self, entries: list[dict]) -> None:
        """Entry 1 is the ``Stop`` trigger invoking ``log_qa_event.py record-question``.

        Validates: Requirements 2.1
        """
        first = entries[0]
        assert first.get("trigger") == "Stop", "entry 1 trigger must be 'Stop'"
        command = first["action"]["command"]
        assert "log_qa_event.py" in command, (
            "entry 1 command must reference log_qa_event.py"
        )
        assert "record-question" in command, (
            "entry 1 command must invoke record-question"
        )

    def test_second_entry_is_userpromptsubmit_record_answer(
        self, entries: list[dict]
    ) -> None:
        """Entry 2 is ``UserPromptSubmit`` invoking ``log_qa_event.py record-answer``.

        Validates: Requirements 2.1
        """
        second = entries[1]
        assert second.get("trigger") == "UserPromptSubmit", (
            "entry 2 trigger must be 'UserPromptSubmit'"
        )
        command = second["action"]["command"]
        assert "log_qa_event.py" in command, (
            "entry 2 command must reference log_qa_event.py"
        )
        assert "record-answer" in command, (
            "entry 2 command must invoke record-answer"
        )
