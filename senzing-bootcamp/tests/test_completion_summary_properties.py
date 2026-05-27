"""Property-based tests for completion summary session logging.

Feature: completion-summary
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from session_logger import (
    COMPLETION_EVENT_TYPES,
    CompletionLogEntry,
    append_completion_entry,
    build_completion_entry,
    serialize_completion_entry,
    truncate_field,
)
from generate_completion_summary import filter_secrets


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_VALID_ACTION_TYPES = [
    "file_create", "file_modify", "file_delete", "command_run", "mcp_tool_call",
]
_FILE_ACTION_TYPES = {"file_create", "file_modify", "file_delete"}
_VALID_ARTIFACT_TYPES = ["script", "config", "data", "report", "visualization"]


@st.composite
def st_question_data(draw) -> dict[str, str]:
    """Generate valid data dict for a question event."""
    text = draw(st.text(min_size=1, max_size=100))
    question_id = draw(st.text(min_size=1, max_size=8, alphabet="abcdef0123456789"))
    return {"text": text, "question_id": question_id}


@st.composite
def st_answer_data(draw) -> dict[str, str]:
    """Generate valid data dict for an answer event."""
    text = draw(st.text(min_size=1, max_size=100))
    question_id = draw(st.text(min_size=1, max_size=8, alphabet="abcdef0123456789"))
    return {"text": text, "question_id": question_id}


@st.composite
def st_action_data(draw) -> dict[str, str]:
    """Generate valid data dict for an action event."""
    action_type = draw(st.sampled_from(_VALID_ACTION_TYPES))
    description = draw(st.text(min_size=1, max_size=100))
    data = {"action_type": action_type, "description": description}
    if action_type in _FILE_ACTION_TYPES:
        file_path = draw(st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz/._"))
        data["file_path"] = file_path
    return data


@st.composite
def st_artifact_data(draw) -> dict[str, str]:
    """Generate valid data dict for an artifact event."""
    file_path = draw(st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz/._"))
    artifact_type = draw(st.sampled_from(_VALID_ARTIFACT_TYPES))
    description = draw(st.text(min_size=1, max_size=100))
    return {"file_path": file_path, "artifact_type": artifact_type, "description": description}


@st.composite
def st_completion_entry(draw) -> CompletionLogEntry:
    """Generate a valid CompletionLogEntry via build_completion_entry."""
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


def st_event_type() -> st.SearchStrategy[str]:
    """Draw from valid completion event types."""
    return st.sampled_from(sorted(COMPLETION_EVENT_TYPES))


def st_module_number() -> st.SearchStrategy[int]:
    """Draw an integer in 0–11."""
    return st.integers(min_value=0, max_value=11)


@st.composite
def st_completion_entry_inputs(draw) -> tuple[str, int, dict[str, str]]:
    """Composite strategy building valid inputs (event_type, module, data) for any event type."""
    event_type = draw(st_event_type())
    module = draw(st_module_number())

    if event_type == "question":
        data = draw(st_question_data())
    elif event_type == "answer":
        data = draw(st_answer_data())
    elif event_type == "action":
        data = draw(st_action_data())
    else:
        data = draw(st_artifact_data())

    return (event_type, module, data)


# ---------------------------------------------------------------------------
# Property 1: Entry serialization produces valid schema-compliant JSON
# Feature: completion-summary, Property 1: Entry serialization produces valid schema-compliant JSON
# ---------------------------------------------------------------------------


class TestEntrySerializationProperty:
    """Property 1: Entry serialization produces valid schema-compliant JSON.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7

    For any valid event type, module number (0–11), and well-formed data dictionary,
    build_completion_entry followed by serialize_completion_entry SHALL produce a JSON
    string that, when parsed, contains exactly the fields event_type, module, timestamp,
    and data, where event_type matches the input, module is an integer in 0–11, timestamp
    is a valid ISO 8601 UTC string, and data contains all required subfields for that
    event type.
    """

    @given(entry_inputs=st_completion_entry_inputs())
    @settings(max_examples=20)
    def test_serialization_produces_valid_schema_compliant_json(
        self, entry_inputs: tuple[str, int, dict[str, str]]
    ) -> None:
        """Serialized entry is valid JSON with exactly the required top-level keys."""
        from datetime import datetime

        event_type, module, data = entry_inputs

        entry = build_completion_entry(event_type, module, data)
        serialized = serialize_completion_entry(entry)

        # 1. Produces valid JSON
        parsed = json.loads(serialized)

        # 2. Has exactly the required keys
        assert set(parsed.keys()) == {"event_type", "module", "timestamp", "data"}

        # 3. event_type matches input
        assert parsed["event_type"] == event_type

        # 4. module is int in 0-11
        assert isinstance(parsed["module"], int)
        assert 0 <= parsed["module"] <= 11
        assert parsed["module"] == module

        # 5. timestamp is valid ISO 8601 UTC
        ts = parsed["timestamp"]
        parsed_ts = datetime.fromisoformat(ts)
        assert parsed_ts.tzinfo is not None

        # 6. data contains all required subfields for the event type
        parsed_data = parsed["data"]
        if event_type == "question":
            assert "text" in parsed_data
            assert "question_id" in parsed_data
        elif event_type == "answer":
            assert "text" in parsed_data
            assert "question_id" in parsed_data
        elif event_type == "action":
            assert "action_type" in parsed_data
            assert parsed_data["action_type"] in _VALID_ACTION_TYPES
            assert "description" in parsed_data
            if parsed_data["action_type"] in _FILE_ACTION_TYPES:
                assert "file_path" in parsed_data
        elif event_type == "artifact":
            assert "file_path" in parsed_data
            assert "artifact_type" in parsed_data
            assert parsed_data["artifact_type"] in _VALID_ARTIFACT_TYPES
            assert "description" in parsed_data


def st_invalid_event_type() -> st.SearchStrategy[str]:
    """Generate strings that are NOT valid completion event types."""
    return st.text(min_size=1, max_size=30).filter(
        lambda s: s not in COMPLETION_EVENT_TYPES
    )


def st_invalid_module_number() -> st.SearchStrategy[int]:
    """Generate integers outside the valid 0-11 range."""
    return st.one_of(
        st.integers(max_value=-1),
        st.integers(min_value=12),
    )


def st_valid_module_number() -> st.SearchStrategy[int]:
    """Generate valid module numbers (0-11)."""
    return st.integers(min_value=0, max_value=11)


# ---------------------------------------------------------------------------
# Property 2: Invalid entries are rejected
# Feature: completion-summary, Property 2: Invalid entries are rejected
# ---------------------------------------------------------------------------


class TestInvalidEntriesRejectedProperty:
    """Property 2: Invalid entries are rejected.

    For any event construction attempt where event_type is not in
    {question, answer, action, artifact}, or module is outside 0-11,
    or required data fields are missing for the given event type,
    build_completion_entry SHALL raise a ValueError and no entry
    SHALL be written to the log.

    **Validates: Requirements 6.7, 6.8**
    """

    @given(event_type=st_invalid_event_type(), module=st_valid_module_number())
    @settings(max_examples=20)
    def test_invalid_event_type_raises_value_error(
        self, event_type: str, module: int
    ) -> None:
        """Invalid event_type (not in valid set) raises ValueError."""
        try:
            build_completion_entry(event_type=event_type, module=module, data={})
            raise AssertionError(
                f"Expected ValueError for event_type={event_type!r} but none raised"
            )
        except ValueError:
            pass

    @given(module=st_invalid_module_number())
    @settings(max_examples=20)
    def test_invalid_module_raises_value_error(self, module: int) -> None:
        """Module outside 0-11 raises ValueError."""
        try:
            build_completion_entry(
                event_type="question",
                module=module,
                data={"text": "hello", "question_id": "abc123"},
            )
            raise AssertionError(
                f"Expected ValueError for module={module!r} but none raised"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_question_missing_text_raises_value_error(self, module: int) -> None:
        """Question event missing 'text' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="question",
                module=module,
                data={"question_id": "abc123"},
            )
            raise AssertionError("Expected ValueError for question missing 'text'")
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_question_missing_question_id_raises_value_error(
        self, module: int
    ) -> None:
        """Question event missing 'question_id' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="question",
                module=module,
                data={"text": "What is entity resolution?"},
            )
            raise AssertionError(
                "Expected ValueError for question missing 'question_id'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_answer_missing_text_raises_value_error(self, module: int) -> None:
        """Answer event missing 'text' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="answer",
                module=module,
                data={"question_id": "abc123"},
            )
            raise AssertionError("Expected ValueError for answer missing 'text'")
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_answer_missing_question_id_raises_value_error(
        self, module: int
    ) -> None:
        """Answer event missing 'question_id' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="answer",
                module=module,
                data={"text": "It deduplicates records."},
            )
            raise AssertionError(
                "Expected ValueError for answer missing 'question_id'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_action_missing_action_type_raises_value_error(
        self, module: int
    ) -> None:
        """Action event missing 'action_type' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="action",
                module=module,
                data={"description": "Created a file"},
            )
            raise AssertionError(
                "Expected ValueError for action missing 'action_type'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_action_missing_description_raises_value_error(
        self, module: int
    ) -> None:
        """Action event missing 'description' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="action",
                module=module,
                data={"action_type": "command_run"},
            )
            raise AssertionError(
                "Expected ValueError for action missing 'description'"
            )
        except ValueError:
            pass

    @given(
        module=st_valid_module_number(),
        action_type=st.sampled_from(["file_create", "file_modify", "file_delete"]),
    )
    @settings(max_examples=20)
    def test_action_file_type_missing_file_path_raises_value_error(
        self, module: int, action_type: str
    ) -> None:
        """Action event with file_* action_type missing 'file_path' raises ValueError."""
        try:
            build_completion_entry(
                event_type="action",
                module=module,
                data={"action_type": action_type, "description": "Did something"},
            )
            raise AssertionError(
                f"Expected ValueError for action_type={action_type!r} missing 'file_path'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_artifact_missing_file_path_raises_value_error(
        self, module: int
    ) -> None:
        """Artifact event missing 'file_path' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="artifact",
                module=module,
                data={"artifact_type": "script", "description": "A script"},
            )
            raise AssertionError(
                "Expected ValueError for artifact missing 'file_path'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_artifact_missing_artifact_type_raises_value_error(
        self, module: int
    ) -> None:
        """Artifact event missing 'artifact_type' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="artifact",
                module=module,
                data={"file_path": "/tmp/out.py", "description": "A script"},
            )
            raise AssertionError(
                "Expected ValueError for artifact missing 'artifact_type'"
            )
        except ValueError:
            pass

    @given(module=st_valid_module_number())
    @settings(max_examples=20)
    def test_artifact_missing_description_raises_value_error(
        self, module: int
    ) -> None:
        """Artifact event missing 'description' field raises ValueError."""
        try:
            build_completion_entry(
                event_type="artifact",
                module=module,
                data={"file_path": "/tmp/out.py", "artifact_type": "script"},
            )
            raise AssertionError(
                "Expected ValueError for artifact missing 'description'"
            )
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Property 4: Append-only JSONL integrity
# Feature: completion-summary, Property 4: Append-only JSONL integrity
# ---------------------------------------------------------------------------


class TestAppendOnlyJSONLIntegrityProperty:
    """Property 4: Append-only JSONL integrity.

    For any sequence of valid CompletionLogEntry objects appended to a log file,
    reading the file back SHALL yield exactly one JSON object per line, the number
    of lines SHALL equal the number of entries appended, and each line SHALL parse
    as valid JSON matching the original entry's serialization.

    **Validates: Requirements 1.6**
    """

    @given(entries=st.lists(st_completion_entry(), min_size=0, max_size=10))
    @settings(max_examples=20)
    def test_append_only_jsonl_integrity(self, entries: list[CompletionLogEntry]) -> None:
        """Appending N entries produces N valid JSON lines matching serialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_log.jsonl")

            # Append each entry one at a time
            for entry in entries:
                append_completion_entry(log_path, entry)

            if len(entries) == 0:
                # If no entries appended, file should not exist
                assert not os.path.exists(log_path), (
                    "File should not exist when no entries are appended"
                )
                return

            # File must exist after appending at least one entry
            assert os.path.exists(log_path), (
                "File should exist after appending entries"
            )

            # Read back all lines
            with open(log_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()

            # Number of lines equals number of entries appended
            assert len(lines) == len(entries), (
                f"Expected {len(entries)} lines, got {len(lines)}"
            )

            # Each line is valid JSON and matches the original serialization
            for i, (line, entry) in enumerate(zip(lines, entries)):
                # Each line ends with newline
                assert line.endswith("\n"), (
                    f"Line {i} does not end with newline"
                )

                # Strip newline for JSON parsing
                stripped = line.rstrip("\n")

                # Must be valid JSON
                parsed = json.loads(stripped)
                assert isinstance(parsed, dict), (
                    f"Line {i} did not parse as a JSON object"
                )

                # Must have the expected fields
                assert "event_type" in parsed, f"Line {i} missing 'event_type'"
                assert "module" in parsed, f"Line {i} missing 'module'"
                assert "timestamp" in parsed, f"Line {i} missing 'timestamp'"
                assert "data" in parsed, f"Line {i} missing 'data'"

                # Serialized content matches what serialize_completion_entry produces
                expected_json = serialize_completion_entry(entry)
                assert stripped == expected_json, (
                    f"Line {i} content mismatch:\n"
                    f"  got:      {stripped}\n"
                    f"  expected: {expected_json}"
                )


# ---------------------------------------------------------------------------
# Property 3: Truncation preserves prefix and enforces limit
# Feature: completion-summary, Property 3: Truncation preserves prefix and enforces limit
# ---------------------------------------------------------------------------


class TestTruncationProperty:
    """Property 3: Truncation preserves prefix and enforces limit.

    For any string s and maximum length n (where n > 0), truncate_field(s, n)
    SHALL return a string whose length is min(len(s), n) and which equals s[:n].

    **Validates: Requirements 1.9**
    """

    @given(
        s=st.text(),
        n=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=20)
    def test_truncation_length_equals_min_of_input_and_limit(self, s: str, n: int) -> None:
        """truncate_field returns a string whose length is min(len(s), n)."""
        result = truncate_field(s, n)
        assert len(result) == min(len(s), n)

    @given(
        s=st.text(),
        n=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=20)
    def test_truncation_equals_prefix_slice(self, s: str, n: int) -> None:
        """truncate_field(s, n) equals s[:n]."""
        result = truncate_field(s, n)
        assert result == s[:n]

    @given(
        s=st.text(min_size=0, max_size=100),
        n=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=20)
    def test_short_strings_unchanged(self, s: str, n: int) -> None:
        """If len(s) <= n, truncate_field returns s unchanged (no modification)."""
        if len(s) <= n:
            result = truncate_field(s, n)
            assert result == s


# ---------------------------------------------------------------------------
# Property 5: Narrative sections are ordered by module number ascending
# Feature: completion-summary, Property 5: Narrative sections ordered by module number ascending
# ---------------------------------------------------------------------------


class TestNarrativeSectionsOrderedProperty:
    """Property 5: Narrative sections are ordered by module number ascending.

    For any set of session log entries spanning multiple modules, build_narrative
    SHALL produce a CompletionNarrative whose sections list is sorted by
    module_number in strictly ascending order.

    **Validates: Requirements 4.1**
    """

    @given(entries=st.lists(st_completion_entry(), min_size=2, max_size=15))
    @settings(max_examples=20)
    def test_narrative_sections_ordered_by_module_number(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """build_narrative produces sections sorted by module_number ascending."""
        from generate_completion_summary import build_narrative

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal progress file
            progress_path = os.path.join(tmpdir, "progress.json")
            Path(progress_path).write_text(
                json.dumps({"modules_completed": [], "track": "core_bootcamp"}),
                encoding="utf-8",
            )

            # Create minimal preferences file
            preferences_path = os.path.join(tmpdir, "preferences.yaml")
            Path(preferences_path).write_text(
                "name: TestUser\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            narrative = build_narrative(entries, progress_path, preferences_path)

            # Sections must be sorted by module_number in strictly ascending order
            module_numbers = [s.module_number for s in narrative.sections]
            assert module_numbers == sorted(module_numbers), (
                f"Sections not in ascending module_number order: {module_numbers}"
            )

            # Strictly ascending means no duplicates
            assert len(module_numbers) == len(set(module_numbers)), (
                f"Duplicate module_numbers found in sections: {module_numbers}"
            )


# ---------------------------------------------------------------------------
# Property 6: Every module with events gets all four subsections
# Feature: completion-summary, Property 6: Every module with events gets all four subsections
# ---------------------------------------------------------------------------

from generate_completion_summary import build_narrative, NarrativeSection


class TestModuleSubsectionsProperty:
    """Property 6: Every module with events gets all four subsections.

    For any set of session log entries where at least one entry exists for a given
    module, the corresponding NarrativeSection SHALL contain non-null lists for
    questions, actions, and artifacts (possibly empty lists, but present), ensuring
    all four content categories are represented.

    **Validates: Requirements 4.2**
    """

    @given(entries=st.lists(st_completion_entry(), min_size=1, max_size=15))
    @settings(max_examples=20)
    def test_every_module_with_events_has_all_subsection_lists(
        self, entries: list[CompletionLogEntry]
    ) -> None:
        """Each module with entries has non-null questions, actions, and artifacts lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal progress file
            progress_path = os.path.join(tmpdir, "progress.json")
            Path(progress_path).write_text(
                json.dumps({"modules_completed": [], "track": "core_bootcamp"}),
                encoding="utf-8",
            )

            # Create minimal preferences file
            preferences_path = os.path.join(tmpdir, "preferences.yaml")
            Path(preferences_path).write_text(
                "name: Tester\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            # Build narrative from entries
            narrative = build_narrative(entries, progress_path, preferences_path)

            # Determine which modules have entries
            modules_with_entries: set[int] = {e.module for e in entries}

            # For each module that has entries, find the corresponding section
            for mod_num in modules_with_entries:
                matching_sections = [
                    s for s in narrative.sections if s.module_number == mod_num
                ]
                assert len(matching_sections) == 1, (
                    f"Expected exactly 1 section for module {mod_num}, "
                    f"got {len(matching_sections)}"
                )
                section = matching_sections[0]

                # Assert questions is a list (not None)
                assert section.questions is not None, (
                    f"Module {mod_num}: questions should not be None"
                )
                assert isinstance(section.questions, list), (
                    f"Module {mod_num}: questions should be a list, "
                    f"got {type(section.questions)}"
                )

                # Assert actions is a list (not None)
                assert section.actions is not None, (
                    f"Module {mod_num}: actions should not be None"
                )
                assert isinstance(section.actions, list), (
                    f"Module {mod_num}: actions should be a list, "
                    f"got {type(section.actions)}"
                )

                # Assert artifacts is a list (not None)
                assert section.artifacts is not None, (
                    f"Module {mod_num}: artifacts should not be None"
                )
                assert isinstance(section.artifacts, list), (
                    f"Module {mod_num}: artifacts should be a list, "
                    f"got {type(section.artifacts)}"
                )


# ---------------------------------------------------------------------------
# Property 8: Narrative metadata completeness
# Feature: completion-summary, Property 8: Narrative metadata completeness
# ---------------------------------------------------------------------------

from generate_completion_summary import build_narrative, render_markdown


@st.composite
def st_bootcamper_name(draw) -> str:
    """Generate a non-empty bootcamper name.

    Names are stripped because the YAML parser strips values on read.
    We filter out names that become empty after stripping.
    """
    name = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("L", "Nd", "Zs")),
    ))
    stripped = name.strip()
    assume(len(stripped) > 0)
    return stripped


@st.composite
def st_track_name(draw) -> str:
    """Generate a valid track name."""
    return draw(st.sampled_from([
        "core_bootcamp", "advanced_bootcamp", "data_engineering", "full_stack",
    ]))


@st.composite
def st_modules_completed_list(draw) -> list[int]:
    """Generate a non-empty list of completed module numbers (1-11)."""
    modules = draw(st.lists(
        st.integers(min_value=1, max_value=11),
        min_size=1,
        max_size=11,
        unique=True,
    ))
    return sorted(modules)


class TestNarrativeMetadataCompletenessProperty:
    """Property 8: Narrative metadata completeness.

    For any valid set of inputs (session log entries, progress file, preferences file),
    the rendered markdown SHALL contain the bootcamper name, start date, completion date,
    duration, track, modules completed count, and artifacts produced count.

    **Validates: Requirements 4.4, 4.5**
    """

    @given(
        entries=st.lists(st_completion_entry(), min_size=1, max_size=10),
        bootcamper_name=st_bootcamper_name(),
        track=st_track_name(),
        modules_completed=st_modules_completed_list(),
    )
    @settings(max_examples=20)
    def test_rendered_markdown_contains_all_metadata(
        self,
        entries: list[CompletionLogEntry],
        bootcamper_name: str,
        track: str,
        modules_completed: list[int],
    ) -> None:
        """Rendered markdown contains bootcamper name, dates, duration, track, and counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create progress file
            progress_path = os.path.join(tmpdir, "bootcamp_progress.json")
            progress_data = {
                "modules_completed": modules_completed,
                "track": track,
                "current_module": modules_completed[-1],
            }
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f)

            # Create preferences file (simple YAML format)
            preferences_path = os.path.join(tmpdir, "bootcamp_preferences.yaml")
            with open(preferences_path, "w", encoding="utf-8") as f:
                f.write(f"name: {bootcamper_name}\n")
                f.write(f"track: {track}\n")

            # Build narrative and render markdown
            narrative = build_narrative(entries, progress_path, preferences_path)
            markdown = render_markdown(narrative)

            # Assert bootcamper name is present
            assert bootcamper_name in markdown, (
                f"Bootcamper name {bootcamper_name!r} not found in rendered markdown"
            )

            # Assert "Started:" with a date is present
            assert "**Started:**" in markdown, (
                "'**Started:**' not found in rendered markdown"
            )

            # Assert "Completed:" with a date is present
            assert "**Completed:**" in markdown, (
                "'**Completed:**' not found in rendered markdown"
            )

            # Assert "Duration:" is present
            assert "**Duration:**" in markdown, (
                "'**Duration:**' not found in rendered markdown"
            )

            # Assert "Track:" is present
            assert "**Track:**" in markdown, (
                "'**Track:**' not found in rendered markdown"
            )

            # Assert "Modules Completed" is present in summary statistics
            assert "Modules Completed" in markdown, (
                "'Modules Completed' not found in rendered markdown"
            )

            # Assert "Artifacts Produced" is present in summary statistics
            assert "Artifacts Produced" in markdown, (
                "'Artifacts Produced' not found in rendered markdown"
            )


# ---------------------------------------------------------------------------
# Property 10: Narrative output respects 500 KB size limit
# Feature: completion-summary, Property 10: Narrative output respects 500 KB size limit
# ---------------------------------------------------------------------------


class TestNarrativeSizeLimitProperty:
    """Property 10: Narrative output respects 500 KB size limit.

    For any set of session log entries (regardless of count or content size),
    write_narrative SHALL produce an output file whose size does not exceed
    512,000 bytes.

    **Validates: Requirements 4.10**
    """

    @given(
        content=st.text(
            min_size=1,
            max_size=600000,
            alphabet=st.characters(categories=("L", "N", "P", "Z")),
        ).map(
            lambda text: "# Senzing Bootcamp Completion Summary\n\n"
            + "\n".join(
                f"## Module {i}: Section {i}\n\n{text[i * 1000:(i + 1) * 1000]}\n"
                for i in range(min(12, max(1, len(text) // 1000)))
            )
            + "\n"
            + text
        ),
    )
    @settings(max_examples=20)
    def test_write_narrative_respects_size_limit(self, content: str) -> None:
        """write_narrative output file never exceeds 512000 bytes."""
        from generate_completion_summary import write_narrative

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "completion_summary.md")
            write_narrative(output_path, content, max_size_bytes=512000)

            file_size = os.path.getsize(output_path)
            assert file_size <= 512000, (
                f"Output file size {file_size} bytes exceeds 512000 byte limit"
            )


# ---------------------------------------------------------------------------
# Property 7: Question-answer pairing via question_id
# Feature: completion-summary, Property 7: Question-answer pairing via question_id
# ---------------------------------------------------------------------------

from generate_completion_summary import build_narrative


@st.composite
def st_question_answer_entries(draw):
    """Generate question entries with known question_ids and some matching answers.

    Returns a tuple of (entries, questions_with_answers, questions_without_answers)
    where:
      - entries: list of CompletionLogEntry objects (questions + some answers)
      - questions_with_answers: dict mapping question_id -> (question_text, answer_text)
      - questions_without_answers: dict mapping question_id -> question_text
    """
    module = draw(st.integers(min_value=1, max_value=11))
    num_questions = draw(st.integers(min_value=1, max_value=5))

    # Generate unique question_ids
    question_ids = [
        draw(st.text(min_size=4, max_size=8, alphabet="abcdef0123456789"))
        for _ in range(num_questions)
    ]
    # Ensure uniqueness by deduplicating
    question_ids = list(dict.fromkeys(question_ids))
    if not question_ids:
        question_ids = ["abcd1234"]

    # Generate question texts
    question_texts = {
        qid: draw(st.text(min_size=1, max_size=80, alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            max_codepoint=127,
        )))
        for qid in question_ids
    }

    # Decide which questions get answers (at least one without answer if possible)
    if len(question_ids) > 1:
        num_answered = draw(st.integers(min_value=0, max_value=len(question_ids) - 1))
    else:
        num_answered = draw(st.integers(min_value=0, max_value=1))

    answered_ids = question_ids[:num_answered]
    unanswered_ids = question_ids[num_answered:]

    # Generate answer texts for answered questions
    answer_texts = {
        qid: draw(st.text(min_size=1, max_size=80, alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            max_codepoint=127,
        )))
        for qid in answered_ids
    }

    # Build entries
    entries: list[CompletionLogEntry] = []
    for qid in question_ids:
        entries.append(build_completion_entry(
            event_type="question",
            module=module,
            data={"text": question_texts[qid], "question_id": qid},
        ))

    for qid in answered_ids:
        entries.append(build_completion_entry(
            event_type="answer",
            module=module,
            data={"text": answer_texts[qid], "question_id": qid},
        ))

    questions_with_answers = {qid: (question_texts[qid], answer_texts[qid]) for qid in answered_ids}
    questions_without_answers = {qid: question_texts[qid] for qid in unanswered_ids}

    return (entries, questions_with_answers, questions_without_answers, module)


class TestQuestionAnswerPairingProperty:
    """Property 7: Question-answer pairing via question_id.

    For any set of question and answer entries sharing the same question_id,
    build_narrative SHALL pair them together in the narrative. For any question
    entry whose question_id has no corresponding answer entry, the narrative
    SHALL include that question with a placeholder indicating no answer was
    recorded (None in the tuple).

    **Validates: Requirements 4.3**
    """

    @given(data=st_question_answer_entries())
    @settings(max_examples=20)
    def test_questions_with_answers_are_paired(self, data) -> None:
        """Questions with matching answer entries are paired as (q_text, a_text)."""
        entries, questions_with_answers, questions_without_answers, module = data

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal progress file
            progress_path = os.path.join(tmpdir, "progress.json")
            Path(progress_path).write_text(
                json.dumps({"modules_completed": [module], "track": "core_bootcamp"}),
                encoding="utf-8",
            )

            # Create minimal preferences file
            preferences_path = os.path.join(tmpdir, "preferences.yaml")
            Path(preferences_path).write_text(
                "name: Tester\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            narrative = build_narrative(entries, progress_path, preferences_path)

            # Find the section for our module
            target_section = None
            for section in narrative.sections:
                if section.module_number == module:
                    target_section = section
                    break

            assert target_section is not None, (
                f"Expected a section for module {module}"
            )

            # For questions with matching answers: assert the pair exists as (q_text, a_text)
            for qid, (q_text, a_text) in questions_with_answers.items():
                assert (q_text, a_text) in target_section.questions, (
                    f"Expected paired (q_text, a_text) for question_id={qid!r} "
                    f"but got questions={target_section.questions}"
                )

    @given(data=st_question_answer_entries())
    @settings(max_examples=20)
    def test_questions_without_answers_have_none_placeholder(self, data) -> None:
        """Questions without matching answer entries appear as (q_text, None)."""
        entries, questions_with_answers, questions_without_answers, module = data

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal progress file
            progress_path = os.path.join(tmpdir, "progress.json")
            Path(progress_path).write_text(
                json.dumps({"modules_completed": [module], "track": "core_bootcamp"}),
                encoding="utf-8",
            )

            # Create minimal preferences file
            preferences_path = os.path.join(tmpdir, "preferences.yaml")
            Path(preferences_path).write_text(
                "name: Tester\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            narrative = build_narrative(entries, progress_path, preferences_path)

            # Find the section for our module
            target_section = None
            for section in narrative.sections:
                if section.module_number == module:
                    target_section = section
                    break

            assert target_section is not None, (
                f"Expected a section for module {module}"
            )

            # For questions without matching answers: assert the pair exists as (q_text, None)
            for qid, q_text in questions_without_answers.items():
                assert (q_text, None) in target_section.questions, (
                    f"Expected (q_text, None) for unanswered question_id={qid!r} "
                    f"but got questions={target_section.questions}"
                )


# ---------------------------------------------------------------------------
# Strategies for Property 9: Secret filtering
# ---------------------------------------------------------------------------

_SENSITIVE_TERMS = ["secret", "password", "token", "key", "credential", "connection_string"]

_SAFE_WORD_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@st.composite
def st_sensitive_key(draw) -> str:
    """Generate a key containing one of the sensitive terms.

    Produces keys like 'db_password', 'api_token', 'my_secret_value'.
    """
    term = draw(st.sampled_from(_SENSITIVE_TERMS))
    prefix = draw(st.text(alphabet=_SAFE_WORD_ALPHABET, min_size=0, max_size=5))
    suffix = draw(st.text(alphabet=_SAFE_WORD_ALPHABET, min_size=0, max_size=5))
    separator = draw(st.sampled_from(["_", ""]))
    if prefix:
        key = prefix + separator + term
    else:
        key = term
    if suffix:
        key = key + separator + suffix
    return key


@st.composite
def st_sensitive_text(draw) -> tuple[str, str]:
    """Generate text with an embedded sensitive key=value pattern.

    Returns (full_text, sensitive_pattern) so the test can verify removal.
    """
    key = draw(st_sensitive_key())
    value = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
        min_size=1,
        max_size=20,
    ))
    pattern = f"{key}={value}"
    # Surround with safe text (no sensitive patterns)
    before = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz ",
        min_size=0,
        max_size=30,
    ))
    after = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz ",
        min_size=0,
        max_size=30,
    ))
    full_text = f"{before} {pattern} {after}"
    return (full_text, pattern)


