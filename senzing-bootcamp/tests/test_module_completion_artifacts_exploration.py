"""Bug condition exploration suite for the module-completion-artifacts bugfix.

Feature: module-completion-artifacts (BUGFIX)

Property 1: Bug Condition — Complete artifact coverage for every completed module.

This suite encodes the *fixed* contract. It is EXPECTED TO FAIL on the unfixed
state — the failures are the success criterion. They surface counterexamples that
confirm the four hypothesized root causes from the design:

    Cause 1  Boundary detection shadowed at track end (final module recap missing)
    Cause 2  Journal/certificate steps not bound to the shared completion trigger
    Cause 3  Duration sourced from LLM session context, not step_history timestamps
    Cause 4  No backfill mechanism for modules completed before the fix

The deterministic planner module that the fix introduces,
``senzing-bootcamp/scripts/completion_artifacts.py``, DOES NOT EXIST YET (it is
created in task 3.1). On the unfixed state the import below fails, so every
concrete test fails at the ``_require_planner()`` gate — an import failure that
*is* the counterexample proving the bug (no planner ⇒ none of causes 1–4 are
addressed). After the fix, the planner exists and the encoded fixed-behavior
assertions run and pass (task 3.6 re-runs this same file).

Bug Condition (from design — ``isBugCondition(input)``):
    isBugCondition(X) =
          coverageGap                 // a completed module is missing an artifact type
       OR certificatesNonUniform      // some completed modules have certs, some do not
       OR placeholderDuration         // placeholder per-module Duration w/ real timing
       OR placeholderTotal            // placeholder Total Duration w/ real timing

Reported defect state mirrored here:
    modules_completed   = [1, 2, 3, 4, 5, 6, 7]   (gate 7_complete: completed)
    recap sections      = [1, 2, 3, 4, 5, 6]      (Module 7 missing)
    journal entries     = [3, 6, 7]               (1, 2, 4, 5 missing)
    certificates        = [6, 7]                  (1-5 missing -> non-uniform)
    recap durations     = "Module N session"      (placeholders)
    total duration      = "Module N session"      (placeholder)

Expected planner API contract (implemented in task 3.1; resolved defensively
here so this file is robust to snake_case/camelCase naming choices):
    ProgressState(modules_completed, step_history, started_at)
    ArtifactInventory(recap_sections, journal_entries, certificates)  # sets[int]
    compute_module_duration(step_history, started_at, module, prior_timestamp) -> str | None
    compute_total_duration(step_history, started_at, modules_completed) -> str | None
    detect_artifact_gaps(modules_completed, inventory) -> ArtifactGapReport
    plan_backfill(progress_state, inventory) -> BackfillPlan
    is_bug_condition(progress_state, inventory, recap_durations, recap_total) -> bool
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Defensive import of the planner module created by task 3.1.
# On the UNFIXED state this module does not exist -> PLANNER_AVAILABLE is False
# and every concrete test fails at its _require_planner() gate (the expected,
# success-case failure that proves the bug).
# ---------------------------------------------------------------------------

PLANNER_AVAILABLE = False
_PLANNER_IMPORT_ERROR: str | None = None
_planner = None  # the imported module

try:  # pragma: no cover - exercised by presence/absence of the planner
    import completion_artifacts as _planner  # type: ignore

    PLANNER_AVAILABLE = True
except Exception as exc:  # noqa: BLE001 - any failure means "not yet implemented"
    _PLANNER_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


def _require_planner(root_cause: str) -> None:
    """Fail with a documented counterexample when the planner is absent.

    Args:
        root_cause: Human-readable description of the counterexample / root cause
            this test surfaces, recorded in the failure message.
    """
    if not PLANNER_AVAILABLE:
        pytest.fail(
            "COUNTEREXAMPLE (bug confirmed): "
            f"{root_cause}\n"
            "The deterministic planner senzing-bootcamp/scripts/completion_artifacts.py "
            "does not exist on the unfixed state, so module-completion artifacts are "
            "not generated/backfilled uniformly and Durations are not computed from "
            f"step_history timestamps. Import error: {_PLANNER_IMPORT_ERROR}"
        )


def _attr(*names: str):
    """Resolve the first attribute present on the planner module.

    Args:
        *names: Candidate attribute names (e.g., "is_bug_condition", "isBugCondition").

    Returns:
        The resolved attribute.

    Raises:
        pytest.Failed: If none of the candidate names exist on the planner.
    """
    for name in names:
        if hasattr(_planner, name):
            return getattr(_planner, name)
    pytest.fail(
        f"Planner module is missing an expected symbol; tried: {', '.join(names)}"
    )


def _attr_cls(*names: str):
    """Resolve the first class/attribute present on the planner module."""
    return _attr(*names)


# ---------------------------------------------------------------------------
# Reported defect fixture data (mirrors config/bootcamp_progress.json + on-disk)
# ---------------------------------------------------------------------------

REPORTED_MODULES_COMPLETED: list[int] = [1, 2, 3, 4, 5, 6, 7]
REPORTED_STARTED_AT = "2025-01-10T09:00:00Z"

# Valid, ordered ISO 8601 timestamps for every completed module. Module 3's
# elapsed time is 11:30 -> 12:42 == 1h 12m (matches the design's worked example).
REPORTED_STEP_HISTORY: dict[str, dict[str, object]] = {
    "1": {"last_completed_step": 5, "updated_at": "2025-01-10T10:12:00Z"},
    "2": {"last_completed_step": 5, "updated_at": "2025-01-10T11:30:00Z"},
    "3": {"last_completed_step": 5, "updated_at": "2025-01-10T12:42:00Z"},
    "4": {"last_completed_step": 5, "updated_at": "2025-01-11T09:00:00Z"},
    "5": {"last_completed_step": 5, "updated_at": "2025-01-11T10:00:00Z"},
    "6": {"last_completed_step": 5, "updated_at": "2025-01-11T11:00:00Z"},
    "7": {"last_completed_step": 5, "updated_at": "2025-01-11T12:00:00Z"},
}

# Partial on-disk artifact inventory exactly as reported.
REPORTED_RECAP_SECTIONS = {1, 2, 3, 4, 5, 6}          # Module 7 missing
REPORTED_JOURNAL_ENTRIES = {3, 6, 7}                  # 1, 2, 4, 5 missing
REPORTED_CERTIFICATES = {6, 7}                        # 1-5 missing (non-uniform)

# Placeholder Duration text currently written into the recap.
REPORTED_RECAP_DURATIONS: dict[int, str] = {
    m: f"Module {m} session" for m in REPORTED_MODULES_COMPLETED
}
REPORTED_RECAP_TOTAL = "Module N session"

_PLACEHOLDER_RE = re.compile(r"module\s+\w+\s+session", re.IGNORECASE)
_DURATION_RE = re.compile(r"\d+\s*(d|h|m|s)", re.IGNORECASE)


def _is_placeholder(text: str | None) -> bool:
    """Return True for empty/missing values and non-time 'Module N session' strings."""
    if text is None or not str(text).strip():
        return True
    if _PLACEHOLDER_RE.search(str(text)):
        return True
    return _DURATION_RE.search(str(text)) is None


def _looks_like_duration(text: str | None) -> bool:
    """Return True when text reads as a real elapsed duration (e.g., '1h 12m')."""
    return text is not None and bool(_DURATION_RE.search(str(text)))


def _make_progress_state():
    """Construct the planner's ProgressState for the reported defect."""
    progress_state_cls = _attr_cls("ProgressState")
    return progress_state_cls(
        modules_completed=list(REPORTED_MODULES_COMPLETED),
        step_history=dict(REPORTED_STEP_HISTORY),
        started_at=REPORTED_STARTED_AT,
    )


