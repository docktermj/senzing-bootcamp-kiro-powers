"""Bug-condition EXPLORATION tests for the module-transition-question-duplication bugfix.

These tests encode the EXPECTED (fixed) behavior from design **Property 1**
("Bug Condition — Transition Question Rendered Exactly Once") and are
deliberately AUTHORED TO FAIL on the current (unfixed) steering/hook files.
Their failure CONFIRMS the bug condition exists:

    isBugCondition(input) :=
        input.isModuleCompletionTurn
        AND input.expectsInput
        AND (count of rendered 👉 "Ready to (start|move on to) Module N+1"
             questions in the turn) > 1

The defect is that the module-completion guidance offers a "re-surface the
forward question as the final message" path with **no explicit rule** that the
forward module-transition 👉 question must be rendered exactly once per turn,
and **no de-duplication** between the turn's recap/next-step/closing text and
the single ``config/.question_pending`` marker. As a result the same transition
question can be shown twice (once inline as the "Proceed" next-step option, once
re-surfaced as the final message; or an inline prose prompt plus an
``ask-bootcamper`` Phase 1 appended closing 👉).

Scoped-PBT approach — the property is scoped to the concrete "render-once" /
de-duplication content patterns the fix must add to four files:

    1. ``module-completion-next-steps.md`` — states the "Proceed: Ready to move
       on to Module N?" prompt and the final-message 👉 transition question are
       the SAME question rendered exactly once, with a de-dup note tying the one
       rendered 👉 question to the single ``config/.question_pending`` marker.
    2. ``module-completion.md`` — the Final-Message Ordering rule carries an
       explicit "render exactly once" clause for the forward transition question.
    3. ``module-transitions.md`` — states the module-transition question is
       presented to the bootcamper exactly once per turn.
    4. ``ask-bootcamper.json`` — Phase 1 / Phase 1.5 recognize an already-present
       inline transition prompt (phrased without a leading 👉) and do NOT add or
       leave a second copy.

**DO NOT "fix" these tests or the code when they fail here** — the failure is
the SUCCESS case for an exploration test. After the fix these same tests pass,
validating the render-once behavior.

Feature: module-transition-question-duplication

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5** (the fixed behavior these encode)
Explores defect Requirements 1.1, 1.2, 1.3, 1.4, 1.5.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: repo root -> senzing-bootcamp)
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"
HOOKS_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "hooks"

NEXT_STEPS_PATH: Path = STEERING_DIR / "module-completion-next-steps.md"
COMPLETION_PATH: Path = STEERING_DIR / "module-completion.md"
TRANSITIONS_PATH: Path = STEERING_DIR / "module-transitions.md"
ASK_BOOTCAMPER_PATH: Path = HOOKS_DIR / "ask-bootcamper.json"


# ---------------------------------------------------------------------------
# File / section parsing helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a file."""
    return path.read_text(encoding="utf-8")


def _heading_level(line: str) -> int | None:
    """Return the ATX heading level of a markdown line, or None if not a heading.

    Args:
        line: A single line of markdown text.

    Returns:
        The number of leading ``#`` characters (1-6) for an ATX heading, or
        ``None`` when the line is not a heading.
    """
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return None
    level = len(stripped) - len(stripped.lstrip("#"))
    return level if 1 <= level <= 6 else None


def extract_md_section(text: str, heading_substr: str) -> str:
    """Extract a markdown section by heading substring.

    Finds the first ATX heading line containing ``heading_substr`` and returns
    that heading plus all lines until the next heading of the same or higher
    level (or end of file).

    Args:
        text: Full markdown document text.
        heading_substr: Case-insensitive substring identifying the heading.

    Returns:
        The section text (heading included), or an empty string if not found.
    """
    lines = text.splitlines()
    needle = heading_substr.lower()
    start: int | None = None
    start_level = 0

    for i, line in enumerate(lines):
        level = _heading_level(line)
        if level is not None and needle in line.lower():
            start = i
            start_level = level
            break

    if start is None:
        return ""

    end = len(lines)
    for j in range(start + 1, len(lines)):
        level = _heading_level(lines[j])
        if level is not None and level <= start_level:
            end = j
            break

    return "\n".join(lines[start:end])


