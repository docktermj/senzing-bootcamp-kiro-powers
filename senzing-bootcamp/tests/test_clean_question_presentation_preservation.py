"""Preservation property tests for the clean-question-presentation bugfix.

Property 3 (Preservation) — Turn Boundary, Gate, One Question Rule, and Harness
Unchanged.

Following the bugfix **observation-first** methodology, these tests record the
behavior that the fix must PRESERVE. They are run against the UNFIXED tree first
and are EXPECTED TO PASS — a passing run captures the baseline that
``renderedTurn_original(X) == renderedTurn_fixed(X)`` must hold for every input
where the bug condition does NOT apply (``isBugCondition(X)`` is false):
non-question turns, gate-execution turns with non-marker evidence, explicit
re-display requests, and every harness-predicate input.

The conversational-eval harness engine (``eval_conversations.py``) is NOT
modified by the fix; it is the guiding constraint. These tests evaluate the
recorded baseline through that engine so the observations they lock in are the
engine's own, unchanged behavior:

- ``ends_with_question_then_stop`` accepts BOTH a turn that ends on the 👉 line
  (empty / whitespace trailing) AND a turn that ends on a ``🛑 STOP`` boundary
  line — the backward compatibility that lets the fix drop the rendered marker
  without touching the predicate.
- ``gate_not_bypassed`` passes on the Module 3 gate turn via its non-marker
  execution evidence ("Your visualization is running", "Checkpoint written:
  module_3_verification..."), so removing the rendered ``🛑 STOP`` line does not
  weaken gate enforcement.
- Every shipped fixture that poses a 👉 question already carries exactly one 👉
  and ends on it (the One Question Rule / leading-question guarantee).
- The internal-directive glyphs the preserved presence tests rely on remain in
  the steering (module-01 keeps its internal ``🛑 STOP`` directives; module-02
  keeps its informational Step 5a with no rendered ``🛑`` and two 👉 prompts).
- A turn that re-displays a question at the bootcamper's explicit request poses
  one clean question and is therefore NOT a duplicate violation (C(X) false).
- The full shipped-fixture run exits 0 and non-question turns are unaffected.

Bug_Condition: NOT isBugCondition(X) — non-question turns, non-marker gate
    evidence, explicit re-display, harness-predicate inputs.
Expected_Behavior: renderedTurn_original(X) == renderedTurn_fixed(X) for all X
    where NOT isBugCondition(X).

Feature: clean-question-presentation

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

from __future__ import annotations

import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from eval_conversations import (  # noqa: E402
    POINTER,
    AssertionSpec,
    Scenario,
    Turn,
    evaluate_scenario,
    load_scenarios,
    run,
)

# ---------------------------------------------------------------------------
# Paths and marker constants
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_EVAL_DIR = _BOOTCAMP_DIR / "tests" / "eval"
_MODULE01_FILE = _STEERING_DIR / "module-01-phase1-discovery.md"
_MODULE02_FILE = _STEERING_DIR / "module-02-sdk-setup.md"

_STOP = "\U0001f6d1"  # 🛑  U+1F6D1 — hard-stop marker
_GATE = "\u26d4"  # ⛔  U+26D4 — mandatory-gate marker

# A hard-stop boundary line — the fixture-authoring convention the harness
# treats as a valid turn boundary (never substantive content, never a
# self-answer). Assembled with the em dash the shipped fixtures use.
_BOUNDARY_LINE = f"{_STOP} STOP \u2014 End your response here."

# The Module 3 visualization gate fixture whose non-marker execution evidence
# ("visualization is running" / "Checkpoint written: module_3_verification...")
# keeps gate_not_bypassed passing after the rendered 🛑 STOP line is removed.
_GATE_FIXTURE = "module3_gate_not_bypassed.json"

# Every shipped fixture whose agent turn poses a 👉 question. Each already
# carries exactly one 👉 and ends on that question — the One Question Rule /
# leading-question guarantee the fix must preserve.
_POINTER_FIXTURES: tuple[str, ...] = (
    "single_question_stop.json",
    "confirmation_question_disambiguation.json",
    "license_insufficient_search_docs.json",
    "mcp_first_sdk_reference.json",
    "sql_redirect_reporting_guide.json",
    "module3_gate_not_bypassed.json",
)

# Shipped non-question fixtures (no 👉) — module transitions / substantive
# answers. They must stay completely unaffected by the fix.
_NON_QUESTION_FIXTURES: tuple[tuple[str, AssertionSpec], ...] = (
    ("module_transition_completeness.json", AssertionSpec("transition_response_completeness")),
    ("substantive_response_after_confirmation.json", AssertionSpec("substantive_response")),
)


# ---------------------------------------------------------------------------
# Helpers (pure, deterministic)
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a file.

    Args:
        path: The file to read.

    Returns:
        The full file contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _evaluate(content: str, assertions: tuple[AssertionSpec, ...]) -> list:
    """Evaluate ``assertions`` against a single rendered turn via the harness engine.

    Args:
        content: The rendered agent-turn text to evaluate.
        assertions: The behavioral assertions to attach to the turn.

    Returns:
        The list of ``EvalFailure`` objects the harness produced (empty on pass).
    """
    turn = Turn(role="agent", content=content, assertions=list(assertions))
    scenario = Scenario(
        scenario="clean_question_presentation_preservation",
        description="Preservation baseline evaluated through the unmodified harness engine.",
        turns=[turn],
        rule_ref=None,
        source=Path("inline"),
    )
    return evaluate_scenario(scenario)


def _evaluate_conversation(
    prior_bootcamper: str, agent_content: str, assertions: tuple[AssertionSpec, ...]
) -> list:
    """Evaluate an agent turn that follows a bootcamper turn, via the harness engine.

    Models a two-turn exchange (the bootcamper speaks, then the agent responds)
    so context-dependent scenarios such as an explicit re-display request are
    represented faithfully; the assertions are attached to the agent turn.

    Args:
        prior_bootcamper: The preceding bootcamper turn text.
        agent_content: The agent-turn text to evaluate.
        assertions: The behavioral assertions to attach to the agent turn.

    Returns:
        The list of ``EvalFailure`` objects the harness produced (empty on pass).
    """
    scenario = Scenario(
        scenario="clean_question_presentation_preservation_conversation",
        description="Preservation baseline for a context-dependent agent turn.",
        turns=[
            Turn(role="bootcamper", content=prior_bootcamper, assertions=[]),
            Turn(role="agent", content=agent_content, assertions=list(assertions)),
        ],
        rule_ref=None,
        source=Path("inline"),
    )
    return evaluate_scenario(scenario)


def _format(failures: list, content: str) -> str:
    """Build an assertion message that names each failure and shows the turn.

    Args:
        failures: The harness ``EvalFailure`` list.
        content: The rendered turn that produced the failures.

    Returns:
        A human-readable multi-line message for the failing assertion.
    """
    reasons = "\n".join(f"  - {f.assertion_type}: {f.message}" for f in failures)
    return (
        "expected the preserved baseline behavior to hold, but the harness "
        f"reported:\n{reasons}\n--- rendered turn ---\n{content}"
    )


def _fixture_agent_turns(fixture_name: str) -> list[Turn]:
    """Load a shipped fixture and return its agent turns.

    Args:
        fixture_name: The fixture filename under ``senzing-bootcamp/tests/eval``.

    Returns:
        The agent turns recorded in the fixture.
    """
    scenario = load_scenarios(_EVAL_DIR / fixture_name)[0]
    return [t for t in scenario.turns if t.role == "agent"]


def _fixture_pointer_turns(fixture_name: str) -> list[Turn]:
    """Load a shipped fixture and return the agent turns that pose a 👉 question.

    Args:
        fixture_name: The fixture filename under ``senzing-bootcamp/tests/eval``.

    Returns:
        The agent turns whose recorded content contains the 👉 pointer.
    """
    return [t for t in _fixture_agent_turns(fixture_name) if POINTER in t.content]


def _strip_stop_lines(content: str) -> str:
    """Remove every line carrying the 🛑 marker, mimicking the fixed rendering.

    The fix drops the rendered ``🛑 STOP`` boundary line so a question turn ends
    on the 👉 question. Applying that transformation here lets the preservation
    tests observe that gate enforcement and turn bounding survive the removal.

    Args:
        content: The recorded agent-turn text.

    Returns:
        The content with any line containing the 🛑 glyph removed, trailing
        whitespace stripped.
    """
    kept = [line for line in content.splitlines() if _STOP not in line]
    return "\n".join(kept).rstrip()


# ---------------------------------------------------------------------------
# Strategies (st_-prefixed, constrained to the relevant input space)
# ---------------------------------------------------------------------------

# Plain words with no pointer, no "?", and none of the compound conjunctions —
# safe filler for a single clean pointer question.
_PLAIN_WORDS: tuple[str, ...] = (
    "how",
    "many",
    "data",
    "sources",
    "systems",
    "will",
    "we",
    "use",
    "ready",
    "continue",
    "next",
    "explore",
    "the",
    "records",
)

# Benign lead-in vocabulary: no pointer, no "?", no conjunction, no execution
# marker, and no skip/bypass language — so prepending it to a gate turn cannot
# alter the gate_not_bypassed / boundary verdict on its own.
_SAFE_WORDS: tuple[str, ...] = (
    "great",
    "thanks",
    "for",
    "confirming",
    "let",
    "us",
    "keep",
    "going",
    "with",
    "the",
    "walkthrough",
    "today",
)


@st.composite
def st_pointer_question_line(draw: st.DrawFn) -> str:
    """Build a single clean pointer question line: 👉 + plain words + '?'."""
    words = draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=8))
    return f"{POINTER} " + " ".join(words) + "?"


@st.composite
def st_bounded_question_turn(draw: st.DrawFn) -> tuple[str, str]:
    """Build a bounded question turn and the boundary kind it ends on.

    The turn always ends on the 👉 question line, optionally followed by only
    whitespace or by the ``🛑 STOP`` boundary line. Returns the boundary kind
    alongside the text so a test can record that BOTH the empty-trailing form and
    the ``🛑 STOP`` form are accepted by the unmodified harness.
    """
    line = draw(st_pointer_question_line())
    kind = draw(st.sampled_from(["empty", "whitespace", "stop_boundary"]))
    if kind == "empty":
        return line, kind
    if kind == "whitespace":
        return f"{line}\n   \n\t", kind
    return f"{line}\n\n{_BOUNDARY_LINE}", kind


@st.composite
def st_compound_question_turn(draw: st.DrawFn) -> str:
    """Build a genuine compound question (two '?' or a distinctive conjunction).

    Used to record that the compound-question predicate still FLAGS a real
    compound, so the compound-rewrite protocol (Rule 3) is preserved.
    """
    left = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=4)))
    right = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=4)))
    if draw(st.booleans()):
        return f"{POINTER} {left}? {right}?"
    conj = draw(
        st.sampled_from(
            ["or would you rather", "or should we", "or would you prefer", "alternatively"]
        )
    )
    return f"{POINTER} {left} {conj} {right}?"


@st.composite
def st_benign_lead_in(draw: st.DrawFn) -> str:
    """Build benign lead-in prose with no pointer, '?', conjunction, or gate signal."""
    words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=8))
    return " ".join(words)


# ---------------------------------------------------------------------------
# Property 3.1 / 3.2 — turn boundary and stop-and-wait preserved
# ---------------------------------------------------------------------------


class TestTurnBoundaryPreserved:
    """The harness bounds a turn from the trailing 👉 alone AND from a 🛑 STOP line.

    Records the backward compatibility the fix depends on: the unmodified engine
    already accepts a turn that ends on the 👉 question (empty / whitespace
    trailing) as correctly bounded, and it still accepts a turn that ends on a
    ``🛑 STOP`` boundary line. In both forms the agent does not self-answer, so
    the stop-and-wait guarantee is intact.

    Validates: Requirements 3.1, 3.2
    """

    _BOUNDARY_ASSERTIONS: tuple[AssertionSpec, ...] = (
        AssertionSpec("exactly_one_pointer"),
        AssertionSpec("ends_with_question_then_stop"),
        AssertionSpec("no_self_answer"),
    )

    @given(payload=st_bounded_question_turn())
    def test_both_boundary_forms_are_accepted(self, payload: tuple[str, str]) -> None:
        """A turn ending on the 👉 line OR on a 🛑 STOP line bounds correctly.

        Passes on the unfixed tree for every boundary kind (empty trailing,
        whitespace trailing, and a rendered ``🛑 STOP`` line), recording that the
        engine bounds the turn either way and never treats the trailing content
        as a self-answer.

        Args:
            payload: A ``(turn_text, boundary_kind)`` pair from the strategy.
        """
        content, _kind = payload
        failures = _evaluate(content, self._BOUNDARY_ASSERTIONS)
        assert not failures, _format(failures, content)


# ---------------------------------------------------------------------------
# Property 3.3 — mandatory gate execution preserved via non-marker evidence
# ---------------------------------------------------------------------------


class TestGateExecutionPreserved:
    """The Module 3 gate stays executed-and-not-bypassed without a rendered marker.

    Records that ``gate_not_bypassed`` passes on the Module 3 visualization gate
    turn both as shipped (with the ``🛑 STOP`` line) and after that line is
    removed — because the turn retains non-marker execution evidence ("Your
    visualization is running", "Checkpoint written: module_3_verification..."). A
    benign lead-in prepended to the marker-stripped turn does not change the
    verdict, so removing the rendered marker cannot weaken gate enforcement.

    Validates: Requirements 3.3
    """

    _GATE_ASSERTIONS: tuple[AssertionSpec, ...] = (
        AssertionSpec("gate_not_bypassed", {"step": "3.9"}),
        AssertionSpec("exactly_one_pointer"),
        AssertionSpec("ends_with_question_then_stop"),
    )

    def test_gate_turn_passes_as_shipped(self) -> None:
        """A 🛑 STOP-bounded gate turn (built from the shipped fixture) passes gate_not_bypassed.

        Task 4.3 removed the rendered ``🛑 STOP`` line from the shipped
        ``module3_gate_not_bypassed.json`` as part of the C1 fix, so reading the
        marker from the shipped fixture is no longer valid — the marker-free
        shipped form is now covered by ``test_gate_turn_passes_without_rendered_marker``.
        This test preserves the DISTINCT backward-compatibility coverage it was
        written for — a gate turn that ends on a ``🛑 STOP`` boundary line is still
        recognized as executed-and-not-bypassed and correctly bounded — by
        synthesizing that boundary form inline: it appends the internal
        ``_BOUNDARY_LINE`` to the shipped (marker-free) gate content rather than
        depending on a rendered marker the fixture no longer carries.
        """
        turns = _fixture_pointer_turns(_GATE_FIXTURE)
        assert turns, f"{_GATE_FIXTURE} has no 👉 gate turn to evaluate"
        content = f"{_strip_stop_lines(turns[0].content)}\n\n{_BOUNDARY_LINE}"
        assert _STOP in content, "the synthesized gate turn must end on a 🛑 STOP boundary line"
        failures = _evaluate(content, self._GATE_ASSERTIONS)
        assert not failures, _format(failures, content)

    def test_gate_turn_passes_without_rendered_marker(self) -> None:
        """With the 🛑 STOP line removed, the gate still passes via non-marker evidence."""
        turns = _fixture_pointer_turns(_GATE_FIXTURE)
        assert turns, f"{_GATE_FIXTURE} has no 👉 gate turn to evaluate"
        content = _strip_stop_lines(turns[0].content)
        assert _STOP not in content, "the 🛑 STOP line should be stripped for this observation"
        assert "visualization is running" in content.lower()
        assert "module_3_verification" in content.lower()
        failures = _evaluate(content, self._GATE_ASSERTIONS)
        assert not failures, _format(failures, content)

    @given(lead_in=st_benign_lead_in())
    def test_marker_stripped_gate_is_stable_under_benign_lead_in(self, lead_in: str) -> None:
        """A benign lead-in on the marker-stripped gate turn keeps the verdict.

        Args:
            lead_in: Generated benign prose prepended to the gate turn.
        """
        turns = _fixture_pointer_turns(_GATE_FIXTURE)
        assert turns, f"{_GATE_FIXTURE} has no 👉 gate turn to evaluate"
        base = _strip_stop_lines(turns[0].content)
        content = f"{lead_in}\n\n{base}" if lead_in else base
        failures = _evaluate(content, self._GATE_ASSERTIONS)
        assert not failures, _format(failures, content)


# ---------------------------------------------------------------------------
# Property 3.1 — One Question Rule / leading-question guarantee preserved
# ---------------------------------------------------------------------------


class TestOneQuestionRulePreserved:
    """Every shipped fixture that poses a 👉 question carries exactly one, ended on.

    Records the One Question Rule / leading-question guarantee across the shipped
    pointer-bearing fixtures: each agent question turn contains exactly one 👉 and
    ends on that question.

    Validates: Requirements 3.1
    """

    _ONE_QUESTION_ASSERTIONS: tuple[AssertionSpec, ...] = (
        AssertionSpec("exactly_one_pointer"),
        AssertionSpec("ends_with_question_then_stop"),
    )

    @given(fixture_name=st.sampled_from(_POINTER_FIXTURES))
    def test_pointer_fixture_has_single_leading_question(self, fixture_name: str) -> None:
        """Each shipped 👉 fixture ends with exactly one leading question.

        Args:
            fixture_name: The generated shipped-fixture filename.
        """
        turns = _fixture_pointer_turns(fixture_name)
        assert turns, f"{fixture_name} has no 👉 agent turn to evaluate"
        for turn in turns:
            failures = _evaluate(turn.content, self._ONE_QUESTION_ASSERTIONS)
            assert not failures, _format(failures, turn.content)


# ---------------------------------------------------------------------------
# Property 3.4 — compound-question rewrite protocol preserved
# ---------------------------------------------------------------------------


class TestCompoundQuestionRulePreserved:
    """The compound-question predicate still flags real compounds, passes clean ones.

    Records that the harness compound-question detection (the deterministic proxy
    for the Rule 3 compound-rewrite protocol) is unchanged: a single clean
    question passes ``no_compound_question`` while a genuine compound (two '?' or
    a distinctive conjunction joining alternatives) is still flagged.

    Validates: Requirements 3.4
    """

    _NO_COMPOUND: tuple[AssertionSpec, ...] = (AssertionSpec("no_compound_question"),)

    @given(line=st_pointer_question_line())
    def test_single_clean_question_passes(self, line: str) -> None:
        """A single, non-compound question passes no_compound_question.

        Args:
            line: A generated single clean pointer question line.
        """
        failures = _evaluate(line, self._NO_COMPOUND)
        assert not failures, _format(failures, line)

    @given(content=st_compound_question_turn())
    def test_genuine_compound_is_still_flagged(self, content: str) -> None:
        """A genuine compound question is still detected (predicate unchanged).

        Args:
            content: A generated compound question turn.
        """
        failures = _evaluate(content, self._NO_COMPOUND)
        assert failures, (
            "expected the compound-question rule to still flag a genuine compound, "
            f"but it passed:\n--- rendered turn ---\n{content}"
        )


# ---------------------------------------------------------------------------
# Property 3.5 / 3.6 — explicit re-display and clean corrective output preserved
# ---------------------------------------------------------------------------


class TestExplicitRedisplayPreserved:
    """Re-displaying a question at the bootcamper's request is not a duplicate.

    Records the C(X)-false edge case: when the bootcamper explicitly asks to see
    the question again, the agent re-displays a single clean 👉 question. That
    turn satisfies expectedBehavior (exactly one 👉, non-compound, no self-answer,
    ends on the question), so it is NOT flagged as a duplicate violation — the
    re-display and clean-corrective-output behaviors are preserved.

    Validates: Requirements 3.5, 3.6
    """

    _EXPECTED_BEHAVIOR: tuple[AssertionSpec, ...] = (
        AssertionSpec("exactly_one_pointer"),
        AssertionSpec("no_compound_question"),
        AssertionSpec("no_self_answer"),
        AssertionSpec("ends_with_question_then_stop"),
    )

    @given(line=st_pointer_question_line())
    def test_redisplay_on_explicit_request_is_clean(self, line: str) -> None:
        """A re-display turn poses one clean question and is not a duplicate.

        Args:
            line: The generated single clean pointer question being re-displayed.
        """
        agent_content = f"Sure — here is that question again:\n\n{line}"
        failures = _evaluate_conversation(
            "Can you show me that question again?", agent_content, self._EXPECTED_BEHAVIOR
        )
        assert not failures, _format(failures, agent_content)


# ---------------------------------------------------------------------------
# Property 3.7 — harness engine and non-question turns unchanged; run exits 0
# ---------------------------------------------------------------------------


class TestHarnessAndNonQuestionTurnsPreserved:
    """The shipped run exits 0 and non-question turns are completely unaffected.

    Records that a full run over the shipped Eval_Directory reports zero failures
    (exit 0), and that non-question turns (module transitions, substantive
    answers) still satisfy their assertions through the unmodified engine.

    Validates: Requirements 3.7
    """

    def test_full_shipped_run_exits_zero(self) -> None:
        """A full run over the shipped Eval_Directory exits 0 (CI parity)."""
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = run(_EVAL_DIR)
        assert code == 0

    @pytest.mark.parametrize(
        "fixture_name,assertion",
        _NON_QUESTION_FIXTURES,
        ids=[name for name, _ in _NON_QUESTION_FIXTURES],
    )
    def test_non_question_turn_unaffected(
        self, fixture_name: str, assertion: AssertionSpec
    ) -> None:
        """A non-question shipped fixture still satisfies its assertion.

        Args:
            fixture_name: The shipped non-question fixture filename.
            assertion: The assertion that fixture exercises.
        """
        turns = _fixture_agent_turns(fixture_name)
        assert turns, f"{fixture_name} has no agent turn to evaluate"
        for turn in turns:
            assert POINTER not in turn.content, (
                f"precondition: {fixture_name} models a non-question turn"
            )
            failures = _evaluate(turn.content, (assertion,))
            assert not failures, _format(failures, turn.content)


# ---------------------------------------------------------------------------
# Property 3.3 / 3.6 — preserved internal-directive presence in steering
# ---------------------------------------------------------------------------


class TestInternalDirectivePresencePreserved:
    """The internal-directive glyphs the preserved presence tests rely on remain.

    Records the steering baseline that keeps the preserved presence tests passing
    (``test_business_case_offer_steering.py``, ``test_licensing_guidance.py``,
    ``test_module2_license_acquisition_info.py``): module-01 discovery keeps its
    internal ``🛑 STOP`` directives, and module-02 keeps its informational Step 5a
    with no rendered ``🛑`` glyph and exactly two 👉 prompts. These internal
    directives still govern agent behavior; only their user-facing rendering
    beside a question changes under the fix.

    Validates: Requirements 3.3, 3.6
    """

    def test_module01_keeps_internal_stop_directives(self) -> None:
        """module-01 discovery retains its internal 🛑 STOP directives."""
        content = _read(_MODULE01_FILE)
        assert f"{_STOP} STOP" in content, (
            "module-01 discovery must keep its internal 🛑 STOP directive "
            "(the Business Case Offer presence test depends on it)"
        )

    def test_module02_step5a_stays_informational(self) -> None:
        """module-02 keeps zero rendered 🛑 glyphs and exactly two 👉 prompts."""
        content = _read(_MODULE02_FILE)
        assert content.count(_STOP) == 0, (
            f"module-02 must render no 🛑 glyph, found {content.count(_STOP)}"
        )
        assert content.count(POINTER) == 2, (
            f"module-02 must keep exactly two 👉 prompts, found {content.count(POINTER)}"
        )
