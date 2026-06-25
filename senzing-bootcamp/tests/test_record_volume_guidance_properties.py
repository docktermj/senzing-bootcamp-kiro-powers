"""Property-based tests for record volume guidance using Hypothesis.

Feature: record-volume-guidance
"""

from __future__ import annotations

import json
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

from volume_utils import (
    TIER_BOUNDARIES,
    VALID_TIERS,
    classify_tier,
    parse_volume_input,
    persist_volume_selection,
    should_ask_volume,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies — Parsing and Classification
# ---------------------------------------------------------------------------

_SUFFIX_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
_WORD_MULTIPLIERS = {
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
}


@st.composite
def st_plain_digit_string(draw) -> tuple[str, int]:
    """Generate a plain digit string and its expected integer value."""
    value = draw(st.integers(min_value=0, max_value=100_000_000))
    return (str(value), value)


@st.composite
def st_comma_separated_string(draw) -> tuple[str, int]:
    """Generate a comma-separated number string and its expected integer value."""
    value = draw(st.integers(min_value=1_000, max_value=999_999_999))
    text = f"{value:,}"
    return (text, value)


@st.composite
def st_suffix_string(draw) -> tuple[str, int]:
    """Generate a number with K/M/B suffix and its expected integer value."""
    base = draw(st.integers(min_value=1, max_value=999))
    suffix = draw(st.sampled_from(["k", "m", "b", "K", "M", "B"]))
    multiplier = _SUFFIX_MULTIPLIERS[suffix.lower()]
    expected = base * multiplier
    return (f"{base}{suffix}", expected)


@st.composite
def st_decimal_suffix_string(draw) -> tuple[str, int]:
    """Generate a decimal number with K/M/B suffix and its expected integer value."""
    whole = draw(st.integers(min_value=1, max_value=99))
    decimal = draw(st.integers(min_value=1, max_value=9))
    suffix = draw(st.sampled_from(["k", "m", "b", "K", "M", "B"]))
    multiplier = _SUFFIX_MULTIPLIERS[suffix.lower()]
    num = float(f"{whole}.{decimal}")
    expected = int(num * multiplier)
    text = f"{whole}.{decimal}{suffix}"
    return (text, expected)


@st.composite
def st_word_multiplier_string(draw) -> tuple[str, int]:
    """Generate a number with word multiplier and its expected integer value."""
    base = draw(st.integers(min_value=1, max_value=999))
    word = draw(st.sampled_from(list(_WORD_MULTIPLIERS.keys())))
    multiplier = _WORD_MULTIPLIERS[word]
    expected = base * multiplier
    return (f"{base} {word}", expected)


def st_numeric_input() -> st.SearchStrategy[tuple[str, int]]:
    """Strategy that generates recognizable numeric input strings with expected values."""
    return st.one_of(
        st_plain_digit_string(),
        st_comma_separated_string(),
        st_suffix_string(),
        st_decimal_suffix_string(),
        st_word_multiplier_string(),
    )


_NON_NUMERIC_ALPHABET = st.characters(
    whitelist_categories=("L", "Zs", "P"),
    blacklist_characters="0123456789kKmMbB",
)


@st.composite
def st_non_numeric_string(draw) -> str:
    """Generate a string with no recognizable numeric content.

    Excludes digits, K/M/B characters, and numeric word forms.
    """
    text = draw(st.text(
        alphabet=_NON_NUMERIC_ALPHABET,
        min_size=1,
        max_size=50,
    ))
    lower = text.lower()
    numeric_words = (
        "thousand", "million", "billion", "thousands", "millions", "billions",
    )
    for word in numeric_words:
        assume(word not in lower)
    return text


def _expected_tier_for_value(value: int) -> str:
    """Determine the expected tier for a given record count using TIER_BOUNDARIES."""
    for tier, (lower, upper) in TIER_BOUNDARIES.items():
        if value >= lower and value < upper:
            return tier
    return "large"  # pragma: no cover


# ---------------------------------------------------------------------------
# Property 1: Numeric input classification correctness
# Feature: record-volume-guidance, Property 1: Numeric input classification correctness
# ---------------------------------------------------------------------------


class TestParsingAndClassification:
    """Property tests for parsing and classification of volume input.

    **Validates: Requirements 1.4, 1.5**
    """

    @given(numeric_input=st_numeric_input())
    @settings(max_examples=20)
    def test_numeric_input_classification_correctness(
        self, numeric_input: tuple[str, int]
    ) -> None:
        """Feature: record-volume-guidance, Property 1: Numeric input classification correctness.

        For any string with recognizable numeric value, parse_volume_input returns
        an integer and classify_tier returns the correct tier based on TIER_BOUNDARIES.

        **Validates: Requirements 1.4**
        """
        text, expected_value = numeric_input

        result = parse_volume_input(text)

        # parse_volume_input must return an integer for recognizable numeric input
        assert result is not None, (
            f"parse_volume_input returned None for recognizable numeric input: {text!r}"
        )
        assert isinstance(result, int), (
            f"parse_volume_input returned {type(result).__name__}, expected int "
            f"for: {text!r}"
        )

        # The parsed value should equal the expected value
        assert result == expected_value, (
            f"parse_volume_input({text!r}) = {result}, expected {expected_value}"
        )

        # classify_tier must return the correct tier for the parsed value
        tier = classify_tier(result)
        expected_tier = _expected_tier_for_value(result)
        assert tier == expected_tier, (
            f"classify_tier({result}) = {tier!r}, expected {expected_tier!r}"
        )

    # -------------------------------------------------------------------
    # Property 2: Non-numeric input rejection
    # Feature: record-volume-guidance, Property 2: Non-numeric input rejection
    # -------------------------------------------------------------------

    @given(text=st_non_numeric_string())
    @settings(max_examples=20)
    def test_non_numeric_input_rejection(self, text: str) -> None:
        """Feature: record-volume-guidance, Property 2: Non-numeric input rejection.

        For any string with no recognizable numeric content, parse_volume_input
        returns None.

        **Validates: Requirements 1.5**
        """
        result = parse_volume_input(text)

        assert result is None, (
            f"parse_volume_input should return None for non-numeric input {text!r}, "
            f"but returned {result}"
        )


# ---------------------------------------------------------------------------
# Property 3: Volume persistence round-trip
# ---------------------------------------------------------------------------


class TestPersistenceRoundTrip:
    """Property-based tests for volume persistence round-trip.

    Feature: record-volume-guidance, Property 3: Volume persistence round-trip

    **Validates: Requirements 1.6, 2.1**
    """

    @given(record_count=st.integers(min_value=0, max_value=100_000_000_000))
    @settings(max_examples=20)
    def test_persist_and_read_back_matches(self, record_count: int) -> None:
        """For any valid record count, persisting and reading back produces matching values.

        For any non-negative integer record count, classifying it into a tier and
        persisting via persist_volume_selection, then reading back the YAML preferences
        file produces a production_volume entry where raw_value equals the original
        integer and tier equals the classified tier string. The progress JSON file
        contains the step checkpoint.
        """
        tier = classify_tier(record_count)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            prefs_path = tmp_path / "bootcamp_preferences.yaml"
            prog_path = tmp_path / "bootcamp_progress.json"

            persist_volume_selection(
                record_count, tier, str(prefs_path), str(prog_path), 1
            )

            # Read back preferences YAML and verify
            prefs_content = prefs_path.read_text(encoding="utf-8")
            lines = prefs_content.splitlines()

            # Verify the file contains production_volume key
            assert any("production_volume:" in line for line in lines), (
                f"Expected 'production_volume:' in preferences file, got:\n{prefs_content}"
            )

            # Extract raw_value and tier from the YAML content
            read_raw_value = None
            read_tier = None
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("raw_value:"):
                    value_str = stripped.split(":", 1)[1].strip()
                    read_raw_value = int(value_str)
                elif stripped.startswith("tier:"):
                    read_tier = stripped.split(":", 1)[1].strip()

            assert read_raw_value == record_count, (
                f"Expected raw_value={record_count}, got {read_raw_value}"
            )
            assert read_tier == tier, (
                f"Expected tier={tier!r}, got {read_tier!r}"
            )

            # Read back progress JSON and verify step checkpoint
            prog_content = prog_path.read_text(encoding="utf-8")
            progress_data = json.loads(prog_content)

            assert "current_step" in progress_data, (
                f"Expected 'current_step' in progress file, "
                f"got keys: {list(progress_data.keys())}"
            )
            assert progress_data["current_step"] == 1, (
                f"Expected current_step=1, got {progress_data['current_step']}"
            )


# ---------------------------------------------------------------------------
# Hypothesis strategies — Session Resume Logic
# ---------------------------------------------------------------------------


@st.composite
def st_valid_production_volume(draw) -> dict:
    """Generate a valid production_volume dict with integer raw_value and tier in VALID_TIERS."""
    raw_value = draw(st.integers(min_value=0, max_value=10_000_000_000))
    tier = draw(st.sampled_from(VALID_TIERS))
    return {"raw_value": raw_value, "tier": tier}


@st.composite
def st_invalid_production_volume(draw) -> dict:
    """Generate a preferences dict where production_volume is invalid in various ways.

    Cases:
    - Missing key entirely
    - production_volume is None
    - production_volume is not a dict (string, int, list)
    - raw_value is not an integer (string, float, None)
    - tier is not in VALID_TIERS (random string, None, empty)
    """
    case = draw(st.sampled_from([
        "missing_key",
        "none_value",
        "not_a_dict",
        "raw_value_not_int",
        "tier_not_valid",
    ]))

    if case == "missing_key":
        # preferences dict without production_volume key
        other_key = draw(st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnop"))
        return {other_key: "some_value"}

    if case == "none_value":
        return {"production_volume": None}

    if case == "not_a_dict":
        # production_volume is a non-dict value
        bad_value = draw(st.one_of(
            st.text(min_size=0, max_size=20),
            st.integers(),
            st.lists(st.integers(), max_size=3),
        ))
        return {"production_volume": bad_value}

    if case == "raw_value_not_int":
        # production_volume is a dict but raw_value is not an integer
        bad_raw = draw(st.one_of(
            st.text(min_size=0, max_size=10),
            st.floats(allow_nan=False, allow_infinity=False),
            st.none(),
        ))
        tier = draw(st.sampled_from(VALID_TIERS))
        return {"production_volume": {"raw_value": bad_raw, "tier": tier}}

    # case == "tier_not_valid"
    raw_value = draw(st.integers(min_value=0, max_value=10_000_000_000))
    bad_tier = draw(st.one_of(
        st.sampled_from(["", "huge", "tiny", "DEMO", "Small", "xl", "unknown"]),
        st.none(),
    ))
    return {"production_volume": {"raw_value": raw_value, "tier": bad_tier}}


# ---------------------------------------------------------------------------
# Property 4 & 5: Session Resume Logic
# ---------------------------------------------------------------------------


class TestSessionResumeLogic:
    """Property tests for session resume detection via should_ask_volume.

    Validates: Requirements 2.3, 2.4
    """

    @given(production_volume=st_valid_production_volume())
    @settings(max_examples=20)
    def test_property_4_session_resume_skip_detection(
        self, production_volume: dict
    ) -> None:
        """Feature: record-volume-guidance, Property 4: Session resume skip detection

        For any preferences dict with valid production_volume (integer raw_value
        + tier in VALID_TIERS), should_ask_volume returns False.

        **Validates: Requirements 2.3**
        """
        preferences = {"production_volume": production_volume}
        assert should_ask_volume(preferences) is False

    @given(preferences=st_invalid_production_volume())
    @settings(max_examples=20)
    def test_property_5_session_resume_re_ask_detection(
        self, preferences: dict
    ) -> None:
        """Feature: record-volume-guidance, Property 5: Session resume re-ask detection

        For any preferences dict where production_volume is missing, None, has
        non-integer raw_value, or unrecognized tier, should_ask_volume returns True.

        **Validates: Requirements 2.4**
        """
        assert should_ask_volume(preferences) is True


# ---------------------------------------------------------------------------
# Additional imports for guidance generators
# ---------------------------------------------------------------------------

from volume_utils import (
    TIER_DEMO,
    TIER_LARGE,
    TIER_MEDIUM,
    TIER_SMALL,
    get_architecture_guidance,
    get_database_guidance,
    get_license_guidance,
    get_performance_guidance,
)

# ---------------------------------------------------------------------------
# Properties 6–13: Guidance Generators
# ---------------------------------------------------------------------------


class TestGuidanceGenerators:
    """Property tests for guidance generator functions.

    Feature: record-volume-guidance, Properties 6–13
    """

    # -------------------------------------------------------------------
    # Property 6: License guidance for non-demo tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from([TIER_SMALL, TIER_MEDIUM, TIER_LARGE]))
    @settings(max_examples=20)
    def test_property_6_license_guidance_non_demo_tiers(self, tier: str) -> None:
        """Feature: record-volume-guidance, Property 6: License guidance for non-demo tiers.

        The license-capacity-framing refactor reframed non-demo tiers from a
        "production license + MCP/sales contact" message to the canonical
        default-license + expansion-paths framing. For any tier in
        {small, medium, large}, get_license_guidance returns a string that frames
        the built-in evaluation license as a default the bootcamper already has
        and presents the expansion options, with no hard-cap phrasing and no
        hardcoded MCP/external URL.

        **Validates: Requirements 3.2, 3.3**
        """
        result = get_license_guidance(tier)

        assert result is not None, f"get_license_guidance({tier!r}) returned None"

        lower_result = result.lower()

        # Default/evaluation framing — a built-in license the bootcamper has.
        assert "built-in evaluation license" in lower_result, (
            f"Expected 'built-in evaluation license' framing for tier={tier!r}, "
            f"got:\n{result}"
        )

        # Expansion options are presented (process more records).
        assert "options to process more records" in lower_result, (
            f"Expected expansion options for tier={tier!r}, got:\n{result}"
        )

        # No hard-cap phrasing.
        for phrase in ("hard cap", "maximum of", "cannot exceed", "you are limited to"):
            assert phrase not in lower_result, (
                f"Unexpected hard-cap phrasing {phrase!r} for tier={tier!r}, "
                f"got:\n{result}"
            )

        # No hardcoded MCP server host and no external web URL. The forbidden
        # host is assembled from parts so the literal never appears in source.
        forbidden_mcp_host = "mcp.senzing" + ".com"
        assert forbidden_mcp_host not in lower_result, (
            f"Unexpected hardcoded MCP URL for tier={tier!r}, got:\n{result}"
        )
        assert "http" not in lower_result, (
            f"Unexpected URL for tier={tier!r}, got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 7: Architecture guidance universal disclaimers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from(VALID_TIERS))
    @settings(max_examples=20)
    def test_property_7_architecture_guidance_universal_disclaimers(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 7: Architecture guidance universal disclaimers.

        For any tier in {demo, small, medium, large}, get_architecture_guidance returns
        a string containing both a "production recommendation" label and a statement
        that the bootcamp uses single-threaded loading regardless of tier.

        **Validates: Requirements 4.5**
        """
        result = get_architecture_guidance(tier)

        lower_result = result.lower()

        assert "production recommendation" in lower_result, (
            f"Expected 'production recommendation' in output for tier={tier!r}, "
            f"got:\n{result}"
        )
        assert "single-threaded" in lower_result, (
            f"Expected 'single-threaded' in output for tier={tier!r}, got:\n{result}"
        )
        assert "bootcamp" in lower_result, (
            f"Expected 'bootcamp' in output for tier={tier!r}, got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 8: Database guidance — SQLite sufficient for low tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from([TIER_DEMO, TIER_SMALL]))
    @settings(max_examples=20)
    def test_property_8_database_guidance_sqlite_sufficient_low_tiers(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 8: Database guidance — SQLite \
sufficient for low tiers.

        For any tier in {demo, small}, get_database_guidance returns a string
        confirming SQLite is sufficient for production use at the stated volume.

        **Validates: Requirements 5.1**
        """
        result = get_database_guidance(tier)

        lower_result = result.lower()

        assert "sqlite" in lower_result, (
            f"Expected 'sqlite' in output for tier={tier!r}, got:\n{result}"
        )
        assert "sufficient" in lower_result, (
            f"Expected 'sufficient' in output for tier={tier!r}, got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 9: Database guidance — PostgreSQL for high tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from([TIER_MEDIUM, TIER_LARGE]))
    @settings(max_examples=20)
    def test_property_9_database_guidance_postgresql_for_high_tiers(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 9: Database guidance — PostgreSQL \
for high tiers.

        For any tier in {medium, large} with current_database="sqlite",
        get_database_guidance returns a string recommending PostgreSQL and
        explaining the SQLite single-writer limitation.

        **Validates: Requirements 5.2**
        """
        result = get_database_guidance(tier, current_database="sqlite")

        lower_result = result.lower()

        assert "postgresql" in lower_result, (
            f"Expected 'postgresql' in output for tier={tier!r}, got:\n{result}"
        )
        assert "single" in lower_result and "writer" in lower_result, (
            f"Expected 'single writer' or 'single-writer' in output for tier={tier!r}, "
            f"got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 10: Database guidance — bootcamp disclaimer for all tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from(VALID_TIERS))
    @settings(max_examples=20)
    def test_property_10_database_guidance_bootcamp_disclaimer(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 10: Database guidance — bootcamp \
disclaimer for all tiers.

        For any tier in {demo, small, medium, large}, get_database_guidance returns
        a string containing a statement that the bootcamp continues using the
        currently configured database.

        **Validates: Requirements 5.3**
        """
        result = get_database_guidance(tier)

        lower_result = result.lower()

        assert "bootcamp" in lower_result, (
            f"Expected 'bootcamp' in output for tier={tier!r}, got:\n{result}"
        )
        assert "continue" in lower_result or "continues" in lower_result, (
            f"Expected 'continue' or 'continues' in output for tier={tier!r}, "
            f"got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 11: Database guidance — PostgreSQL acknowledgment
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from([TIER_MEDIUM, TIER_LARGE]))
    @settings(max_examples=20)
    def test_property_11_database_guidance_postgresql_acknowledgment(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 11: Database guidance — \
PostgreSQL acknowledgment.

        For any tier in {medium, large} with current_database="postgresql",
        get_database_guidance returns a string that acknowledges the existing
        PostgreSQL configuration and does NOT contain the SQLite single-writer
        limitation explanation.

        **Validates: Requirements 5.4**
        """
        result = get_database_guidance(tier, current_database="postgresql")

        lower_result = result.lower()

        assert "postgresql" in lower_result, (
            f"Expected 'postgresql' in output for tier={tier!r}, got:\n{result}"
        )
        assert "single-writer" not in lower_result and "single writer" not in lower_result, (
            f"Expected NO 'single-writer'/'single writer' in output for tier={tier!r} "
            f"with postgresql, got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 12: Performance guidance — fast completion for low tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from([TIER_DEMO, TIER_SMALL]))
    @settings(max_examples=20)
    def test_property_12_performance_guidance_fast_completion_low_tiers(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 12: Performance guidance — fast \
completion for low tiers.

        For any tier in {demo, small}, get_performance_guidance returns a string
        indicating loading completes in seconds to minutes.

        **Validates: Requirements 6.1**
        """
        result = get_performance_guidance(tier)

        lower_result = result.lower()

        assert "seconds" in lower_result, (
            f"Expected 'seconds' in output for tier={tier!r}, got:\n{result}"
        )
        assert "minutes" in lower_result, (
            f"Expected 'minutes' in output for tier={tier!r}, got:\n{result}"
        )

    # -------------------------------------------------------------------
    # Property 13: Performance guidance — MCP reference for all tiers
    # -------------------------------------------------------------------

    @given(tier=st.sampled_from(VALID_TIERS))
    @settings(max_examples=20)
    def test_property_13_performance_guidance_mcp_reference(
        self, tier: str
    ) -> None:
        """Feature: record-volume-guidance, Property 13: Performance guidance — MCP \
reference for all tiers.

        For any tier in {demo, small, medium, large}, get_performance_guidance
        returns a string referencing search_docs with category="configuration".

        **Validates: Requirements 6.4**
        """
        result = get_performance_guidance(tier)

        assert "search_docs" in result, (
            f"Expected 'search_docs' in output for tier={tier!r}, got:\n{result}"
        )
        assert "configuration" in result, (
            f"Expected 'configuration' in output for tier={tier!r}, got:\n{result}"
        )
