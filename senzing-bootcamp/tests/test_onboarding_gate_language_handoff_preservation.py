"""Preservation property tests for onboarding-gate-language-handoff bugfix.

These tests observe the UNFIXED hook and steering files and capture the
baseline behavior that MUST remain intact after the gate-handoff fix is
applied. Written BEFORE the fix, they are EXPECTED TO PASS on unfixed code —
each one encodes an invariant the fix must not disturb.

The fix (see design.md / tasks.md task 3) makes only two additive changes:

  * It inserts a *gate-scoped* genericization constraint into Phase 1 of the
    ``ask-bootcamper`` hook (only active when a ⛔ mandatory gate is present).
  * It inserts a readiness-signal transition directive *between* Step 3 and
    Step 4 of ``onboarding-phase1b-intro-language.md``.

Everything else must stay exactly as it is today. These properties pin that
"everything else":

  Property 2A — Non-Gate Phase 1 Preservation (Requirements 3.1, 3.3)
    For non-gate step contexts, Phase 1 still produces a contextual closing
    question with full session awareness, and any forward-looking constraint
    the fix adds is gate-scoped rather than global.

  Property 2B — Follow-Up Question Handling Preservation (Requirement 3.2)
    Follow-up questions (not readiness signals) at the entity-resolution-intro
    gate are still answered via search_docs and the gate is re-presented.

  Property 2C — Question Pending Suppression Preservation (Requirement 3.5)
    Phase 1 still suppresses its output when ``config/.question_pending``
    exists (condition 1 of Phase 1).

  Property 2D — Non-Gate Transition Preservation (Requirement 3.4)
    The existing Step 4 -> Step 5 -> track-selection routing in the steering
    file is unchanged.

Feature: onboarding-gate-language-handoff

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

EXPECTED OUTCOME on UNFIXED code: every test PASSES, establishing the baseline
behavior to preserve.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location (senzing-bootcamp/)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent

_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.json"
_STEERING_FILE = _BOOTCAMP_DIR / "steering" / "onboarding-phase1b-intro-language.md"
# The mandatory gate itself lives in the file Step 3 loads via #[[file:]].
_GATE_FILE = _BOOTCAMP_DIR / "steering" / "entity-resolution-intro.md"

# ---------------------------------------------------------------------------
# Gate markers — the detection criteria the fix relies on (design.md)
# ---------------------------------------------------------------------------

_GATE_MARKER = "⛔ **MANDATORY GATE**"
_STOP_MARKER = "🛑 **STOP"

# Readiness-signal vocabulary — used only to prove that generated follow-up
# questions are NOT readiness signals (they must exercise the follow-up path).
_READINESS_SIGNALS = frozenset(
    {
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
        "i'm ready to move on",
    }
)

# Question stems that mark a message as an actual follow-up question.
_QUESTION_STEMS = (
    "how",
    "what",
    "why",
    "when",
    "where",
    "can you",
    "could you",
    "does",
    "do",
    "is",
)


# ---------------------------------------------------------------------------
# Fix-pattern detectors (only match the fix's precise vocabulary)
# ---------------------------------------------------------------------------
# The fix's Phase 1 constraint uses "MUST NOT name/preview/reference specific
# ... content/step" plus "generic forward-looking language". These patterns are
# intentionally narrow so they match nothing on unfixed code (the gate-scoping
# property is then vacuously satisfied) and only the fix's own text afterwards.
_FORWARD_CONSTRAINT_RE = re.compile(
    r"(must\s+not\s+(?:name|preview|reference)[^.]*"
    r"\b(?:specific|upcoming|subsequent|next|step)\b"
    r"|generic\s+forward-looking"
    r"|genericize[sd]?)",
    re.IGNORECASE,
)
_GATE_QUALIFIER_RE = re.compile(
    r"(⛔|mandatory\s+gate|gate\s+is\s+(?:active|detected)|"
    r"active\s+.{0,20}gate|at\s+(?:a|the|any)\s+.{0,20}gate)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers — locate and parse source-of-truth files
# ---------------------------------------------------------------------------


def _read_hook_prompt() -> str:
    """Return the ``action.prompt`` value from the v1 ask-bootcamper hook.

    Returns:
        The full Stop-hook prompt text.
    """
    data = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
    return data["hooks"][0]["action"]["prompt"]


def _read_steering() -> str:
    """Return the full text of the onboarding-phase1b steering file.

    Returns:
        The steering file text.
    """
    return _STEERING_FILE.read_text(encoding="utf-8")


def _read_gate_file() -> str:
    """Return the full text of the entity-resolution-intro gate file.

    Returns:
        The gate file text (loaded by Step 3 via ``#[[file:]]``).
    """
    return _GATE_FILE.read_text(encoding="utf-8")


def _extract_phase1_section(prompt: str) -> str:
    """Extract the Phase 1 (Closing_Question_Phase) block from the hook prompt.

    Scopes Phase 1 to the text between the ``PHASE 1: CLOSING QUESTION`` heading
    and the ``PHASE 2: STEP SEQUENCING`` heading so gate-marker detection never
    picks up Phase 2's own ``⛔ mandatory gates`` sequencing reference.

    Args:
        prompt: The full hook prompt text.

    Returns:
        The Phase 1 section text, or ``""`` if the layout changed.
    """
    start = re.search(r"PHASE 1: CLOSING QUESTION", prompt)
    if not start:
        return ""
    end = re.search(r"PHASE 2: STEP SEQUENCING", prompt)
    if end:
        return prompt[start.start():end.start()]
    return prompt[start.start():]


def _normalize_ws(text: str) -> str:
    """Collapse all runs of whitespace to single spaces.

    Lets multi-line prose (wrapped list items in the gate file) be matched with
    simple single-space substrings.

    Args:
        text: The raw text.

    Returns:
        The text with every whitespace run collapsed to one space.
    """
    return re.sub(r"\s+", " ", text).strip()


def _phase1_has_closing_question_machinery(phase1_section: str) -> bool:
    """Return True if Phase 1 still contains its closing-question generation logic.

    The baseline machinery is a contextual recap plus a ``👉`` closing question.

    Args:
        phase1_section: The extracted Phase 1 text.

    Returns:
        Whether the recap + ``👉`` closing-question machinery is present.
    """
    lowered = phase1_section.lower()
    return (
        "recap" in lowered
        and "closing question" in lowered
        and "👉" in phase1_section
    )


def _phase1_forward_constraints_are_gate_scoped(phase1_section: str) -> bool:
    """Return True if every forward-looking constraint in Phase 1 is gate-scoped.

    On unfixed code there are no such constraints, so this is vacuously True —
    which is exactly the baseline (non-gate closing questions may reference
    upcoming content freely). After the fix, every genericization constraint
    must sit next to a mandatory-gate qualifier so it only fires at a gate.

    Args:
        phase1_section: The extracted Phase 1 text.

    Returns:
        Whether all forward-looking constraints are qualified by a gate.
    """
    for match in _FORWARD_CONSTRAINT_RE.finditer(phase1_section):
        window = phase1_section[max(0, match.start() - 250):match.end() + 250]
        if not _GATE_QUALIFIER_RE.search(window):
            return False
    return True


def _gate_followup_rule_present(gate_text: str) -> bool:
    """Return True if the gate instructs answer-via-search_docs then re-present.

    Args:
        gate_text: The full entity-resolution-intro gate file text.

    Returns:
        Whether the follow-up handling rule (answer with search_docs, then
        re-present the gate) is present.
    """
    normalized = _normalize_ws(gate_text).lower()
    return (
        "asks a follow-up question" in normalized
        and "search_docs" in normalized
        and "re-present this gate" in normalized
    )


def _context_is_non_gate(ctx: dict) -> bool:
    """Return True when the generated context has no active mandatory gate.

    Args:
        ctx: A generated session context (see :func:`st_non_gate_contexts`).

    Returns:
        Whether the assistant message is free of both gate markers.
    """
    message = ctx["assistantMessage"]
    return _GATE_MARKER not in message and _STOP_MARKER not in message


def _phase1_yields_contextual_closing_question(
    phase1_section: str, ctx: dict
) -> bool:
    """Model whether Phase 1 would emit a contextual closing question for ``ctx``.

    Mirrors the documented Phase 1 conditions for a non-gate context: no pending
    question, no existing ``👉``, the last message is not already a question, and
    substantive work was done. When those hold and the closing-question
    machinery is present, Phase 1 emits a contextual closing question.

    Args:
        phase1_section: The extracted Phase 1 text.
        ctx: A generated non-gate session context.

    Returns:
        Whether a contextual closing question would be produced.
    """
    if not _context_is_non_gate(ctx):
        return False
    if ctx["questionPending"]:
        return False
    if ctx["assistantHasPointer"]:
        return False
    if ctx["assistantEndsWithQuestion"]:
        return False
    if not ctx["workAccomplished"]:
        return False
    return _phase1_has_closing_question_machinery(phase1_section)


def _is_readiness_signal(message: str) -> bool:
    """Return True if ``message`` is one of the recognized readiness signals.

    Args:
        message: The bootcamper message.

    Returns:
        Whether the normalized message is a readiness signal.
    """
    return message.strip().lower() in _READINESS_SIGNALS


def _is_followup_question(message: str) -> bool:
    """Return True if ``message`` is an actual follow-up question, not readiness.

    A follow-up question contains a ``?`` and opens with a question stem, and is
    never one of the readiness signals.

    Args:
        message: The bootcamper message.

    Returns:
        Whether the message is a follow-up question.
    """
    if _is_readiness_signal(message):
        return False
    if "?" not in message:
        return False
    lowered = message.strip().lower()
    return any(lowered.startswith(stem) for stem in _QUESTION_STEMS)


# ---------------------------------------------------------------------------
# Non-gate step vocabulary for generated contexts
# ---------------------------------------------------------------------------

_NON_GATE_STEPS = [
    "prerequisite check",
    "directory structure setup",
    "team detection",
    "verbosity preference selection",
    "comprehension check",
    "license overview",
    "data source mapping recap",
    "bootcamp overview",
]

# Natural forward-looking references that are allowed at non-gate steps.
_NATURAL_FORWARD_REFERENCES = [
    "Next we'll introduce entity resolution.",
    "Coming up, we'll pick your programming language.",
    "After this, we'll move into the bootcamp overview.",
    "We'll continue with track selection shortly.",
    "",
]

# Follow-up question bodies bootcampers ask at the gate.
_FOLLOWUP_QUESTIONS = [
    "How does Senzing match records without rules?",
    "What's the difference between matching and relating?",
    "What kinds of data does entity resolution work with?",
    "Can you explain entity resolution?",
    "Why do false positives happen?",
    "How is a possible match different from a match?",
    "What is a disclosed relationship?",
    "Could you give an example of a false negative?",
    "Does entity resolution need training data?",
    "When should I use candidate selection?",
]


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_non_gate_contexts(draw: st.DrawFn) -> dict:
    """Draw a session context for a NON-gate step (no mandatory gate active).

    The assistant message never contains either gate marker and may include a
    natural forward-looking reference (allowed for non-gate steps). Preconditions
    are clean and work was accomplished, so the Phase 1 closing-question path is
    exercised.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-gate session-context dict.
    """
    step = draw(st.sampled_from(_NON_GATE_STEPS))
    forward_ref = draw(st.sampled_from(_NATURAL_FORWARD_REFERENCES))
    assistant_message = f"Completed the {step}. {forward_ref}".strip()
    return {
        "trigger": "Stop",
        "step": step,
        "assistantMessage": assistant_message,
        "questionPending": False,
        "assistantHasPointer": False,
        "assistantEndsWithQuestion": False,
        "workAccomplished": True,
    }


@st.composite
def st_followup_questions(draw: st.DrawFn) -> str:
    """Draw an actual follow-up question a bootcamper might ask at the gate.

    Every drawn value contains a ``?`` and opens with a question stem, and is
    never a readiness signal, so it exercises the follow-up handling path.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A follow-up question string.
    """
    return draw(st.sampled_from(_FOLLOWUP_QUESTIONS))


# ---------------------------------------------------------------------------
# Property 2A — Non-Gate Phase 1 Preservation
# ---------------------------------------------------------------------------


class TestNonGatePhase1Preservation:
    """Property 2A — Phase 1's non-gate closing-question behavior is preserved.

    On UNFIXED code Phase 1 has no gate-awareness constraint, so it freely
    produces contextual closing questions with full session awareness. The fix
    only adds a gate-scoped constraint; non-gate behavior must be untouched.

    **Validates: Requirements 3.1, 3.3**
    """

    def test_phase1_section_exists(self) -> None:
        """Baseline: the Phase 1 (Closing_Question_Phase) section exists."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert phase1, (
            "Could not locate the Phase 1 (Closing_Question_Phase) section in "
            "ask-bootcamper.json — the prompt layout may have changed."
        )

    def test_phase1_retains_closing_question_machinery(self) -> None:
        """Phase 1 still produces a contextual recap + 👉 closing question."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert _phase1_has_closing_question_machinery(phase1), (
            "Phase 1 must retain its contextual recap + 👉 closing-question "
            "machinery (Requirements 3.1, 3.3)."
        )
        assert "brief recap of what was accomplished" in phase1, (
            "Phase 1 must retain its 'brief recap of what was accomplished' "
            "session-awareness wording."
        )
        assert "contextual 👉 question" in phase1, (
            "Phase 1 must retain its 'contextual 👉 question' instruction."
        )

    def test_phase1_retains_precondition_checks(self) -> None:
        """Phase 1 still guards on its three baseline pre-conditions."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert "config/.question_pending does NOT exist" in phase1, (
            "Phase 1 must retain the question_pending pre-condition."
        )
        assert "does NOT contain a 👉" in phase1, (
            "Phase 1 must retain the existing-👉 pre-condition."
        )
        assert "does NOT end with a question" in phase1, (
            "Phase 1 must retain the trailing-question pre-condition."
        )

    def test_phase1_forward_constraints_are_gate_scoped(self) -> None:
        """Any forward-looking constraint in Phase 1 must be gate-scoped.

        Vacuously true on unfixed code (no such constraint exists, so non-gate
        closing questions may reference upcoming content freely). The fix must
        keep its genericization constraint qualified by a mandatory gate so it
        never fires for non-gate steps.
        """
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert _phase1_forward_constraints_are_gate_scoped(phase1), (
            "A forward-looking genericization constraint in Phase 1 is NOT "
            "gate-scoped. Non-gate closing questions must remain free to "
            "reference upcoming content naturally (Requirements 3.1, 3.3)."
        )

    @given(ctx=st_non_gate_contexts())
    def test_non_gate_context_yields_contextual_closing_question(
        self, ctx: dict
    ) -> None:
        """For any non-gate context, Phase 1 still yields a closing question.

        Args:
            ctx: A generated non-gate session context.
        """
        assert _context_is_non_gate(ctx), (
            f"Generated context should be non-gate but contained a gate marker: "
            f"{ctx['assistantMessage']!r}"
        )
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert _phase1_yields_contextual_closing_question(phase1, ctx), (
            "Non-gate context "
            f"(step={ctx['step']!r}) should still produce a contextual closing "
            "question with full session awareness, but Phase 1's non-gate "
            "closing-question path was not preserved."
        )


