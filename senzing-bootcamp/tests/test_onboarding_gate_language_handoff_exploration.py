"""Bug condition exploration tests for onboarding-gate-language-handoff bugfix.

These tests parse the UNFIXED hook and steering files and confirm the bug
exists in two related scenarios that both surface at the entity-resolution-intro
mandatory gate (onboarding Step 3):

  Scenario 1 — Phase 1 Preview Leak
    The ``ask-bootcamper`` hook's Phase 1 (Closing_Question_Phase) has no
    gate-awareness constraint, so its closing question can preview specific
    upcoming-step content (e.g. "picking your programming language") while a
    ⛔ mandatory gate is still active and uncleared.

  Scenario 2 — Gate Transition Directive
    ``onboarding-phase1b-intro-language.md`` has no explicit directive between
    Step 3 and Step 4 that routes a bootcamper's readiness signal directly to
    Step 4, so a "ready"/"let's go"/"continue" signal can dead-end back into the
    same gate instead of advancing to programming-language selection.

Feature: onboarding-gate-language-handoff

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

EXPECTED OUTCOME on UNFIXED code:
- The gate-awareness constraint assertions FAIL (Phase 1 has no gate constraint)
- The transition-directive assertions FAIL (steering has no Step 3 -> Step 4 route)
- The bug-condition property FAILS, surfacing counterexamples that prove the gap
The sanity/baseline assertions (section exists, region exists) PASS.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location (senzing-bootcamp/)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent

_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.json"
_STEERING_FILE = _BOOTCAMP_DIR / "steering" / "onboarding-phase1b-intro-language.md"

# ---------------------------------------------------------------------------
# Gate markers — the detection criteria the fix relies on (design.md)
# ---------------------------------------------------------------------------

_GATE_MARKER = "⛔ **MANDATORY GATE**"
_STOP_MARKER = "🛑 **STOP"

# Readiness-signal vocabulary the bootcamper may use at the gate.
_READINESS_SIGNALS = [
    "ready",
    "let's go",
    "continue",
    "next",
    "move on",
    "yes",
    "sure",
    "yep",
    "what's next",
    "let's keep going",
    "I'm ready to move on",
]

# ---------------------------------------------------------------------------
# Fix-detection patterns
# ---------------------------------------------------------------------------
# Scenario 1: after the fix, Phase 1 detects an active mandatory gate and
# constrains forward-looking references to generic phrasing.
_GATE_AWARENESS_DETECTION = re.compile(r"(⛔|mandatory\s+gate)", re.IGNORECASE)
_GENERIC_FORWARD_CONSTRAINT = re.compile(
    r"(generic\s+forward"
    r"|forward-looking"
    r"|genericize"
    r"|must\s+not\s+(name|preview|reference)"
    r"|keep\s+.*generic)",
    re.IGNORECASE,
)

# Scenario 2: after the fix, the Step 3 -> Step 4 region routes readiness
# signals directly to Step 4.
_TRANSITION_TO_STEP4 = re.compile(
    r"(immediately\s+)?(proceed|advance|transition|move\s+on|continue|go)\s+"
    r"(directly\s+|immediately\s+|straight\s+)?to\s+Step\s+4",
    re.IGNORECASE,
)
_READINESS_SIGNAL_LIST = re.compile(
    r"(ready|let'?s\s+go|continue|next|move\s+on)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers — locate and parse source-of-truth files
# ---------------------------------------------------------------------------


def _read_hook_prompt() -> str:
    """Return the ``action.prompt`` value from the v1 ask-bootcamper hook."""
    data = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
    return data["hooks"][0]["action"]["prompt"]


def _read_steering() -> str:
    """Return the full text of the onboarding-phase1b steering file."""
    return _STEERING_FILE.read_text(encoding="utf-8")


def _extract_phase1_section(prompt: str) -> str:
    """Extract the Phase 1 (Closing_Question_Phase) block from the hook prompt.

    The prompt delimits phases with a banner line followed by a
    ``PHASE N: ...`` heading. Returns the text from the Phase 1 heading up to
    (but not including) the Phase 2 heading, so gate-awareness detection is
    scoped to Phase 1 and never picks up the ``⛔ mandatory gates`` reference
    that already lives in Phase 2's sequential-step enforcement.
    """
    start = re.search(r"PHASE 1: CLOSING QUESTION", prompt)
    if not start:
        return ""
    end = re.search(r"PHASE 2: STEP SEQUENCING", prompt)
    if end:
        return prompt[start.start():end.start()]
    return prompt[start.start():]


def _extract_step3_to_step4_region(steering_text: str) -> str:
    """Extract the region between the Step 3 and Step 4 headings.

    This is exactly where the fix inserts the readiness-signal transition
    directive. Returns the text from ``## 3. Entity Resolution Introduction``
    up to (but not including) ``## 4. Bootcamp Introduction``. After the preface
    reorder (track before language), Step 4 in phase 1b is the Bootcamp
    Introduction (programming language selection moved to phase 2); the Step 3 ->
    Step 4 gate-clearance transition directive is unchanged and still lives here.
    """
    start = re.search(
        r"^##\s+3\.\s+Entity Resolution Introduction", steering_text, re.MULTILINE
    )
    end = re.search(
        r"^##\s+4\.\s+Bootcamp Introduction", steering_text, re.MULTILINE
    )
    if not start or not end:
        return ""
    return steering_text[start.start():end.start()]


def _phase1_has_gate_awareness_constraint(phase1_section: str) -> bool:
    """Return True if Phase 1 contains a gate-awareness genericization constraint.

    The fix adds BOTH a mandatory-gate detection reference AND a
    generic-forward-language constraint. On unfixed code neither is present.
    """
    return bool(
        _GATE_AWARENESS_DETECTION.search(phase1_section)
        and _GENERIC_FORWARD_CONSTRAINT.search(phase1_section)
    )


def _steering_has_transition_directive(region: str) -> bool:
    """Return True if the Step 3 -> Step 4 region routes readiness to Step 4.

    The fix adds BOTH a "proceed to Step 4" routing directive AND a
    readiness-signal recognition list. On unfixed code the region only holds a
    ``#[[file:]]`` reference and a comment that says the agent MUST NOT proceed
    past the step — it never routes readiness signals to Step 4.
    """
    return bool(
        _TRANSITION_TO_STEP4.search(region)
        and _READINESS_SIGNAL_LIST.search(region)
    )


def _is_readiness_signal(message: str) -> bool:
    """Return True if ``message`` is one of the recognized readiness signals."""
    normalized = message.strip().lower()
    return normalized in {s.lower() for s in _READINESS_SIGNALS}


def is_bug_condition(ctx: dict) -> bool:
    """Return True when the generated session context satisfies the bug condition.

    Models ``isBugCondition`` from design.md across both scenarios:
      - Scenario 1: trigger == "Stop" at an active, uncleared mandatory gate.
      - Scenario 2: trigger == "UserPromptSubmit" at an active gate where the
        bootcamper signaled readiness to move on.

    Args:
        ctx: A generated session context (see :func:`st_gate_active_context`).

    Returns:
        Whether the context is a bug-condition input.
    """
    gate_active = (
        _GATE_MARKER in ctx["assistantMessage"]
        and _STOP_MARKER in ctx["assistantMessage"]
        and ctx.get("currentStepHasMandatoryGate", False)
        and ctx.get("mandatoryGateNotCleared", False)
    )
    if not gate_active:
        return False
    if ctx["trigger"] == "Stop":
        return True
    if ctx["trigger"] == "UserPromptSubmit":
        return _is_readiness_signal(ctx["userMessage"])
    return False


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_readiness_signals(draw: st.DrawFn) -> str:
    """Draw a readiness signal a bootcamper might send at the gate.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of the recognized readiness-signal phrases.
    """
    return draw(st.sampled_from(_READINESS_SIGNALS))


@st.composite
def st_gate_active_context(draw: st.DrawFn) -> dict:
    """Draw a session context in which the entity-resolution-intro gate is active.

    The generated assistant message always contains both gate markers
    (``⛔ **MANDATORY GATE**`` and ``🛑 **STOP``) so the gate is detectably
    active. The trigger is either ``Stop`` (Scenario 1) or ``UserPromptSubmit``
    (Scenario 2), and the user message is a readiness signal.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A session-context dict consumable by :func:`is_bug_condition`.
    """
    trigger = draw(st.sampled_from(["Stop", "UserPromptSubmit"]))
    readiness = draw(st_readiness_signals())
    lead = draw(
        st.sampled_from(
            [
                "Here's the entity resolution introduction.",
                "Let's explore entity resolution together.",
                "Take a moment to explore the ER concepts.",
                "",
            ]
        )
    )
    assistant_message = (
        f"{lead}\n\n"
        "> ⛔ **MANDATORY GATE** — Entity Resolution Exploration\n"
        ">\n"
        "> 🛑 **STOP — End your response here.** "
        "Wait for the bootcamper's real input."
    ).strip()
    return {
        "trigger": trigger,
        "assistantMessage": assistant_message,
        "userMessage": readiness,
        "currentStepHasMandatoryGate": True,
        "mandatoryGateNotCleared": True,
    }


# ---------------------------------------------------------------------------
# Scenario 1 — Phase 1 Preview Leak (gate-awareness constraint absent)
# ---------------------------------------------------------------------------


class TestScenario1Phase1PreviewLeak:
    """Scenario 1 — Phase 1 lacks a gate-awareness genericization constraint.

    On UNFIXED code the constraint assertion FAILS: Phase 1 has no instruction
    to keep forward-looking references generic when a mandatory gate is active,
    so its closing question can preview specific Step 4 content.

    **Validates: Requirements 1.1, 1.3, 2.1, 2.3**
    """

    def test_phase1_section_exists(self) -> None:
        """Baseline: the Phase 1 (Closing_Question_Phase) section exists."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert phase1, (
            "Could not locate the Phase 1 (Closing_Question_Phase) section in "
            "ask-bootcamper.json — the prompt layout may have changed."
        )

    def test_phase1_has_gate_awareness_constraint(self) -> None:
        """Phase 1 must contain a gate-awareness genericization constraint.

        The fix inserts detection of an active ⛔ mandatory gate plus a
        constraint that forward-looking references stay generic. On unfixed
        code neither is present, so this assertion FAILS — confirming the bug.
        """
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert _phase1_has_gate_awareness_constraint(phase1), (
            "Bug condition (Scenario 1): Phase 1 of ask-bootcamper.json has NO "
            "gate-awareness constraint. When a ⛔ mandatory gate is active the "
            "closing question is free to preview specific upcoming-step content "
            "(e.g. 'picking your programming language'). The fix must add a "
            "mandatory-gate detection AND a generic-forward-language constraint "
            "to the 'SECOND — Recap and closing question' block."
        )