def ask_bootcamper_prompt() -> str:
    """Return the ``action.prompt`` text of the ``ask-bootcamper`` Stop hook."""
    entry = json.loads(_read(ASK_BOOTCAMPER_PATH))["hooks"][0]
    return entry["action"]["prompt"]


def phase1_and_phase1_5_region() -> str:
    """Return the ``ask-bootcamper`` prompt text spanning Phase 1 and Phase 1.5.

    Scopes to the two phases the fix must strengthen (Phase 1 Closing Question
    and Phase 1.5 Leading-Question Count Audit), excluding Phase 4's unrelated
    "Inline prose 'or'" compound-question detection and Phase 2's
    ``module_transition`` retry text.

    Returns:
        The substring from the "PHASE 1: CLOSING QUESTION" header up to the
        "PHASE 2: STEP SEQUENCING" header, or an empty string if not found.
    """
    prompt = ask_bootcamper_prompt()
    start = prompt.find("PHASE 1: CLOSING QUESTION")
    end = prompt.find("PHASE 2: STEP SEQUENCING")
    if start == -1 or end == -1 or end <= start:
        return ""
    return prompt[start:end]


# ---------------------------------------------------------------------------
# Render-once / de-duplication content checks (shared by unit tests and the PBT)
#
# Each returns (present, detail). ``present`` is True only when the required
# render-once / de-dup guidance is found. On the UNFIXED files every check
# returns False — that is the expected exploration-test outcome.
# ---------------------------------------------------------------------------

# "same ... question" (allowing markdown bold markers between the words).
_SAME_QUESTION_RE = re.compile(r"same\b[\s\S]{0,20}question", re.IGNORECASE)
# "rendered/render/shown/presented ... once".
_RENDER_ONCE_RE = re.compile(
    r"(render\w*|shown|present\w*)[\s\S]{0,40}\bonce\b", re.IGNORECASE
)
# De-dup note tying one rendered question to the single pending marker.
_DEDUP_RE = re.compile(r"exactly one rendered", re.IGNORECASE)
# "render exactly once" / "a single time" / "does not duplicate" / replace-inline.
_RENDER_EXACTLY_ONCE_CLAUSE_RE = re.compile(
    r"(a single time"
    r"|render\w*\s+exactly\s+once"
    r"|exactly\s+once\b"
    r"|does not duplicate"
    r"|replaces?\b[\s\S]{0,60}inline)",
    re.IGNORECASE,
)
# "exactly once per turn" / "once per turn" / "a single time".
_ONCE_PER_TURN_RE = re.compile(
    r"(exactly\s+once\s+per\s+turn|once\s+per\s+turn|a single time)", re.IGNORECASE
)


def check_next_steps_same_question_once() -> tuple[bool, str]:
    """`module-completion-next-steps.md` states Proceed prompt == final 👉, once.

    Validates fixed Requirements 2.1, 2.2. Explores defect Requirements 1.1, 1.2.
    """
    text = _read(NEXT_STEPS_PATH)
    has_same = _SAME_QUESTION_RE.search(text) is not None
    has_once = _RENDER_ONCE_RE.search(text) is not None
    ok = has_same and has_once
    detail = (
        f"module-completion-next-steps.md missing 'same question rendered once' "
        f"guidance (same_question={has_same}, render_once={has_once}); the file "
        f"lists the 'Proceed: Ready to move on to Module [N]?' option and "
        f"separately requires the forward 👉 question as the final message with "
        f"no note that these are the SAME question rendered exactly once."
    )
    return ok, detail


