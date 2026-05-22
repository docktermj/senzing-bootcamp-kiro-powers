"""Property-based tests for preferences schema validation.

Feature: preferences-schema-validation
Covers correctness properties from the design document.
"""

import re
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import parse_yaml


# ---------------------------------------------------------------------------
# Strategies for YAML round-trip (Property 8)
# ---------------------------------------------------------------------------


def st_yaml_scalar():
    """Generate scalar values valid in the preferences YAML format."""
    return st.one_of(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                whitelist_characters="_-",
            ),
        ),
        st.integers(min_value=0, max_value=9999),
        st.booleans(),
        st.none(),
    )


@st.composite
def st_nested_dict(draw):
    """Generate a nested dict with string keys and scalar values.

    Mimics conversation_style or production_specs structures.
    """
    keys = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_",
                ),
            ),
            min_size=1,
            max_size=4,
            unique=True,
        )
    )
    result = {}
    for key in keys:
        result[key] = draw(st_yaml_scalar())
    return result


@st.composite
def st_string_list(draw):
    """Generate a list of strings (like hooks_installed)."""
    return draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(
                    whitelist_categories=("L", "N"),
                    whitelist_characters="_-",
                ),
            ),
            min_size=1,
            max_size=5,
        )
    )


@st.composite
def st_dict_list(draw):
    """Generate a list of dicts with name/version keys (like runtimes_installed)."""
    num_items = draw(st.integers(min_value=1, max_value=3))
    items = []
    for _ in range(num_items):
        name = draw(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_-",
                ),
            )
        )
        version = draw(
            st.text(
                min_size=1,
                max_size=10,
                alphabet=st.characters(
                    whitelist_categories=("N",),
                    whitelist_characters=".",
                ),
            )
        )
        items.append({"name": name, "version": version})
    return items


@st.composite
def st_preferences_dict(draw):
    """Generate a valid preferences-like dict with mixed value types.

    Produces dicts containing:
    - Flat key-value pairs with scalar values (str, int, bool, None)
    - Nested dicts (like conversation_style/production_specs)
    - Lists of strings (like hooks_installed)
    - Lists of dicts with name/version (like runtimes_installed_during_onboarding)
    """
    result = {}

    # Generate some flat scalar key-value pairs
    num_scalars = draw(st.integers(min_value=1, max_value=5))
    scalar_keys = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_",
                ),
            ),
            min_size=num_scalars,
            max_size=num_scalars,
            unique=True,
        )
    )
    for key in scalar_keys:
        result[key] = draw(st_yaml_scalar())

    # Optionally add a nested dict
    if draw(st.booleans()):
        nested_key = draw(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_",
                ),
            ).filter(lambda k: k not in result)
        )
        result[nested_key] = draw(st_nested_dict())

    # Optionally add a string list
    if draw(st.booleans()):
        list_key = draw(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_",
                ),
            ).filter(lambda k: k not in result)
        )
        result[list_key] = draw(st_string_list())

    # Optionally add a list of dicts
    if draw(st.booleans()):
        dict_list_key = draw(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(
                    whitelist_categories=("Ll",),
                    whitelist_characters="_",
                ),
            ).filter(lambda k: k not in result)
        )
        result[dict_list_key] = draw(st_dict_list())

    return result


# ---------------------------------------------------------------------------
# Helpers for YAML round-trip
# ---------------------------------------------------------------------------


def _needs_quoting(value: str) -> bool:
    """Check if a string value needs quoting to survive YAML round-trip.

    Values that look like integers, booleans, or null must be quoted so the
    parser doesn't interpret them as a different type.

    Args:
        value: String value to check.

    Returns:
        True if the value needs quoting.
    """
    if value in ("null", "~", ""):
        return True
    if value.lower() in ("true", "false"):
        return True
    try:
        int(value)
        return True
    except ValueError:
        return False


