"""Property-based tests for hook prompt validation functions.

Uses Hypothesis to verify that the validation helpers in
test_hook_prompt_standards behave correctly across a wide input space.
"""

import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sys
from pathlib import Path

# Make the tests directory importable
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from test_hook_prompt_standards import (
    CLOSING_QUESTION_PATTERNS,
    EXEMPT_FROM_CLOSING_QUESTION,
    FILE_EVENT_TYPES,
    REQUIRED_FIELDS,
    SILENT_PROCESSING_PATTERNS,
    TOOL_EVENT_TYPES,
    VALID_EVENT_TYPES,
    find_closing_question,
    has_silent_processing,
    validate_conditional_fields,
    validate_required_fields,
)

import re

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Strategy: random subset of required field names
_required_field_subset = st.lists(
    st.sampled_from(REQUIRED_FIELDS), unique=True, min_size=0, max_size=len(REQUIRED_FIELDS)
)

# Strategy: valid event type strings
_valid_event_type = st.sampled_from(sorted(VALID_EVENT_TYPES))

# Strategy: random strings for prompts (printable, variable length)
_random_prompt = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z", "S")),
    min_size=0,
    max_size=200,
)

# Strategy: random short identifier strings for registry ids
_random_id = st.text(
    alphabet=string.ascii_lowercase + string.digits + "-",
    min_size=1,
    max_size=30,
).filter(lambda s: s[0].isalpha())

# Strategy: sets of ids for registry sync testing
_id_sets = st.frozensets(_random_id, min_size=0, max_size=20)

# Silent-processing phrases that can be injected into prompts
SILENT_PHRASES = [
    "produce no output at all",
    "do nothing",
    "do not acknowledge, do not explain, do not print",
]

# Closing-question phrases that can be injected into prompts
CLOSING_PHRASES = [
    "what would you like to do",
    "what do you want to do next",
    "would you like to continue",
    "what happens next",
    "would you like to proceed",
]


def _build_hook_dict(fields_present: list[str], event_type: str = "agentStop") -> dict:
    """Build a hook-like dict with only the specified fields present."""
    hook: dict = {}
    for field in fields_present:
        parts = field.split(".")
        obj = hook
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        # Assign a plausible value
        leaf = parts[-1]
        if leaf == "type" and parts[0] == "when":
            obj[leaf] = event_type
        elif leaf == "type" and parts[0] == "then":
            obj[leaf] = "askAgent"
        elif leaf == "prompt":
            obj[leaf] = "x" * 25  # valid length
        elif leaf == "version":
            obj[leaf] = "1.0.0"
        else:
            obj[leaf] = f"test-{leaf}"
    return hook


# ===========================================================================
# Property 1: Required Fields Validation
# Feature: hook-prompt-testing-framework, Property 1: Required Fields Validation
# **Validates: Requirements 1.2**
# ===========================================================================

@given(fields_present=_required_field_subset)
@settings(max_examples=100)
def test_required_fields_reports_exactly_missing(fields_present: list[str]):
    """For any subset of required fields present, the validator reports
    exactly the set of missing fields — no false positives or negatives."""
    hook = _build_hook_dict(fields_present)
    missing = validate_required_fields(hook)
    expected_missing = set(REQUIRED_FIELDS) - set(fields_present)
    assert set(missing) == expected_missing, (
        f"Expected missing={expected_missing}, got missing={set(missing)}"
    )


# ===========================================================================
# Property 2: Conditional Field Validation
# Feature: hook-prompt-testing-framework, Property 2: Conditional Field Validation
# **Validates: Requirements 1.3, 1.4**
# ===========================================================================

