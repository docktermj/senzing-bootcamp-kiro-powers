"""Preservation suite for the module5-mapping-workflow-guidance bugfix.

Feature: module5-mapping-workflow-guidance (BUGFIX)

Property 3: Preservation — Normal Mapping Workflow Unchanged.

This suite captures the BASELINE behavior of the Module 5 Phase 2 / Phase 3
mapping-workflow guidance that the fix MUST preserve. Following the
observation-first methodology, every assertion was observed to hold on the
UNFIXED steering files first, then encoded here. It is EXPECTED TO PASS on the
unfixed guidance — that pass is the baseline; the same assertions must keep
passing after the fix to prove no regression for non-bug inputs.

The artifact under test is steering/documentation text, so the assertions check
for the presence of the guidance the fix must NOT remove, rather than executable
runtime output.

Bug Condition (from design):
    isBugCondition(X) =
        ( X.step == 4 AND ( NOT X.scriptAvailability['sz_verbatim_check.py']
                            OR NOT X.scriptAvailability['sz_routing_report.py'] ) )  # Aspect A
        OR ( X.step == 5 AND X.menuReturned == True )                                # Aspect B

Preservation scope (NOT isBugCondition): all validation scripts hosted, every
step other than the Step 4 gate and the Step 5 menu, and the explicit
test_load / load+resolve Phase 3 selections.

Expected outcome on the UNFIXED steering files:
    - Test 3.1 (analyzer / Entity-Specification validation present)  -> PASSES
    - Test 3.2 (mapping_workflow-driven validation checks present)   -> PASSES
    - Test 3.3 (per-source progression + Step 4 approval present)    -> PASSES
    - Test 3.4 (explicit Phase 3 steps 5-8 path present)             -> PASSES
    - Test 3.5 (real load deferred to Module 6)                      -> PASSES
    - PBT (non-bug WorkflowState inputs preserve the above)          -> PASSES
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Real steering files under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_PHASE2_FILE: Path = _POWER_ROOT / "steering" / "module-05-phase2-data-mapping.md"
_PHASE3_FILE: Path = _POWER_ROOT / "steering" / "module-05-phase3-test-load.md"

_VERBATIM_SCRIPT = "sz_verbatim_check.py"
_ROUTING_SCRIPT = "sz_routing_report.py"
_ANALYZER_SCRIPT = "sz_json_analyzer.py"

# The two explicit Phase 3 selections that must keep entering Steps 5-8.
_EXPLICIT_PHASE3_CHOICES = ("test_load", "load+resolve")


# ---------------------------------------------------------------------------
# Bug condition model (from design)
# ---------------------------------------------------------------------------


@dataclass
class WorkflowState:
    """A per-source mapping_workflow state.

    Attributes:
        step: The current mapping_workflow step (1-based).
        script_availability: Map of validation script name -> available (bool).
        menu_returned: Whether the Step 5 detect_environment menu was surfaced.
        remaining_sources: Count of unmapped data sources still remaining.
        selected_option: The bootcamper's explicit Step 5 selection, if any
            (e.g. "test_load" / "load+resolve"). Does not affect the bug
            condition; used only to model the preserved explicit Phase 3 paths.
    """

    step: int
    script_availability: dict[str, bool] = field(default_factory=dict)
    menu_returned: bool = False
    remaining_sources: int = 0
    selected_option: str | None = None


def is_bug_condition(state: WorkflowState) -> bool:
    """Return whether the bug manifests for the given workflow state.

    Mirrors the design's isBugCondition exactly (step, scriptAvailability,
    menuReturned). The ``selected_option`` field is intentionally NOT consulted.

    Args:
        state: The mapping_workflow state to evaluate.

    Returns:
        True when the bug condition holds for the given state.
    """
    gate_blocked = state.step == 4 and (
        not state.script_availability.get(_VERBATIM_SCRIPT, True)
        or not state.script_availability.get(_ROUTING_SCRIPT, True)
    )
    dead_end = state.step == 5 and state.menu_returned
    return gate_blocked or dead_end


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_phase2() -> str:
    """Read the Module 5 Phase 2 steering file contents."""
    return _PHASE2_FILE.read_text(encoding="utf-8")


def _read_phase3() -> str:
    """Read the Module 5 Phase 3 steering file contents."""
    return _PHASE3_FILE.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace and lowercase for resilient phrase matching."""
    return re.sub(r"\s+", " ", text).lower()


def _has_analyzer_validation(phase2_norm: str) -> bool:
    """Baseline: structural / Entity-Specification validation is present (3.1).

    The unfixed guidance anchors mapping validation on ``analyze_record`` and the
    Senzing entity specification reference. The script-name anchor
    (``sz_json_analyzer.py``) is also accepted so the assertion keeps holding
    after the fix names the analyzer explicitly.
    """
    has_analyze_record = "analyze_record" in phase2_norm
    has_entity_spec = (
        "senzing_entity_specification" in phase2_norm
        or "entity specification" in phase2_norm
    )
    names_analyzer = _ANALYZER_SCRIPT.lower() in phase2_norm
    return (has_analyze_record and has_entity_spec) or names_analyzer


