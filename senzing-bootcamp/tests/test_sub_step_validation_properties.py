"""Property-based tests for sub-step identifier validation.

Feature: mid-module-session-persistence
Covers Property 2 (valid identifiers pass) and Property 3 (invalid identifiers fail).
"""

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


@st.composite
def st_valid_sub_step(draw):
    """Generate a valid sub-step identifier: int, dotted string, or lettered string."""
    choice = draw(st.sampled_from(["int", "dotted", "lettered"]))
    if choice == "int":
        return draw(st.integers(min_value=1, max_value=30))
    elif choice == "dotted":
        parent = draw(st.integers(min_value=1, max_value=12))
        sub = draw(st.integers(min_value=1, max_value=20))
        return f"{parent}.{sub}"
    else:
        parent = draw(st.integers(min_value=1, max_value=12))
        letter = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
        return f"{parent}{letter}"


@st.composite
def st_invalid_current_step(draw):
    """Generate an invalid current_step value that should fail validation.

    Generates values that are NOT valid per the schema: strings that don't
    match any recognized sub-step format, and non-int/str/None types.
    Note: negative integers are valid (the schema accepts any int), so they
    are excluded from this strategy.
    """
    choice = draw(st.sampled_from([
        "empty", "no_digits", "special_chars", "nested_object",
        "multi_letter", "nested_dotted",
    ]))
    if choice == "empty":
        return ""
    elif choice == "no_digits":
        return draw(st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=5,
        ))
    elif choice == "special_chars":
        return draw(st.text(
            alphabet=st.characters(whitelist_categories=("P", "S")),
            min_size=1,
            max_size=5,
        ))
    elif choice == "nested_object":
        return {"nested": True}
    elif choice == "multi_letter":
        parent = draw(st.integers(min_value=1, max_value=12))
        letters = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=2, max_size=4))
        return f"{parent}{letters}"
    else:  # nested_dotted — e.g., "5.3.1"
        a = draw(st.integers(min_value=1, max_value=12))
        b = draw(st.integers(min_value=1, max_value=20))
        c = draw(st.integers(min_value=1, max_value=20))
        return f"{a}.{b}.{c}"


# ---------------------------------------------------------------------------
# Property 2: Valid Sub-Step Identifiers Pass Schema Validation
# ---------------------------------------------------------------------------


class TestValidSubStepIdentifiersPassValidation:
    """Property 2: Valid Sub-Step Identifiers Pass Schema Validation.

    Validates: Requirements 2.1, 2.2, 2.4, 9.1, 9.2
    """

    @given(step_value=st_valid_sub_step())
    @settings(max_examples=10)
    def test_valid_sub_step_as_current_step(self, step_value):
        """Valid sub-step identifiers produce zero validation errors as current_step."""
        data = {
            "current_step": step_value,
            "step_history": {
                "5": {
                    "last_completed_step": step_value
                        if isinstance(step_value, (int, str)) else 1,
                    "updated_at": "2026-06-15T14:30:00+00:00",
                }
            },
        }
        errors = validate_progress_schema(data)
        assert errors == [], (
            f"Expected zero errors for valid sub-step {step_value!r}, got: {errors}"
        )

    @given(step_value=st_valid_sub_step())
    @settings(max_examples=10)
    def test_valid_sub_step_as_last_completed_step(self, step_value):
        """Valid sub-step identifiers produce zero errors as last_completed_step."""
        data = {
            "step_history": {
                "3": {
                    "last_completed_step": step_value,
                    "updated_at": "2026-06-15T14:30:00+00:00",
                }
            },
        }
        errors = validate_progress_schema(data)
        assert errors == [], (
            f"Expected zero errors for last_completed_step {step_value!r}, got: {errors}"
        )


# ---------------------------------------------------------------------------
# Property 3: Invalid Current-Step Values Fail Validation
# ---------------------------------------------------------------------------


class TestInvalidCurrentStepValuesFailValidation:
    """Property 3: Invalid Current-Step Values Fail Validation.

    Validates: Requirements 2.3, 9.3
    """

    @given(step_value=st_invalid_current_step())
    @settings(max_examples=10)
    def test_invalid_current_step_produces_errors(self, step_value):
        """Invalid current_step values produce at least one validation error."""
        data = {"current_step": step_value}
        errors = validate_progress_schema(data)
        assert len(errors) >= 1, (
            f"Expected at least one error for invalid current_step {step_value!r}, "
            f"got zero errors"
        )
