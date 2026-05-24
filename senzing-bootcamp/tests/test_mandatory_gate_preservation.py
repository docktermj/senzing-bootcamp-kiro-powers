"""Preservation property tests for mandatory-visualization-gate bugfix.

These tests observe UNFIXED code behavior and assert properties that must be
preserved after the fix is applied. ALL tests are EXPECTED TO PASS on unfixed
code — they capture baseline behavior that must not regress.

The preservation goal from the design:
  FOR ALL X WHERE NOT isBugCondition(X) DO
    ASSERT agentBehavior(X) = agentBehavior'(X)
  END FOR

Specifically:
- Non-mandatory steps execute without interference
- Bootcamper-initiated skips of non-⛔ steps proceed normally
- Bootcamper-initiated skip attempts on ⛔ steps are refused
- Context budget management operates independently of step skip logic

Feature: mandatory-visualization-gate

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"
_STEERING_DIR = _BOOTCAMP_DIR / "steering"

# Key files for preservation checking
_SKIP_PROTOCOL = _STEERING_DIR / "skip-step-protocol.md"
_MODULE3_STEERING = _STEERING_DIR / "module-03-system-verification.md"
_GATE_HOOK = _HOOKS_DIR / "gate-module3-visualization.kiro.hook"

# ---------------------------------------------------------------------------
# Baselines — snapshot UNFIXED file content
# ---------------------------------------------------------------------------

_UNFIXED_SKIP_PROTOCOL = _SKIP_PROTOCOL.read_text(encoding="utf-8")
_UNFIXED_MODULE3 = _MODULE3_STEERING.read_text(encoding="utf-8")
_UNFIXED_GATE_HOOK = _GATE_HOOK.read_text(encoding="utf-8")
_UNFIXED_GATE_HOOK_JSON = json.loads(_UNFIXED_GATE_HOOK)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# All Module 3 steps (1-12)
_ALL_STEPS = list(range(1, 13))

# Non-mandatory steps (all steps except Step 9 which has ⛔)
_NON_MANDATORY_STEPS = [s for s in _ALL_STEPS if s != 9]

# Mandatory gate step
_MANDATORY_GATE_STEP = 9

# Checkpoint keys for Step 9 (the mandatory gate)
_STEP9_CHECKPOINT_KEYS = ("web_service", "web_page")

# All checkpoint keys for Module 3 verification
_ALL_CHECKPOINT_KEYS = (
    "mcp_connectivity",
    "truthset_acquisition",
    "sdk_initialization",
    "code_generation",
    "build_compilation",
    "data_loading",
    "results_validation",
    "database_operations",
    "web_service",
    "web_page",
)


def _extract_step_section(content: str, step_number: int) -> str:
    """Extract a step section from the Module 3 steering file.

    Args:
        content: Full markdown content of the steering file.
        step_number: The step number to extract.

    Returns:
        The full text of the step section, or empty string if not found.
    """
    pattern = re.compile(
        rf"^###\s+Step\s+{step_number}:",
        re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    start = match.start()
    # Find next step heading or phase heading
    next_heading = re.compile(r"^###?\s+(?:Step\s+\d+|Phase)", re.MULTILINE)
    next_match = next_heading.search(content, start + 1)
    if next_match:
        return content[start:next_match.start()]
    return content[start:]


def _step_has_mandatory_gate_marker(content: str, step_number: int) -> bool:
    """Check if a step section contains the ⛔ mandatory gate marker.

    Args:
        content: Full markdown content of the steering file.
        step_number: The step number to check.

    Returns:
        True if the step contains ⛔, False otherwise.
    """
    section = _extract_step_section(content, step_number)
    return "⛔" in section


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_non_mandatory_step(draw: st.DrawFn) -> int:
    """Generate a non-mandatory step number (1-8, 10-12).

    Returns:
        A step number that does NOT have a ⛔ mandatory gate marker.
    """
    return draw(st.sampled_from(_NON_MANDATORY_STEPS))


@st.composite
def st_progress_with_step9_checkpoints(draw: st.DrawFn) -> dict:
    """Generate a progress state where all ⛔ mandatory gate checkpoints exist.

    This represents a state where Step 9 was properly executed — the
    web_service and web_page checkpoints are present with passed status.

    Returns:
        A progress dict with Step 9 checkpoints present.
    """
    current_step = draw(st.integers(min_value=10, max_value=12))
    extra_checks = draw(st.booleans())

    checks: dict = {
        "web_service": {"status": "passed", "port": 8080},
        "web_page": {"status": "passed", "url": "http://localhost:8080/"},
    }
    if extra_checks:
        checks["mcp_connectivity"] = {"status": "passed", "duration_ms": 100}
        checks["sdk_initialization"] = {"status": "passed", "duration_ms": 300}
        checks["data_loading"] = {"status": "passed", "records_loaded": 35}

    return {
        "current_module": 3,
        "modules_completed": [1, 2],
        "current_step": current_step,
        "language": "python",
        "module_3_verification": {"checks": checks},
    }


@st.composite
def st_bootcamper_skip_entry(draw: st.DrawFn) -> dict:
    """Generate a bootcamper-initiated skip entry for a non-mandatory step.

    This represents a legitimate skip via the skip-step protocol.

    Returns:
        A dict with module.step key and skip metadata.
    """
    module = draw(st.integers(min_value=1, max_value=11))
    step = draw(st.sampled_from(_NON_MANDATORY_STEPS))
    reason = draw(st.sampled_from(["a", "b", "c"]))
    note = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("L", "N", "Z"),
    )))

    return {
        "key": f"{module}.{step}",
        "entry": {
            "reason": reason,
            "note": note,
            "skipped_at": "2026-05-13T10:00:00Z",
        },
    }


@st.composite
def st_progress_advancing_past_non_mandatory(draw: st.DrawFn) -> dict:
    """Generate a progress state where current_step advances past a non-⛔ step.

    This represents normal step advancement that should never be blocked.

    Returns:
        A progress dict with current_step past a non-mandatory step.
    """
    # Pick a non-mandatory step that was "just completed"
    completed_step = draw(st.sampled_from([s for s in _NON_MANDATORY_STEPS if s < 12]))
    current_step = completed_step + 1

    return {
        "current_module": 3,
        "modules_completed": [1, 2],
        "current_step": current_step,
        "language": "python",
        "module_3_verification": {
            "checks": {},
        },
    }


# ---------------------------------------------------------------------------
# Property 2.1: Non-mandatory steps have no ⛔ marker
# ---------------------------------------------------------------------------


class TestNonMandatoryStepsNoGateMarker:
    """For all non-mandatory steps, no ⛔ marker exists in the steering file.

    This confirms that the validation script (once created) should report no
    violation for these steps regardless of checkpoint state.

    **Validates: Requirements 3.3**
    """

    @given(step_num=st_non_mandatory_step())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_mandatory_steps_have_no_gate_marker(self, step_num: int) -> None:
        """For any non-mandatory step, the ⛔ marker is absent.

        Args:
            step_num: A generated non-mandatory step number.
        """
        content = _MODULE3_STEERING.read_text(encoding="utf-8")
        section = _extract_step_section(content, step_num)

        # Non-mandatory steps must NOT have the ⛔ marker
        assert "⛔" not in section, (
            f"Step {step_num} unexpectedly contains ⛔ mandatory gate marker. "
            f"Only Step 9 should have this marker. Non-mandatory steps must "
            f"remain free of enforcement markers."
        )


# ---------------------------------------------------------------------------
# Property 2.2: Step advancement past non-⛔ steps has no enforcement
# ---------------------------------------------------------------------------


class TestNoEnforcementOnNonMandatoryAdvancement:
    """For all steps where current_step advances past a non-⛔ step, no
    enforcement fires.

    The existing gate-module3-visualization.kiro.hook only fires on Module 3
    COMPLETION writes (adding 3 to modules_completed), not on step advancement.
    Non-mandatory step advancement must remain unblocked.

    **Validates: Requirements 3.3**
    """

    @given(progress=st_progress_advancing_past_non_mandatory())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_existing_hook_does_not_block_non_mandatory_advancement(
        self, progress: dict
    ) -> None:
        """For any step advancement past a non-⛔ step, the existing hook
        does not fire (it only fires on module completion writes).

        Args:
            progress: A generated progress state advancing past a non-mandatory step.
        """
        # The existing gate hook's prompt only checks for Module 3 COMPLETION
        # writes (adding 3 to modules_completed or setting status to 'passed').
        # It does NOT check individual step advancement.
        hook_prompt = _UNFIXED_GATE_HOOK_JSON["then"]["prompt"]

        # Verify the hook only cares about module completion, not step advancement
        assert "modules_completed" in hook_prompt or "module_3_verification.status" in hook_prompt, (
            "Gate hook prompt should reference module completion conditions"
        )

        # The hook does NOT reference current_step advancement
        assert "current_step" not in hook_prompt, (
            "Existing gate hook should NOT reference current_step — "
            "it only gates module completion, not step advancement. "
            f"Progress state: current_step={progress['current_step']}"
        )

    def test_enforcement_hook_does_not_interfere_with_non_mandatory_advancement(self) -> None:
        """The enforce-mandatory-gate hook does not block non-mandatory step advancement.

        The hook only fires when current_step advances past Step 9 (the ⛔
        mandatory gate). For all other step advancements, the hook's prompt
        explicitly states to produce no output — meaning non-mandatory step
        advancement remains completely unblocked.
        """
        enforce_hook = _HOOKS_DIR / "enforce-mandatory-gate.kiro.hook"
        # After the fix, this hook EXISTS
        assert enforce_hook.exists(), (
            "enforce-mandatory-gate.kiro.hook must exist after the fix is applied."
        )

        # Read and parse the hook
        hook_data = json.loads(enforce_hook.read_text(encoding="utf-8"))
        hook_prompt = hook_data["then"]["prompt"]

        # The hook only checks for advancement past Step 9 specifically
        # For non-Step-9 advancement, it produces no output (no interference)
        assert "Step 9" in hook_prompt, (
            "Enforcement hook must specifically reference Step 9 (the mandatory gate)"
        )
        assert "produce no output" in hook_prompt, (
            "Enforcement hook must produce no output for non-mandatory advancement — "
            "this ensures non-mandatory steps are not blocked"
        )


# ---------------------------------------------------------------------------
# Property 2.3: Bootcamper-initiated skips are legitimate
# ---------------------------------------------------------------------------


class TestBootcamperSkipsLegitimate:
    """For all bootcamper-initiated skip entries in skipped_steps, the system
    treats them as legitimate.

    The skip-step protocol handles bootcamper-initiated skips of non-mandatory
    steps. The existing gate hook accepts skipped_steps["3.9"] as a valid
    alternative to checkpoints.

    **Validates: Requirements 3.1, 3.2**
    """

    @given(skip_entry=st_bootcamper_skip_entry())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_skip_protocol_structure_supports_bootcamper_skips(
        self, skip_entry: dict
    ) -> None:
        """For any bootcamper-initiated skip, the protocol defines the handling.

        The skip-step-protocol.md defines the structure for recording skips
        and the protocol for handling them.

        Args:
            skip_entry: A generated skip entry with module.step key and metadata.
        """
        # The skip protocol must define the recording structure
        protocol_content = _SKIP_PROTOCOL.read_text(encoding="utf-8")

        # Protocol must have the skipped_steps JSON structure
        assert "skipped_steps" in protocol_content, (
            "Skip protocol must define skipped_steps recording structure"
        )

        # Protocol must define reason field
        assert "reason" in protocol_content, (
            "Skip protocol must define reason field for skip entries"
        )

        # The skip entry structure must match what the protocol defines
        entry = skip_entry["entry"]
        assert entry["reason"] in ("a", "b", "c"), (
            f"Skip reason '{entry['reason']}' not in protocol-defined options"
        )

    def test_existing_gate_hook_accepts_skipped_steps_entry(self) -> None:
        """The existing gate hook treats skipped_steps['3.9'] as legitimate.

        CONDITION B in the hook prompt: if skipped_steps contains '3.9',
        the hook produces no output (allows the write).
        """
        hook_prompt = _UNFIXED_GATE_HOOK_JSON["then"]["prompt"]

        # The hook must check for skipped_steps entry as an alternative
        assert "skipped_steps" in hook_prompt, (
            "Gate hook must check skipped_steps as alternative to checkpoints"
        )
        assert "3.9" in hook_prompt, (
            "Gate hook must specifically check for skipped_steps['3.9']"
        )

    def test_skip_protocol_refuses_mandatory_gate_skips(self) -> None:
        """The skip protocol explicitly states mandatory gates cannot be skipped.

        This is the existing behavior: bootcamper attempts to skip a ⛔ step
        are refused with help offered.
        """
        protocol_content = _SKIP_PROTOCOL.read_text(encoding="utf-8")

        # Must contain the mandatory gate constraint
        assert "Mandatory gates" in protocol_content, (
            "Skip protocol must mention mandatory gates constraint"
        )
        assert "cannot be skipped" in protocol_content, (
            "Skip protocol must state mandatory gates cannot be skipped"
        )
        assert "⛔" in protocol_content, (
            "Skip protocol must reference ⛔ symbol for mandatory gates"
        )


# ---------------------------------------------------------------------------
# Property 2.4: Validation passes when all ⛔ checkpoints exist
# ---------------------------------------------------------------------------


class TestValidationPassesWithCheckpoints:
    """For progress states where all ⛔ mandatory gate checkpoints exist,
    validation passes regardless of other state.

    The existing gate hook (CONDITION A) checks for web_service and web_page
    checkpoints. When both exist with 'passed' status, the hook produces no
    output — allowing the write.

    **Validates: Requirements 3.4**
    """

    @given(progress=st_progress_with_step9_checkpoints())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_gate_hook_allows_completion_when_checkpoints_exist(
        self, progress: dict
    ) -> None:
        """When Step 9 checkpoints exist, the gate hook does not block.

        The hook's CONDITION A checks for web_service.status='passed' and
        web_page.status='passed'. When both are present, the hook produces
        no output regardless of other progress state.

        Args:
            progress: A generated progress state with Step 9 checkpoints present.
        """
        checks = progress["module_3_verification"]["checks"]

        # Verify our generated state has the required checkpoints
        assert "web_service" in checks, "Generated state must have web_service"
        assert "web_page" in checks, "Generated state must have web_page"
        assert checks["web_service"]["status"] == "passed", (
            "web_service must have passed status"
        )
        assert checks["web_page"]["status"] == "passed", (
            "web_page must have passed status"
        )

        # The hook prompt defines CONDITION A — both checkpoints with 'passed'
        hook_prompt = _UNFIXED_GATE_HOOK_JSON["then"]["prompt"]
        assert "web_service" in hook_prompt, (
            "Hook must check web_service checkpoint"
        )
        assert "web_page" in hook_prompt, (
            "Hook must check web_page checkpoint"
        )
        assert "passed" in hook_prompt, (
            "Hook must check for 'passed' status"
        )

    def test_gate_hook_condition_a_structure(self) -> None:
        """The gate hook CONDITION A checks both web_service and web_page status.

        This verifies the exact structure that the fix must preserve.
        """
        hook_prompt = _UNFIXED_GATE_HOOK_JSON["then"]["prompt"]

        # Must check web_service.status equals "passed"
        assert re.search(r"web_service.*passed", hook_prompt, re.DOTALL), (
            "Hook CONDITION A must check web_service status equals passed"
        )

        # Must check web_page.status equals "passed"
        assert re.search(r"web_page.*passed", hook_prompt, re.DOTALL), (
            "Hook CONDITION A must check web_page status equals passed"
        )


# ---------------------------------------------------------------------------
# Property 2.5: Context budget management independent of skip logic
# ---------------------------------------------------------------------------


class TestContextBudgetIndependence:
    """Context budget management operates independently of step skip logic.

    The steering files define context budget rules (unloading files, adaptive
    pacing) that must continue to operate without using budget pressure as
    justification to skip ⛔ mandatory gate steps.

    **Validates: Requirements 3.4**
    """

    def test_skip_protocol_does_not_reference_context_budget(self) -> None:
        """The skip-step protocol has no context budget triggers.

        Context budget is NOT a valid reason to skip steps — the protocol
        only responds to bootcamper-initiated trigger phrases.
        """
        protocol_content = _SKIP_PROTOCOL.read_text(encoding="utf-8")

        # The trigger phrases section should not include context/budget terms
        trigger_section_match = re.search(
            r"## Trigger Phrases\n(.*?)(?=\n##|\Z)",
            protocol_content,
            re.DOTALL,
        )
        assert trigger_section_match, "Trigger Phrases section must exist"
        trigger_section = trigger_section_match.group(1)

        # Context budget is NOT a trigger phrase
        assert "context" not in trigger_section.lower(), (
            "Context budget must NOT be a skip trigger phrase"
        )
        assert "budget" not in trigger_section.lower(), (
            "Budget must NOT be a skip trigger phrase"
        )

    def test_gate_hook_does_not_reference_context_budget(self) -> None:
        """The existing gate hook has no context budget logic.

        The hook only checks for checkpoints and skipped_steps entries —
        it does not consider context budget state.
        """
        hook_prompt = _UNFIXED_GATE_HOOK_JSON["then"]["prompt"]

        assert "context" not in hook_prompt.lower() or "context" in "context budget" not in hook_prompt.lower(), (
            "Gate hook should not reference context budget"
        )
        # More precise check: no "budget" in the hook prompt
        assert "budget" not in hook_prompt.lower(), (
            "Gate hook must not reference budget — enforcement is independent "
            "of context budget state"
        )

    def test_module3_step9_does_not_allow_budget_skip(self) -> None:
        """Step 9's ⛔ designation does not include budget as a valid skip reason.

        The mandatory gate text states the step cannot be skipped — period.
        No exception for context budget.
        """
        content = _MODULE3_STEERING.read_text(encoding="utf-8")
        step9_section = _extract_step_section(content, _MANDATORY_GATE_STEP)

        # Step 9 has the mandatory gate marker
        assert "⛔" in step9_section, (
            "Step 9 must have ⛔ mandatory gate marker"
        )

        # The mandatory gate text says it cannot be skipped
        assert "cannot be skipped" in step9_section.lower() or "mandatory" in step9_section.lower(), (
            "Step 9 must state it cannot be skipped"
        )


# ---------------------------------------------------------------------------
# Property 2.6: Skip protocol structure preserved
# ---------------------------------------------------------------------------


class TestSkipProtocolStructurePreserved:
    """The skip-step-protocol.md structure is preserved on unfixed code.

    This captures the baseline structure that must not regress:
    - Trigger phrases section exists
    - Protocol steps (Acknowledge, Record, Assess, Proceed) exist
    - Constraints section with mandatory gate rule exists
    - Revisiting section exists

    **Validates: Requirements 3.1, 3.2**
    """

    def test_protocol_has_trigger_phrases(self) -> None:
        """Skip protocol defines trigger phrases for bootcamper-initiated skips."""
        content = _SKIP_PROTOCOL.read_text(encoding="utf-8")
        assert "## Trigger Phrases" in content, (
            "Skip protocol must have Trigger Phrases section"
        )
        # Must have at least the core trigger phrases
        assert "skip this step" in content, "Must have 'skip this step' trigger"
        assert "I'm stuck" in content, "Must have 'I'm stuck' trigger"

    def test_protocol_has_four_steps(self) -> None:
        """Skip protocol defines the 4-step handling process."""
        content = _SKIP_PROTOCOL.read_text(encoding="utf-8")
        assert "### 1. Acknowledge" in content, "Must have step 1: Acknowledge"
        assert "### 2. Record" in content, "Must have step 2: Record"
        assert "### 3. Assess" in content, "Must have step 3: Assess"
        assert "### 4. Proceed" in content, "Must have step 4: Proceed"

    def test_protocol_has_constraints_section(self) -> None:
        """Skip protocol has Constraints section with mandatory gate rule."""
        content = _SKIP_PROTOCOL.read_text(encoding="utf-8")
        assert "## Constraints" in content, (
            "Skip protocol must have Constraints section"
        )

    def test_protocol_has_revisiting_section(self) -> None:
        """Skip protocol has Revisiting Skipped Steps section."""
        content = _SKIP_PROTOCOL.read_text(encoding="utf-8")
        assert "## Revisiting Skipped Steps" in content, (
            "Skip protocol must have Revisiting section"
        )


# ---------------------------------------------------------------------------
# Property 2.7: Existing gate hook structure preserved
# ---------------------------------------------------------------------------


class TestExistingGateHookPreserved:
    """The gate-module3-visualization.kiro.hook structure is preserved.

    This hook provides the existing (reactive) enforcement that blocks Module 3
    completion when Step 9 checkpoints are missing. It must continue to work
    independently after the fix adds the new proactive enforcement hook.

    **Validates: Requirements 3.3, 3.4**
    """

    def test_gate_hook_is_pretooluse_write(self) -> None:
        """Gate hook fires on preToolUse write operations."""
        hook_data = json.loads(_GATE_HOOK.read_text(encoding="utf-8"))
        assert hook_data["when"]["type"] == "preToolUse", (
            "Gate hook must be preToolUse type"
        )
        assert "write" in hook_data["when"].get("toolTypes", []), (
            "Gate hook must fire on write tool types"
        )

    def test_gate_hook_has_required_fields(self) -> None:
        """Gate hook has all required JSON fields per security rules."""
        hook_data = json.loads(_GATE_HOOK.read_text(encoding="utf-8"))
        assert "name" in hook_data, "Hook must have 'name' field"
        assert "version" in hook_data, "Hook must have 'version' field"
        assert "when" in hook_data, "Hook must have 'when' field"
        assert "then" in hook_data, "Hook must have 'then' field"

    def test_gate_hook_checks_both_conditions(self) -> None:
        """Gate hook checks CONDITION A (checkpoints) and CONDITION B (skipped)."""
        hook_data = json.loads(_GATE_HOOK.read_text(encoding="utf-8"))
        prompt = hook_data["then"]["prompt"]

        # Must check both conditions
        assert "CONDITION A" in prompt, "Hook must define CONDITION A"
        assert "CONDITION B" in prompt, "Hook must define CONDITION B"
