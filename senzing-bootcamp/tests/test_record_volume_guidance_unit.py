"""Unit tests for record volume guidance utility functions.

Verifies specific parsing examples, tier boundary values, and guidance content
for the volume_utils module. These are example-based assertions that complement
the property-based tests.

Feature: record-volume-guidance
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — scripts aren't packages, import via sys.path manipulation
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import pytest  # noqa: E402

from volume_utils import (  # noqa: E402
    classify_tier,
    get_architecture_guidance,
    get_license_guidance,
    get_performance_guidance,
    parse_volume_input,
)

# ---------------------------------------------------------------------------
# TestParseVolumeInput
# ---------------------------------------------------------------------------


class TestParseVolumeInput:
    """Test specific parsing examples for parse_volume_input.

    Validates: Requirements 1.4, 1.5
    """

    def test_plain_digits(self) -> None:
        """Parse plain digit string '500'."""
        assert parse_volume_input("500") == 500

    def test_suffix_m_uppercase(self) -> None:
        """Parse abbreviation '1M' as 1,000,000."""
        assert parse_volume_input("1M") == 1_000_000

    def test_word_multiplier_million(self) -> None:
        """Parse word form '10 million' as 10,000,000."""
        assert parse_volume_input("10 million") == 10_000_000

    def test_comma_separated(self) -> None:
        """Parse comma-separated '1,000,000' as 1,000,000."""
        assert parse_volume_input("1,000,000") == 1_000_000

    def test_decimal_suffix(self) -> None:
        """Parse decimal abbreviation '1.5M' as 1,500,000."""
        assert parse_volume_input("1.5M") == 1_500_000

    def test_unparseable_text_returns_none(self) -> None:
        """Non-numeric text 'hello world' returns None.

        Validates: Requirement 1.5
        """
        assert parse_volume_input("hello world") is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None.

        Validates: Requirement 1.5
        """
        assert parse_volume_input("") is None


# ---------------------------------------------------------------------------
# TestClassifyTier
# ---------------------------------------------------------------------------


class TestClassifyTier:
    """Test tier boundary values for classify_tier.

    Validates: Requirements 1.4
    """

    def test_zero_is_demo(self) -> None:
        """0 records classifies as demo tier."""
        assert classify_tier(0) == "demo"

    def test_499_is_demo(self) -> None:
        """499 records (upper boundary - 1) classifies as demo tier."""
        assert classify_tier(499) == "demo"

    def test_500_is_small(self) -> None:
        """500 records (small lower boundary) classifies as small tier."""
        assert classify_tier(500) == "small"

    def test_499999_is_small(self) -> None:
        """499,999 records (small upper boundary - 1) classifies as small tier."""
        assert classify_tier(499_999) == "small"

    def test_500000_is_medium(self) -> None:
        """500,000 records (medium lower boundary) classifies as medium tier."""
        assert classify_tier(500_000) == "medium"

    def test_9999999_is_medium(self) -> None:
        """9,999,999 records (medium upper boundary - 1) classifies as medium tier."""
        assert classify_tier(9_999_999) == "medium"

    def test_10000000_is_large(self) -> None:
        """10,000,000 records (large lower boundary) classifies as large tier."""
        assert classify_tier(10_000_000) == "large"

    def test_negative_raises_value_error(self) -> None:
        """Negative record count raises ValueError."""
        with pytest.raises(ValueError):
            classify_tier(-1)


# ---------------------------------------------------------------------------
# TestLicenseGuidance
# ---------------------------------------------------------------------------


_HARD_CAP_PHRASES = ("hard cap", "maximum of", "cannot exceed", "you are limited to")