def _has_workflow_driven_validation(phase2_norm: str) -> bool:
    """Baseline: validation runs through mapping_workflow generate/validate (3.2).

    When the verbatim/routing checks are available they run as part of the
    mapping_workflow generate/validate flow. The durable anchors are the
    workflow actions that drive mapping and the quality verdict.
    """
    return (
        "mapping_workflow" in phase2_norm
        and "schema_mappings" in phase2_norm
        and "verdict" in phase2_norm
    )


def _has_per_source_progression(phase2_norm: str) -> bool:
    """Baseline: normal per-source progression + Step 4 approval gate (3.3)."""
    starts_workflow = "mapping_workflow(action='start')" in phase2_norm
    per_source = "per-source" in phase2_norm or "per source" in phase2_norm
    approval_gate = "iterate vs. proceed" in phase2_norm or "review" in phase2_norm
    status_tracked = "mapping_status" in phase2_norm
    return starts_workflow and per_source and approval_gate and status_tracked


def _has_explicit_phase3_path(phase3_norm: str) -> bool:
    """Baseline: explicit test_load / load+resolve enters Phase 3 Steps 5-8 (3.4)."""
    is_optional = "optional" in phase3_norm
    uses_workflow_steps = "mapping_workflow" in phase3_norm and (
        "steps 5\u20138" in phase3_norm  # en-dash form used in the file
        or "steps 5-8" in phase3_norm
        or "steps 5" in phase3_norm
    )
    test_load_path = "test load" in phase3_norm or "test_load" in phase3_norm
    return is_optional and uses_workflow_steps and test_load_path


def _defers_real_load_to_module6(phase2_norm: str, phase3_norm: str) -> bool:
    """Baseline: the production/real load is deferred to Module 6 (3.5)."""
    return "module 6" in phase2_norm and "module 6" in phase3_norm


# ---------------------------------------------------------------------------
# Strategies — non-bug WorkflowState inputs only
# ---------------------------------------------------------------------------


@st.composite
def st_non_bug_state(draw) -> WorkflowState:
    """Draw a WorkflowState for which ``is_bug_condition`` is False.

    Covers: all three scripts hosted, every step other than the Step 4 gate and
    the Step 5 menu, with arbitrary remaining-source counts.
    """
    step = draw(st.integers(min_value=1, max_value=13))
    verbatim = draw(st.booleans())
    routing = draw(st.booleans())
    analyzer = draw(st.booleans())
    # Step 5 here represents the non-menu case; the menu case is the bug (Aspect B).
    menu_returned = draw(st.booleans()) if step != 5 else False
    state = WorkflowState(
        step=step,
        script_availability={
            _VERBATIM_SCRIPT: verbatim,
            _ROUTING_SCRIPT: routing,
            _ANALYZER_SCRIPT: analyzer,
        },
        menu_returned=menu_returned,
        remaining_sources=draw(st.integers(min_value=0, max_value=5)),
    )
    # Guarantee the non-bug invariant regardless of the drawn availability.
    assume(not is_bug_condition(state))
    return state


@st.composite
def st_all_scripts_hosted_state(draw) -> WorkflowState:
    """Draw a non-bug state with all three validation scripts hosted (HTTP 200)."""
    step = draw(st.integers(min_value=1, max_value=13))
    assume(step != 5)  # avoid the Step 5 menu (Aspect B)
    state = WorkflowState(
        step=step,
        script_availability={
            _VERBATIM_SCRIPT: True,
            _ROUTING_SCRIPT: True,
            _ANALYZER_SCRIPT: True,
        },
        menu_returned=False,
        remaining_sources=draw(st.integers(min_value=0, max_value=5)),
    )
    assert not is_bug_condition(state)
    return state


@st.composite
def st_explicit_phase3_choice_state(draw) -> WorkflowState:
    """Draw a Step 5 state where the bootcamper explicitly chose a Phase 3 path.

    This models requirement 3.4: an explicit ``test_load`` / ``load+resolve``
    selection that must continue to enter Phase 3 (Steps 5-8). It is the
    user-driven path, distinct from the unguided dead-end (Aspect B).
    """
    return WorkflowState(
        step=5,
        script_availability={
            _VERBATIM_SCRIPT: True,
            _ROUTING_SCRIPT: True,
            _ANALYZER_SCRIPT: True,
        },
        menu_returned=True,
        remaining_sources=draw(st.integers(min_value=0, max_value=5)),
        selected_option=draw(st.sampled_from(_EXPLICIT_PHASE3_CHOICES)),
    )


