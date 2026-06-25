"""Bug condition exploration suite for the module5-mapping-workflow-guidance bugfix.

Feature: module5-mapping-workflow-guidance (BUGFIX)

Property 1: Bug Condition — Resilient Validation When Scripts Are Unavailable.
Property 2: Bug Condition — Forward Guidance After the Step 5 Menu.

This suite encodes the *fixed* (post-fix) contract for the Module 5 Phase 2
mapping-workflow guidance. It is EXPECTED TO FAIL on the unfixed steering file:
the failures are the success criterion — they surface counterexamples proving
the bug exists. The artifact under test is steering/documentation text, so the
assertions check for the presence of the required guidance branches and the
conditions under which they apply, rather than executable runtime output.

Bug Condition (from design):
    isBugCondition(X) =
        ( X.step == 4 AND ( NOT X.scriptAvailability['sz_verbatim_check.py']
                            OR NOT X.scriptAvailability['sz_routing_report.py'] ) )  # Aspect A
        OR ( X.step == 5 AND X.menuReturned == True )                                # Aspect B

Expected outcome on the UNFIXED steering file:
    - Test 1 (verbatim unavailable -> skip-as-optional branch)   -> FAILS  (no branch)
    - Test 2 (routing unavailable  -> skip-as-optional branch)   -> FAILS  (no branch)
    - Test 3 (sz_json_analyzer.py named as primary validation)   -> FAILS  (not named)
    - Test 4 (Step 5 detect_environment menu explained)          -> FAILS  (no handling)
    - Test 5 (skip test load + continue to next source)          -> FAILS  (no guidance)
    - PBT  (bug condition enumeration)                           -> PASSES (models input space)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Real steering file under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_FILE: Path = _POWER_ROOT / "steering" / "module-05-phase2-data-mapping.md"

_VERBATIM_SCRIPT = "sz_verbatim_check.py"
_ROUTING_SCRIPT = "sz_routing_report.py"
_ANALYZER_SCRIPT = "sz_json_analyzer.py"


# ---------------------------------------------------------------------------
# Bug condition model (from design)
# ---------------------------------------------------------------------------


@dataclass
class WorkflowState:
    """A per-source mapping_workflow state characterizing the bug condition.

    Attributes:
        step: The current mapping_workflow step (1-based).
        script_availability: Map of validation script name -> available (bool).
        menu_returned: Whether the Step 5 detect_environment menu was surfaced.
        remaining_sources: Count of unmapped data sources still remaining.
    """

    step: int
    script_availability: dict[str, bool] = field(default_factory=dict)
    menu_returned: bool = False
    remaining_sources: int = 0


def is_bug_condition(state: WorkflowState) -> bool:
    """Return whether the bug manifests for the given workflow state.

    The bug manifests at two points (per design):
      - Aspect A: At Step 4, a required validation script (verbatim-fidelity or
        routing-coverage) is unavailable while the guidance still treats its check
        as required, leaving the workflow blocked.
      - Aspect B: The Step 5 detect_environment menu is returned with no forward
        guidance.

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


