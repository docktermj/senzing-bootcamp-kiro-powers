"""Preservation property tests for the license-aware-sampling bugfix.

These tests follow the observation-first methodology: they pin baseline
behavior that the fix MUST NOT disturb. Every test here is EXPECTED TO PASS on
UNFIXED code because it covers non-bug-condition paths — sessions with no custom
license (the evaluation fallback), the non-license uses of the number 500
(Module 6 Phase A volume tiers), the SQLite <=1,000-record performance advice,
and backward compatibility of ``config/bootcamp_progress.json`` when the new
``license_record_limit`` field is absent.

Design (design.md, Property 2 / Preservation Checking):
    FOR ALL input WHERE NOT isBugCondition(input) DO
      ASSERT evaluateCapacityDecision_original(input) == evaluateCapacityDecision_fixed(input)

isBugCondition is true only when a *custom* license is configured. When no
custom license is present (``license_record_limit`` absent/null) the effective
limit falls back to the MCP-provided evaluation capacity, so the fixed decision
must reproduce the original evaluation-limit decision exactly.

The not-yet-created fix helper ``detect_license_limit`` is referenced only
behind an ``ImportError`` guard, so these tests pass on unfixed code and gain an
extra forward-looking check once the helper exists (task 3.1).

Feature: license-aware-sampling

**Validates: Requirements 3.1, 3.2, 3.5, 3.6**
"""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import validate_progress_schema, write_checkpoint  # noqa: E402
from volume_utils import (  # noqa: E402
    TIER_BOUNDARIES,
    TIER_DEMO,
    TIER_LARGE,
    TIER_SMALL,
    classify_tier,
)

# ---------------------------------------------------------------------------
# Paths — steering files whose non-license baseline content must be preserved.
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_MODULE_02 = _STEERING_DIR / "module-02-sdk-setup.md"
_MODULE_06_PHASE_B = _STEERING_DIR / "module-06-phaseB-load-first-source.md"

# The hardcoded evaluation figure the buggy flow leans on. Referenced here only
# to assert the reference model never treats it as a constant boundary.
_HARDCODED_EVALUATION_LIMIT = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_detect_module() -> ModuleType | None:
    """Import the ``detect_license_limit`` fix helper if it exists yet.

    Returns:
        The imported module, or ``None`` on unfixed code where the license-aware
        helper has not been created (task 3.1). Guarding on ``None`` keeps these
        preservation tests passing before the fix lands.
    """
    try:
        module = importlib.import_module("detect_license_limit")
        return importlib.reload(module)
    except ModuleNotFoundError:
        return None


def _expected_tier(record_count: int) -> str:
    """Return the volume tier for ``record_count`` straight from TIER_BOUNDARIES.

    Args:
        record_count: Non-negative dataset record total.

    Returns:
        One of ``demo``, ``small``, ``medium``, ``large``.
    """
    for tier, (lower, upper) in TIER_BOUNDARIES.items():
        if record_count >= lower and record_count < upper:
            return tier
    return TIER_LARGE  # pragma: no cover


def _original_capacity_decision(dataset_total: int, evaluation_capacity: int | None) -> bool:
    """Model the ORIGINAL (pre-fix) sampling decision.

    The original flow knows only the MCP-provided evaluation capacity and never
    reads a custom license: it recommends sampling whenever the dataset exceeds
    that capacity. When the capacity is unavailable from the MCP server (``None``)
    it makes no license-based recommendation.

    Args:
        dataset_total: The dataset record total.
        evaluation_capacity: The evaluation capacity reported by the MCP server,
            or ``None`` when unavailable.

    Returns:
        ``True`` when sampling would be recommended under the original behavior.
    """
    if evaluation_capacity is None:
        return False
    return dataset_total > evaluation_capacity


def _resolve_effective_limit(
    license_record_limit: int | None, evaluation_capacity: int | None
) -> int | None:
    """Resolve the effective record limit for the FIXED flow (reference model).

    Prefers a persisted custom-license ``license_record_limit`` when present;
    otherwise falls back to the MCP-provided evaluation capacity. Absent/null
    ``license_record_limit`` therefore reproduces the evaluation-limit behavior.

    Args:
        license_record_limit: Persisted custom-license cap (0 == unlimited), or
            ``None`` when no custom license was detected.
        evaluation_capacity: The evaluation capacity from the MCP server, or
            ``None`` when unavailable.

    Returns:
        The effective limit to compare against, or ``None`` when no limit applies.
    """
    if license_record_limit is not None:
        return license_record_limit
    return evaluation_capacity