class TestLicenseGuidance:
    """Test license guidance content for demo tier.

    Validates: Requirement 3.1

    The license-capacity-framing refactor removed the hardcoded "500-record"
    literal (capacity figures now come from the MCP server, never hardcoded).
    The demo tier now frames the built-in evaluation license as sufficient for
    the stated volume rather than asserting a fixed figure.
    """

    def test_demo_tier_frames_builtin_license_as_sufficient(self) -> None:
        """Demo tier frames the built-in evaluation license as sufficient.

        No "500-record" literal is required — the figure is sourced from the MCP
        server, not hardcoded.
        """
        result = get_license_guidance("demo")
        assert result is not None
        lower = result.lower()
        assert "built-in evaluation license" in lower
        assert "sufficient" in lower

    def test_demo_tier_no_hardcoded_figure_by_default(self) -> None:
        """Demo tier omits any hardcoded capacity figure when none is supplied."""
        result = get_license_guidance("demo")
        assert result is not None
        assert "500-record" not in result

    def test_demo_tier_no_hard_cap_phrasing(self) -> None:
        """Demo tier never presents the limit as a hard cap."""
        result = get_license_guidance("demo")
        assert result is not None
        lower = result.lower()
        for phrase in _HARD_CAP_PHRASES:
            assert phrase not in lower, f"unexpected hard-cap phrasing: {phrase!r}"

    def test_demo_tier_mentions_evaluation(self) -> None:
        """Demo tier guidance mentions 'evaluation'."""
        result = get_license_guidance("demo")
        assert result is not None
        assert "evaluation" in result


# ---------------------------------------------------------------------------
# TestArchitectureGuidance
# ---------------------------------------------------------------------------


class TestArchitectureGuidance:
    """Test architecture guidance content per tier.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """

    def test_demo_contains_single_threaded(self) -> None:
        """Demo tier recommends single-threaded loading.

        Validates: Requirement 4.1
        """
        result = get_architecture_guidance("demo")
        assert "single-threaded" in result.lower() or "Single-threaded" in result

    def test_small_contains_multi_threading(self) -> None:
        """Small tier mentions multi-threading.

        Validates: Requirement 4.2
        """
        result = get_architecture_guidance("small")
        assert "100,000" in result
        # Check for multi-threading mention (case-insensitive)
        lower = result.lower()
        assert "multi-thread" in lower or "multi thread" in lower

    def test_medium_contains_thread_pool(self) -> None:
        """Medium tier recommends thread pool.

        Validates: Requirement 4.3
        """
        result = get_architecture_guidance("medium")
        assert "thread pool" in result.lower()

    def test_medium_contains_generate_scaffold(self) -> None:
        """Medium tier references generate_scaffold MCP tool.

        Validates: Requirement 4.3
        """
        result = get_architecture_guidance("medium")
        assert "generate_scaffold" in result

    def test_large_contains_distributed(self) -> None:
        """Large tier recommends distributed architecture.

        Validates: Requirement 4.4
        """
        result = get_architecture_guidance("large")
        lower = result.lower()
        assert "distributed" in lower

    def test_large_contains_sdk_guide(self) -> None:
        """Large tier references sdk_guide MCP tool.

        Validates: Requirement 4.4
        """
        result = get_architecture_guidance("large")
        assert "sdk_guide" in result


# ---------------------------------------------------------------------------
# TestPerformanceGuidance
# ---------------------------------------------------------------------------


class TestPerformanceGuidance:
    """Test performance guidance for medium and large tiers.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_medium_contains_minutes_to_hours(self) -> None:
        """Medium tier indicates minutes to hours.

        Validates: Requirement 6.2
        """
        result = get_performance_guidance("medium")
        assert "minutes to hours" in result

    def test_medium_references_module_8(self) -> None:
        """Medium tier references Module 8.

        Validates: Requirement 6.2
        """
        result = get_performance_guidance("medium")
        assert "Module 8" in result

    def test_large_contains_hours_to_days(self) -> None:
        """Large tier indicates hours to days.

        Validates: Requirement 6.3
        """
        result = get_performance_guidance("large")
        assert "hours to days" in result

    def test_large_references_module(self) -> None:
        """Large tier references Module.

        Validates: Requirement 6.3
        """
        result = get_performance_guidance("large")
        assert "Module" in result

    def test_large_references_module_11(self) -> None:
        """Large tier references Module 11.

        Validates: Requirement 6.3
        """
        result = get_performance_guidance("large")
        assert "11" in result


# ---------------------------------------------------------------------------
# TestDefaultFallback
# ---------------------------------------------------------------------------


class TestDefaultFallback:
    """Test default fallback to demo tier for unparseable input.

    Validates: Requirement 1.7
    """

    def test_unparseable_returns_none(self) -> None:
        """Unparseable input returns None, which triggers demo default in steering."""
        assert parse_volume_input("hello world") is None

    def test_gibberish_returns_none(self) -> None:
        """Gibberish text returns None."""
        assert parse_volume_input("no numbers here at all") is None

    def test_whitespace_only_returns_none(self) -> None:
        """Whitespace-only input returns None."""
        assert parse_volume_input("   ") is None