def _read_steering() -> str:
    """Read the Module 5 Phase 2 steering file contents."""
    return _STEERING_FILE.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace and lowercase for resilient phrase matching."""
    return re.sub(r"\s+", " ", text).lower()


def _mentions_unavailable(content: str, script: str) -> bool:
    """Return whether the guidance ties `script` to an unavailable/404 skip branch.

    Looks for the script name appearing near unavailability + skip/optional/proceed
    language, which encodes the "if <script> unavailable -> skip as optional, proceed"
    degradation branch the fix must add.
    """
    norm = _norm(content)
    if script.lower() not in norm:
        return False
    unavailable_cues = ("unavailable", "404", "not available", "missing")
    skip_cues = ("skip", "optional", "best-effort", "best effort", "proceed", "continue")
    for match in re.finditer(re.escape(script.lower()), norm):
        window = norm[max(0, match.start() - 240): match.end() + 240]
        if any(c in window for c in unavailable_cues) and any(
            c in window for c in skip_cues
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_gate_blocked_state(draw) -> WorkflowState:
    """Draw a Step 4 state where at least one gated script is unavailable (Aspect A)."""
    verbatim = draw(st.booleans())
    routing = draw(st.booleans())
    # Ensure at least one of the gated scripts is unavailable.
    if verbatim and routing:
        if draw(st.booleans()):
            verbatim = False
        else:
            routing = False
    return WorkflowState(
        step=4,
        script_availability={
            _VERBATIM_SCRIPT: verbatim,
            _ROUTING_SCRIPT: routing,
            _ANALYZER_SCRIPT: True,  # analyzer hosted (HTTP 200)
        },
        menu_returned=False,
        remaining_sources=draw(st.integers(min_value=0, max_value=5)),
    )


@st.composite
def st_dead_end_state(draw) -> WorkflowState:
    """Draw a Step 5 state with the detect_environment menu returned (Aspect B)."""
    return WorkflowState(
        step=5,
        script_availability={
            _VERBATIM_SCRIPT: draw(st.booleans()),
            _ROUTING_SCRIPT: draw(st.booleans()),
            _ANALYZER_SCRIPT: True,
        },
        menu_returned=True,
        remaining_sources=draw(st.integers(min_value=1, max_value=5)),
    )


# ---------------------------------------------------------------------------
# Property 1 — Resilient validation when scripts are unavailable (Aspect A)
# These assertions encode the FIXED contract and FAIL on the unfixed steering.
# ---------------------------------------------------------------------------


class TestResilientValidationGuidance:
    """Step 4 guidance must degrade unavailable validation scripts to optional.

    These assertions encode the FIXED contract and are EXPECTED TO FAIL on the
    unfixed steering file — proving the hard-gate framing with no unavailability
    branch is present.

    Validates: Requirements 2.1, 2.2, 2.3
    """

    def test_verbatim_unavailable_skip_branch_present(self) -> None:
        """Test 1: an "if sz_verbatim_check.py unavailable -> skip, proceed" branch exists.

        Bug Condition Aspect A; expected behavior 2.1.
        """
        content = _read_steering()
        assert _mentions_unavailable(content, _VERBATIM_SCRIPT), (
            f"Step 4 guidance is missing an 'if {_VERBATIM_SCRIPT} unavailable "
            "(HTTP 404) -> skip as optional/best-effort, proceed' branch. The "
            "verbatim-fidelity check is still framed as a hard gate with no "
            "unavailability off-ramp (bug present)."
        )

    def test_routing_unavailable_skip_branch_present(self) -> None:
        """Test 2: an "if sz_routing_report.py unavailable -> skip, proceed" branch exists.

        Bug Condition Aspect A; expected behavior 2.2.
        """
        content = _read_steering()
        assert _mentions_unavailable(content, _ROUTING_SCRIPT), (
            f"Step 4 guidance is missing an 'if {_ROUTING_SCRIPT} unavailable "
            "(HTTP 404) -> skip as optional/best-effort, proceed' branch. The "
            "routing-coverage report is still required with no degradation "
            "branch (bug present)."
        )

    def test_analyzer_named_as_primary_validation(self) -> None:
        """Test 3: sz_json_analyzer.py is named as the primary validation to proceed.

        The guidance must name sz_json_analyzer.py as sufficient to proceed when the
        verbatim/routing scripts are absent. Expected behavior 2.3.
        """
        content = _read_steering()
        norm = _norm(content)
        assert _ANALYZER_SCRIPT.lower() in norm, (
            f"Step 4 guidance does not name {_ANALYZER_SCRIPT} as the primary "
            "mapping validation that allows the workflow to proceed when the "
            "verbatim/routing scripts are unavailable (bug present)."
        )
        idx = norm.find(_ANALYZER_SCRIPT.lower())
        window = norm[max(0, idx - 240): idx + 240]
        assert any(
            cue in window for cue in ("primary", "proceed", "sufficient", "continue")
        ), (
            f"{_ANALYZER_SCRIPT} is mentioned but not anchored as the primary "
            "validation sufficient to proceed without the other scripts (bug present)."
        )


# ---------------------------------------------------------------------------
# Property 2 — Forward guidance after the Step 5 menu (Aspect B)
# These assertions encode the FIXED contract and FAIL on the unfixed steering.
# ---------------------------------------------------------------------------


class TestStep5MenuForwardGuidance:
    """Guidance must explain the Step 5 detect_environment menu and continuation.

    These assertions encode the FIXED contract and are EXPECTED TO FAIL on the
    unfixed steering file — proving there is no Step 5 menu handling.

    Validates: Requirements 2.4, 2.5
    """

    def test_detect_environment_menu_explained(self) -> None:
        """Test 4: Steps 5-8 are labeled optional and the four options enumerated.

        Bug Condition Aspect B; expected behavior 2.4.
        """
        content = _read_steering()
        norm = _norm(content)
        assert "detect_environment" in norm, (
            "Step 5 guidance does not reference the mapping_workflow "
            "'detect_environment' menu at all (bug present)."
        )
        assert ("optional" in norm) and (
            "steps 5" in norm or "steps 5-8" in norm or "steps 5–8" in norm
        ), (
            "Guidance does not state that Steps 5–8 are optional sandbox "
            "validation (bug present)."
        )
        # All four menu options must be enumerated.
        for option in ("skip", "test_load", "load+resolve", "done"):
            assert option in norm, (
                "Step 5 menu guidance does not enumerate the four "
                f"detect_environment options; missing {option!r} (bug present)."
            )

    def test_skip_and_continue_to_next_source(self) -> None:
        """Test 5: recommend skipping the per-source test load and continue next source.

        The guidance must recommend skipping the per-source test load (real load
        deferred to Module 6) and continuing to the next unmapped source when sources
        remain. Bug Condition Aspect B; expected behavior 2.5.
        """
        content = _read_steering()
        norm = _norm(content)
        defers_to_m6 = "module 6" in norm
        recommends_skip = "skip" in norm and (
            "test load" in norm or "test_load" in norm
        )
        continues_next = "next" in norm and (
            "unmapped source" in norm or "next source" in norm or "next data source" in norm
        )
        assert defers_to_m6 and recommends_skip and continues_next, (
            "Step 5 guidance does not recommend skipping the per-source test load "
            "(real load deferred to Module 6) and continuing to the next unmapped "
            "source when sources remain (bug present). "
            f"[defers_to_module_6={defers_to_m6}, recommends_skip_test_load="
            f"{recommends_skip}, continues_to_next_source={continues_next}]"
        )


# ---------------------------------------------------------------------------
# PBT — Bug condition enumeration — PASSES (models the bug input space)
# ---------------------------------------------------------------------------


class TestBugConditionEnumeration:
    """Enumerate the bug-condition input space across both aspects.

    These property tests model the WorkflowState input space and PASS — they
    confirm which states are bug conditions, independent of the steering text.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """

    @given(state=st_gate_blocked_state())
    @settings(max_examples=20)
    def test_step4_unavailable_script_is_bug_condition(
        self, state: WorkflowState
    ) -> None:
        """Any Step 4 state with a gated script unavailable is a bug condition (Aspect A)."""
        assert is_bug_condition(state), (
            "Expected bug condition at Step 4 with an unavailable gated script: "
            f"{state!r}"
        )

    @given(state=st_dead_end_state())
    @settings(max_examples=20)
    def test_step5_menu_returned_is_bug_condition(self, state: WorkflowState) -> None:
        """Any Step 5 state with the detect_environment menu returned is a bug (Aspect B)."""
        assert is_bug_condition(state), (
            f"Expected bug condition at Step 5 with menu returned: {state!r}"
        )

    @given(
        step=st.integers(min_value=1, max_value=13),
        verbatim=st.booleans(),
        routing=st.booleans(),
    )
    @settings(max_examples=20)
    def test_all_scripts_hosted_not_bug_at_non_gate_steps(
        self, step: int, verbatim: bool, routing: bool
    ) -> None:
        """All scripts hosted and not at the Step 5 menu is NOT a bug condition."""
        state = WorkflowState(
            step=step,
            script_availability={
                _VERBATIM_SCRIPT: True,
                _ROUTING_SCRIPT: True,
                _ANALYZER_SCRIPT: True,
            },
            menu_returned=False,
            remaining_sources=0,
        )
        assert not is_bug_condition(state), (
            "All scripts hosted and no Step 5 menu must not be a bug condition: "
            f"{state!r}"
        )
