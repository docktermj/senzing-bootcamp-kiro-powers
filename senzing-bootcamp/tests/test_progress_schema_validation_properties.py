"""Property-based tests for progress file schema validation.

Feature: progress-file-schema-validation
Covers Property 1 (JSON round-trip), Property 2 (valid dicts validate),
Property 3 (corrupted dicts detected), and Property 4 (backward compatibility).
"""

import json
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import validate_progress_schema


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

OPTIONAL_FIELDS = [
    "current_step",
    "track",
    "preferences",
    "session_id",
    "started_at",
    "last_activity",
    "step_history",
]


@st.composite
def st_sub_step_identifier(draw):
    """Generate a valid sub-step identifier string (dotted or lettered)."""
    choice = draw(st.sampled_from(["dotted", "lettered"]))
    if choice == "dotted":
        parent = draw(st.integers(min_value=1, max_value=12))
        sub = draw(st.integers(min_value=1, max_value=20))
        return f"{parent}.{sub}"
    else:
        parent = draw(st.integers(min_value=1, max_value=12))
        letter = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        return f"{parent}{letter}"


@st.composite
def st_progress_file(draw):
    """Generate a fully valid progress dict with all constraints satisfied.

    All required fields are always present. Optional fields are randomly
    included or excluded.
    """
    # Required fields
    current_module = draw(st.integers(min_value=1, max_value=11))
    modules_completed = draw(
        st.lists(st.integers(min_value=1, max_value=11), max_size=11, unique=True)
    )
    data_sources = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("L", "N", "P")),
            ),
            max_size=5,
        )
    )
    database_type = draw(st.sampled_from(["sqlite", "postgresql", "mysql"]))

    result = {
        "current_module": current_module,
        "modules_completed": modules_completed,
        "data_sources": data_sources,
        "database_type": database_type,
    }

    # Optional: current_step
    if draw(st.booleans()):
        current_step = draw(
            st.one_of(
                st.none(),
                st.integers(min_value=1, max_value=26),
                st_sub_step_identifier(),
            )
        )
        result["current_step"] = current_step

    # Optional: track
    if draw(st.booleans()):
        result["track"] = draw(
            st.sampled_from(["core_bootcamp", "advanced_topics"])
        )

    # Optional: preferences
    if draw(st.booleans()):
        result["preferences"] = draw(
            st.dictionaries(
                keys=st.text(
                    min_size=1,
                    max_size=10,
                    alphabet=st.characters(whitelist_categories=("L",)),
                ),
                values=st.one_of(
                    st.text(min_size=0, max_size=20),
                    st.booleans(),
                ),
                max_size=5,
            )
        )

    # Optional: session_id
    if draw(st.booleans()):
        result["session_id"] = draw(
            st.text(
                min_size=1,
                max_size=36,
                alphabet=st.characters(whitelist_categories=("L", "N")),
            )
        )

    # Optional: started_at
    if draw(st.booleans()):
        dt = draw(st.datetimes())
        result["started_at"] = dt.isoformat()

    # Optional: last_activity
    if draw(st.booleans()):
        dt = draw(st.datetimes())
        result["last_activity"] = dt.isoformat()

    # Optional: step_history
    if draw(st.booleans()):
        num_entries = draw(st.integers(min_value=0, max_value=5))
        keys = draw(
            st.lists(
                st.integers(min_value=1, max_value=12),
                min_size=num_entries,
                max_size=num_entries,
                unique=True,
            )
        )
        step_history = {}
        for k in keys:
            last_completed = draw(
                st.one_of(
                    st.integers(min_value=1, max_value=26),
                    st_sub_step_identifier(),
                )
            )
            updated_dt = draw(st.datetimes())
            step_history[str(k)] = {
                "last_completed_step": last_completed,
                "updated_at": updated_dt.isoformat(),
            }
        result["step_history"] = step_history

    return result


