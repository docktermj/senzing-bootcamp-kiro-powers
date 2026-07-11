"""Bug-condition EXPLORATION tests for the question-format-consistency bugfix.

These tests encode the EXPECTED (fixed) behavior from design Property 1
("Bug Condition — Question Format Missing at Session-Recreation and
Track-Completion Paths") and are deliberately AUTHORED TO FAIL on the current
(unfixed) steering files. Their failure CONFIRMS the formatting-guidance gaps
exist at the two uncovered paths:

    isBugCondition(input) :=
        # Path A — session-recreation re-presentation
        (input.isSessionResumeTurn
         AND input.pendingQuestionExists
         AND input.isNewSession
         AND NOT input.pendingQuestionRenderedWithPointerAndBold)
        OR
        # Path B — graduation / track-completion closing turn
        ((input.isTrackCompletionTurn OR input.isGraduationFinalTurn)
         AND (NOT input.closingQuestionExists
              OR NOT input.closingQuestionHasPointerPrefix))

The fixed steering must satisfy the standard question convention: every
question presented to the bootcamper — including a re-presented pending
question and the bootcamp-completion question — carries the 👉 prefix at the
start of the line with the question text wrapped in bold (`**...**`), and the
👉 stays OUTSIDE the bold span.

Scoped-PBT approach — the property is scoped to the concrete failing cases by
parsing the four target steering files and asserting the required content
patterns are present:

    1. `session-resume-phase2-state-repair.md` has an explicit pending-question
       re-rendering instruction (👉 + bold) for re-presentation across a
       session boundary. (The guidance lives in this phase-2 companion file —
       reached from the session-resume flow, which hands back to Step 3
       "Summarize and Confirm" — rather than inline in `session-resume.md`
       Step 3, whose closing turn must carry exactly one 👉 question.)
    2. `module-completion-track.md` has an unconditional bootcamp-completion
       closing-question subsection with a 👉 + bold formatted question.
    3. `agent-behavior-rules.md` Rule 4 has a "Session-Recreation
       Re-Rendering" clause.
    4. `agent-behavior-rules.md` Rule 4 has a "Track-Completion / Graduation
       Terminal Turn" clause.
    5. `graduation.md` Mandatory Closing Step ends with a 👉 + bold closing
       question.

**DO NOT "fix" these tests or the steering files when they fail here** — the
failure is the SUCCESS case for an exploration test. After the fix (tasks
3.1–3.4) these same tests will pass and validate the expected behavior.

Feature: question-format-consistency (bugfix)

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6** (the fixed behavior
these encode across the two uncovered paths).
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: repo root -> senzing-bootcamp/steering)
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"
SESSION_RESUME_PATH: Path = STEERING_DIR / "session-resume.md"
# The pending-question re-rendering guidance was relocated here (a phase-2
# session-resume companion) so it lives OUT of session-resume.md's guarded
# Step 3 single-👉 closing zone while remaining reachable from the resume flow.
SESSION_RESUME_STATE_REPAIR_PATH: Path = (
    STEERING_DIR / "session-resume-phase2-state-repair.md"
)
MODULE_COMPLETION_TRACK_PATH: Path = STEERING_DIR / "module-completion-track.md"
AGENT_BEHAVIOR_RULES_PATH: Path = STEERING_DIR / "agent-behavior-rules.md"
GRADUATION_PATH: Path = STEERING_DIR / "graduation.md"

# The standard pointer indicator that must prefix every yielding question.
POINTER: str = "\U0001f449"  # 👉

# Canonical "standard question renderer" pattern: a 👉 pointer at the start,
# outside the bold span, immediately wrapping the question text in CommonMark
# bold. This is the format the fix must instruct the agent to produce.
POINTER_BOLD_RE: re.Pattern[str] = re.compile(rf"{POINTER}\s*\*\*[^*]+\*\*")


# ---------------------------------------------------------------------------
# Parsing helpers (minimal stdlib scanners, consistent with repo conventions)
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file.

    Args:
        path: Path to the steering Markdown file.

    Returns:
        The file's text, or the empty string when the file does not exist.
    """
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, start_pattern: str) -> str:
    """Return a Markdown section from its heading to the next same-level heading.

    Finds the first line matching ``start_pattern`` (a ``## `` heading) and
    returns everything up to — but not including — the next top-level ``## ``
    heading, or end-of-file when none follows. Sub-headings (``###``) and lines
    inside HTML comments (which carry leading whitespace) are retained.

    Args:
        text: The full file text.
        start_pattern: A regex matched against each line (e.g. ``r"^##\\s+Step 3"``).

    Returns:
        The section text, or the empty string when the heading is not found.
    """
    lines = text.splitlines()
    start_re = re.compile(start_pattern)

    start_idx: int | None = None
    for i, line in enumerate(lines):
        if start_re.match(line):
            start_idx = i
            break
    if start_idx is None:
        return ""

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if re.match(r"^##\s", lines[j]):
            end_idx = j
            break

    return "\n".join(lines[start_idx:end_idx])