@st.composite
def st_safe_text(draw) -> str:
    """Generate text that does NOT contain sensitive key=value patterns.

    Uses words that don't contain any sensitive terms and avoids '=' adjacent
    to words containing sensitive terms.
    """
    # Generate words that cannot contain sensitive terms
    words = draw(st.lists(
        st.text(alphabet="abcdfghijlmnquvwxz", min_size=1, max_size=8),
        min_size=1,
        max_size=10,
    ))
    # Join with spaces — no '=' signs, so no key=value patterns possible
    return " ".join(words)


# ---------------------------------------------------------------------------
# Property 9: Secret filtering removes sensitive key-value patterns
# Feature: completion-summary, Property 9: Secret filtering removes sensitive key-value patterns
# ---------------------------------------------------------------------------


class TestSecretFilteringProperty:
    """Property 9: Secret filtering removes sensitive key-value patterns.

    For any text containing a pattern matching key=value where key contains one of
    {secret, password, token, key, credential, connection_string}, filter_secrets
    SHALL return text with that pattern removed. For any text not containing such
    patterns, filter_secrets SHALL return the text unchanged.

    **Validates: Requirements 4.8**
    """

    @given(data=st_sensitive_text())
    @settings(max_examples=20)
    def test_sensitive_pattern_is_removed(self, data: tuple[str, str]) -> None:
        """Text containing a sensitive key=value pattern has that pattern removed."""
        full_text, pattern = data
        result = filter_secrets(full_text)
        assert pattern not in result, (
            f"Sensitive pattern {pattern!r} was not removed from result: {result!r}"
        )

    @given(text=st_safe_text())
    @settings(max_examples=20)
    def test_safe_text_unchanged(self, text: str) -> None:
        """Text without sensitive key=value patterns is returned unchanged."""
        result = filter_secrets(text)
        assert result == text, (
            f"Safe text was modified:\n  input:  {text!r}\n  output: {result!r}"
        )