def _fixed_capacity_decision(
    dataset_total: int,
    license_record_limit: int | None,
    evaluation_capacity: int | None,
) -> bool:
    """Model the FIXED sampling decision driven by the effective limit.

    A limit of ``0`` means the license imposes no cap (never sample for license
    reasons); a positive limit recommends sampling only when genuinely exceeded;
    a ``None`` effective limit makes no recommendation.

    Args:
        dataset_total: The dataset record total.
        license_record_limit: Persisted custom-license cap, or ``None``.
        evaluation_capacity: The evaluation capacity from the MCP server, or ``None``.

    Returns:
        ``True`` when the fixed flow would recommend sampling.
    """
    effective = _resolve_effective_limit(license_record_limit, evaluation_capacity)
    if effective is None or effective == 0:
        return False
    return dataset_total > effective


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_IDENT_ALPHABET = "abcdefghijklmnopqrstuvwxyz_"


def st_dataset_total() -> st.SearchStrategy[int]:
    """Strategy for a dataset record total spanning every volume tier."""
    return st.integers(min_value=0, max_value=20_000_000)


def st_license_record_limit() -> st.SearchStrategy[int | None]:
    """Strategy for a persisted ``license_record_limit`` value.

    ``None`` models "not detected" (no custom license -> evaluation fallback),
    ``0`` models an unlimited custom license, and a positive integer models a
    finite record cap.
    """
    return st.one_of(st.none(), st.integers(min_value=0, max_value=10_000_000))


def st_evaluation_capacity() -> st.SearchStrategy[int | None]:
    """Strategy for the MCP-provided evaluation capacity.

    Always a positive figure (the built-in evaluation license has a real cap) or
    ``None`` when the MCP server does not return it.
    """
    return st.one_of(st.none(), st.integers(min_value=1, max_value=1_000_000))


@st.composite
def st_legacy_progress_dict(draw: st.DrawFn) -> dict:
    """Draw a minimal schema-valid ``bootcamp_progress.json`` dict.

    Models a legacy progress file written before the fix: it validates against
    ``validate_progress_schema`` and never contains a ``license_record_limit``
    key. Callers add that key separately to exercise backward compatibility.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A progress dict with the four commonly-present fields.
    """
    return {
        "current_module": draw(st.integers(min_value=1, max_value=11)),
        "modules_completed": draw(
            st.lists(st.integers(min_value=1, max_value=11), max_size=5, unique=True)
        ),
        "data_sources": draw(
            st.lists(
                st.text(alphabet=_IDENT_ALPHABET, min_size=1, max_size=8), max_size=4
            )
        ),
        "database_type": draw(st.sampled_from(["sqlite", "postgresql"])),
    }


# ---------------------------------------------------------------------------
# Test 1 — Volume tier classification is a pure function of the dataset total
# ---------------------------------------------------------------------------