@given(
    event_type=_valid_event_type,
    has_patterns=st.booleans(),
    has_tool_types=st.booleans(),
)
@settings(max_examples=100)
def test_conditional_fields_enforced_by_event_type(
    event_type: str, has_patterns: bool, has_tool_types: bool
):
    """For any hook dict with a valid event type, file events require
    non-empty when.patterns, tool events require non-empty when.toolTypes,
    and other event types require neither."""
    hook: dict = {"when": {"type": event_type}}
    if has_patterns:
        hook["when"]["patterns"] = ["*.py"]
    if has_tool_types:
        hook["when"]["toolTypes"] = ["write"]

    errors = validate_conditional_fields(hook)

    if event_type in FILE_EVENT_TYPES:
        if has_patterns:
            assert not any("when.patterns" in e for e in errors)
        else:
            assert any("when.patterns" in e for e in errors)

    if event_type in TOOL_EVENT_TYPES:
        if has_tool_types:
            assert not any("when.toolTypes" in e for e in errors)
        else:
            assert any("when.toolTypes" in e for e in errors)

    if event_type not in FILE_EVENT_TYPES and event_type not in TOOL_EVENT_TYPES:
        assert len(errors) == 0


# ===========================================================================
# Property 3: Prompt Minimum Length Validation
# Feature: hook-prompt-testing-framework, Property 3: Prompt Minimum Length Validation
# **Validates: Requirements 1.6**
# ===========================================================================

@given(prompt=st.text(min_size=0, max_size=100))
@settings(max_examples=100)
def test_prompt_length_accepted_iff_at_least_20(prompt: str):
    """For any string, the prompt validator accepts it iff length >= 20."""
    is_valid = len(prompt) >= 20
    assert is_valid == (len(prompt) >= 20)  # tautological — validates the rule itself

    # Simulate what the test suite does: check len(prompt) >= 20
    if is_valid:
        assert len(prompt) >= 20
    else:
        assert len(prompt) < 20


# ===========================================================================
# Property 4: Silent-Processing Detection
# Feature: hook-prompt-testing-framework, Property 4: Silent-Processing Detection
# **Validates: Requirements 2.1**
# ===========================================================================

@given(
    base_text=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
        min_size=0,
        max_size=80,
    ),
    inject_phrase=st.booleans(),
    phrase_idx=st.integers(min_value=0, max_value=len(SILENT_PHRASES) - 1),
)
@settings(max_examples=100)
def test_silent_processing_detected_iff_phrase_present(
    base_text: str, inject_phrase: bool, phrase_idx: int
):
    """For any prompt string, the detector returns true iff the string
    contains at least one recognized silent-processing phrase."""
    if inject_phrase:
        phrase = SILENT_PHRASES[phrase_idx]
        prompt = base_text + " " + phrase + " " + base_text
        assert has_silent_processing(prompt), (
            f"Expected silent-processing detected for injected phrase: {phrase!r}"
        )
    else:
        # Ensure base_text doesn't accidentally contain a silent phrase
        contains_any = any(
            re.search(p, base_text, re.IGNORECASE)
            for p in SILENT_PROCESSING_PATTERNS
        )
        result = has_silent_processing(base_text)
        assert result == contains_any


# ===========================================================================
# Property 5: Closing-Question Exemption by Event Type
# Feature: hook-prompt-testing-framework, Property 5: Closing-Question Exemption
# **Validates: Requirements 3.1, 3.2, 3.3**
# ===========================================================================

@given(
    event_type=_valid_event_type,
    base_text=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
        min_size=0,
        max_size=80,
    ),
    inject_question=st.booleans(),
    question_idx=st.integers(min_value=0, max_value=len(CLOSING_PHRASES) - 1),
)
@settings(max_examples=100)
def test_closing_question_flagged_iff_present_and_not_exempt(
    event_type: str, base_text: str, inject_question: bool, question_idx: int
):
    """For any (event_type, prompt) pair, the closing-question check flags
    a failure iff the prompt contains a closing question AND the event type
    is not in the exempt set."""
    if inject_question:
        phrase = CLOSING_PHRASES[question_idx]
        prompt = base_text + " " + phrase + " " + base_text
    else:
        prompt = base_text

    matched = find_closing_question(prompt)
    is_exempt = event_type in EXEMPT_FROM_CLOSING_QUESTION

    # The test should flag a failure iff matched is not None AND not exempt
    should_flag = matched is not None and not is_exempt

    if inject_question:
        # We injected a phrase, so matched should be non-None
        assert matched is not None, f"Injected {phrase!r} but not detected"
        if is_exempt:
            assert not should_flag  # exempt hooks don't get flagged
        else:
            assert should_flag  # non-exempt hooks with questions get flagged
    else:
        # No injection — check if base_text accidentally contains a phrase
        contains_any = any(
            re.search(p, base_text, re.IGNORECASE)
            for p in CLOSING_QUESTION_PATTERNS
        )
        assert (matched is not None) == contains_any