def _format_scalar(value) -> str:
    """Format a scalar value for YAML output.

    Args:
        value: Scalar value (str, int, bool, or None).

    Returns:
        YAML-safe string representation.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    # str — quote if ambiguous
    if _needs_quoting(value):
        return f'"{value}"'
    return value


def format_as_yaml(data: dict) -> str:
    """Format a preferences-like dict as YAML text.

    Handles scalars, nested dicts, lists of scalars, and lists of dicts.

    Args:
        data: Dict to format.

    Returns:
        YAML-formatted string.
    """
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_val in value.items():
                lines.append(f"  {sub_key}: {_format_scalar(sub_val)}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for item_key, item_val in item.items():
                        if first:
                            lines.append(
                                f"  - {item_key}: {_format_scalar(item_val)}"
                            )
                            first = False
                        else:
                            lines.append(
                                f"    {item_key}: {_format_scalar(item_val)}"
                            )
                else:
                    lines.append(f"  - {_format_scalar(item)}")
        else:
            lines.append(f"{key}: {_format_scalar(value)}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Property Tests - YAML Round-Trip (Property 8)
# ---------------------------------------------------------------------------


class TestYamlRoundTrip:
    """Property-based tests for YAML round-trip parsing.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """

    @given(data=st_preferences_dict())
    @settings(max_examples=20)
    def test_yaml_round_trip_parsing(self, data):
        """Property 8: YAML round-trip parsing.

        For any valid preferences dict (containing scalars, nested dicts, and
        lists as used by the preferences file format), formatting the dict as
        YAML text and parsing it with parse_yaml() SHALL produce an equivalent
        dict.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
        """
        yaml_text = format_as_yaml(data)
        parsed = parse_yaml(yaml_text)
        assert parsed == data, (
            f"Round-trip failed.\n"
            f"Original: {data!r}\n"
            f"YAML text:\n{yaml_text}\n"
            f"Parsed: {parsed!r}"
        )



# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_malformed_yaml_text(draw):
    """Generate malformed YAML text with unexpected top-level indentation.

    Creates a valid key-value line prefixed with spaces, which the parser
    rejects as unexpected indentation at the top level.
    """
    # Generate a valid key name (alphanumeric, starting with a letter)
    key = draw(
        st.text(
            min_size=1,
            max_size=15,
            alphabet=st.characters(whitelist_categories=("Ll",)),
        )
    )
    # Generate a simple scalar value
    value = draw(
        st.text(
            min_size=1,
            max_size=15,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        )
    )
    # Generate leading spaces (at least 1 to trigger indentation error)
    num_spaces = draw(st.integers(min_value=1, max_value=8))
    indent = " " * num_spaces

    # The malformed line: indented key-value pair at top level
    malformed_line = f"{indent}{key}: {value}"

    # Optionally prepend valid lines or blank lines before the malformed one
    prefix_lines = draw(
        st.lists(
            st.sampled_from(["", "# a comment"]),
            min_size=0,
            max_size=3,
        )
    )

    lines = prefix_lines + [malformed_line]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestMalformedYamlErrors:
    """Property-based tests for malformed YAML error reporting.

    **Validates: Requirements 4.8**
    """

    @given(malformed_text=st_malformed_yaml_text())
    @settings(max_examples=20)
    def test_malformed_yaml_raises_valueerror_with_line_info(self, malformed_text):
        """Property 10: Malformed YAML raises ValueError with line info.

        For any text input containing syntactically invalid YAML (e.g.,
        inconsistent indentation, malformed key-value pairs), parse_yaml()
        SHALL raise a ValueError whose message contains a line number.

        **Validates: Requirements 4.8**
        """
        try:
            parse_yaml(malformed_text)
            # If parse_yaml didn't raise, that's a test failure
            assert False, (
                f"Expected ValueError for malformed YAML, but parse_yaml() "
                f"succeeded. Input: {malformed_text!r}"
            )
        except ValueError as exc:
            error_msg = str(exc)
            # The error message must contain "Line" or a digit (line number)
            has_line_keyword = "Line" in error_msg or "line" in error_msg
            has_digit = bool(re.search(r"\d", error_msg))
            assert has_line_keyword or has_digit, (
                f"Expected error message to contain 'Line' or a line number, "
                f"got: {error_msg!r}"
            )


# ---------------------------------------------------------------------------
# Strategies for comments transparency
# ---------------------------------------------------------------------------


def st_yaml_key():
    """Generate a valid YAML key (simple alphanumeric + underscores)."""
    return st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True)


def st_yaml_scalar_value():
    """Generate a valid YAML scalar value (string, int, bool, null)."""
    return st.one_of(
        st.just("null"),
        st.just("true"),
        st.just("false"),
        st.integers(min_value=0, max_value=9999).map(str),
        st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,10}", fullmatch=True),
    )


@st.composite
def st_flat_yaml_lines(draw):
    """Generate a list of flat key-value YAML lines with unique keys.

    Returns a list of strings like ["key1: value1", "key2: value2"].
    """
    num_entries = draw(st.integers(min_value=1, max_value=6))
    keys = draw(
        st.lists(
            st_yaml_key(),
            min_size=num_entries,
            max_size=num_entries,
            unique=True,
        )
    )
    lines = []
    for key in keys:
        value = draw(st_yaml_scalar_value())
        lines.append(f"{key}: {value}")
    return lines


def st_comment_line():
    """Generate a YAML comment line."""
    return st.from_regex(r"# [a-zA-Z0-9 ]{0,20}", fullmatch=True)


def st_blank_or_comment():
    """Generate either a blank line or a comment line."""
    return st.one_of(
        st.just(""),
        st.just("   "),
        st_comment_line(),
    )


# ---------------------------------------------------------------------------
# Property Tests - Comments Transparency
# ---------------------------------------------------------------------------


class TestCommentsTransparency:
    """Property-based tests for comments and blank lines transparency.

    **Validates: Requirements 4.6, 4.7**
    """

    @given(
        yaml_lines=st_flat_yaml_lines(),
        insertions=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=100),
                st_blank_or_comment(),
            ),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=20)
    def test_comments_and_blank_lines_transparent_to_parsing(
        self, yaml_lines, insertions
    ):
        """Property 9: Comments and blank lines are transparent to parsing.

        For any valid YAML text that parses successfully, inserting comment
        lines (starting with #) or blank lines at arbitrary positions SHALL
        not change the parsed result.

        **Validates: Requirements 4.6, 4.7**
        """
        # Build baseline YAML text from flat key-value lines
        baseline_text = "\n".join(yaml_lines)
        baseline_result = parse_yaml(baseline_text)

        # Insert comments and blank lines between existing lines
        modified_lines = list(yaml_lines)
        for position_hint, insertion_line in insertions:
            # Clamp position to valid range (0 to len inclusive)
            pos = position_hint % (len(modified_lines) + 1)
            modified_lines.insert(pos, insertion_line)

        modified_text = "\n".join(modified_lines)
        modified_result = parse_yaml(modified_text)

        assert modified_result == baseline_result, (
            f"Inserting comments/blanks changed parse result.\n"
            f"Baseline: {baseline_result!r}\n"
            f"Modified: {modified_result!r}\n"
            f"Original lines: {yaml_lines!r}\n"
            f"Modified lines: {modified_lines!r}"
        )


# ---------------------------------------------------------------------------
# Strategies for unknown top-level keys (Property 2)
# ---------------------------------------------------------------------------

from preferences_utils import KNOWN_TOP_LEVEL_KEYS, validate_preferences_schema


@st.composite
def st_unknown_top_level_key(draw):
    """Generate a string key that is NOT in KNOWN_TOP_LEVEL_KEYS.

    Produces alphanumeric+underscore keys that are filtered to exclude
    any key present in the known set.
    """
    key = draw(
        st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(
                whitelist_categories=("Ll", "N"),
                whitelist_characters="_",
            ),
        ).filter(lambda k: k not in KNOWN_TOP_LEVEL_KEYS)
    )
    return key


# ---------------------------------------------------------------------------
# Property Tests - Unknown Top-Level Keys (Property 2)
# ---------------------------------------------------------------------------


class TestUnknownTopLevelKeys:
    """Property-based tests for unknown top-level key rejection.

    **Validates: Requirements 1.1**
    """

    @given(unknown_key=st_unknown_top_level_key())
    @settings(max_examples=20)
    def test_unknown_top_level_keys_are_rejected(self, unknown_key):
        """Property 2: Unknown top-level keys are rejected.

        For any string not present in the Known_Keys set, when that string
        appears as a top-level key in a preferences dict,
        validate_preferences_schema() SHALL return a non-empty error list
        containing the unrecognized key name.

        **Validates: Requirements 1.1**
        """
        # Start with a valid base preferences dict
        prefs = {"database_type": "sqlite", unknown_key: "some_value"}

        errors = validate_preferences_schema(prefs)

        # Must return non-empty error list
        assert len(errors) > 0, (
            f"Expected errors for unknown key '{unknown_key}', got empty list"
        )

        # At least one error message must contain the unknown key name
        assert any(unknown_key in err for err in errors), (
            f"Expected at least one error containing '{unknown_key}', "
            f"got: {errors!r}"
        )


# ---------------------------------------------------------------------------
# Strategies for unknown nested keys (Property 3)
# ---------------------------------------------------------------------------

from preferences_utils import (
    CONVERSATION_STYLE_KEYS,
    PRODUCTION_SPECS_KEYS,
    validate_preferences_schema,
)


def st_unknown_key(known_keys: set[str]):
    """Generate a string key that is NOT in the given known_keys set.

    Args:
        known_keys: Set of keys to exclude from generation.

    Returns:
        Hypothesis strategy producing strings not in known_keys.
    """
    return st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("Ll",),
            whitelist_characters="_",
        ),
    ).filter(lambda k: k not in known_keys)


# ---------------------------------------------------------------------------
# Property Tests - Unknown Nested Keys (Property 3)
# ---------------------------------------------------------------------------


class TestUnknownNestedKeys:
    """Property-based tests for unknown nested key rejection.

    **Validates: Requirements 1.2, 1.3**
    """

    @given(unknown_key=st_unknown_key(CONVERSATION_STYLE_KEYS))
    @settings(max_examples=20)
    def test_unknown_conversation_style_key_rejected(self, unknown_key):
        """Property 3: Unknown nested keys in conversation_style are rejected.

        For any string not present in the allowed sub-key set for
        conversation_style, when that string appears as a nested key within
        conversation_style, validate_preferences_schema() SHALL return a
        non-empty error list identifying the unrecognized nested key.

        **Validates: Requirements 1.2**
        """
        prefs = {
            "database_type": "sqlite",
            "conversation_style": {unknown_key: "some_value"},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for unknown conversation_style key '{unknown_key}', "
            f"got none"
        )
        assert any(unknown_key in err for err in errors), (
            f"Expected error mentioning unknown key '{unknown_key}', "
            f"got: {errors!r}"
        )

    @given(unknown_key=st_unknown_key(PRODUCTION_SPECS_KEYS))
    @settings(max_examples=20)
    def test_unknown_production_specs_key_rejected(self, unknown_key):
        """Property 3: Unknown nested keys in production_specs are rejected.

        For any string not present in the allowed sub-key set for
        production_specs, when that string appears as a nested key within
        production_specs, validate_preferences_schema() SHALL return a
        non-empty error list identifying the unrecognized nested key.

        **Validates: Requirements 1.3**
        """
        prefs = {
            "database_type": "sqlite",
            "production_specs": {unknown_key: "some_value"},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for unknown production_specs key '{unknown_key}', "
            f"got none"
        )
        assert any(unknown_key in err for err in errors), (
            f"Expected error mentioning unknown key '{unknown_key}', "
            f"got: {errors!r}"
        )


# ---------------------------------------------------------------------------
# Import validate_preferences_schema
# ---------------------------------------------------------------------------

from preferences_utils import (
    validate_preferences_schema,
    CONVERSATION_STYLE_KEYS,
    PRODUCTION_SPECS_KEYS,
    VALID_MAPPING_VERBOSITY,
    VALID_HARDWARE_TARGET,
    VALID_VERBOSITY_PRESET,
    VALID_QUESTION_FRAMING,
    VALID_TONE,
    VALID_PACING,
)


# ---------------------------------------------------------------------------
# Strategies for valid preferences (Property 1)
# ---------------------------------------------------------------------------

# Enum maps for conversation_style sub-keys
_CONVERSATION_STYLE_ENUMS: dict[str, tuple[str, ...]] = {
    "verbosity_preset": VALID_VERBOSITY_PRESET,
    "question_framing": VALID_QUESTION_FRAMING,
    "tone": VALID_TONE,
    "pacing": VALID_PACING,
}


def _st_non_empty_str():
    """Generate a non-empty string suitable for preference values."""
    return st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="_-",
        ),
    )


@st.composite
def st_valid_conversation_style(draw):
    """Generate a valid conversation_style value: None, a string, or a valid dict."""
    choice = draw(st.sampled_from(["none", "string", "dict"]))
    if choice == "none":
        return None
    if choice == "string":
        return draw(_st_non_empty_str())
    # dict with only CONVERSATION_STYLE_KEYS sub-keys with valid enum values
    keys_to_include = draw(
        st.lists(
            st.sampled_from(sorted(CONVERSATION_STYLE_KEYS)),
            min_size=0,
            max_size=len(CONVERSATION_STYLE_KEYS),
            unique=True,
        )
    )
    result = {}
    for key in keys_to_include:
        result[key] = draw(st.sampled_from(_CONVERSATION_STYLE_ENUMS[key]))
    return result


@st.composite
def st_valid_hooks_installed(draw):
    """Generate a valid hooks_installed value: None or list of strings."""
    if draw(st.booleans()):
        return None
    return draw(
        st.lists(_st_non_empty_str(), min_size=0, max_size=5)
    )


@st.composite
def st_valid_runtimes_installed(draw):
    """Generate a valid runtimes_installed_during_onboarding value.

    None or list of dicts with "name" (str) and "version" (str).
    """
    if draw(st.booleans()):
        return None
    num_items = draw(st.integers(min_value=0, max_value=3))
    items = []
    for _ in range(num_items):
        items.append({
            "name": draw(_st_non_empty_str()),
            "version": draw(_st_non_empty_str()),
        })
    return items


@st.composite
def st_valid_production_specs(draw):
    """Generate a valid production_specs value.

    None or dict with only PRODUCTION_SPECS_KEYS sub-keys:
    cpu_cores/ram_gb as int, storage_type/database as str.
    """
    if draw(st.booleans()):
        return None
    keys_to_include = draw(
        st.lists(
            st.sampled_from(sorted(PRODUCTION_SPECS_KEYS)),
            min_size=0,
            max_size=len(PRODUCTION_SPECS_KEYS),
            unique=True,
        )
    )
    result = {}
    for key in keys_to_include:
        if key in ("cpu_cores", "ram_gb"):
            result[key] = draw(st.integers(min_value=1, max_value=128))
        else:
            result[key] = draw(_st_non_empty_str())
    return result


@st.composite
def st_valid_preferences(draw):
    """Generate a valid preferences dict with correctly-typed values.

    Always includes "database_type" with a non-empty string value.
    Includes a random subset of optional keys with correctly-typed values.
    """
    result: dict = {}

    # Required key: database_type (non-empty string)
    result["database_type"] = draw(_st_non_empty_str())

    # Optional str|None keys
    str_or_none_keys = [
        "language", "track", "deployment_target", "cloud_provider",
        "verbosity", "pacing_overrides", "license", "team_member_id",
        "detail_level",
    ]
    for key in str_or_none_keys:
        if draw(st.booleans()):
            result[key] = draw(st.one_of(st.none(), _st_non_empty_str()))

    # Optional enum str|None keys
    if draw(st.booleans()):
        result["mapping_verbosity"] = draw(
            st.one_of(st.none(), st.sampled_from(VALID_MAPPING_VERBOSITY))
        )
    if draw(st.booleans()):
        result["hardware_target"] = draw(
            st.one_of(st.none(), st.sampled_from(VALID_HARDWARE_TARGET))
        )

    # Optional bool|None keys
    bool_or_none_keys = [
        "license_guidance_deferred", "skip_graduation",
        "scoop_installed_during_onboarding",
        "prerequisite_installation_deferred",
    ]
    for key in bool_or_none_keys:
        if draw(st.booleans()):
            result[key] = draw(st.one_of(st.none(), st.booleans()))

    # Optional conversation_style
    if draw(st.booleans()):
        result["conversation_style"] = draw(st_valid_conversation_style())

    # Optional hooks_installed
    if draw(st.booleans()):
        result["hooks_installed"] = draw(st_valid_hooks_installed())

    # Optional runtimes_installed_during_onboarding
    if draw(st.booleans()):
        result["runtimes_installed_during_onboarding"] = draw(
            st_valid_runtimes_installed()
        )

    # Optional production_specs
    if draw(st.booleans()):
        result["production_specs"] = draw(st_valid_production_specs())

    return result


# ---------------------------------------------------------------------------
# Property Tests - Valid Preferences Validate Cleanly (Property 1)
# ---------------------------------------------------------------------------


class TestValidPreferencesClean:
    """Property-based tests for valid preferences validation.

    **Validates: Requirements 2.1, 6.1, 6.2**
    """

    @given(data=st_valid_preferences())
    @settings(max_examples=20)
    def test_valid_preferences_validate_cleanly(self, data):
        """Property 1: Valid preferences validate cleanly.

        For any preferences dict containing only keys from the Known_Keys set
        with correctly-typed values (including random subsets of optional keys),
        validate_preferences_schema() SHALL return an empty error list.

        **Validates: Requirements 2.1, 6.1, 6.2**
        """
        errors = validate_preferences_schema(data)
        assert errors == [], (
            f"Expected no validation errors for valid preferences, "
            f"got: {errors!r}\nInput: {data!r}"
        )


# ---------------------------------------------------------------------------
# Strategies for all errors collected (Property 6)
# ---------------------------------------------------------------------------


@st.composite
def st_multiple_violations_dict(draw):
    """Generate a preferences dict with multiple distinct violations.

    Creates a dict with:
    - N unknown top-level keys (each generates 1 error)
    - A valid database_type to avoid the missing-required-key error conflating counts

    Returns a tuple of (preferences_dict, expected_minimum_error_count).
    """
    # Generate 1-5 random unknown keys (not in KNOWN_TOP_LEVEL_KEYS)
    num_unknown = draw(st.integers(min_value=1, max_value=5))
    unknown_keys = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(
                    whitelist_categories=("Ll", "N"),
                    whitelist_characters="_",
                ),
            ).filter(lambda k: k not in KNOWN_TOP_LEVEL_KEYS),
            min_size=num_unknown,
            max_size=num_unknown,
            unique=True,
        )
    )

    # Start with a valid base to avoid missing-required-key noise
    prefs: dict = {"database_type": "sqlite"}

    # Add all unknown keys
    for key in unknown_keys:
        prefs[key] = "some_value"

    expected_min_errors = num_unknown

    return prefs, expected_min_errors


# ---------------------------------------------------------------------------
# Property Tests - All Errors Collected (Property 6)
# ---------------------------------------------------------------------------


class TestAllErrorsCollected:
    """Property-based tests for all errors collected without short-circuiting.

    **Validates: Requirements 1.4**
    """

    @given(violation_data=st_multiple_violations_dict())
    @settings(max_examples=20)
    def test_all_errors_collected_without_short_circuiting(self, violation_data):
        """Property 6: All errors collected without short-circuiting.

        For any preferences dict containing N distinct violations (unknown keys,
        type mismatches, enum violations), validate_preferences_schema() SHALL
        return an error list with at least N entries.

        **Validates: Requirements 1.4**
        """
        prefs, expected_min_errors = violation_data

        errors = validate_preferences_schema(prefs)

        assert len(errors) >= expected_min_errors, (
            f"Expected at least {expected_min_errors} errors, got {len(errors)}.\n"
            f"Preferences: {prefs!r}\n"
            f"Errors: {errors!r}"
        )


# ---------------------------------------------------------------------------
# Strategies for enum constraint violations (Property 5)
# ---------------------------------------------------------------------------

from preferences_utils import (
    validate_preferences_schema,
    VALID_MAPPING_VERBOSITY,
    VALID_HARDWARE_TARGET,
    VALID_VERBOSITY_PRESET,
    VALID_QUESTION_FRAMING,
    VALID_TONE,
    VALID_PACING,
)


def st_invalid_enum_value(valid_values: tuple[str, ...]):
    """Generate a string that is NOT in the given set of valid enum values.

    Args:
        valid_values: Tuple of allowed enum strings to exclude.

    Returns:
        Hypothesis strategy producing strings not in valid_values.
    """
    return st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="_-",
        ),
    ).filter(lambda s: s not in valid_values)


# ---------------------------------------------------------------------------
# Property Tests - Enum Constraint Violations (Property 5)
# ---------------------------------------------------------------------------


class TestEnumConstraintViolations:
    """Property-based tests for enum constraint violation detection.

    **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
    """

    @given(invalid_value=st_invalid_enum_value(VALID_MAPPING_VERBOSITY))
    @settings(max_examples=20)
    def test_invalid_mapping_verbosity_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (mapping_verbosity).

        For any string value not in the allowed mapping_verbosity set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.3**
        """
        prefs = {"database_type": "sqlite", "mapping_verbosity": invalid_value}
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid mapping_verbosity '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )

    @given(invalid_value=st_invalid_enum_value(VALID_HARDWARE_TARGET))
    @settings(max_examples=20)
    def test_invalid_hardware_target_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (hardware_target).

        For any string value not in the allowed hardware_target set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.4**
        """
        prefs = {"database_type": "sqlite", "hardware_target": invalid_value}
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid hardware_target '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )

    @given(invalid_value=st_invalid_enum_value(VALID_VERBOSITY_PRESET))
    @settings(max_examples=20)
    def test_invalid_verbosity_preset_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (verbosity_preset).

        For any string value not in the allowed verbosity_preset set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.5**
        """
        prefs = {
            "database_type": "sqlite",
            "conversation_style": {"verbosity_preset": invalid_value},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid verbosity_preset '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )

    @given(invalid_value=st_invalid_enum_value(VALID_QUESTION_FRAMING))
    @settings(max_examples=20)
    def test_invalid_question_framing_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (question_framing).

        For any string value not in the allowed question_framing set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.6**
        """
        prefs = {
            "database_type": "sqlite",
            "conversation_style": {"question_framing": invalid_value},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid question_framing '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )

    @given(invalid_value=st_invalid_enum_value(VALID_TONE))
    @settings(max_examples=20)
    def test_invalid_tone_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (tone).

        For any string value not in the allowed tone set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.7**
        """
        prefs = {
            "database_type": "sqlite",
            "conversation_style": {"tone": invalid_value},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid tone '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )

    @given(invalid_value=st_invalid_enum_value(VALID_PACING))
    @settings(max_examples=20)
    def test_invalid_pacing_rejected(self, invalid_value):
        """Property 5: Enum constraint violations are rejected (pacing).

        For any string value not in the allowed pacing set,
        validate_preferences_schema() SHALL return a non-empty error list
        identifying the invalid value.

        **Validates: Requirements 3.8**
        """
        prefs = {
            "database_type": "sqlite",
            "conversation_style": {"pacing": invalid_value},
        }
        errors = validate_preferences_schema(prefs)
        assert len(errors) > 0, (
            f"Expected errors for invalid pacing '{invalid_value}', got none"
        )
        error_text = " ".join(errors)
        assert invalid_value in error_text, (
            f"Expected error to mention invalid value '{invalid_value}', "
            f"got: {errors}"
        )


# ---------------------------------------------------------------------------
# Strategies for type mismatch errors (Property 4)
# ---------------------------------------------------------------------------

# Define the schema type expectations for each key category
_STR_OR_NONE_KEYS = [
    "language", "track", "deployment_target", "cloud_provider",
    "verbosity", "mapping_verbosity", "pacing_overrides", "license",
    "team_member_id", "detail_level", "hardware_target",
]

_BOOL_OR_NONE_KEYS = [
    "license_guidance_deferred", "skip_graduation",
    "scoop_installed_during_onboarding", "prerequisite_installation_deferred",
]

_LIST_OR_NONE_KEYS = [
    "hooks_installed", "runtimes_installed_during_onboarding",
]

_DICT_OR_NONE_KEYS = [
    "production_specs",
]


def st_wrong_type_for_str_or_none():
    """Generate a value that is NOT str and NOT None (wrong for str|None keys)."""
    return st.one_of(
        st.integers(min_value=-100, max_value=100),
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3),
        st.just(True),
        st.just(False),
    )


def st_wrong_type_for_bool_or_none():
    """Generate a value that is NOT bool and NOT None (wrong for bool|None keys)."""
    return st.one_of(
        st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=("L",))),
        st.integers(min_value=-100, max_value=100),
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=2),
    )