# ---------------------------------------------------------------------------
# Property 2B — Follow-Up Question Handling Preservation
# ---------------------------------------------------------------------------


class TestFollowUpQuestionHandlingPreservation:
    """Property 2B — Follow-up questions at the gate are still answered.

    On UNFIXED code the entity-resolution-intro gate instructs the agent to
    answer follow-up questions via search_docs and re-present the gate. The fix
    only routes *readiness signals* to Step 4; the follow-up path is preserved.

    **Validates: Requirement 3.2**
    """

    def test_gate_file_exists(self) -> None:
        """Baseline: the entity-resolution-intro gate file exists."""
        assert _GATE_FILE.exists(), (
            f"entity-resolution-intro.md not found at {_GATE_FILE}"
        )

    def test_gate_followup_rule_present(self) -> None:
        """The gate still instructs answer-via-search_docs then re-present."""
        gate_text = _read_gate_file()
        assert _gate_followup_rule_present(gate_text), (
            "The entity-resolution-intro gate must still instruct the agent to "
            "answer follow-up questions using search_docs and then re-present "
            "the gate (Requirement 3.2)."
        )

    @given(question=st_followup_questions())
    def test_followup_questions_route_to_answer_then_represent(
        self, question: str
    ) -> None:
        """For any follow-up question, the answer-then-re-present rule applies.

        Args:
            question: A generated follow-up question.
        """
        assert _is_followup_question(question), (
            f"Generated value {question!r} should be a follow-up question, not "
            "a readiness signal."
        )
        gate_text = _read_gate_file()
        assert _gate_followup_rule_present(gate_text), (
            f"Follow-up question {question!r} must still be handled by the "
            "answer-with-search_docs then re-present-gate rule (Requirement 3.2)."
        )