def pending_rerender_section() -> str:
    """Return the "Pending Question Re-Rendering" section from its phase-2 home.

    The fix (task 3.1, as remediated) relocates the pending-question
    re-rendering guidance out of ``session-resume.md`` Step 3 — whose closing
    turn must contain exactly one 👉 question — into the phase-2 companion
    ``session-resume-phase2-state-repair.md``, adjacent to that file's
    "return to the Phase-1 flow at Step 3 (Summarize and Confirm)" handoff.

    Returns:
        The text of the ``## Pending Question Re-Rendering`` section, or the
        empty string when the section is absent.
    """
    return _extract_section(
        _read(SESSION_RESUME_STATE_REPAIR_PATH),
        r"^##\s+Pending Question Re-?Rendering",
    )


def rule4_text() -> str:
    """Return the text of Rule 4 (Consistent Pointer Indicator) in agent-behavior-rules.md."""
    return _extract_section(_read(AGENT_BEHAVIOR_RULES_PATH), r"^##\s+Rule\s+4\b")


def mandatory_closing_step_text() -> str:
    """Return the Mandatory Closing Step section of graduation.md."""
    return _extract_section(_read(GRADUATION_PATH), r"^##\s+Mandatory Closing Step")


# ---------------------------------------------------------------------------
# Detection logic — encodes the EXPECTED (fixed) guidance.
#
# Each predicate returns False on the current UNFIXED steering files (the gap)
# and True once the corresponding fix (tasks 3.1–3.4) is applied.
# ---------------------------------------------------------------------------


def session_resume_has_rerender_instruction() -> bool:
    """Whether session-resume.md Step 3 instructs re-rendering pending questions.

    The fix (task 3.1, as remediated) adds a "Pending Question Re-Rendering"
    section to the phase-2 companion ``session-resume-phase2-state-repair.md``
    that instructs the agent, when ``config/.question_pending`` exists from a
    prior session, to re-render the stored question with the standard 👉 + bold
    format rather than echoing the raw stored text.

    Returns:
        True when that section carries the re-rendering subsection AND references
        the ``.question_pending`` source AND uses the canonical 👉 + bold template.
    """
    section = pending_rerender_section()
    has_subsection = re.search(r"pending question re-?rendering", section, re.IGNORECASE) is not None
    mentions_rerender = re.search(r"re-?render", section, re.IGNORECASE) is not None
    references_pending_file = ".question_pending" in section
    has_pointer_bold_template = POINTER_BOLD_RE.search(section) is not None
    return (
        has_subsection
        and mentions_rerender
        and references_pending_file
        and has_pointer_bold_template
    )


def module_completion_has_closing_question() -> bool:
    """Whether module-completion-track.md defines a 👉 + bold closing question.

    The fix (task 3.2) adds an unconditional "Bootcamp-Completion Closing
    Question" subsection at the end of the celebration flow, using the
    ``👉 **...**`` format.

    Returns:
        True when the file carries a closing-question subsection heading AND a
        👉 + bold formatted question line.
    """
    text = _read(MODULE_COMPLETION_TRACK_PATH)
    has_subsection = re.search(r"closing question", text, re.IGNORECASE) is not None
    has_pointer_bold = POINTER_BOLD_RE.search(text) is not None
    return has_subsection and has_pointer_bold