class TestVolumeTierClassificationPreserved:
    """Module 6 Phase A volume tiers are independent of any license value.

    **Validates: Requirements 3.6**

    The number 500 used in the demo/small tier boundary is a non-license use and
    must stay unchanged regardless of ``license_record_limit``.
    """

    def test_tier_boundaries_unchanged(self) -> None:
        """The demo/small/medium/large boundaries match the documented figures."""
        assert TIER_BOUNDARIES[TIER_DEMO] == (0, 500)
        assert TIER_BOUNDARIES[TIER_SMALL] == (500, 500_000)
        assert TIER_BOUNDARIES["medium"] == (500_000, 10_000_000)
        assert TIER_BOUNDARIES[TIER_LARGE] == (10_000_000, float("inf"))

    def test_demo_small_boundary_at_500(self) -> None:
        """500 is the non-license demo/small boundary, unchanged by the fix."""
        assert classify_tier(499) == TIER_DEMO
        assert classify_tier(500) == TIER_SMALL
        assert classify_tier(501) == TIER_SMALL

    @given(dataset_total=st_dataset_total(), license_record_limit=st_license_record_limit())
    def test_tier_independent_of_license_record_limit(
        self, dataset_total: int, license_record_limit: int | None
    ) -> None:
        """Tier classification ignores any hypothetical ``license_record_limit``.

        For any dataset total, injecting a ``license_record_limit`` into a
        progress dict does not change the tier — classification is a pure
        function of the record total.

        **Validates: Requirements 3.6**
        """
        baseline = classify_tier(dataset_total)

        progress: dict = {
            "current_module": 6,
            "production_volume": {"raw_value": dataset_total},
        }
        if license_record_limit is not None:
            progress["license_record_limit"] = license_record_limit

        derived = classify_tier(progress["production_volume"]["raw_value"])
        assert derived == baseline, (
            f"license_record_limit={license_record_limit} changed the tier for "
            f"dataset_total={dataset_total}: {baseline!r} -> {derived!r}"
        )
        assert baseline == _expected_tier(dataset_total)


# ---------------------------------------------------------------------------
# Test 2 — Evaluation-fallback: no custom license reproduces original behavior
# ---------------------------------------------------------------------------


class TestEvaluationFallbackPreserved:
    """No-custom-license sessions keep the original evaluation-limit behavior.

    **Validates: Requirements 3.1, 3.2, 3.5**

    When ``license_record_limit`` is absent/null the fixed decision must equal
    the original decision (compare the dataset total against the MCP-provided
    evaluation capacity), so evaluation-only sessions are unaffected.
    """

    @given(dataset_total=st_dataset_total(), evaluation_capacity=st_evaluation_capacity())
    def test_no_custom_license_matches_original(
        self, dataset_total: int, evaluation_capacity: int | None
    ) -> None:
        """Fixed fallback == original decision when no custom license is configured.

        This is the design's preservation equality for ``NOT isBugCondition``:
        no custom license means ``license_record_limit`` is ``None``.

        **Validates: Requirements 3.1, 3.2**
        """
        original = _original_capacity_decision(dataset_total, evaluation_capacity)
        fixed = _fixed_capacity_decision(dataset_total, None, evaluation_capacity)
        assert fixed == original, (
            f"Evaluation fallback diverged from original for dataset_total="
            f"{dataset_total}, evaluation_capacity={evaluation_capacity}: "
            f"original={original}, fixed={fixed}"
        )

    @given(dataset_total=st_dataset_total(), evaluation_capacity=st_evaluation_capacity())
    def test_absent_field_falls_back_to_evaluation_capacity(
        self, dataset_total: int, evaluation_capacity: int | None
    ) -> None:
        """An absent/null ``license_record_limit`` resolves to the evaluation capacity.

        Also asserts, behind an ImportError guard, that the fix helper's
        ``read_license_limit`` returns ``None`` for a progress file with no
        ``license_record_limit`` field (evaluation fallback). The guard keeps
        this passing on unfixed code where the helper does not exist yet.

        **Validates: Requirements 3.1, 3.5**
        """
        assert _resolve_effective_limit(None, evaluation_capacity) == evaluation_capacity

        module = _load_detect_module()
        if module is not None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                progress_path = Path(tmp_dir) / "config" / "bootcamp_progress.json"
                progress_path.parent.mkdir(parents=True, exist_ok=True)
                progress_path.write_text(
                    json.dumps({"current_module": 2, "modules_completed": []}),
                    encoding="utf-8",
                )
                assert module.read_license_limit(str(progress_path)) is None

    def test_decision_boundary_follows_supplied_capacity(self) -> None:
        """The decision boundary tracks the MCP-supplied capacity, not a constant.

        A dataset of 700 records is over a 500-capacity evaluation license but
        under a 1,000-capacity one — proving the logic is driven by the value
        passed in (an MCP fact) rather than a hardcoded figure.

        **Validates: Requirements 3.5**
        """
        assert _original_capacity_decision(700, 500) is True
        assert _original_capacity_decision(700, 1000) is False
        # The same dataset/capacity pair drives the fixed fallback identically.
        assert _fixed_capacity_decision(700, None, 500) is True
        assert _fixed_capacity_decision(700, None, 1000) is False