def st_wrong_type_for_list_or_none():
    """Generate a value that is NOT list and NOT None (wrong for list|None keys)."""
    return st.one_of(
        st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=("L",))),
        st.integers(min_value=-100, max_value=100),
        st.just(True),
    )


def st_wrong_type_for_dict_or_none():
    """Generate a value that is NOT dict and NOT None (wrong for dict|None keys)."""
    return st.one_of(
        st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=("L",))),
        st.integers(min_value=-100, max_value=100),
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=2),
    )


def st_wrong_type_for_database_type():
    """Generate a value that is NOT str (wrong for database_type which is str, non-nullable)."""
    return st.one_of(
        st.integers(min_value=-100, max_value=100),
        st.just(True),
        st.just(False),
        st.just(None),
        st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=2),
    )


@st.composite
def st_type_mismatch_entry(draw):
    """Generate a (key, wrong_value) pair where the value has the wrong type.

    Picks a known key from the schema and assigns a value whose type does
    not match the schema definition for that key.

    Returns:
        Tuple of (key_name, wrong_value).
    """
    # Choose which category of key to test
    category = draw(st.sampled_from([
        "str_or_none", "bool_or_none", "list_or_none",
        "dict_or_none", "database_type",
    ]))

    if category == "str_or_none":
        key = draw(st.sampled_from(_STR_OR_NONE_KEYS))
        value = draw(st_wrong_type_for_str_or_none())
    elif category == "bool_or_none":
        key = draw(st.sampled_from(_BOOL_OR_NONE_KEYS))
        value = draw(st_wrong_type_for_bool_or_none())
    elif category == "list_or_none":
        key = draw(st.sampled_from(_LIST_OR_NONE_KEYS))
        value = draw(st_wrong_type_for_list_or_none())
    elif category == "dict_or_none":
        key = draw(st.sampled_from(_DICT_OR_NONE_KEYS))
        value = draw(st_wrong_type_for_dict_or_none())
    else:
        # database_type: str (non-nullable)
        key = "database_type"
        value = draw(st_wrong_type_for_database_type())

    return (key, value)