def _make_inventory(
    recap_sections=REPORTED_RECAP_SECTIONS,
    journal_entries=REPORTED_JOURNAL_ENTRIES,
    certificates=REPORTED_CERTIFICATES,
):
    """Construct the planner's ArtifactInventory from explicit module sets."""
    inventory_cls = _attr_cls("ArtifactInventory")
    return inventory_cls(
        recap_sections=set(recap_sections),
        journal_entries=set(journal_entries),
        certificates=set(certificates),
    )


def _modules_of(plan_field) -> set[int]:
    """Coerce a backfill-plan field (set/list/iterable of ints) to a set[int]."""
    return {int(m) for m in plan_field}


def _plan_modules(plan, *names: str) -> set[int]:
    """Resolve a per-type module collection from a BackfillPlan defensively."""
    for name in names:
        if hasattr(plan, name):
            return _modules_of(getattr(plan, name))
    pytest.fail(f"BackfillPlan is missing an expected field; tried: {', '.join(names)}")
    return set()  # unreachable


def _report_modules(report, *names: str) -> set[int]:
    """Resolve a per-type missing-module collection from an ArtifactGapReport."""
    for name in names:
        if hasattr(report, name):
            return _modules_of(getattr(report, name))
    pytest.fail(f"ArtifactGapReport is missing an expected field; tried: {', '.join(names)}")
    return set()  # unreachable


