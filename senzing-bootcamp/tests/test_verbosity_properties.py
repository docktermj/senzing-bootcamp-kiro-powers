"""Property-based tests for verbosity.py using Hypothesis.

Feature: bootcamp-verbosity-control
"""

import sys
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from verbosity import (
    VerbosityPreferences,
    CATEGORIES,
    PRESETS,
    NL_TERM_MAP,
    resolve_preset,
    serialize_preferences,
    deserialize_preferences,
    adjust_category,
    detect_preset,
    match_nl_term,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_preset_name():
    """Strategy for valid preset names."""
    return st.sampled_from(["concise", "standard", "detailed"])


def st_category_level():
    """Strategy for valid category levels (1-3)."""
    return st.integers(min_value=1, max_value=3)


def st_categories():
    """Strategy for a complete categories dict with all five categories."""
    return st.fixed_dictionaries({cat: st_category_level() for cat in CATEGORIES})


@st.composite
def st_verbosity_preferences(draw):
    """Strategy that builds a valid VerbosityPreferences instance."""
    preset = draw(st.sampled_from(["concise", "standard", "detailed", "custom"]))
    categories = draw(st_categories())
    return VerbosityPreferences(preset=preset, categories=categories)


def st_delta():
    """Strategy for adjustment deltas (+1 or -1)."""
    return st.sampled_from([+1, -1])


def st_non_matching_term():
    """Strategy for strings that are NOT keys in NL_TERM_MAP."""
    return st.text(min_size=1, max_size=50).filter(
        lambda t: t.lower().strip() not in NL_TERM_MAP
    )


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestProperty1SerializationRoundTrip:
    """Property 1: Preferences Serialization Round-Trip.

    Feature: bootcamp-verbosity-control
    Property 1: Preferences Serialization Round-Trip

    Validates: Requirements 2.5, 3.3, 4.2, 5.4, 6.2
    """

    @given(prefs=st_verbosity_preferences())
    @settings(max_examples=10)
    def test_round_trip_preserves_values(self, prefs):
        """serialize then deserialize produces identical preset and categories."""
        yaml_text = serialize_preferences(prefs)
        restored = deserialize_preferences(yaml_text)
        assert restored.preset == prefs.preset
        assert restored.categories == prefs.categories


class TestProperty2CategoryLevelClamping:
    """Property 2: Category Level Adjustment Clamping.

    Feature: bootcamp-verbosity-control
    Property 2: Category Level Adjustment Clamping

    Validates: Requirements 5.1, 5.2
    """

    @given(
        prefs=st_verbosity_preferences(),
        category=st.sampled_from(CATEGORIES),
        delta=st_delta(),
    )
    @settings(max_examples=10)
    def test_adjusted_level_equals_clamped_value(self, prefs, category, delta):
        """adjust_category produces clamp(original + delta, 1, 3) for the target category."""
        original_level = prefs.categories[category]
        expected = max(1, min(3, original_level + delta))
        result = adjust_category(prefs, category, delta)
        assert result.categories[category] == expected

    @given(
        prefs=st_verbosity_preferences(),
        category=st.sampled_from(CATEGORIES),
        delta=st_delta(),
    )
    @settings(max_examples=10)
    def test_other_categories_unchanged(self, prefs, category, delta):
        """adjust_category leaves all other category levels unchanged."""
        result = adjust_category(prefs, category, delta)
        for cat in CATEGORIES:
            if cat != category:
                assert result.categories[cat] == prefs.categories[cat]

class TestProperty3PresetDetectionAfterAdjustment:
    """Property 3: Preset Detection After Adjustment.

    Feature: bootcamp-verbosity-control
    Property 3: Preset Detection After Adjustment

    Validates: Requirements 5.5
    """

    @given(
        preset_name=st_preset_name(),
        category=st.sampled_from(CATEGORIES),
        delta=st_delta(),
    )
    @settings(max_examples=10)
    def test_preset_detection_after_single_adjustment(self, preset_name, category, delta):
        """After adjusting one category from a named preset, detect_preset returns
        the correct preset name or 'custom'."""
        prefs = resolve_preset(preset_name)
        adjusted = adjust_category(prefs, category, delta)
        detected = detect_preset(adjusted.categories)

        # Check if the adjusted categories match any named preset
        matches_named = False
        for name, levels in PRESETS.items():
            if adjusted.categories == levels:
                matches_named = True
                assert detected == name
                break

        if not matches_named:
            assert detected == "custom"

class TestProperty4UnrecognizedTermRejection:
    """Property 4: Unrecognized Natural Language Term Rejection.

    Feature: bootcamp-verbosity-control
    Property 4: Unrecognized Natural Language Term Rejection

    Validates: Requirements 5.6
    """

    @given(term=st_non_matching_term())
    @settings(max_examples=10)
    def test_non_matching_term_returns_none(self, term):
        """Any string not in NL_TERM_MAP returns None from match_nl_term."""
        assert match_nl_term(term) is None

    @given(term=st.sampled_from(sorted(NL_TERM_MAP.keys())))
    @settings(max_examples=10)
    def test_matching_term_returns_correct_category(self, term):
        """Any key in NL_TERM_MAP returns the correct category from match_nl_term."""
        expected = NL_TERM_MAP[term]
        assert match_nl_term(term) == expected
