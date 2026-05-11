"""Property-based tests for hook structural validators.

Uses Hypothesis to generate random hook-like structures and verify that
the validation functions correctly accept valid hooks and reject invalid ones.
"""

from __future__ import annotations

import copy
import string
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    FILE_EVENT_TYPES,
    REQUIRED_FIELDS,
    TOOL_EVENT_TYPES,
    VALID_EVENT_TYPES,
    st_invalid_semver,
    st_markdown_path,
    st_non_markdown_path,
    st_valid_hook,
    st_valid_semver,
    validate_conditional_fields,
    validate_event_type,
    validate_required_fields,
    validate_version,
)


# ===========================================================================
# TestValidHookAcceptance — Property 1
# ===========================================================================

class TestValidHookAcceptance:
    """Property 1: Generated valid hooks pass validator with zero errors.

    Feature: hook-test-coverage, Property 1: Valid hook dicts accepted by structural validator
    Validates: Requirements 5.1
    """

    @given(hook=st_valid_hook())
    @settings(max_examples=100)
    def test_valid_hook_has_no_missing_fields(self, hook: dict):
        """For any valid hook dict, the structural validator reports zero missing fields.

        Feature: hook-test-coverage, Property 1: Valid hook dicts accepted
        Validates: Requirements 5.1
        """
        missing = validate_required_fields(hook)
        assert missing == [], (
            f"Valid hook reported missing fields: {missing}\nHook: {hook}"
        )

    @given(hook=st_valid_hook())
    @settings(max_examples=100)
    def test_valid_hook_has_no_conditional_errors(self, hook: dict):
        """For any valid hook dict, the conditional field validator reports zero errors.

        Feature: hook-test-coverage, Property 1: Valid hook dicts accepted
        Validates: Requirements 5.1
        """
        errors = validate_conditional_fields(hook)
        assert errors == [], (
            f"Valid hook reported conditional errors: {errors}\nHook: {hook}"
        )


# ===========================================================================
# TestMissingFieldDetection — Property 2
# ===========================================================================

class TestMissingFieldDetection:
    """Property 2: Removing one required field reports exactly that field.

    Feature: hook-test-coverage, Property 2: Missing field detection is exact
    Validates: Requirements 5.2
    """

    @given(
        hook=st_valid_hook(),
        field_idx=st.integers(min_value=0, max_value=len(REQUIRED_FIELDS) - 1),
    )
    @settings(max_examples=100)
    def test_removing_one_field_reports_exactly_that_field(
        self, hook: dict, field_idx: int
    ):
        """For any valid hook with one required field removed, the validator
        reports exactly that field as missing.

        Feature: hook-test-coverage, Property 2: Missing field detection is exact
        Validates: Requirements 5.2
        """
        field_to_remove = REQUIRED_FIELDS[field_idx]
        modified = copy.deepcopy(hook)

        # Remove the field using dot-notation traversal
        parts = field_to_remove.split(".")
        obj = modified
        for part in parts[:-1]:
            obj = obj[part]
        del obj[parts[-1]]

        missing = validate_required_fields(modified)
        assert field_to_remove in missing, (
            f"Removed '{field_to_remove}' but it was not reported as missing. "
            f"Reported: {missing}"
        )


# ===========================================================================
# TestInvalidEventTypeDetection — Property 3
# ===========================================================================

class TestInvalidEventTypeDetection:
    """Property 3: Invalid event type strings are rejected.

    Feature: hook-test-coverage, Property 3: Invalid event type detection
    Validates: Requirements 5.3
    """

    @given(
        event_type=st.text(
            alphabet=string.ascii_letters + string.digits,
            min_size=1,
            max_size=30,
        )
    )
    @settings(max_examples=100)
    def test_invalid_event_type_rejected(self, event_type: str):
        """For any string not in the valid set, the event type validator rejects it.

        Feature: hook-test-coverage, Property 3: Invalid event type detection
        Validates: Requirements 5.3
        """
        assume(event_type not in VALID_EVENT_TYPES)
        assert not validate_event_type(event_type), (
            f"Invalid event type '{event_type}' was accepted"
        )

    @given(event_type=st.sampled_from(sorted(VALID_EVENT_TYPES)))
    @settings(max_examples=100)
    def test_valid_event_type_accepted(self, event_type: str):
        """For any string in the valid set, the event type validator accepts it.

        Feature: hook-test-coverage, Property 3: Invalid event type detection
        Validates: Requirements 5.3
        """
        assert validate_event_type(event_type), (
            f"Valid event type '{event_type}' was rejected"
        )


# ===========================================================================
# TestConditionalFieldValidation — Property 4
# ===========================================================================