@st.composite
def st_corrupted_progress_file(draw):
    """Generate a corrupted progress dict by replacing one field with an invalid value.

    Returns a tuple of (corrupted_dict, corrupted_field_name).
    """
    valid = draw(st_progress_file())

    # Choose which field to corrupt — pick from fields present in the dict
    # plus required fields that are always present
    corruptible_fields = [
        "current_module",
        "modules_completed",
        "data_sources",
        "database_type",
    ]
    # Add optional fields that are present
    for field in OPTIONAL_FIELDS:
        if field in valid:
            corruptible_fields.append(field)

    field_to_corrupt = draw(st.sampled_from(corruptible_fields))

    # Apply corruption based on field type
    if field_to_corrupt == "current_module":
        # Replace with wrong type or out-of-range value
        corruption = draw(st.sampled_from(["wrong_type", "out_of_range"]))
        if corruption == "wrong_type":
            valid["current_module"] = draw(
                st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("L",)))
            )
        else:
            valid["current_module"] = draw(
                st.one_of(
                    st.integers(max_value=0),
                    st.integers(min_value=12),
                )
            )

    elif field_to_corrupt == "modules_completed":
        corruption = draw(st.sampled_from(["wrong_type", "bad_element"]))
        if corruption == "wrong_type":
            valid["modules_completed"] = "not_a_list"
        else:
            # Insert an out-of-range element
            valid["modules_completed"] = [draw(
                st.one_of(
                    st.integers(max_value=0),
                    st.integers(min_value=12),
                )
            )]

    elif field_to_corrupt == "data_sources":
        corruption = draw(st.sampled_from(["wrong_type", "bad_element"]))
        if corruption == "wrong_type":
            valid["data_sources"] = 42
        else:
            valid["data_sources"] = [123]

    elif field_to_corrupt == "database_type":
        valid["database_type"] = draw(st.one_of(st.just(123), st.just([]), st.just(True)))

    elif field_to_corrupt == "current_step":
        # Replace with invalid string that doesn't match sub-step format
        valid["current_step"] = draw(
            st.sampled_from(["", "abc", "5.3.1", "7ab", "not-valid"])
        )

    elif field_to_corrupt == "track":
        valid["track"] = draw(
            st.text(
                min_size=1,
                max_size=10,
                alphabet=st.characters(whitelist_categories=("L",)),
            ).filter(lambda x: x not in ("core_bootcamp", "advanced_topics"))
        )

    elif field_to_corrupt == "preferences":
        corruption = draw(st.sampled_from(["wrong_type", "bad_value"]))
        if corruption == "wrong_type":
            valid["preferences"] = "not_a_dict"
        else:
            valid["preferences"] = {"key": 12345}

    elif field_to_corrupt == "session_id":
        corruption = draw(st.sampled_from(["wrong_type", "empty"]))
        if corruption == "wrong_type":
            valid["session_id"] = 12345
        else:
            valid["session_id"] = ""

    elif field_to_corrupt == "started_at":
        corruption = draw(st.sampled_from(["wrong_type", "bad_format"]))
        if corruption == "wrong_type":
            valid["started_at"] = 12345
        else:
            valid["started_at"] = "not-a-date"

    elif field_to_corrupt == "last_activity":
        corruption = draw(st.sampled_from(["wrong_type", "bad_format"]))
        if corruption == "wrong_type":
            valid["last_activity"] = 12345
        else:
            valid["last_activity"] = "not-a-date"

    elif field_to_corrupt == "step_history":
        corruption = draw(st.sampled_from(["wrong_type", "bad_key", "missing_field"]))
        if corruption == "wrong_type":
            valid["step_history"] = "not_a_dict"
        elif corruption == "bad_key":
            valid["step_history"] = {
                "abc": {"last_completed_step": 1, "updated_at": "2026-01-01T00:00:00"}
            }
        else:
            valid["step_history"] = {"1": {}}

    return (valid, field_to_corrupt)