def check_next_steps_dedup_marker() -> tuple[bool, str]:
    """`module-completion-next-steps.md` ties one rendered 👉 to one pending marker.

    Validates fixed Requirement 2.3. Explores defect Requirement 1.3.
    """
    text = _read(NEXT_STEPS_PATH)
    ok = _DEDUP_RE.search(text) is not None
    detail = (
        "module-completion-next-steps.md missing de-duplication note that the "
        "turn contains 'exactly one rendered' forward transition 👉 question "
        "matching the single config/.question_pending marker."
    )
    return ok, detail


def check_completion_render_once_clause() -> tuple[bool, str]:
    """`module-completion.md` Final-Message Ordering has a render-once clause.

    Validates fixed Requirements 2.1, 2.2, 2.3. Explores defect Requirements 1.2, 1.3.
    """
    section = extract_md_section(_read(COMPLETION_PATH), "Final-Message Ordering")
    ok = bool(section) and _RENDER_EXACTLY_ONCE_CLAUSE_RE.search(section) is not None
    detail = (
        "module-completion.md 'Final-Message Ordering' section describes "
        "ordering (recap-before vs. re-surface) but carries NO explicit "
        "'render exactly once' clause: it does not state the forward transition "
        "👉 question appears a single time and that the re-surface path replaces "
        "(does not duplicate) any earlier inline rendering."
    )
    return ok, detail


def check_transitions_once_per_turn() -> tuple[bool, str]:
    """`module-transitions.md` states the transition question is shown once per turn.

    Validates fixed Requirements 2.1, 2.5. Explores defect Requirements 1.1, 1.5.
    """
    text = _read(TRANSITIONS_PATH)
    region = (
        extract_md_section(text, "Module Completion")
        + "\n"
        + extract_md_section(text, "Transition Integrity")
    )
    ok = _ONCE_PER_TURN_RE.search(region) is not None
    detail = (
        "module-transitions.md 'Module Completion' / 'Transition Integrity' "
        "sections do not state the forward transition question is presented to "
        "the bootcamper exactly once per turn."
    )
    return ok, detail


def check_hook_inline_transition_recognition() -> tuple[bool, str]:
    """`ask-bootcamper.json` Phase 1 / 1.5 recognize an inline transition prompt.

    Validates fixed Requirement 2.4. Explores defect Requirement 1.4.
    """
    region = phase1_and_phase1_5_region()
    has_inline = re.search(r"inline", region, re.IGNORECASE) is not None
    has_transition = re.search(r"transition", region, re.IGNORECASE) is not None
    ok = has_inline and has_transition
    detail = (
        f"ask-bootcamper Phase 1 / Phase 1.5 do not recognize an already-present "
        f"inline transition prompt (inline={has_inline}, transition={has_transition}). "
        f"Phase 1's guard only checks whether the message contains a 👉 anywhere, "
        f"so a transition prompt phrased inline (no leading 👉) can slip past and "
        f"get a second closing 👉 appended."
    )
    return ok, detail


def check_hook_no_second_transition_copy() -> tuple[bool, str]:
    """`ask-bootcamper.json` Phase 1 / 1.5 forbid a second copy of the transition.

    Validates fixed Requirement 2.4. Explores defect Requirement 1.4.
    """
    region = phase1_and_phase1_5_region()
    ok = (
        re.search(
            r"(second copy|duplicate transition|already[- ]present\s+transition"
            r"|not\s+add[\s\S]{0,60}transition)",
            region,
            re.IGNORECASE,
        )
        is not None
    )
    detail = (
        "ask-bootcamper Phase 1 / Phase 1.5 do not instruct the agent to avoid "
        "adding or leaving a second copy of an already-present transition prompt "
        "(no 'do not add a second copy' / 'duplicate transition' de-dup guidance)."
    )
    return ok, detail


# ---------------------------------------------------------------------------
# Registry of render-once requirements (drives the scoped property test)
# ---------------------------------------------------------------------------