# ===========================================================================
# Test case 1 — Final-module recap missing (Cause 1)
# ===========================================================================


class TestFinalModuleRecapMissing:
    """The final module of a track must get a recap section.

    Reported: recap has Modules 1–6 only; Module 7 (final Core module) is absent
    because boundary detection is shadowed by the track-completion celebration.

    Validates: Requirements 2.1
    """

    def test_module_7_recap_section_is_produced(self) -> None:
        """A recap section is expected for Module 7 (fails on unfixed flow)."""
        _require_planner(
            "Module 7 recap section absent — recap contains sections only for "
            "Modules 1-6 (Cause 1: boundary detection shadowed at track end)."
        )
        detect_artifact_gaps = _attr("detect_artifact_gaps")
        plan_backfill = _attr("plan_backfill")

        inventory = _make_inventory()
        progress = _make_progress_state()

        # The planner must report Module 7 as a missing recap section ...
        report = detect_artifact_gaps(REPORTED_MODULES_COMPLETED, inventory)
        missing_recap = _report_modules(report, "missing_recap", "missing_recap_sections")
        assert 7 in missing_recap, (
            "Module 7 must be reported as a missing recap section."
        )

        # ... and the backfill plan + existing sections must cover every module.
        plan = plan_backfill(progress, inventory)
        plan_recap = _plan_modules(plan, "recap_modules", "recap_sections", "missing_recap")
        covered = REPORTED_RECAP_SECTIONS | plan_recap
        assert covered.issuperset(set(REPORTED_MODULES_COMPLETED)), (
            "After backfill, every completed module (including 7) must have a recap "
            f"section. Covered={sorted(covered)}"
        )


# ===========================================================================
# Test case 2 — Journal/certificate not bound to shared trigger (Cause 2)
# ===========================================================================


class TestJournalAndCertificateCoverage:
    """Journal entries and certificates must exist for every completed module.

    Reported: journal has [3, 6, 7]; certificates [6, 7] — the journal_entry and
    completion_certificate steps run only on an explicit workflow invocation, not
    on the shared boundary-detection trigger.

    Validates: Requirements 2.4, 2.5, 2.6
    """

    def test_all_modules_get_journal_entries_and_uniform_certificates(self) -> None:
        """Entries + certificates expected for all 7 modules (fails on unfixed flow)."""
        _require_planner(
            "Journal entries present only for [3, 6, 7] and certificates only for "
            "[6, 7] — missing journal entries for [1, 2, 4, 5] and certificates for "
            "[1, 2, 3, 4, 5] (Cause 2: artifact steps not bound to the shared trigger; "
            "non-uniform certificates)."
        )
        detect_artifact_gaps = _attr("detect_artifact_gaps")
        plan_backfill = _attr("plan_backfill")

        inventory = _make_inventory()
        progress = _make_progress_state()

        report = detect_artifact_gaps(REPORTED_MODULES_COMPLETED, inventory)
        missing_journal = _report_modules(
            report, "missing_journal", "missing_journal_entries"
        )
        missing_cert = _report_modules(
            report, "missing_certificate", "missing_certificates", "missing_certs"
        )
        assert {1, 2, 4, 5}.issubset(missing_journal), (
            f"Journal gaps must include 1, 2, 4, 5. Reported missing={sorted(missing_journal)}"
        )
        assert {1, 2, 3, 4, 5}.issubset(missing_cert), (
            "Certificate gaps must include 1-5 (uniform-certificate rule). "
            f"Reported missing={sorted(missing_cert)}"
        )

        plan = plan_backfill(progress, inventory)
        plan_journal = _plan_modules(
            plan, "journal_modules", "journal_entries", "missing_journal"
        )
        plan_cert = _plan_modules(
            plan, "certificate_modules", "certificates", "missing_certificate"
        )
        journal_covered = REPORTED_JOURNAL_ENTRIES | plan_journal
        cert_covered = REPORTED_CERTIFICATES | plan_cert
        assert journal_covered.issuperset(set(REPORTED_MODULES_COMPLETED)), (
            f"After backfill, all modules must have journal entries. Covered={sorted(journal_covered)}"
        )
        assert cert_covered == set(REPORTED_MODULES_COMPLETED), (
            "After backfill, certificates must be uniform: one per completed module "
            f"(or none). Covered={sorted(cert_covered)}"
        )