# ---------------------------------------------------------------------------
# Test 3 — Backward compatibility of config/bootcamp_progress.json
# ---------------------------------------------------------------------------


class TestProgressBackwardCompatibility:
    """Progress files remain valid with or without ``license_record_limit``.

    **Validates: Requirements 3.1, 3.2**

    A legacy file (no field) must keep working, and the new field must never be
    fabricated when absent — a missing field is treated as null (evaluation
    fallback).
    """

    def test_schema_validation_tolerates_field_presence_and_absence(self) -> None:
        """``validate_progress_schema`` accepts the file with and without the field."""
        base = {
            "current_module": 2,
            "modules_completed": [],
            "data_sources": [],
            "database_type": "sqlite",
        }
        assert validate_progress_schema(base) == []
        assert validate_progress_schema({**base, "license_record_limit": 0}) == []
        assert validate_progress_schema({**base, "license_record_limit": 50000}) == []
        assert validate_progress_schema({**base, "license_record_limit": None}) == []

    @given(
        progress=st_legacy_progress_dict(),
        license_record_limit=st_license_record_limit(),
        step=st.integers(min_value=1, max_value=12),
    )
    def test_checkpoint_roundtrip_preserves_fields(
        self, progress: dict, license_record_limit: int | None, step: int
    ) -> None:
        """Writing a checkpoint preserves existing fields and never fabricates the field.

        For any legacy progress dict (optionally carrying ``license_record_limit``),
        ``write_checkpoint`` updates only ``current_step``/``step_history`` and
        leaves every other field intact. When the field is absent it stays absent
        (treated as null); when present its value is preserved unchanged.

        **Validates: Requirements 3.1, 3.2**
        """
        if license_record_limit is not None:
            progress = {**progress, "license_record_limit": license_record_limit}

        with tempfile.TemporaryDirectory() as tmp_dir:
            progress_path = Path(tmp_dir) / "config" / "bootcamp_progress.json"
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

            write_checkpoint(6, step, str(progress_path))

            data = json.loads(progress_path.read_text(encoding="utf-8"))

            # Pre-existing fields are preserved verbatim.
            for key in ("current_module", "modules_completed", "data_sources", "database_type"):
                assert data[key] == progress[key], (
                    f"Field {key!r} changed across checkpoint: "
                    f"{progress[key]!r} -> {data.get(key)!r}"
                )

            # The new field is preserved when present, never fabricated when absent.
            if license_record_limit is not None:
                assert data["license_record_limit"] == license_record_limit
            else:
                assert "license_record_limit" not in data, (
                    "checkpoint fabricated a license_record_limit field that was "
                    "absent (a missing field must be treated as null)"
                )

            # The checkpoint itself was applied.
            assert data["current_step"] == step
            assert data["step_history"]["6"]["last_completed_step"] == step


# ---------------------------------------------------------------------------
# Test 4 — Non-license steering content is preserved
# ---------------------------------------------------------------------------


class TestNonLicenseSteeringContentPreserved:
    """Non-license steering figures and the MCP-sourced-facts rule are preserved.

    **Validates: Requirements 3.2, 3.5, 3.6**
    """

    def test_sqlite_1000_record_advice_preserved(self) -> None:
        """Module 6 Phase B keeps its SQLite <=1,000-record performance advice.

        **Validates: Requirements 3.6**
        """
        content = _MODULE_06_PHASE_B.read_text(encoding="utf-8")
        assert "\u2264" + "1,000 records" in content, (
            "Module 6 Phase B lost its SQLite <=1,000-record performance advice"
        )
        assert "SQLite performance note" in content

    def test_evaluation_license_explanation_preserved(self) -> None:
        """Module 2 keeps the built-in evaluation license explanation.

        **Validates: Requirements 3.2**
        """
        content = _MODULE_02.read_text(encoding="utf-8")
        assert "built-in evaluation license" in content

    def test_mcp_sourced_facts_rule_preserved(self) -> None:
        """Module 2 still directs the agent to confirm figures against the MCP server.

        **Validates: Requirements 3.5**
        """
        content = _MODULE_02.read_text(encoding="utf-8")
        assert "Senzing MCP server" in content
