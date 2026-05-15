"""Property-based tests for compare_results.py using Hypothesis.

Feature: mapping-regression-testing
"""

import dataclasses
import json
import os
import string
import sys
from pathlib import Path
from string import ascii_letters, digits

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from compare_results import (
    ERStatistics,
    ComparisonResult,
    accept_baseline,
    assess_quality,
    baseline_path,
    compare,
    format_report,
    load_statistics,
    main,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_datasource_name() -> st.SearchStrategy[str]:
    """Generate datasource name strings (alphanumeric + underscores)."""
    return st.text(
        alphabet=ascii_letters + digits + "_",
        min_size=1,
        max_size=30,
    )


@st.composite
def st_er_statistics(draw):
    """Generate a random ERStatistics instance with non-negative integer counts."""
    datasource = draw(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=string.ascii_letters + string.digits + "_",
        )
    )
    entity_count = draw(st.integers(min_value=0, max_value=1_000_000))
    record_count = draw(st.integers(min_value=0, max_value=1_000_000))
    match_count = draw(st.integers(min_value=0, max_value=1_000_000))
    possible_match_count = draw(st.integers(min_value=0, max_value=1_000_000))
    relationship_count = draw(st.integers(min_value=0, max_value=1_000_000))
    captured_at = draw(st.just("2026-01-01T00:00:00Z"))

    return ERStatistics(
        datasource=datasource,
        entity_count=entity_count,
        record_count=record_count,
        match_count=match_count,
        possible_match_count=possible_match_count,
        relationship_count=relationship_count,
        captured_at=captured_at,
    )


# ---------------------------------------------------------------------------
# Property 1: Comparison produces correct deltas with complete output
# ---------------------------------------------------------------------------


class TestComparisonDeltaProperties:
    """Property tests for comparison delta correctness.

    **Validates: Requirements 1, 3**
    """

    @given(baseline=st_er_statistics(), current=st_er_statistics())
    @settings(max_examples=10)
    def test_deltas_equal_current_minus_baseline(
        self, baseline: ERStatistics, current: ERStatistics
    ) -> None:
        """For any two ERStatistics, each delta equals current - baseline."""
        result = compare(baseline, current)

        assert result.entity_delta == current.entity_count - baseline.entity_count
        assert result.record_delta == current.record_count - baseline.record_count
        assert result.match_delta == current.match_count - baseline.match_count
        assert (
            result.possible_match_delta
            == current.possible_match_count - baseline.possible_match_count
        )
        assert (
            result.relationship_delta
            == current.relationship_count - baseline.relationship_count
        )

    @given(baseline=st_er_statistics(), current=st_er_statistics())
    @settings(max_examples=10)
    def test_quality_assessment_is_valid_value(
        self, baseline: ERStatistics, current: ERStatistics
    ) -> None:
        """Quality assessment is always one of the three valid values."""
        result = compare(baseline, current)

        assert result.quality_assessment in {"improved", "degraded", "unchanged"}


# ---------------------------------------------------------------------------
# Property 2: Baseline path construction
# ---------------------------------------------------------------------------


class TestBaselinePathProperties:
    """Property tests for baseline_path() function.

    **Validates: Requirements 7**
    """

    @given(datasource=st_datasource_name())
    @settings(max_examples=10)
    def test_returns_path_object(self, datasource: str) -> None:
        """baseline_path always returns a Path object."""
        result = baseline_path(datasource)
        assert isinstance(result, Path)

    @given(datasource=st_datasource_name())
    @settings(max_examples=10)
    def test_matches_expected_pattern(self, datasource: str) -> None:
        """Result matches config/er_baseline_{datasource_lower}.json."""
        result = baseline_path(datasource)
        expected = f"config/er_baseline_{datasource.lower()}.json"
        assert str(result) == expected

    @given(datasource=st_datasource_name())
    @settings(max_examples=10)
    def test_starts_with_config(self, datasource: str) -> None:
        """Path always starts with 'config/'."""
        result = baseline_path(datasource)
        assert str(result).startswith("config/")

    @given(datasource=st_datasource_name())
    @settings(max_examples=10)
    def test_ends_with_json(self, datasource: str) -> None:
        """Path always ends with '.json'."""
        result = baseline_path(datasource)
        assert str(result).endswith(".json")





# ---------------------------------------------------------------------------
# Property 3: Incremental baseline update preserves last accepted state
# ---------------------------------------------------------------------------


