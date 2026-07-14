"""Bug-condition exploration test for the clean-question-presentation duplicate question.

Property 2 (Bug Condition) — Question Shown Exactly Once.

These tests reproduce the CURRENT rendered comprehension-check turn — the one
observed before track selection, where the agent first composes a prose "or"
compound question ("Does everything make sense so far, or is there anything
you'd like me to clarify?"), the compound-question self-correction regenerates a
clean single question, and BOTH reach the bootcamper in the same turn — then
assert the FIXED behavior (``expectedBehavior`` from design.md) through the
conversational-eval harness predicates (``eval_conversations.py`` is NOT
modified).

They are EXPECTED TO FAIL on the unfixed tree — the failures are the
counterexamples that confirm Bug_Condition C2 (a comprehension-check question
rendered twice: the "or ... clarify?" compound and its regeneration) exists. DO
NOT "fix" these tests when they fail: the failure is the correct, expected
outcome for this exploration task, and the same assertions become the fix oracle
once the steering composes one clean single question and the modeled turn is
edited to it (they flip to PASS in task 4.6).

Bug_Condition: isBugCondition(X) C2 branch — duplicated OR (composedCompoundFirst
    AND regeneratedQuestionAlreadyShown).
Expected_Behavior: expectedBehavior(result) — count_pointers == 1, NOT
    hasCompoundQuestion, questionShownExactlyOnce.

Scoped to the concrete observed case (the pre-track comprehension check, modeled
in ``eval_exploration/comprehension_check_duplicate.json``) while still
generating over the transcript-text domain via Hypothesis. The exploration
fixture lives outside ``senzing-bootcamp/tests/eval`` on purpose so the default
harness run and the shipped-fixture count/zero-failure oracles stay unaffected
while the bug is still surfaced here.

Feature: clean-question-presentation

Validates: Requirements 1.4, 1.5, 2.4, 2.5
"""

from __future__ import annotations

import sys
from pathlib import Path

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
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_EXPLORATION_DIR = _BOOTCAMP_DIR / "tests" / "eval_exploration"
_DUPLICATE_FIXTURE = _EXPLORATION_DIR / "comprehension_check_duplicate.json"

# The fixed-behavior assertion set for the C2 branch — mirrors the C2-relevant
# clauses of expectedBehavior(result) in design.md: exactly one 👉 (the question
# is shown exactly once) and a single, non-compound question (no compound "or"
# alternative and no second question mark from a regenerated duplicate).
_EXPECTED_BEHAVIOR_ASSERTIONS: tuple[AssertionSpec, ...] = (
    AssertionSpec("exactly_one_pointer"),
    AssertionSpec("no_compound_question"),
)


# ---------------------------------------------------------------------------
# Helpers (pure, deterministic)
# ---------------------------------------------------------------------------


def _comprehension_check_turns() -> list[Turn]:
    """Load the exploration fixture and return its 👉 agent turns.

    Returns:
        The agent turns from ``comprehension_check_duplicate.json`` whose recorded
        content contains the 👉 pointer — i.e. the comprehension-check turn(s).
    """
    scenario = load_scenarios(_DUPLICATE_FIXTURE)[0]
    return [t for t in scenario.turns if t.role == "agent" and POINTER in t.content]


def _evaluate(content: str, assertions: tuple[AssertionSpec, ...]) -> list:
    """Evaluate ``assertions`` against a rendered turn via the harness engine.

    Args:
        content: The rendered agent-turn text to evaluate.
        assertions: The behavioral assertions to attach to the turn.

    Returns:
        The list of ``EvalFailure`` objects the harness produced (empty on pass).
    """
    turn = Turn(role="agent", content=content, assertions=list(assertions))
    scenario = Scenario(
        scenario="clean_question_presentation_duplicate_question",
        description="Exploration reproduction of the duplicate-question bug condition (C2).",
        turns=[turn],
        rule_ref=None,
        source=Path("inline"),
    )
    return evaluate_scenario(scenario)


def _format(failures: list, content: str) -> str:
    """Build an assertion message that names each violation and shows the turn.

    Args:
        failures: The harness ``EvalFailure`` list.
        content: The rendered turn that produced the failures.

    Returns:
        A human-readable multi-line message for the failing assertion.
    """
    reasons = "\n".join(f"  - {f.assertion_type}: {f.message}" for f in failures)
    return (
        "expected the comprehension-check question shown exactly once "
        f"(expectedBehavior), but the harness found:\n{reasons}\n"
        f"--- rendered turn ---\n{content}"
    )


