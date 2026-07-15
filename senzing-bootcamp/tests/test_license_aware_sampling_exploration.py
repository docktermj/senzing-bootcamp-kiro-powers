"""Bug condition exploration tests for the license-aware-sampling bugfix.

These tests encode the EXPECTED (license-aware) capacity-decision behavior and
are EXPECTED TO FAIL on unfixed code — failure confirms the bug exists.

Bug (from bugfix.md / design.md): the bootcamp drives every sampling/capacity
decision from the hardcoded ~500-record evaluation limit and never reads the
active license's real ``recordLimit``. When a custom license is configured
(``recordLimit`` of 0 == unlimited, or a cap larger than the dataset), the
agent still recommends downsampling toward <=500.

The fix (task 3.1) introduces ``senzing-bootcamp/scripts/detect_license_limit.py``
which:
  * parses ``recordLimit`` from a license JSON blob,
  * persists it to ``config/bootcamp_progress.json`` under ``license_record_limit``
    (0 == unlimited, positive == cap), and
  * exposes ``evaluate_capacity_decision(dataset_total, effective_limit)`` that
    drives the sampling decision from the effective license limit, never the
    hardcoded 500.

This module pins that contract. On UNFIXED code the module does not exist, so
every test fails with a clear message (the bug: there is no license-aware
threshold logic). After the fix these same tests validate the corrected
behavior (see task 3.9).

Feature: license-aware-sampling

**Validates: Requirements 1.1, 1.2, 1.5, 2.1, 2.2, 2.5**
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# The decision points named by the bug condition (design.md isBugCondition).
# ---------------------------------------------------------------------------

_BUG_DECISION_POINTS = (
    "module1_step6a",
    "module4_step6",
    "module6_loading",
    "module8_performance",
)

# The hardcoded evaluation figure the buggy flow compares against.
_HARDCODED_EVALUATION_LIMIT = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_detect_module() -> ModuleType | None:
    """Import ``detect_license_limit`` from ``scripts/`` (on ``sys.path`` via conftest).

    Returns:
        The imported module, or ``None`` when it does not exist yet (the
        unfixed state — the license-aware helper has not been implemented).
    """
    try:
        module = importlib.import_module("detect_license_limit")
        return importlib.reload(module)
    except ModuleNotFoundError:
        return None


_MISSING_MODULE_MSG = (
    "BUG CONFIRMED: senzing-bootcamp/scripts/detect_license_limit.py does not "
    "exist, so there is no license-aware threshold logic. Every capacity "
    "decision falls back to the hardcoded 500-record evaluation limit instead "
    "of the active license's recordLimit."
)


def _expected_recommend_sampling(dataset_total: int, effective_limit: int) -> bool:
    """The correct, license-aware sampling recommendation.

    ``effective_limit == 0`` means the license imposes no cap, so sampling is
    never recommended for license reasons. A positive limit recommends sampling
    only when the dataset genuinely exceeds it.
    """
    return effective_limit > 0 and dataset_total > effective_limit


# ---------------------------------------------------------------------------
# Test 1 — the helper parses and persists the real recordLimit
# ---------------------------------------------------------------------------


class TestDetectLicenseLimitPersistence:
    """Detected ``recordLimit`` is parsed and persisted for cross-module reuse.

    **Validates: Requirements 2.1, 2.4**

    On unfixed code the helper module is absent, so these fail — proving there
    is no mechanism to detect or persist the active license limit.
    """

    def test_parses_and_persists_unlimited_record_limit(self, tmp_path: Path) -> None:
        module = _load_detect_module()
        assert module is not None, _MISSING_MODULE_MSG

        progress_path = tmp_path / "config" / "bootcamp_progress.json"
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        # A legacy progress file with no license_record_limit field.
        progress_path.write_text(
            json.dumps({"current_module": 2, "modules_completed": []}),
            encoding="utf-8",
        )

        # A real observed license: EVAL/STANDARD, recordLimit 0 (no cap).
        license_json = {
            "customer": "Senzing Public Test License",
            "contract": "EVAL",
            "licenseType": "STANDARD",
            "recordLimit": 0,
            "expireDate": "2027-03-12",
        }

        record_limit = module.parse_record_limit(license_json)
        assert record_limit == 0

        module.persist_license_limit(record_limit, str(progress_path))

        data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert data["license_record_limit"] == 0, (
            "detect_license_limit must persist the detected recordLimit (0 == "
            "unlimited) to config/bootcamp_progress.json for later modules."
        )
        # Existing fields must be preserved (no corruption).
        assert data["current_module"] == 2
        assert data["modules_completed"] == []

    def test_read_back_matches_persisted_limit(self, tmp_path: Path) -> None:
        module = _load_detect_module()
        assert module is not None, _MISSING_MODULE_MSG

        progress_path = tmp_path / "config" / "bootcamp_progress.json"
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps({}), encoding="utf-8")

        module.persist_license_limit(50000, str(progress_path))
        assert module.read_license_limit(str(progress_path)) == 50000


# ---------------------------------------------------------------------------
# Test 2 — capacity decisions use the effective limit, not the hardcoded 500
# ---------------------------------------------------------------------------


class TestCapacityDecisionUsesEffectiveLimit:
    """Concrete bug-condition examples from design.md.

    **Validates: Requirements 1.1, 1.2, 1.5, 2.1, 2.2, 2.5**
    """

    def test_unlimited_license_does_not_recommend_sampling(self) -> None:
        # Module 1 Step 6a: 5,726 records, custom license recordLimit 0 (unlimited).
        module = _load_detect_module()
        assert module is not None, _MISSING_MODULE_MSG

        decision = module.evaluate_capacity_decision(dataset_total=5726, effective_limit=0)
        assert decision.recommend_sampling is False, (
            "With an unlimited license (recordLimit 0), no sampling should be "
            "recommended for license reasons — yet the buggy flow compares "
            "5726 > 500 and recommends downsampling."
        )
        assert decision.comparison_limit == 0
        assert decision.comparison_limit != _HARDCODED_EVALUATION_LIMIT
        assert decision.hardcoded_500_not_used is True

    def test_large_cap_above_dataset_does_not_recommend_sampling(self) -> None:
        # Module 4 Step 6: 2,000 records, custom license allows 50,000.
        module = _load_detect_module()
        assert module is not None, _MISSING_MODULE_MSG

        decision = module.evaluate_capacity_decision(dataset_total=2000, effective_limit=50000)
        assert decision.recommend_sampling is False
        assert decision.comparison_limit == 50000
        assert decision.comparison_limit != _HARDCODED_EVALUATION_LIMIT
        assert decision.hardcoded_500_not_used is True

    def test_cap_below_dataset_recommends_sampling_against_real_limit(self) -> None:
        # Genuine over-limit: dataset exceeds the real cap -> sampling recommended,
        # but compared against the real limit, not 500.
        module = _load_detect_module()
        assert module is not None, _MISSING_MODULE_MSG

        decision = module.evaluate_capacity_decision(dataset_total=1500, effective_limit=1000)
        assert decision.recommend_sampling is True
        assert decision.comparison_limit == 1000
        assert decision.hardcoded_500_not_used is True


# ---------------------------------------------------------------------------
# PBT — Bug Condition property (Property 1)
# ---------------------------------------------------------------------------


class TestBugConditionProperty:
    """Property 1: capacity decisions are driven by the effective license limit.

    **Validates: Requirements 1.1, 1.2, 1.5, 2.1, 2.2, 2.5**

    For any capacity-decision context where a custom license is configured
    (``license_record_limit`` is 0/unlimited or larger than the dataset) the
    threshold logic MUST compare against that effective limit and recommend
    sampling only when the dataset genuinely exceeds a positive cap — never
    against the hardcoded 500.

    On UNFIXED code ``detect_license_limit`` does not exist, so the property
    fails on the very first generated example, surfacing the counterexample.
    """

    @given(
        record_limit=st.integers(min_value=0, max_value=10_000_000),
        dataset_total=st.integers(min_value=1, max_value=10_000_000),
        decision_point=st.sampled_from(_BUG_DECISION_POINTS),
    )
    def test_recommend_sampling_uses_effective_limit(
        self, record_limit: int, dataset_total: int, decision_point: str
    ) -> None:
        module = _load_detect_module()
        assert module is not None, (
            f"{_MISSING_MODULE_MSG} Counterexample: at decision point "
            f"'{decision_point}', a custom license with recordLimit="
            f"{record_limit} and a dataset of {dataset_total} records still "
            f"gets compared against the hardcoded {_HARDCODED_EVALUATION_LIMIT}."
        )

        decision = module.evaluate_capacity_decision(
            dataset_total=dataset_total, effective_limit=record_limit
        )

        expected = _expected_recommend_sampling(dataset_total, record_limit)
        assert decision.recommend_sampling == expected, (
            f"At '{decision_point}' with recordLimit={record_limit} and "
            f"dataset={dataset_total}: expected recommend_sampling={expected} "
            f"(effectiveLimit>0 AND datasetTotal>effectiveLimit), got "
            f"{decision.recommend_sampling}."
        )
        # The decision must compare against the effective limit, never 500.
        assert decision.comparison_limit == record_limit
        assert decision.hardcoded_500_not_used is True
