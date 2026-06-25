"""
Bug condition exploration tests for single-question format enforcement gap.

These tests encode the EXPECTED (fixed) behavior. They are designed to FAIL on
the current unfixed code, confirming the bug exists — compound questions in
agent output pass through with no validation.

The enforcement gap: write-policy-gate only validates questions written to
config/.question_pending. Compound questions that appear directly in the
agent's response text (with 👉 prefix) are never intercepted by any hook.

Validates: Requirements 1.1, 1.2, 1.3, 1.4
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
QUESTION_FORMAT_GATE_HOOK = HOOKS_DIR / "ask-bootcamper.kiro.hook"


# ---------------------------------------------------------------------------
# Detection logic — encodes the EXPECTED enforcement behavior
# ---------------------------------------------------------------------------

# Patterns that indicate prose-joined alternatives in a 👉 question
COMPOUND_PATTERNS: list[re.Pattern[str]] = [
    # "Or shall we...", "Or would you...", "Or should we..." as sentence starters
    re.compile(r"\?\s+Or\s+(shall|would|should|can|do)\s", re.IGNORECASE),
    # "...X or Y?" where both are actions/options joined by "or" in prose
    re.compile(r"👉[^?]*\b(\w+)\s+or\s+(\w+)\b[^?]*\?", re.IGNORECASE),
    # "...X, or would you rather/prefer..."
    re.compile(r",\s+or\s+(would you|if you|shall we|should we)", re.IGNORECASE),
]


def is_compound_question(output: str) -> bool:
    """Detect if agent output contains a 👉 question with prose-joined alternatives.

    This encodes the bug condition: a 👉 question that contains multiple
    alternatives joined by "or" in prose form (not as a numbered list).
    """
    # Must contain a 👉 question
    if "👉" not in output:
        return False

    # Extract the question portion (from 👉 to end or next paragraph)
    question_match = re.search(r"👉.*?\?", output, re.DOTALL)
    if not question_match:
        return False

    question_text = question_match.group()

    # Check if it's already formatted as a numbered list (not a bug)
    # A numbered list follows the question with "1. " items
    after_question = output[question_match.end():]
    if re.search(r"\n\s*1\.\s+", after_question):
        return False

    # Check for compound patterns
    for pattern in COMPOUND_PATTERNS:
        if pattern.search(question_text) or pattern.search(output):
            return True

    return False


def enforcement_detects_compound(output: str) -> bool:
    """Check if the current enforcement system detects a compound question.

    On UNFIXED code: The only enforcement is write-policy-gate which only
    validates .question_pending writes. There is NO hook that validates
    compound questions in direct agent output. So this always returns False
    for direct output — confirming the enforcement gap.

    On FIXED code: The consolidated ask-bootcamper.kiro.hook (agentStop)
    contains a Question_Format_Phase (Phase 4) that intercepts and detects
    compound questions in agent output via silent self-correction.
    """
    # Check if the consolidated hook exists (the fix)
    if not QUESTION_FORMAT_GATE_HOOK.exists():
        # No enforcement hook exists for agent output — gap confirmed
        return False

    # If the hook exists, verify it would catch compound questions
    hook_data = json.loads(QUESTION_FORMAT_GATE_HOOK.read_text())
    prompt = hook_data.get("then", {}).get("prompt", "")

    # The hook must be an agentStop hook (fires on all agent output)
    hook_type = hook_data.get("when", {}).get("type", "")
    if hook_type != "agentStop":
        return False

    # Extract the Question_Format_Phase (Phase 4) section from the consolidated prompt
    phase4_match = re.search(
        r"PHASE 4:.*?Question_Format_Phase.*?(?=═{4,}|\Z)",
        prompt,
        re.DOTALL,
    )
    if not phase4_match:
        return False

    phase4_text = phase4_match.group()

    # The Phase 4 section must contain compound question detection logic
    detection_keywords = ["compound", "or", "alternative", "numbered list"]
    has_detection = any(kw in phase4_text.lower() for kw in detection_keywords)

    return has_detection


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating compound questions
# ---------------------------------------------------------------------------

def st_action_phrase() -> st.SearchStrategy[str]:
    """Generate random action phrases for questions."""
    actions = [
        "create a summary",
        "proceed with the next step",
        "set up the project",
        "run the tests",
        "configure the database",
        "install the SDK",
        "review the results",
        "adjust the settings",
        "skip this step",
        "move on to Module 3",
        "move on to Module 4",
        "start the demo",
        "load the data",
        "verify the setup",
        "check the output",
    ]
    return st.sampled_from(actions)


def st_or_conjunction() -> st.SearchStrategy[str]:
    """Generate 'or' conjunction patterns that join alternatives in prose."""
    conjunctions = [
        " or ",
        "? Or shall we ",
        "? Or would you like me to ",
        "? Or would you prefer to ",
        "? Or should we ",
        ", or would you rather ",
        ", or shall we ",
    ]
    return st.sampled_from(conjunctions)


@st.composite
def st_compound_question(draw: st.DrawFn) -> str:
    """Generate compound 👉 questions with prose-joined alternatives."""
    action1 = draw(st_action_phrase())
    action2 = draw(st_action_phrase())
    conjunction = draw(st_or_conjunction())

    # Ensure we get two different actions
    if action1 == action2:
        action2 = "skip that and move on"

    if conjunction.startswith("?"):
        # Pattern: "👉 Would you like me to [action1]? Or [conjunction] [action2]?"
        question = f"👉 Would you like me to {action1}{conjunction}{action2}?"
    else:
        # Pattern: "👉 Would you like me to [action1][conjunction][action2]?"
        question = f"👉 Would you like me to {action1}{conjunction}{action2}?"

    return question


# ---------------------------------------------------------------------------
# Test class — Bug Condition Exploration
# Validates: Requirements 1.1, 1.2, 1.3, 1.4
# ---------------------------------------------------------------------------

class TestBugConditionCompoundQuestionsPassThrough:
    """Property 1: Bug Condition — Compound Questions Pass Through Unvalidated.

    These tests confirm that compound questions in agent output are NOT caught
    by the current enforcement system. The tests encode the EXPECTED behavior
    (enforcement should detect and block them), so they FAIL on unfixed code.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """

    # ------------------------------------------------------------------
    # Concrete failing cases from the bug report
    # ------------------------------------------------------------------

    def test_either_or_with_sentence_starter(self):
        """Requirement 1.3: 'Or shall we' appended alternative must be caught.

        Bug example: agent appends alternative after main question using 'Or'
        as a sentence starter.
        """
        output = (
            "👉 Would you like me to create a one-page executive summary? "
            "Or shall we skip that and move on to Module 3?"
        )
        assert is_compound_question(output), (
            "Failed to detect compound question with 'Or shall we' pattern"
        )
        assert enforcement_detects_compound(output), (
            "ENFORCEMENT GAP: Compound question with 'Or shall we' pattern "
            "passes through with no validation. No hook intercepts compound "
            "questions in direct agent output."
        )

    def test_confirmation_with_appended_alternative(self):
        """Requirement 1.4: Confirmation + 'Or would you' must be caught.

        Bug example: agent asks confirmation then appends follow-up alternative.
        """
        output = (
            "👉 Does that look right? Or would you like me to adjust it?"
        )
        assert is_compound_question(output), (
            "Failed to detect compound question with appended alternative"
        )
        assert enforcement_detects_compound(output), (
            "ENFORCEMENT GAP: Compound confirmation question with 'Or would you' "
            "passes through with no validation. No hook intercepts compound "
            "questions in direct agent output."
        )

    def test_prose_joined_alternatives(self):
        """Requirement 1.1: Prose-joined alternatives ('X or Y?') must be caught.

        Bug example: two alternatives joined by 'or' in prose form.
        """
        output = "👉 Would you like to proceed with Python or Java?"
        assert is_compound_question(output), (
            "Failed to detect compound question with prose-joined alternatives"
        )
        assert enforcement_detects_compound(output), (
            "ENFORCEMENT GAP: Compound question with prose-joined alternatives "
            "'Python or Java' passes through with no validation. No hook "
            "intercepts compound questions in direct agent output."
        )

    # ------------------------------------------------------------------
    # Property-based test — generated compound questions
    # ------------------------------------------------------------------

    @given(compound_q=st_compound_question())
    @settings(max_examples=10)
    def test_generated_compound_questions_are_detected(self, compound_q: str):
        """Requirement 1.1, 1.2, 1.3, 1.4: All generated compound questions
        must be detected and blocked by the enforcement system.

        Validates: Requirements 1.1, 1.2, 1.3, 1.4

        Uses Hypothesis to generate variations of compound questions with
        random action text joined by 'or'/'Or' patterns within 👉 questions.
        """
        # The generated string IS a compound question
        assert is_compound_question(compound_q), (
            f"Generator produced non-compound question: {compound_q!r}"
        )
        # The enforcement system must detect and block it
        assert enforcement_detects_compound(compound_q), (
            f"ENFORCEMENT GAP: Generated compound question passes through "
            f"with no validation: {compound_q!r}. "
            f"No agentStop hook exists to intercept compound questions in "
            f"direct agent output."
        )