# ---------------------------------------------------------------------------
# Property Tests - Type Mismatch Errors (Property 4)
# ---------------------------------------------------------------------------


class TestTypeMismatchErrors:
    """Property-based tests for type mismatch error reporting.

    **Validates: Requirements 3.1, 2.2, 2.3, 2.4, 2.5**
    """

    @given(entry=st_type_mismatch_entry())
    @settings(max_examples=20)
    def test_type_mismatches_produce_descriptive_errors(self, entry):
        """Property 4: Type mismatches produce descriptive errors.

        For any known key whose value has a type not matching the schema
        definition, validate_preferences_schema() SHALL return a non-empty
        error list where at least one error message contains the key name.

        **Validates: Requirements 3.1, 2.2, 2.3, 2.4, 2.5**
        """
        key, wrong_value = entry

        # Build a preferences dict with database_type + the mistyped key
        if key == "database_type":
            prefs = {"database_type": wrong_value}
        else:
            prefs = {"database_type": "sqlite", key: wrong_value}

        errors = validate_preferences_schema(prefs)

        # Must return non-empty error list
        assert len(errors) > 0, (
            f"Expected errors for type mismatch on '{key}' "
            f"(value={wrong_value!r}, type={type(wrong_value).__name__}), "
            f"got empty list"
        )

        # At least one error message must contain the key name
        assert any(key in err for err in errors), (
            f"Expected at least one error containing key name '{key}', "
            f"got: {errors!r}"
        )