def rule4_has_session_recreation_clause() -> bool:
    """Whether Rule 4 carries a "Session-Recreation Re-Rendering" clause.

    Returns:
        True when Rule 4 explicitly addresses re-rendering a pending question
        after a session boundary (task 3.3, clause 1).
    """
    return re.search(r"session-?recreation re-?rendering", rule4_text(), re.IGNORECASE) is not None


def rule4_has_track_completion_clause() -> bool:
    """Whether Rule 4 carries a "Track-Completion / Graduation Terminal Turn" clause.

    Returns:
        True when Rule 4 explicitly subjects the track-completion/graduation
        terminal turn to the 👉 + bold convention (task 3.3, clause 2).
    """
    text = rule4_text()
    mentions_track_completion = re.search(r"track-?completion", text, re.IGNORECASE) is not None
    mentions_terminal_turn = re.search(r"terminal turn", text, re.IGNORECASE) is not None
    return mentions_track_completion and mentions_terminal_turn


def graduation_closing_has_pointer_question() -> bool:
    """Whether graduation.md's Mandatory Closing Step ends with a 👉 + bold question.

    The fix (task 3.4) makes the graduation-final turn end with exactly one
    ``👉 **...**`` closing question.

    Returns:
        True when the Mandatory Closing Step section contains a 👉 + bold
        formatted question.
    """
    return POINTER_BOLD_RE.search(mandatory_closing_step_text()) is not None


def rerender_pending_question(text: str) -> str | None:
    """Model the re-rendered pending question the session-resume guidance produces.

    On UNFIXED steering, the session-resume flow carries no re-rendering
    instruction, so there is no guidance to apply and this returns ``None`` (the
    gap). On FIXED steering, the phase-2 re-rendering guidance re-renders the
    stored question through the standard renderer, producing ``👉 **{text}**``.

    Args:
        text: The raw stored pending-question text (lines 2+ of
            ``config/.question_pending``).

    Returns:
        The canonically rendered question, or ``None`` when no re-rendering
        instruction exists.
    """
    if not session_resume_has_rerender_instruction():
        return None
    return f"{POINTER} **{text}**"


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_question_text() -> st.SearchStrategy[str]:
    """Generate realistic stored pending-question texts.

    Produces non-empty single-line strings free of the ``*`` bold marker and of
    line breaks, modelling the raw question text persisted to
    ``config/.question_pending``.

    Returns:
        A Hypothesis strategy of question-text strings.
    """
    return (
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po"),
                blacklist_characters="*\n\r",
            ),
            min_size=1,
            max_size=80,
        )
        .map(str.strip)
        .filter(lambda s: len(s) > 0 and "*" not in s)
    )


# ---------------------------------------------------------------------------
# Path A — Session-recreation re-presentation guidance gap
# ---------------------------------------------------------------------------


class TestSessionRecreationRePresentationGap:
    """Session-resume must re-render a pending question with 👉 + bold.

    **Validates: Requirements 1.1, 1.2, 1.3**

    Scoped to Path A of the bug condition. AUTHORED TO FAIL on unfixed code,
    where the session-resume flow echoes the stored pending question without any
    re-rendering instruction, so the 👉 prefix and bold styling are lost across a
    session boundary. After the fix (as remediated) the guidance lives in the
    phase-2 companion ``session-resume-phase2-state-repair.md`` — out of
    ``session-resume.md`` Step 3's single-👉 closing zone but reachable from the
    resume flow.
    """

    def test_state_repair_has_pending_question_rerender_instruction(self) -> None:
        """The phase-2 state-repair file must instruct re-rendering with 👉 + bold.

        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        assert session_resume_has_rerender_instruction(), (
            "session-resume-phase2-state-repair.md has no pending-question "
            "re-rendering instruction: it lacks a 'Pending Question Re-Rendering' "
            "section telling the agent to re-render a stored config/.question_pending "
            "question with the 👉 prefix and bold formatting when re-presenting "
            "it across a session boundary. Without it the re-presentation path "
            "echoes the raw stored text, losing the 👉 prefix and bold styling."
        )

    @given(text=st_question_text())
    def test_rerendered_pending_question_uses_pointer_and_bold(self, text: str) -> None:
        """For any stored question text, the re-rendered form must be ``👉 **{text}**``.

        The re-rendering instruction must produce the standard pointer+bold
        pattern for arbitrary stored pending-question content, with 👉 outside
        the bold span.

        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        rendered = rerender_pending_question(text)
        assert rendered is not None, (
            "session-resume-phase2-state-repair.md carries no re-rendering "
            f"instruction, so a stored pending question ({text!r}) cannot be "
            "re-rendered through the standard renderer — it is echoed as raw, "
            "unformatted text."
        )
        assert rendered.startswith(f"{POINTER} "), (
            f"Re-rendered pending question {rendered!r} does not start with the "
            "👉 prefix at the start of the line."
        )
        assert POINTER_BOLD_RE.fullmatch(rendered), (
            f"Re-rendered pending question {rendered!r} does not match the "
            "standard 👉 **{text}** renderer (pointer outside the bold span, "
            "question text wrapped in bold)."
        )
        assert rendered == f"{POINTER} **{text}**"