# ---------------------------------------------------------------------------
# Benign-prose strategy (constrained to the input space)
# ---------------------------------------------------------------------------
#
# A lead-in generator that never introduces a second 👉 pointer, a question mark,
# or a compound conjunction — so the pass/fail verdict is driven solely by the
# modeled comprehension-check question content, not by the generated wrapper.
# This keeps the property a genuine oracle: it fails while the duplicate/compound
# is present and passes once the turn is a single clean question.
_SAFE_WORDS: tuple[str, ...] = (
    "Great",
    "thanks",
    "for",
    "walking",
    "through",
    "the",
    "entity",
    "resolution",
    "overview",
    "with",
    "me",
    "today",
    "we",
    "covered",
    "a",
    "lot",
    "of",
    "ground",
    "and",
    "the",
    "concepts",
    "landed",
    "well",
)


def st_benign_lead_in() -> st.SearchStrategy[str]:
    """Return a strategy for benign lead-in prose with no 👉, "?", or conjunction.

    Draws from a fixed safe vocabulary (no "or"/"alternatively", no pointer, no
    question mark) so prepending the result to a rendered turn cannot itself add a
    pointer, a second question mark, or a compound conjunction.

    Returns:
        A Hypothesis strategy producing a single benign lead-in line.
    """
    return st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=8).map(
        lambda words: " ".join(words)
    )


# ---------------------------------------------------------------------------
# Harness-evaluated reproduction (mirrors expectedBehavior via the predicates)
# ---------------------------------------------------------------------------


class TestDuplicateQuestionExplorationHarness:
    """Reproduce C2 by evaluating the current rendered turn with the fix oracle.

    Each test asserts the FIXED behavior; on the unfixed tree the harness returns
    failures whose messages are the counterexamples that confirm the bug.

    Validates: Requirements 1.4, 1.5, 2.4, 2.5
    """

    def test_comprehension_check_turn_shown_exactly_once(self) -> None:
        """The comprehension-check turn must pose one clean question, shown once.

        EXPECTED TO FAIL on the unfixed tree with ``expected exactly one pointer,
        found 2`` and ``compound question detected (multiple question marks: found
        2)`` — the compound "or" question and its regenerated clean question both
        appear, so the bootcamper sees the question twice.
        """
        turns = _comprehension_check_turns()
        assert turns, (
            "precondition: the comprehension-check 👉 turn was not found in "
            f"{_DUPLICATE_FIXTURE.name}"
        )
        failures: list = []
        for turn in turns:
            failures.extend(_evaluate(turn.content, _EXPECTED_BEHAVIOR_ASSERTIONS))
        assert not failures, _format(failures, "\n\n".join(t.content for t in turns))


# ---------------------------------------------------------------------------
# Scoped property-based reproduction over the transcript-text domain
# ---------------------------------------------------------------------------


class TestDuplicateQuestionProperty:
    """Property: the comprehension-check turn honors expectedBehavior (shown once).

    Scopes to the concrete observed case while generating over the transcript-text
    domain: a benign lead-in is prepended to the modeled comprehension-check turn.
    Because the lead-in adds no pointer, question mark, or conjunction, the verdict
    is decided entirely by the modeled question content.

    Validates: Requirements 1.4, 1.5, 2.4, 2.5
    """

    @given(lead_in=st_benign_lead_in())
    def test_rendered_question_turn_shown_exactly_once(self, lead_in: str) -> None:
        """For any benign lead-in, the turn must pose one clean question, shown once.

        EXPECTED TO FAIL on the unfixed tree; Hypothesis reports the failing
        ``lead_in`` and the harness message is the counterexample.

        Args:
            lead_in: The generated benign lead-in prose prepended to the turn.
        """
        turns = _comprehension_check_turns()
        assert turns, (
            "precondition: the comprehension-check 👉 turn was not found in "
            f"{_DUPLICATE_FIXTURE.name}"
        )
        base = "\n\n".join(t.content for t in turns)
        content = f"{lead_in}\n\n{base}" if lead_in else base
        failures = _evaluate(content, _EXPECTED_BEHAVIOR_ASSERTIONS)
        assert not failures, _format(failures, content)