# ---------------------------------------------------------------------------
# Strategies for missing required key (Property 7)
# ---------------------------------------------------------------------------

# Optional keys are all KNOWN_TOP_LEVEL_KEYS except "database_type"
_OPTIONAL_KEYS = sorted(KNOWN_TOP_LEVEL_KEYS - {"database_type"})


@st.composite
def st_prefs_without_database_type(draw):
    """Generate a preferences dict with a random subset of optional keys but NO database_type.

    All optional keys accept None as a valid value, so we use None for simplicity.
    This ensures the only validation error is the missing required key.
    """
    # Pick a random subset of optional keys (at least 0, up to all)
    subset = draw(
        st.lists(
            st.sampled_from(_OPTIONAL_KEYS),
            min_size=0,
            max_size=len(_OPTIONAL_KEYS),
            unique=True,
        )
    )
    prefs = {key: None for key in subset}
    # Explicitly ensure database_type is NOT present
    prefs.pop("database_type", None)
    return prefs


# ---------------------------------------------------------------------------
# Property Tests - Missing Required Key (Property 7)
# ---------------------------------------------------------------------------


class TestMissingRequiredKey:
    """Property-based tests for missing required key detection.

    **Validates: Requirements 6.3, 3.2**
    """

    @given(prefs=st_prefs_without_database_type())
    @settings(max_examples=20)
    def test_missing_database_type_produces_error(self, prefs):
        """Property 7: Missing required key detected.

        For any valid preferences dict with the database_type key removed,
        validate_preferences_schema() SHALL return a non-empty error list
        indicating the required key is missing.

        **Validates: Requirements 6.3, 3.2**
        """
        errors = validate_preferences_schema(prefs)

        # Must return non-empty error list
        assert len(errors) > 0, (
            f"Expected errors for missing 'database_type', got empty list. "
            f"Input: {prefs!r}"
        )

        # At least one error must mention "database_type"
        assert any("database_type" in err for err in errors), (
            f"Expected at least one error containing 'database_type', "
            f"got: {errors!r}"
        )