@st.composite
def st_optional_field_subset(draw):
    """Generate a random subset of optional field names."""
    return draw(
        st.lists(
            st.sampled_from(OPTIONAL_FIELDS),
            max_size=len(OPTIONAL_FIELDS),
            unique=True,
        )
    )


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestProgressSchemaProperties:
    """Property-based tests for progress file schema validation.

    Validates: Requirements 2.1, 2.7, 3.1, 3.2, 5.1, 5.2, 5.3
    """

    # ------------------------------------------------------------------
    # Property 1 (remove-verification-track): Invalid track rejection
    # ------------------------------------------------------------------

    @given(
        invalid_track=st.text(min_size=1, max_size=50).filter(
            lambda x: x not in ("core_bootcamp", "advanced_topics")
        )
    )
    @settings(max_examples=100)
    def test_invalid_track_rejection_produces_descriptive_error(self, invalid_track):
        """Property 1: Invalid track rejection produces descriptive error.

        For any string not in ("core_bootcamp", "advanced_topics") — including
        "quick_demo" — when used as the track field in a progress record,
        validate_progress_schema() SHALL return a non-empty error list
        containing both the invalid value and the tuple of accepted tracks.

        **Validates: Requirements 3.2, 3.3**
        """
        progress = {
            "current_module": 1,
            "modules_completed": [],
            "data_sources": [],
            "database_type": "sqlite",
            "track": invalid_track,
        }
        errors = validate_progress_schema(progress)
        assert len(errors) > 0, (
            f"Expected non-empty error list for invalid track {invalid_track!r}, "
            f"got no errors"
        )
        error_text = " ".join(errors)
        # The error message uses repr() for the invalid value
        assert repr(invalid_track) in error_text, (
            f"Expected error to contain the invalid value {invalid_track!r}, "
            f"got: {errors}"
        )
        valid_tracks_repr = repr(("core_bootcamp", "advanced_topics"))
        assert valid_tracks_repr in error_text, (
            f"Expected error to contain valid tracks tuple {valid_tracks_repr}, "
            f"got: {errors}"
        )

    @given(progress=st_progress_file())
    @settings(max_examples=100)
    def test_json_round_trip_serialization(self, progress):
        """Property 1: JSON Round-Trip Serialization.

        For any valid progress file dict, serializing to JSON and deserializing
        back produces an equal dict.

        Validates: Requirements 5.1
        """
        serialized = json.dumps(progress)
        deserialized = json.loads(serialized)
        assert deserialized == progress, (
            f"Round-trip failed: original={progress!r}, deserialized={deserialized!r}"
        )

    @given(progress=st_progress_file())
    @settings(max_examples=100)
    def test_valid_dicts_validate_cleanly(self, progress):
        """Property 2: Valid Dicts Validate Cleanly.

        For any valid progress file dict, validate_progress_schema returns an
        empty error list.

        Validates: Requirements 2.1, 5.2
        """
        errors = validate_progress_schema(progress)
        assert errors == [], (
            f"Expected zero errors for valid dict, got: {errors}\nDict: {progress!r}"
        )

    @given(data=st_corrupted_progress_file())
    @settings(max_examples=100)
    def test_corrupted_dicts_are_detected(self, data):
        """Property 3: Corrupted Dicts Are Detected.

        For any corrupted progress file dict, validate_progress_schema returns
        a non-empty error list identifying the corrupted field.

        Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 5.3
        """
        corrupted_dict, field_name = data
        errors = validate_progress_schema(corrupted_dict)
        assert len(errors) > 0, (
            f"Expected errors for corrupted field '{field_name}', got none.\n"
            f"Dict: {corrupted_dict!r}"
        )
        # At least one error should mention the corrupted field
        error_text = " ".join(errors)
        assert field_name in error_text, (
            f"Expected error mentioning '{field_name}', got: {errors}"
        )

    @given(progress=st_progress_file(), fields_to_remove=st_optional_field_subset())
    @settings(max_examples=100)
    def test_backward_compatibility_under_field_removal(self, progress, fields_to_remove):
        """Property 4: Backward Compatibility Under Field Removal.

        For any valid progress file dict with optional fields removed,
        validate_progress_schema returns an empty error list.

        Validates: Requirements 2.7, 3.1, 3.2
        """
        for field in fields_to_remove:
            progress.pop(field, None)
        errors = validate_progress_schema(progress)
        assert errors == [], (
            f"Expected zero errors after removing {fields_to_remove}, got: {errors}\n"
            f"Dict: {progress!r}"
        )