# ===========================================================================
# Test case 3 — Placeholder per-module Duration (Cause 3)
# ===========================================================================


class TestPlaceholderPerModuleDuration:
    """A completed module's Duration must be computed from real ISO timestamps.

    Reported: recap Module 3 Duration reads 'Module 3 session' while
    step_history["3"].updated_at and the prior timestamp are valid ISO 8601.

    Validates: Requirements 2.2
    """

    def test_module_3_duration_is_computed_not_placeholder(self) -> None:
        """Module 3 Duration must be a real elapsed time (fails on unfixed flow)."""
        # Sanity: the reported value is a placeholder (documents the defect input).
        assert _is_placeholder(REPORTED_RECAP_DURATIONS[3]), (
            "Reported Module 3 Duration should be the placeholder 'Module 3 session'."
        )
        _require_planner(
            "Module 3 Duration reads 'Module 3 session' (placeholder) instead of a "
            "computed elapsed time, although step_history has valid ISO 8601 "
            "timestamps (Cause 3: Duration sourced from LLM session context, not "
            "step_history)."
        )
        compute_module_duration = _attr("compute_module_duration")

        prior_ts = REPORTED_STEP_HISTORY["2"]["updated_at"]  # 2025-01-10T11:30:00Z
        result = compute_module_duration(
            REPORTED_STEP_HISTORY, REPORTED_STARTED_AT, 3, prior_ts
        )
        assert result is not None, "Module 3 has valid bounds; Duration must be computed."
        assert not _is_placeholder(result), (
            f"Module 3 Duration must be a real elapsed time, not a placeholder. Got: {result!r}"
        )
        assert _looks_like_duration(result), f"Expected an elapsed time, got: {result!r}"
        # 11:30 -> 12:42 == 1h 12m.
        assert "1h" in result and "12m" in result, (
            f"Module 3 elapsed time should be 1h 12m. Got: {result!r}"
        )


# ===========================================================================
# Test case 4 — Placeholder Total Duration (Cause 3)
# ===========================================================================


class TestPlaceholderTotalDuration:
    """The recap header Total Duration must be a real cumulative elapsed time.

    Reported: header Total Duration is a placeholder while reliable per-module
    timing exists in step_history.

    Validates: Requirements 2.3
    """

    def test_total_duration_is_computed_not_placeholder(self) -> None:
        """Total Duration must roll up real per-module times (fails on unfixed flow)."""
        assert _is_placeholder(REPORTED_RECAP_TOTAL), (
            "Reported Total Duration should be a placeholder."
        )
        _require_planner(
            "Header Total Duration is a placeholder ('Module N session') although "
            "reliable per-module timing exists in step_history (Cause 3)."
        )
        compute_total_duration = _attr("compute_total_duration")

        result = compute_total_duration(
            REPORTED_STEP_HISTORY, REPORTED_STARTED_AT, REPORTED_MODULES_COMPLETED
        )
        assert result is not None, "Reliable timing exists; Total Duration must be computed."
        assert not _is_placeholder(result), (
            f"Total Duration must be a real cumulative time, not a placeholder. Got: {result!r}"
        )
        assert _looks_like_duration(result), f"Expected a cumulative time, got: {result!r}"