# ---------------------------------------------------------------------------
# Path B — Track-completion / graduation closing-question guidance gap
# ---------------------------------------------------------------------------


class TestTrackCompletionClosingQuestionGap:
    """Track-completion and graduation turns must end with a 👉 + bold question.

    **Validates: Requirements 1.4, 1.5, 1.6**

    Scoped to Path B of the bug condition. AUTHORED TO FAIL on unfixed code,
    where ``module-completion-track.md`` has no unconditional closing 👉
    question after its celebration offers, and ``graduation.md``'s Mandatory
    Closing Step ends with a bold statement carrying a celebratory emoji but no
    👉 prefix.
    """

    def test_module_completion_track_has_closing_pointer_question(self) -> None:
        """A 👉 + bold bootcamp-completion closing question must exist.

        **Validates: Requirements 1.4, 1.5, 1.6**
        """
        assert module_completion_has_closing_question(), (
            "module-completion-track.md has no unconditional bootcamp-completion "
            "closing question: it defines no 'Closing Question' subsection and "
            "contains no 👉 **...** formatted question. When all celebration "
            "offers are declined, the track-completion turn ends with plain "
            "statements rather than a clearly marked 👉 closing question."
        )

    def test_graduation_mandatory_closing_step_has_pointer_question(self) -> None:
        """The graduation Mandatory Closing Step must end with a 👉 + bold question.

        **Validates: Requirements 1.4, 1.5, 1.6**
        """
        assert graduation_closing_has_pointer_question(), (
            "graduation.md Mandatory Closing Step has no 👉 **...** closing "
            "question: the post-graduation announcement ends with a bold "
            "statement (e.g. '📗 **Your recap is ready.**') but no 👉-prefixed "
            "closing question inviting final discussion."
        )


# ---------------------------------------------------------------------------
# Rule 4 coverage gap — the convention does not address the two paths
# ---------------------------------------------------------------------------


class TestRule4CoverageGap:
    """Rule 4 must explicitly cover both uncovered paths.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**

    AUTHORED TO FAIL on unfixed code, where Rule 4 defines the 👉 + bold
    convention and the leading-question guarantee but does not address
    re-rendering a stored question after a session boundary nor the
    track-completion/graduation terminal turn.
    """

    def test_rule4_has_session_recreation_rerendering_clause(self) -> None:
        """Rule 4 must carry a "Session-Recreation Re-Rendering" clause.

        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        assert rule4_has_session_recreation_clause(), (
            "agent-behavior-rules.md Rule 4 has no 'Session-Recreation "
            "Re-Rendering' clause: it does not instruct the agent to re-render "
            "a pending config/.question_pending question with the 👉 prefix and "
            "bold formatting after a session boundary."
        )

    def test_rule4_has_track_completion_terminal_turn_clause(self) -> None:
        """Rule 4 must carry a "Track-Completion / Graduation Terminal Turn" clause.

        **Validates: Requirements 1.4, 1.5, 1.6**
        """
        assert rule4_has_track_completion_clause(), (
            "agent-behavior-rules.md Rule 4 has no 'Track-Completion / "
            "Graduation Terminal Turn' clause: it does not subject the "
            "bootcamp-completion terminal turn to the 👉 + bold convention "
            "regardless of any celebratory emoji present."
        )