class TestIncrementalBaselineProperties:
    """Property tests for incremental baseline update via accept_baseline().

    **Validates: Requirements 8**
    """

    @given(
        sequence=st.lists(
            st.tuples(
                st.builds(
                    ERStatistics,
                    datasource=st.just("TESTDATA"),
                    entity_count=st.integers(min_value=0, max_value=100_000),
                    record_count=st.integers(min_value=0, max_value=100_000),
                    match_count=st.integers(min_value=0, max_value=100_000),
                    possible_match_count=st.integers(min_value=0, max_value=100_000),
                    relationship_count=st.integers(min_value=0, max_value=100_000),
                    captured_at=st.just("2026-04-20T14:30:00Z"),
                ),
                st.booleans(),
            ),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_baseline_equals_last_accepted(self, sequence) -> None:
        """Stored baseline equals the most recently accepted snapshot."""
        import shutil
        import tempfile

        tmp_dir = tempfile.mkdtemp()
        tmp_path = Path(tmp_dir)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            last_accepted: ERStatistics | None = None

            for stats, accept in sequence:
                # Write stats to a temp JSON file
                temp_file = tmp_path / "current_stats.json"
                temp_file.write_text(
                    json.dumps(dataclasses.asdict(stats)), encoding="utf-8"
                )

                if accept:
                    accept_baseline(str(temp_file), stats.datasource)
                    last_accepted = stats

            # All stats use the same datasource ("TESTDATA")
            bl_path = tmp_path / baseline_path("TESTDATA")

            if last_accepted is None:
                # No stats were accepted — baseline file should not exist
                assert not bl_path.exists()
            else:
                # Baseline should match the most recently accepted stats
                assert bl_path.exists()
                stored = json.loads(bl_path.read_text(encoding="utf-8"))
                expected = dataclasses.asdict(last_accepted)
                assert stored == expected
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Example-based unit tests (Task 3.5)
# ---------------------------------------------------------------------------


class TestIdenticalBaselines:
    """Compare two identical ERStatistics → all deltas zero, assessment 'unchanged'.

    **Validates: Requirements 10**
    """

    def test_identical_statistics_produce_zero_deltas(self):
        """When baseline and current are identical, all deltas are zero."""
        stats = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=900,
            record_count=1000,
            match_count=100,
            possible_match_count=10,
            relationship_count=50,
            captured_at="2026-04-20T14:30:00Z",
        )
        result = compare(stats, stats)

        assert result.entity_delta == 0
        assert result.record_delta == 0
        assert result.match_delta == 0
        assert result.possible_match_delta == 0
        assert result.relationship_delta == 0

    def test_identical_statistics_assessment_unchanged(self):
        """When baseline and current are identical, assessment is 'unchanged'."""
        stats = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=900,
            record_count=1000,
            match_count=100,
            possible_match_count=10,
            relationship_count=50,
            captured_at="2026-04-20T14:30:00Z",
        )
        result = compare(stats, stats)

        assert result.quality_assessment == "unchanged"


class TestImprovedResults:
    """Current has more matches and fewer entities → assessment 'improved'.

    **Validates: Requirements 10**
    """

    def test_more_matches_fewer_entities_is_improved(self):
        """More matches (200 vs 100) and fewer entities (800 vs 900) → improved."""
        baseline = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=900,
            record_count=1000,
            match_count=100,
            possible_match_count=10,
            relationship_count=50,
            captured_at="2026-04-20T14:30:00Z",
        )
        current = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=800,
            record_count=1000,
            match_count=200,
            possible_match_count=15,
            relationship_count=60,
            captured_at="2026-04-21T10:00:00Z",
        )
        result = compare(baseline, current)

        assert result.entity_delta == -100
        assert result.match_delta == 100
        assert result.quality_assessment == "improved"

    def test_only_more_matches_is_improved(self):
        """More matches with same entity count → improved."""
        baseline = ERStatistics(
            datasource="VENDORS",
            entity_count=500,
            record_count=600,
            match_count=100,
            possible_match_count=5,
            relationship_count=20,
            captured_at="2026-04-20T14:30:00Z",
        )
        current = ERStatistics(
            datasource="VENDORS",
            entity_count=500,
            record_count=600,
            match_count=150,
            possible_match_count=5,
            relationship_count=20,
            captured_at="2026-04-21T10:00:00Z",
        )
        result = compare(baseline, current)

        assert result.match_delta == 50
        assert result.quality_assessment == "improved"