# ===========================================================================
# Test case 5 — No backfill mechanism (Cause 4)
# ===========================================================================


class TestBackfillFillsTheGap:
    """A partial artifact set must be completed by a deterministic backfill plan.

    Reported: partial artifact set with no trigger and no backfill routine.

    Validates: Requirements 2.6, 3.5
    """

    def test_backfill_plan_completes_the_set_without_duplicates(self) -> None:
        """Backfill must fill every gap and never re-emit existing artifacts."""
        _require_planner(
            "No backfill mechanism exists: a project with a partial artifact set "
            "([1..7] complete but recap [1-6], journal [3,6,7], certs [6,7]) has no "
            "routine to fill the missing recap sections, journal entries, or "
            "certificates (Cause 4)."
        )
        plan_backfill = _attr("plan_backfill")

        inventory = _make_inventory()
        progress = _make_progress_state()
        plan = plan_backfill(progress, inventory)

        plan_recap = _plan_modules(plan, "recap_modules", "recap_sections", "missing_recap")
        plan_journal = _plan_modules(
            plan, "journal_modules", "journal_entries", "missing_journal"
        )
        plan_cert = _plan_modules(
            plan, "certificate_modules", "certificates", "missing_certificate"
        )

        all_modules = set(REPORTED_MODULES_COMPLETED)
        # Backfill plan == the exact set difference (no duplicates of existing artifacts).
        assert plan_recap == all_modules - REPORTED_RECAP_SECTIONS, (
            f"Recap backfill must be exactly the missing set. Got {sorted(plan_recap)}"
        )
        assert plan_journal == all_modules - REPORTED_JOURNAL_ENTRIES, (
            f"Journal backfill must be exactly the missing set. Got {sorted(plan_journal)}"
        )
        assert plan_cert == all_modules - REPORTED_CERTIFICATES, (
            f"Certificate backfill must be exactly the missing set. Got {sorted(plan_cert)}"
        )
        # No artifact already on disk is re-emitted.
        assert plan_recap.isdisjoint(REPORTED_RECAP_SECTIONS)
        assert plan_journal.isdisjoint(REPORTED_JOURNAL_ENTRIES)
        assert plan_cert.isdisjoint(REPORTED_CERTIFICATES)


# ===========================================================================
# Test case 6 — Edge case: unreliable timing -> omit Duration (not placeholder)
# ===========================================================================


class TestUnreliableTimingOmitsDuration:
    """When timing cannot be derived, Duration is omitted rather than placeholdered.

    step_history["4"] is missing/unparseable, so the Module 4 ### Duration field
    must be omitted (planner returns None), never a placeholder.

    Validates: Requirements 2.2
    """

    def test_module_4_duration_omitted_when_timestamp_unparseable(self) -> None:
        """compute_module_duration returns None for unreliable bounds (omission)."""
        _require_planner(
            "Module 4 timing is unreliable (step_history['4'] missing/unparseable); "
            "the recap must OMIT the ### Duration field rather than emit a placeholder "
            "such as 'Module 4 session'."
        )
        compute_module_duration = _attr("compute_module_duration")

        # Build a step_history where module 4 is unparseable, prior bounds are valid.
        broken_history = dict(REPORTED_STEP_HISTORY)
        broken_history["4"] = {"last_completed_step": 5, "updated_at": "not-a-timestamp"}
        prior_ts = REPORTED_STEP_HISTORY["3"]["updated_at"]

        result_unparseable = compute_module_duration(
            broken_history, REPORTED_STARTED_AT, 4, prior_ts
        )
        assert result_unparseable is None, (
            "Unparseable upper bound must yield None (Duration omitted), "
            f"not a value/placeholder. Got: {result_unparseable!r}"
        )

        # Also: a completely missing module entry must yield None.
        missing_history = dict(REPORTED_STEP_HISTORY)
        missing_history.pop("4")
        result_missing = compute_module_duration(
            missing_history, REPORTED_STARTED_AT, 4, prior_ts
        )
        assert result_missing is None, (
            f"Missing module timestamp must yield None (Duration omitted). Got: {result_missing!r}"
        )


