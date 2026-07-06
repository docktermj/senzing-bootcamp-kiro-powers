"""Property-based tests for the write_policy_gate_auto_approve merge semantics.

Feature: auto-approve-write-policy-gate

The feature is steering-content only: there is no runtime merge script. The
onboarding agent records the decision under the dedicated
``write_policy_gate_auto_approve`` key using the power's documented
"merge, don't clobber" convention (design.md §"Preferences key" / Correctness
Property 1 and Property 4). This module provides a small *reference* merge
helper that mirrors that documented behavior and property-tests its invariants:

  * Merge preserves every other key/value and sets exactly the target value
    (Req 4.3, Property 1).
  * A missing file is created with only the new key (Req 4.5, Property 4).
  * Malformed YAML is never clobbered — the original bytes are left untouched
    (Req 4.7, Property 4).

The reference helper reuses the production YAML round-trip (``parse_yaml`` /
``_serialize_preferences`` from ``preferences_utils``) so the model matches how
the power actually reads and writes preference files.

Requirements: 4.3, 4.5, 4.7
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import _serialize_preferences, parse_yaml

# The dedicated key the onboarding decision is recorded under.
TARGET_KEY = "write_policy_gate_auto_approve"

# The two distinct, resolved decision values (design Data Models).
DECISION_VALUES = ("accepted", "declined")


# ---------------------------------------------------------------------------
# Reference merge helper (models the documented "merge, don't clobber" rule)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MergeResult:
    """Outcome of a reference merge.

    Attributes:
        success: True when the decision was recorded (or the file created).
        created: True when the file did not exist and was created fresh.
        error: A human-readable reason when ``success`` is False.
    """

    success: bool
    created: bool = False
    error: str | None = None


def merge_auto_approve_decision(path: Path | str, value: str) -> MergeResult:
    """Record ``value`` under ``TARGET_KEY``, preserving all other content.

    Mirrors the onboarding agent's documented merge semantics:

    * File missing -> create it containing only ``TARGET_KEY`` (Req 4.5).
    * File present and valid -> set only ``TARGET_KEY``, leaving every other
      key and value intact (Req 4.3).
    * File present but unparseable -> do not overwrite; the original bytes are
      preserved and a failure is reported (Req 4.7).

    Args:
        path: Path to the preferences YAML file.
        value: The decision to record (``accepted`` or ``declined``).

    Returns:
        A :class:`MergeResult` describing what happened.
    """
    path = Path(path)

    if not path.exists():
        path.write_text(_serialize_preferences({TARGET_KEY: value}), encoding="utf-8")
        return MergeResult(success=True, created=True)

    original = path.read_text(encoding="utf-8")
    try:
        existing = parse_yaml(original) if original.strip() else {}
    except ValueError as exc:
        # Malformed YAML: never clobber the user's file.
        return MergeResult(success=False, error=f"unparseable: {exc}")

    existing[TARGET_KEY] = value
    path.write_text(_serialize_preferences(existing), encoding="utf-8")
    return MergeResult(success=True)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_IDENTIFIER = st.text(
    alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_"),
    min_size=1,
    max_size=15,
)

# Safe string values: letters/digits/underscore/hyphen, non-empty. The
# production serializer quotes anything ambiguous, so these round-trip cleanly.
_SAFE_STR = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"), whitelist_characters="_-"
    ),
    min_size=1,
    max_size=20,
)


def st_scalar():
    """Draw a scalar preference value that round-trips through the serializer."""
    return st.one_of(
        _SAFE_STR,
        st.integers(min_value=0, max_value=9999),
        st.booleans(),
        st.none(),
    )


@st.composite
def st_preference_map(draw) -> dict:
    """Draw an arbitrary valid preference map that excludes ``TARGET_KEY``.

    Produces flat scalar entries plus optional nested flat dicts and lists of
    scalars, mirroring the shapes the real preferences file uses. The target
    key is never included so merge behavior is observed against a clean base.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A dict of preference keys to round-trip-safe values.
    """
    keys = draw(
        st.lists(
            _IDENTIFIER.filter(lambda k: k != TARGET_KEY),
            min_size=0,
            max_size=6,
            unique=True,
        )
    )
    result: dict = {}
    for key in keys:
        shape = draw(st.sampled_from(("scalar", "scalar", "list", "nested")))
        if shape == "scalar":
            result[key] = draw(st_scalar())
        elif shape == "list":
            result[key] = draw(st.lists(_SAFE_STR, min_size=0, max_size=4))
        else:  # nested flat dict
            sub_keys = draw(
                st.lists(_IDENTIFIER, min_size=1, max_size=3, unique=True)
            )
            result[key] = {sk: draw(st_scalar()) for sk in sub_keys}
    return result


@st.composite
def st_malformed_yaml(draw) -> str:
    """Draw YAML text that ``parse_yaml`` rejects (unexpected top-level indent).

    An indented key/value line at the top level triggers a ValueError in the
    minimal parser, standing in for a corrupt/unparseable preferences file.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        Malformed YAML text.
    """
    key = draw(_IDENTIFIER)
    value = draw(_SAFE_STR)
    indent = " " * draw(st.integers(min_value=1, max_value=8))
    prefix = draw(st.lists(st.sampled_from(["", "# comment"]), min_size=0, max_size=3))
    return "\n".join(prefix + [f"{indent}{key}: {value}"])


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestPreferenceMergeProperties:
    """Property-based tests for the write_policy_gate_auto_approve merge.

    **Validates: Requirements 4.3, 4.5, 4.7**
    """

    @given(base=st_preference_map(), value=st.sampled_from(DECISION_VALUES))
    def test_merge_preserves_other_keys_and_sets_target(
        self, base: dict, value: str, tmp_path_factory
    ):
        """Property 1: merge sets only the target key and preserves the rest.

        For any pre-existing valid preference map, recording a decision sets
        ``write_policy_gate_auto_approve`` to exactly the target value while
        every other key and its value are preserved.

        **Validates: Requirements 4.3**
        """
        path = tmp_path_factory.mktemp("prefs") / "bootcamp_preferences.yaml"
        path.write_text(_serialize_preferences(base), encoding="utf-8")

        result = merge_auto_approve_decision(path, value)
        assert result.success and not result.created

        merged = parse_yaml(path.read_text(encoding="utf-8"))

        # Target key set to exactly the recorded value.
        assert merged[TARGET_KEY] == value

        # Every other key and value preserved unchanged.
        merged_without_target = {k: v for k, v in merged.items() if k != TARGET_KEY}
        assert merged_without_target == base, (
            f"Non-target content changed.\nBase: {base!r}\n"
            f"Merged (minus target): {merged_without_target!r}"
        )

    @given(value=st.sampled_from(DECISION_VALUES))
    def test_missing_file_created_with_only_target_key(
        self, value: str, tmp_path_factory
    ):
        """Property 4 (create): a missing file is created with only the key.

        When the preferences file does not exist, recording a decision creates
        it containing solely ``write_policy_gate_auto_approve`` set to the value.

        **Validates: Requirements 4.5**
        """
        path = tmp_path_factory.mktemp("prefs") / "bootcamp_preferences.yaml"
        assert not path.exists()

        result = merge_auto_approve_decision(path, value)
        assert result.success and result.created
        assert path.exists()

        created = parse_yaml(path.read_text(encoding="utf-8"))
        assert created == {TARGET_KEY: value}

    @given(malformed=st_malformed_yaml(), value=st.sampled_from(DECISION_VALUES))
    def test_malformed_yaml_is_not_clobbered(
        self, malformed: str, value: str, tmp_path_factory
    ):
        """Property 4 (no clobber): unparseable content is left untouched.

        When the preferences file cannot be parsed, recording a decision does
        not overwrite it; the original bytes are preserved and the merge reports
        failure.

        **Validates: Requirements 4.7**
        """
        # Confirm the generated content is genuinely unparseable.
        try:
            parse_yaml(malformed)
            assume(False)  # parseable after all — discard this example
        except ValueError:
            pass

        path = tmp_path_factory.mktemp("prefs") / "bootcamp_preferences.yaml"
        path.write_bytes(malformed.encode("utf-8"))
        before = path.read_bytes()

        result = merge_auto_approve_decision(path, value)

        assert not result.success
        assert path.read_bytes() == before, "Malformed file was clobbered"