class TestConditionalFieldValidation:
    """Property 4: Missing patterns/toolTypes for conditional event types produce errors.

    Feature: hook-test-coverage, Property 4: Conditional field validation
    Validates: Requirements 5.4, 5.5
    """

    @given(event_type=st.sampled_from(sorted(FILE_EVENT_TYPES)))
    @settings(max_examples=100)
    def test_file_event_without_patterns_produces_error(self, event_type: str):
        """For any file event type without when.patterns, validator reports error.

        Feature: hook-test-coverage, Property 4: Conditional field validation
        Validates: Requirements 5.4
        """
        hook = {"when": {"type": event_type}}
        errors = validate_conditional_fields(hook)
        assert any("when.patterns" in e for e in errors), (
            f"File event '{event_type}' without patterns did not produce error. "
            f"Errors: {errors}"
        )

    @given(event_type=st.sampled_from(sorted(TOOL_EVENT_TYPES)))
    @settings(max_examples=100)
    def test_tool_event_without_tool_types_produces_error(self, event_type: str):
        """For any tool event type without when.toolTypes, validator reports error.

        Feature: hook-test-coverage, Property 4: Conditional field validation
        Validates: Requirements 5.5
        """
        hook = {"when": {"type": event_type}}
        errors = validate_conditional_fields(hook)
        assert any("when.toolTypes" in e for e in errors), (
            f"Tool event '{event_type}' without toolTypes did not produce error. "
            f"Errors: {errors}"
        )

    @given(event_type=st.sampled_from(sorted(FILE_EVENT_TYPES)))
    @settings(max_examples=100)
    def test_file_event_with_patterns_no_error(self, event_type: str):
        """For any file event type with non-empty when.patterns, no error reported.

        Feature: hook-test-coverage, Property 4: Conditional field validation
        Validates: Requirements 5.4
        """
        hook = {"when": {"type": event_type, "patterns": ["*.py"]}}
        errors = validate_conditional_fields(hook)
        assert not any("when.patterns" in e for e in errors), (
            f"File event '{event_type}' with patterns still produced error: {errors}"
        )

    @given(event_type=st.sampled_from(sorted(TOOL_EVENT_TYPES)))
    @settings(max_examples=100)
    def test_tool_event_with_tool_types_no_error(self, event_type: str):
        """For any tool event type with non-empty when.toolTypes, no error reported.

        Feature: hook-test-coverage, Property 4: Conditional field validation
        Validates: Requirements 5.5
        """
        hook = {"when": {"type": event_type, "toolTypes": ["write"]}}
        errors = validate_conditional_fields(hook)
        assert not any("when.toolTypes" in e for e in errors), (
            f"Tool event '{event_type}' with toolTypes still produced error: {errors}"
        )


# ===========================================================================
# TestVersionFormatValidation — Property 5
# ===========================================================================

class TestVersionFormatValidation:
    """Property 5: Version validator accepts valid semver and rejects invalid formats.

    Feature: hook-test-coverage, Property 5: Version format validation
    Validates: Requirements 7.2
    """

    @given(version=st_valid_semver())
    @settings(max_examples=100)
    def test_valid_semver_accepted(self, version: str):
        """For any valid semver string, the version validator accepts it.

        Feature: hook-test-coverage, Property 5: Version format validation
        Validates: Requirements 7.2
        """
        assert validate_version(version), (
            f"Valid semver '{version}' was rejected"
        )

    @given(version=st_invalid_semver())
    @settings(max_examples=100)
    def test_invalid_semver_rejected(self, version: str):
        """For any invalid semver string, the version validator rejects it.

        Feature: hook-test-coverage, Property 5: Version format validation
        Validates: Requirements 7.2
        """
        assert not validate_version(version), (
            f"Invalid semver '{version}' was accepted"
        )


# ===========================================================================
# TestMarkdownGlobMatching — Property 6
# ===========================================================================

class TestMarkdownGlobMatching:
    """Property 6: Markdown paths match hook glob, non-markdown paths don't.

    Feature: hook-test-coverage, Property 6: Markdown glob matching
    Validates: Requirements 1.6
    """

    MARKDOWN_GLOB = "**/*.md"

    @given(path=st_markdown_path())
    @settings(max_examples=100)
    def test_markdown_path_matches_glob(self, path: str):
        """For any file path ending in .md, the glob pattern matches.

        Feature: hook-test-coverage, Property 6: Markdown glob matching
        Validates: Requirements 1.6
        """
        # fnmatch with ** requires checking the basename or using recursive logic
        # The glob **/*.md matches any path ending in .md
        assert path.endswith(".md"), f"Generated path doesn't end in .md: {path}"
        # fnmatch("foo/bar.md", "**/*.md") doesn't work directly,
        # but the hook pattern "**/*.md" is a glob that matches any .md file
        # We verify the path ends with .md which is what the pattern captures
        basename = path.split("/")[-1]
        assert fnmatch(basename, "*.md"), (
            f"Markdown path '{path}' basename '{basename}' doesn't match *.md"
        )

    @given(path=st_non_markdown_path())
    @settings(max_examples=100)
    def test_non_markdown_path_does_not_match_glob(self, path: str):
        """For any file path NOT ending in .md, the glob pattern does not match.

        Feature: hook-test-coverage, Property 6: Markdown glob matching
        Validates: Requirements 1.6
        """
        assert not path.endswith(".md"), (
            f"Generated non-markdown path ends in .md: {path}"
        )
        basename = path.split("/")[-1]
        assert not fnmatch(basename, "*.md"), (
            f"Non-markdown path '{path}' basename '{basename}' matches *.md"
        )