class TestDegradedResults:
    """Current has fewer matches and more entities → assessment 'degraded'.

    **Validates: Requirements 10**
    """

    def test_fewer_matches_more_entities_is_degraded(self):
        """Fewer matches (50 vs 100) and more entities (1000 vs 900) → degraded."""
        baseline = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=900,
            record_count=1000,
            match_count=100,
            possible_match_count=10,
            relationship_count=50,
            captured_at="2026-04-20T14:30:00Z",
        )
        current = ERStatistics(
            datasource="CUSTOMERS",
            entity_count=1000,
            record_count=1000,
            match_count=50,
            possible_match_count=8,
            relationship_count=40,
            captured_at="2026-04-21T10:00:00Z",
        )
        result = compare(baseline, current)

        assert result.entity_delta == 100
        assert result.match_delta == -50
        assert result.quality_assessment == "degraded"

    def test_only_fewer_matches_is_degraded(self):
        """Fewer matches with same entity count → degraded."""
        baseline = ERStatistics(
            datasource="VENDORS",
            entity_count=500,
            record_count=600,
            match_count=100,
            possible_match_count=5,
            relationship_count=20,
            captured_at="2026-04-20T14:30:00Z",
        )
        current = ERStatistics(
            datasource="VENDORS",
            entity_count=500,
            record_count=600,
            match_count=70,
            possible_match_count=5,
            relationship_count=20,
            captured_at="2026-04-21T10:00:00Z",
        )
        result = compare(baseline, current)

        assert result.match_delta == -30
        assert result.quality_assessment == "degraded"


class TestMissingBaselineFile:
    """Call load_statistics with a non-existent path → SystemExit with code 1.

    **Validates: Requirements 10**
    """

    def test_missing_file_exits_with_code_1(self):
        """load_statistics raises SystemExit(1) for a non-existent file."""
        with pytest.raises(SystemExit) as exc_info:
            load_statistics("/nonexistent/path/to/stats.json")

        assert exc_info.value.code == 1

    def test_missing_file_prints_error(self, capsys):
        """load_statistics prints an informative error for a missing file."""
        with pytest.raises(SystemExit):
            load_statistics("/nonexistent/path/to/stats.json")

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()