# ===========================================================================
# PBT — Bug-condition enumeration (models the input space; PASSES now)
# ===========================================================================


@dataclass
class _BugInput:
    """A modeled progress + inventory state for bug-condition enumeration."""

    modules_completed: tuple[int, ...]
    recap_sections: frozenset[int]
    journal_entries: frozenset[int]
    certificates: frozenset[int]
    per_module_durations: tuple[str, ...]
    total_duration: str
    timing_reliable: bool


def _model_is_bug_condition(x: _BugInput) -> bool:
    """Local reference model of the design's isBugCondition (no planner needed)."""
    completed = set(x.modules_completed)
    coverage_gap = any(
        (m not in x.recap_sections)
        or (m not in x.journal_entries)
        or (m not in x.certificates)
        for m in completed
    )
    has_cert = completed & x.certificates
    missing_cert = completed - x.certificates
    certificates_non_uniform = bool(has_cert) and bool(missing_cert)
    placeholder_duration = x.timing_reliable and any(
        _is_placeholder(d) for d in x.per_module_durations
    )
    placeholder_total = x.timing_reliable and _is_placeholder(x.total_duration)
    return (
        coverage_gap
        or certificates_non_uniform
        or placeholder_duration
        or placeholder_total
    )


class TestBugConditionEnumeration:
    """Model the bug-condition input space (passes now; documents the contract).

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """

    def test_reported_state_is_a_bug_condition(self) -> None:
        """The concrete reported defect state must satisfy isBugCondition."""
        reported = _BugInput(
            modules_completed=tuple(REPORTED_MODULES_COMPLETED),
            recap_sections=frozenset(REPORTED_RECAP_SECTIONS),
            journal_entries=frozenset(REPORTED_JOURNAL_ENTRIES),
            certificates=frozenset(REPORTED_CERTIFICATES),
            per_module_durations=tuple(
                REPORTED_RECAP_DURATIONS[m] for m in REPORTED_MODULES_COMPLETED
            ),
            total_duration=REPORTED_RECAP_TOTAL,
            timing_reliable=True,
        )
        assert _model_is_bug_condition(reported), (
            "The reported state must be classified as a bug condition."
        )

    @given(
        completed=st.lists(
            st.integers(min_value=1, max_value=11), min_size=1, max_size=11, unique=True
        ),
        drop=st.integers(min_value=0, max_value=11),
    )
    @settings(max_examples=25)
    def test_coverage_gap_is_a_bug_condition(self, completed: list[int], drop: int) -> None:
        """Dropping any artifact type for a completed module is a bug condition."""
        completed_set = frozenset(completed)
        # Remove one completed module from recap coverage to force a coverage gap.
        target = sorted(completed_set)[drop % len(completed_set)]
        recap = completed_set - {target}
        x = _BugInput(
            modules_completed=tuple(sorted(completed_set)),
            recap_sections=recap,
            journal_entries=completed_set,
            certificates=completed_set,
            per_module_durations=tuple("1h 0m" for _ in completed_set),
            total_duration="3h 0m",
            timing_reliable=True,
        )
        assert _model_is_bug_condition(x), (
            f"Missing recap section for module {target} must be a bug condition."
        )

    @given(
        completed=st.lists(
            st.integers(min_value=1, max_value=11), min_size=1, max_size=11, unique=True
        )
    )
    @settings(max_examples=25)
    def test_complete_consistent_state_is_not_a_bug_condition(
        self, completed: list[int]
    ) -> None:
        """A complete, uniform set with real Durations is NOT a bug condition."""
        completed_set = frozenset(completed)
        x = _BugInput(
            modules_completed=tuple(sorted(completed_set)),
            recap_sections=completed_set,
            journal_entries=completed_set,
            certificates=completed_set,
            per_module_durations=tuple("1h 0m" for _ in completed_set),
            total_duration="3h 0m",
            timing_reliable=True,
        )
        assert not _model_is_bug_condition(x), (
            "A complete, uniform, real-Duration state must not be a bug condition."
        )