# ---------------------------------------------------------------------------
# Property 2C — Question Pending Suppression Preservation
# ---------------------------------------------------------------------------


class TestQuestionPendingSuppressionPreservation:
    """Property 2C — Phase 1 still suppresses output when a question is pending.

    Condition 1 of Phase 1 checks that ``config/.question_pending`` does not
    exist; when it does, Phase 1 output is none. The fix must not disturb this.

    **Validates: Requirement 3.5**
    """

    def test_phase1_question_pending_condition_present(self) -> None:
        """Phase 1 still checks for ``config/.question_pending`` existence."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert "config/.question_pending does NOT exist" in phase1, (
            "Phase 1 must retain its config/.question_pending condition "
            "(Requirement 3.5)."
        )

    def test_phase1_suppresses_on_failed_condition(self) -> None:
        """Phase 1 still yields no output when any pre-condition fails."""
        phase1 = _extract_phase1_section(_read_hook_prompt())
        assert "If ANY Phase 1 condition fails: Phase 1 output is none" in phase1, (
            "Phase 1 must retain its suppression rule when a pre-condition "
            "fails, including the pending-question case (Requirement 3.5)."
        )


# ---------------------------------------------------------------------------
# Property 2D — Non-Gate Transition Preservation
# ---------------------------------------------------------------------------

# Literal routing anchors the fix must leave untouched (Step 4 -> 5 -> tracks).
_ROUTING_ANCHORS = [
    "## 4. Programming Language Selection",
    "## 5. Bootcamp Introduction",
    "### 5a. Verbosity Preference",
    "### 5b. Comprehension Check",
    "After Step 5b, load `onboarding-phase2-track-setup.md` for track selection.",
    "proceed directly to track selection (load `onboarding-phase2-track-setup.md`)",
]


class TestNonGateTransitionPreservation:
    """Property 2D — Existing Step 4 -> Step 5 -> track routing is preserved.

    The fix inserts a transition directive *between* Step 3 and Step 4, so the
    downstream routing (Step 4 language selection, Step 5 intro, Step 5b to
    track selection) must remain byte-for-byte present and in order.

    **Validates: Requirement 3.4**
    """

    def test_step_headings_present_and_ordered(self) -> None:
        """Steps 4, 5, 5a, 5b headings still appear in document order."""
        steering = _read_steering()
        positions = []
        for heading in (
            "## 4. Programming Language Selection",
            "## 5. Bootcamp Introduction",
            "### 5a. Verbosity Preference",
            "### 5b. Comprehension Check",
        ):
            idx = steering.find(heading)
            assert idx != -1, f"Missing routing heading: {heading!r}"
            positions.append(idx)
        assert positions == sorted(positions), (
            "Step 4/5/5a/5b headings are out of order — routing flow changed "
            "(Requirement 3.4)."
        )

    def test_track_selection_routing_preserved(self) -> None:
        """The Step 5b -> track-selection routing lines are unchanged."""
        steering = _read_steering()
        assert (
            "After Step 5b, load `onboarding-phase2-track-setup.md` for track selection."
            in steering
        ), "Missing the Step 5b -> track-selection routing directive (Req 3.4)."
        assert (
            "proceed directly to track selection (load `onboarding-phase2-track-setup.md`)"
            in steering
        ), "Missing the acknowledgment -> track-selection routing (Req 3.4)."

    @given(anchor=st.sampled_from(_ROUTING_ANCHORS))
    def test_routing_anchor_preserved(self, anchor: str) -> None:
        """For any non-gate routing anchor, the steering file still contains it.

        Args:
            anchor: A literal routing anchor drawn from the baseline set.
        """
        steering = _read_steering()
        assert anchor in steering, (
            f"Non-gate routing anchor {anchor!r} is missing — existing steering "
            "flow was altered (Requirement 3.4)."
        )