class TestInvalidJSON:
    """Write invalid JSON to a temp file, call load_statistics → SystemExit with code 1.

    **Validates: Requirements 10**
    """

    def test_invalid_json_exits_with_code_1(self, tmp_path):
        """load_statistics raises SystemExit(1) for invalid JSON content."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json!!!", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            load_statistics(str(bad_file))

        assert exc_info.value.code == 1

    def test_invalid_json_prints_parse_error(self, tmp_path, capsys):
        """load_statistics prints a clear parse error for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{{{{", encoding="utf-8")

        with pytest.raises(SystemExit):
            load_statistics(str(bad_file))

        captured = capsys.readouterr()
        assert "failed to parse" in captured.err.lower()


class TestCLIArgParsing:
    """Test main() with valid args using tmp_path fixture.

    **Validates: Requirements 10**
    """

    def test_main_with_valid_baseline_and_current(self, tmp_path):
        """main() runs without error when given valid baseline and current files."""
        stats_data = {
            "datasource": "CUSTOMERS",
            "entity_count": 900,
            "record_count": 1000,
            "match_count": 100,
            "possible_match_count": 10,
            "relationship_count": 50,
            "captured_at": "2026-04-20T14:30:00Z",
        }
        baseline_file = tmp_path / "baseline.json"
        current_file = tmp_path / "current.json"
        baseline_file.write_text(json.dumps(stats_data), encoding="utf-8")
        current_file.write_text(json.dumps(stats_data), encoding="utf-8")

        # Should not raise
        main(["--baseline", str(baseline_file), "--current", str(current_file)])

    def test_main_missing_baseline_saves_current_as_baseline(self, tmp_path):
        """When baseline doesn't exist, main() saves current as baseline."""
        stats_data = {
            "datasource": "VENDORS",
            "entity_count": 500,
            "record_count": 600,
            "match_count": 100,
            "possible_match_count": 5,
            "relationship_count": 20,
            "captured_at": "2026-04-21T10:00:00Z",
        }
        baseline_file = tmp_path / "nonexistent_baseline.json"
        current_file = tmp_path / "current.json"
        current_file.write_text(json.dumps(stats_data), encoding="utf-8")

        # main() should handle missing baseline gracefully (exit 0)
        main(["--baseline", str(baseline_file), "--current", str(current_file)])


# ---------------------------------------------------------------------------
# Property 4: Quality assessment consistency
# ---------------------------------------------------------------------------


class TestQualityAssessmentProperties:
    """Property tests for quality assessment consistency.

    **Validates: Requirements 3**
    """

    @given(
        baseline_match=st.integers(min_value=0, max_value=1_000_000),
        baseline_entity=st.integers(min_value=0, max_value=1_000_000),
        match_increase=st.integers(min_value=1, max_value=1_000_000),
        entity_decrease=st.integers(min_value=0, max_value=1_000_000),
    )
    @settings(max_examples=10)
    def test_improved_when_matches_increased_entities_not_increased(
        self,
        baseline_match: int,
        baseline_entity: int,
        match_increase: int,
        entity_decrease: int,
    ) -> None:
        """Quality is 'improved' when match_count increased and entity_count did not increase."""
        current_match = baseline_match + match_increase  # strictly greater
        current_entity = baseline_entity - min(entity_decrease, baseline_entity)  # <= baseline

        baseline = ERStatistics(
            datasource="TEST",
            entity_count=baseline_entity,
            record_count=1000,
            match_count=baseline_match,
            possible_match_count=0,
            relationship_count=0,
            captured_at="2026-01-01T00:00:00Z",
        )
        current = ERStatistics(
            datasource="TEST",
            entity_count=current_entity,
            record_count=1000,
            match_count=current_match,
            possible_match_count=0,
            relationship_count=0,
            captured_at="2026-01-02T00:00:00Z",
        )

        result = compare(baseline, current)
        assert result.quality_assessment == "improved"

    @given(
        baseline_match=st.integers(min_value=1, max_value=1_000_000),
        baseline_entity=st.integers(min_value=0, max_value=1_000_000),
        match_decrease=st.integers(min_value=1, max_value=1_000_000),
        entity_increase=st.integers(min_value=0, max_value=1_000_000),
    )
    @settings(max_examples=10)
    def test_degraded_when_matches_decreased_entities_not_decreased(
        self,
        baseline_match: int,
        baseline_entity: int,
        match_decrease: int,
        entity_increase: int,
    ) -> None:
        """Quality is 'degraded' when match_count decreased and entity_count did not decrease."""
        current_match = baseline_match - min(match_decrease, baseline_match)
        # Ensure match actually decreased (current < baseline)
        if current_match >= baseline_match:
            current_match = baseline_match - 1
        if current_match < 0:
            return  # Skip: can't have negative match count

        current_entity = baseline_entity + entity_increase  # >= baseline

        baseline = ERStatistics(
            datasource="TEST",
            entity_count=baseline_entity,
            record_count=1000,
            match_count=baseline_match,
            possible_match_count=0,
            relationship_count=0,
            captured_at="2026-01-01T00:00:00Z",
        )
        current = ERStatistics(
            datasource="TEST",
            entity_count=current_entity,
            record_count=1000,
            match_count=current_match,
            possible_match_count=0,
            relationship_count=0,
            captured_at="2026-01-02T00:00:00Z",
        )

        result = compare(baseline, current)
        assert result.quality_assessment == "degraded"


# ---------------------------------------------------------------------------
# Structural tests: Steering and POWER.md integration (Task 5.3)
# ---------------------------------------------------------------------------

# Root of the senzing-bootcamp/ directory
_BOOTCAMP_ROOT = Path(__file__).resolve().parent.parent


class TestSteeringIntegration:
    """Structural tests verifying Module 5 Phase 3 steering contains baseline capture step.

    **Validates: Requirements 4**
    """

    _steering_path = _BOOTCAMP_ROOT / "steering" / "module-05-phase3-test-load.md"

    def test_steering_contains_baseline_capture_step(self) -> None:
        """Module 5 Phase 3 steering contains baseline capture content (step 24a)."""
        content = self._steering_path.read_text(encoding="utf-8")
        # Step 24a is titled "Capture ER Statistics"
        assert "Capture ER Statistics" in content or "er_baseline" in content

    def test_steering_contains_comparison_step(self) -> None:
        """Module 5 Phase 3 steering references compare_results.py for comparison."""
        content = self._steering_path.read_text(encoding="utf-8")
        assert "compare_results.py" in content


class TestPowerMdIntegration:
    """Structural tests verifying POWER.md Useful Commands section lists compare_results.py.

    **Validates: Requirements 9**
    """

    _power_md_path = _BOOTCAMP_ROOT / "POWER.md"

    def test_power_md_lists_compare_results(self) -> None:
        """POWER.md contains compare_results.py in the Useful Commands section."""
        content = self._power_md_path.read_text(encoding="utf-8")
        # Find the Useful Commands section and verify compare_results.py is listed
        useful_commands_idx = content.find("## Useful Commands")
        assert useful_commands_idx != -1, "POWER.md must have a '## Useful Commands' section"
        commands_section = content[useful_commands_idx:]
        assert "compare_results.py" in commands_section