RENDER_ONCE_REQUIREMENTS: dict[str, Callable[[], tuple[bool, str]]] = {
    "next_steps_same_question_once": check_next_steps_same_question_once,
    "next_steps_dedup_marker": check_next_steps_dedup_marker,
    "completion_render_once_clause": check_completion_render_once_clause,
    "transitions_once_per_turn": check_transitions_once_per_turn,
    "hook_inline_transition_recognition": check_hook_inline_transition_recognition,
    "hook_no_second_transition_copy": check_hook_no_second_transition_copy,
}


# ---------------------------------------------------------------------------
# Property 1 (scoped PBT): the render-once guidance must be present in every
# target file. AUTHORED TO FAIL on unfixed code — each requirement is missing.
# ---------------------------------------------------------------------------


class TestTransitionQuestionRenderedExactlyOnceProperty:
    """Scoped property: render-once / de-dup guidance present in all targets.

    **Property 1: Bug Condition — Transition Question Rendered Exactly Once**

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    (explores defect Requirements 1.1, 1.2, 1.3, 1.4, 1.5)

    Scoped to the finite set of render-once/de-dup content requirements the fix
    must add. On UNFIXED files this property fails with a counterexample naming
    the first missing requirement — the expected exploration-test outcome.
    """

    @given(requirement_key=st.sampled_from(sorted(RENDER_ONCE_REQUIREMENTS)))
    def test_render_once_guidance_present_for_all_targets(
        self, requirement_key: str
    ) -> None:
        """For every target render-once requirement, its guidance is present."""
        present, detail = RENDER_ONCE_REQUIREMENTS[requirement_key]()
        assert present, f"[{requirement_key}] {detail}"


# ---------------------------------------------------------------------------
# Unit tests: one per target file / requirement, for clear counterexamples.
# ---------------------------------------------------------------------------


class TestModuleCompletionNextStepsRenderOnce:
    """`module-completion-next-steps.md` render-once + de-dup guidance.

    **Validates: Requirements 2.1, 2.2, 2.3** (explores defect 1.1, 1.2, 1.3)
    """

    def test_states_proceed_prompt_and_final_message_are_same_question_once(
        self,
    ) -> None:
        """Proceed prompt and final-message 👉 are the SAME question rendered once."""
        present, detail = check_next_steps_same_question_once()
        assert present, detail

    def test_has_dedup_note_tying_single_question_pending_marker(self) -> None:
        """Turn contains exactly one rendered forward transition 👉 question."""
        present, detail = check_next_steps_dedup_marker()
        assert present, detail


class TestModuleCompletionRenderOnceClause:
    """`module-completion.md` Final-Message Ordering render-once clause.

    **Validates: Requirements 2.1, 2.2, 2.3** (explores defect 1.2, 1.3)
    """

    def test_final_message_ordering_has_render_exactly_once_clause(self) -> None:
        """Final-Message Ordering states the transition 👉 renders exactly once."""
        present, detail = check_completion_render_once_clause()
        assert present, detail


class TestModuleTransitionsSinglePrompt:
    """`module-transitions.md` single-transition-prompt statement.

    **Validates: Requirements 2.1, 2.5** (explores defect 1.1, 1.5)
    """

    def test_states_transition_question_presented_once_per_turn(self) -> None:
        """Transition question is presented to the bootcamper exactly once per turn."""
        present, detail = check_transitions_once_per_turn()
        assert present, detail


class TestAskBootcamperInlineTransitionRecognition:
    """`ask-bootcamper.json` Phase 1 / Phase 1.5 inline-transition de-dup.

    **Validates: Requirements 2.4** (explores defect 1.4)
    """

    def test_phase1_or_phase1_5_recognizes_inline_transition_prompt(self) -> None:
        """Phase 1 / 1.5 recognize a transition prompt phrased inline (no 👉)."""
        present, detail = check_hook_inline_transition_recognition()
        assert present, detail

    def test_phase1_or_phase1_5_prohibits_second_transition_copy(self) -> None:
        """Phase 1 / 1.5 do not add or leave a second copy of the transition."""
        present, detail = check_hook_no_second_transition_copy()
        assert present, detail