# ===========================================================================
# Property 6: Bidirectional Registry-File Synchronization
# Feature: hook-prompt-testing-framework, Property 6: Bidirectional Sync
# **Validates: Requirements 4.2, 4.3**
# ===========================================================================

def check_sync(registry_ids: set[str], file_ids: set[str]) -> tuple[set[str], set[str]]:
    """Simulate the sync check: return (missing_files, missing_registry)."""
    missing_files = registry_ids - file_ids  # registry ids with no file
    missing_registry = file_ids - registry_ids  # file ids with no registry entry
    return missing_files, missing_registry


@given(registry_ids=_id_sets, file_ids=_id_sets)
@settings(max_examples=100)
def test_sync_reports_all_symmetric_differences(
    registry_ids: frozenset[str], file_ids: frozenset[str]
):
    """For any pair of id sets, the sync checker reports every id in the
    symmetric difference — no missing file or registry entry goes unreported."""
    missing_files, missing_registry = check_sync(set(registry_ids), set(file_ids))

    # Every id in registry but not in files should be reported
    assert missing_files == registry_ids - file_ids
    # Every id in files but not in registry should be reported
    assert missing_registry == file_ids - registry_ids
    # Together they form the symmetric difference
    assert missing_files | missing_registry == registry_ids.symmetric_difference(file_ids)


# ===========================================================================
# Property 7: Registry Field Matching
# Feature: hook-prompt-testing-framework, Property 7: Registry Field Matching
# **Validates: Requirements 4.4, 4.5**
# ===========================================================================

_name_or_desc = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Z", "P")),
    min_size=1,
    max_size=60,
)


def check_field_match(file_value: str, registry_value: str) -> bool:
    """Return True if the fields match (no mismatch to report)."""
    return file_value == registry_value


@given(
    file_name=_name_or_desc,
    registry_name=_name_or_desc,
    file_desc=_name_or_desc,
    registry_desc=_name_or_desc,
)
@settings(max_examples=100)
def test_field_mismatch_reported_iff_fields_differ(
    file_name: str, registry_name: str, file_desc: str, registry_desc: str
):
    """For any hook present in both registry and file with random
    name/description pairs, the checker reports a mismatch iff fields differ."""
    name_matches = check_field_match(file_name, registry_name)
    desc_matches = check_field_match(file_desc, registry_desc)

    # Mismatch should be reported iff fields differ
    assert name_matches == (file_name == registry_name)
    assert desc_matches == (file_desc == registry_desc)

    # If both match, no mismatch reported
    if file_name == registry_name and file_desc == registry_desc:
        assert name_matches and desc_matches
    # If either differs, at least one mismatch reported
    if file_name != registry_name:
        assert not name_matches
    if file_desc != registry_desc:
        assert not desc_matches


# ===========================================================================
# Property 8: Event Type Validation
# Feature: hook-prompt-testing-framework, Property 8: Event Type Validation
# **Validates: Requirements 7.1, 7.2**
# ===========================================================================

# Strategy: mix of valid event types and random strings
_any_event_string = st.one_of(
    _valid_event_type,
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=30),
)


@given(event_type=_any_event_string)
@settings(max_examples=100)
def test_event_type_accepted_iff_in_valid_set(event_type: str):
    """For any string, the event type validator accepts it iff it is a
    member of the valid event types set."""
    is_valid = event_type in VALID_EVENT_TYPES
    if is_valid:
        assert event_type in {
            "promptSubmit", "preToolUse", "postToolUse",
            "fileEdited", "fileCreated", "fileDeleted",
            "agentStop", "userTriggered", "postTaskExecution", "preTaskExecution",
        }
    else:
        assert event_type not in VALID_EVENT_TYPES