# ---------------------------------------------------------------------------
# Property 3 — Preservation (example-based anchors)
# These assertions PASS on the unfixed guidance and must keep passing post-fix.
# ---------------------------------------------------------------------------


class TestNormalMappingWorkflowPreserved:
    """Baseline Module 5 behavior the fix must not change.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """

    def test_analyzer_validation_preserved(self) -> None:
        """3.1: structural + Entity-Specification validation remains present."""
        norm = _norm(_read_phase2())
        assert _has_analyzer_validation(norm), (
            "Baseline mapping validation (analyze_record + entity specification "
            "reference) must remain present in the Phase 2 guidance."
        )

    def test_available_script_checks_preserved(self) -> None:
        """3.2: verbatim/routing checks run via the mapping_workflow flow as before."""
        norm = _norm(_read_phase2())
        assert _has_workflow_driven_validation(norm), (
            "Baseline mapping_workflow-driven validation (schema_mappings + "
            "verdict) must remain present so available-script checks still run."
        )

    def test_per_source_progression_and_approval_preserved(self) -> None:
        """3.3: normal per-source progression and Step 4 approval remain present."""
        norm = _norm(_read_phase2())
        assert _has_per_source_progression(norm), (
            "Baseline per-source mapping_workflow progression (start, per-source "
            "requirement, status tracking, review/approval gate) must remain."
        )

    def test_explicit_phase3_path_preserved(self) -> None:
        """3.4: explicit test_load / load+resolve still enters Phase 3 Steps 5-8."""
        norm = _norm(_read_phase3())
        assert _has_explicit_phase3_path(norm), (
            "Baseline optional Phase 3 path (mapping_workflow steps 5-8 test "
            "load) must remain present in the Phase 3 steering file."
        )

    def test_real_load_deferred_to_module6_preserved(self) -> None:
        """3.5: the production/real load remains deferred to Module 6."""
        phase2_norm = _norm(_read_phase2())
        phase3_norm = _norm(_read_phase3())
        assert _defers_real_load_to_module6(phase2_norm, phase3_norm), (
            "Baseline deferral of the real load to Module 6 must remain present "
            "in both the Phase 2 and Phase 3 guidance."
        )


# ---------------------------------------------------------------------------
# Property 3 — Preservation (property-based over non-bug inputs)
# ---------------------------------------------------------------------------


class TestPreservationOverNonBugInputs:
    """For every non-bug WorkflowState input, the baseline guidance holds.

    These properties generate non-bug inputs across the input domain and assert
    the captured baseline behavior is present, independent of the specific
    (non-bug) state. They PASS on the unfixed guidance and must keep passing.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """

    @given(state=st_non_bug_state())
    @settings(max_examples=30)
    def test_non_bug_states_preserve_core_validation(
        self, state: WorkflowState
    ) -> None:
        """Any non-bug state preserves analyzer + workflow-driven validation (3.1, 3.2)."""
        assert not is_bug_condition(state)
        phase2_norm = _norm(_read_phase2())
        assert _has_analyzer_validation(phase2_norm), (
            f"Analyzer validation must be preserved for non-bug state {state!r}"
        )
        assert _has_workflow_driven_validation(phase2_norm), (
            f"Workflow-driven validation must be preserved for non-bug state {state!r}"
        )

    @given(state=st_all_scripts_hosted_state())
    @settings(max_examples=25)
    def test_all_scripts_hosted_preserve_progression(
        self, state: WorkflowState
    ) -> None:
        """All-scripts-hosted states preserve per-source progression + approval (3.3)."""
        assert not is_bug_condition(state)
        assert state.script_availability[_VERBATIM_SCRIPT] is True
        assert state.script_availability[_ROUTING_SCRIPT] is True
        phase2_norm = _norm(_read_phase2())
        assert _has_per_source_progression(phase2_norm), (
            f"Per-source progression must be preserved for hosted state {state!r}"
        )

    @given(state=st_explicit_phase3_choice_state())
    @settings(max_examples=25)
    def test_explicit_choice_preserves_phase3_path(
        self, state: WorkflowState
    ) -> None:
        """Explicit test_load / load+resolve preserves the Phase 3 path + M6 deferral (3.4, 3.5)."""
        assert state.selected_option in _EXPLICIT_PHASE3_CHOICES
        phase3_norm = _norm(_read_phase3())
        phase2_norm = _norm(_read_phase2())
        assert _has_explicit_phase3_path(phase3_norm), (
            "Explicit Phase 3 path (steps 5-8) must be preserved for choice "
            f"{state.selected_option!r}"
        )
        assert _defers_real_load_to_module6(phase2_norm, phase3_norm), (
            "Real-load deferral to Module 6 must be preserved for choice "
            f"{state.selected_option!r}"
        )