# ---------------------------------------------------------------------------
# Scenario 2 — Gate Transition Directive (missing Step 3 -> Step 4 route)
# ---------------------------------------------------------------------------


class TestScenario2GateTransitionDirective:
    """Scenario 2 — steering lacks a readiness-signal transition directive.

    On UNFIXED code the directive assertion FAILS: the region between Step 3
    and Step 4 only holds a ``#[[file:]]`` reference and a comment saying the
    agent MUST NOT proceed past the step — nothing routes a readiness signal to
    Step 4, so the agent may re-present the same gate.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_step3_to_step4_region_exists(self) -> None:
        """Baseline: the Step 3 -> Step 4 region exists in the steering file."""
        region = _extract_step3_to_step4_region(_read_steering())
        assert region, (
            "Could not locate the Step 3 -> Step 4 region in "
            "onboarding-phase1b-intro-language.md — heading layout may have changed."
        )

    def test_steering_has_transition_directive(self) -> None:
        """The Step 3 -> Step 4 region must route readiness signals to Step 4.

        The fix inserts a directive that recognizes readiness signals and tells
        the agent to proceed directly to Step 4. On unfixed code no such
        directive exists, so this assertion FAILS — confirming the bug.
        """
        region = _extract_step3_to_step4_region(_read_steering())
        assert _steering_has_transition_directive(region), (
            "Bug condition (Scenario 2): the region between Step 3 and Step 4 in "
            "onboarding-phase1b-intro-language.md has NO transition directive "
            "routing readiness signals ('ready', 'let's go', 'continue', 'next', "
            "'move on') directly to Step 4. Without it, a readiness signal at the "
            "entity-resolution-intro gate can dead-end back into the same gate."
        )


# ---------------------------------------------------------------------------
# PBT — Property 1: Bug Condition (gate-active handoff)
# ---------------------------------------------------------------------------


class TestBugConditionProperty:
    """PBT — For any bug-condition context, both fix artifacts must be present.

    Property 1 (Bug Condition): for all generated session contexts where
    ``is_bug_condition`` holds (an active, uncleared mandatory gate on a Stop
    trigger, or a readiness signal at that gate on UserPromptSubmit), the hook's
    Phase 1 MUST contain a gate-awareness constraint AND the steering file MUST
    contain a readiness-signal transition directive.

    On UNFIXED code both artifacts are absent, so the property FAILS and
    surfaces counterexamples that demonstrate the bug exists.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**
    """

    @given(ctx=st_gate_active_context())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_gate_active_requires_awareness_and_transition(
        self, ctx: dict
    ) -> None:
        """For any bug-condition context both handoff safeguards must exist.

        Args:
            ctx: A generated session context at the entity-resolution-intro gate.
        """
        assume(is_bug_condition(ctx))

        phase1 = _extract_phase1_section(_read_hook_prompt())
        region = _extract_step3_to_step4_region(_read_steering())

        gate_ok = _phase1_has_gate_awareness_constraint(phase1)
        transition_ok = _steering_has_transition_directive(region)

        assert gate_ok and transition_ok, (
            "Bug condition holds for context "
            f"(trigger={ctx['trigger']!r}, userMessage={ctx['userMessage']!r}) "
            "but the handoff safeguards are missing: "
            f"Phase 1 gate-awareness constraint present={gate_ok}, "
            f"steering Step 3 -> Step 4 transition directive present={transition_ok}. "
            "The ask-bootcamper hook can preview gate-locked Step 4 content and the "
            "steering file provides no direct route from a readiness signal to Step 4."
        )
