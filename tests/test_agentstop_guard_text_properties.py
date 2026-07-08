"""Property-based tests for agentStop hook question-pending silence guards.

Validates that every hook whose ``when.type`` is ``agentStop`` carries guard text
that yields zero output while a question is pending: a reference to
``config/.question_pending`` paired with a no-output / defer-to-``ask-bootcamper``
clause.

The guard-clause hooks (`module-recap-append`,
`module-completion-celebration`, `enforce-gate-on-stop`,
`enforce-visualization-offers`, and `enforce-critical-artifacts`) open with the
leading clause "If ``config/.question_pending`` exists, produce no output at
all — defer to ``ask-bootcamper``." The `ask-bootcamper` hook owns the
closing question and expresses the same silence semantic with its own
phrasing (it checks that ``config/.question_pending`` does NOT exist and that
phases "produce no output" / are "none"). The assertions below are written to
hold for ALL of the real agentStop hook prompts.

**Validates: Requirements 2.4**
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Feature: hook-architecture-improvements, Property 2

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Resolve the hooks directory relative to this test file so the test does not
# depend on the process working directory.
HOOKS_DIR: Path = Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "hooks"

# The exact path token every agentStop guard must reference.
QUESTION_PENDING_REF: str = "config/.question_pending"

# The six agentStop hook ids (grounded fact from requirements/design).
# enforce-critical-artifacts was added by the guaranteed-graduation-artifacts
# spec; it opens with the same "produce no output at all — defer to
# ask-bootcamper" guard clause as the other enforcement hooks.
EXPECTED_AGENTSTOP_IDS: set[str] = {
    "ask-bootcamper",
    "module-recap-append",
    "module-completion-celebration",
    "enforce-gate-on-stop",
    "enforce-visualization-offers",
    "enforce-critical-artifacts",
}

# Silence / no-output / defer indicators (matched case-insensitively).
#
# The four guard-clause hooks use "produce no output at all — defer to
# ask-bootcamper". `ask-bootcamper` uses its own pending-handling phrasing:
# it instructs that phases "produce no output", that output "is none", and
# that the closing question only fires when `config/.question_pending` "does
# NOT exist". Any one of these satisfies the zero-output-while-pending
# semantic required by Requirement 2.4.
SILENCE_INDICATORS: tuple[str, ...] = (
    "no output",
    "produce no output",
    "zero output",
    "defer to",
    "output is none",
    "does not exist",
)


# ---------------------------------------------------------------------------
# Hook discovery helpers
# ---------------------------------------------------------------------------


def _load_hook(path: Path) -> dict:
    """Load and parse the single v1 hook entry (``hooks[0]``) from a hook file."""
    return json.loads(path.read_text(encoding="utf-8"))["hooks"][0]


def discover_agentstop_hook_files() -> list[Path]:
    """Return the ``.json`` files whose 1.0 ``trigger`` is ``Stop``.

    Returns:
        Sorted list of paths to the real Stop-trigger hook files.
    """
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    matches: list[Path] = []
    for path in sorted(HOOKS_DIR.glob("*.json")):
        entry = _load_hook(path)
        if entry.get("trigger") == "Stop":
            matches.append(path)
    return matches


def load_prompt(path: Path) -> str:
    """Return the ``action.prompt`` string for a v1 hook file."""
    return _load_hook(path)["action"]["prompt"]


# The five real agentStop hook files, discovered once at import time.
AGENTSTOP_HOOK_FILES: list[Path] = discover_agentstop_hook_files()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_agentstop_hook_files() -> st.SearchStrategy[Path]:
    """Strategy sampling over the real agentStop hook files."""
    return st.sampled_from(AGENTSTOP_HOOK_FILES)


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestAgentStopGuardText:
    """Property 2: Every agentStop hook has a question-pending silence guard.

    For any hook whose ``when.type`` is ``agentStop``, its ``then.prompt``
    references ``config/.question_pending`` paired with a no-output /
    defer-to-``ask-bootcamper`` clause.

    **Validates: Requirements 2.4**
    """

    def test_discovers_exactly_the_expected_agentstop_hooks(self) -> None:
        """Sanity check: discovery finds exactly the known agentStop hooks."""
        discovered = {p.name.replace(".json", "") for p in AGENTSTOP_HOOK_FILES}
        assert discovered == EXPECTED_AGENTSTOP_IDS, (
            "agentStop hook discovery drifted from the grounded ids. "
            f"Discovered: {sorted(discovered)}"
        )

    @given(hook_file=st_agentstop_hook_files())
    @settings(max_examples=20)
    def test_prompt_references_question_pending(self, hook_file: Path) -> None:
        """Every agentStop prompt references ``config/.question_pending``.

        **Validates: Requirements 2.4**
        """
        prompt = load_prompt(hook_file)
        assert QUESTION_PENDING_REF in prompt, (
            f"agentStop hook '{hook_file.name}' does not reference "
            f"'{QUESTION_PENDING_REF}' in its then.prompt."
        )

    @given(hook_file=st_agentstop_hook_files())
    @settings(max_examples=20)
    def test_prompt_pairs_pending_with_silence_clause(self, hook_file: Path) -> None:
        """The pending reference is paired with a no-output / defer clause.

        Asserts both halves of the guard: the prompt references
        ``config/.question_pending`` AND contains a silence/no-output/defer
        indicator that yields zero output while a question is pending.

        **Validates: Requirements 2.4**
        """
        prompt = load_prompt(hook_file)
        lowered = prompt.lower()

        assert QUESTION_PENDING_REF in prompt, (
            f"agentStop hook '{hook_file.name}' does not reference "
            f"'{QUESTION_PENDING_REF}' in its then.prompt."
        )

        matched = [ind for ind in SILENCE_INDICATORS if ind in lowered]
        assert matched, (
            f"agentStop hook '{hook_file.name}' references "
            f"'{QUESTION_PENDING_REF}' but lacks any no-output/defer clause. "
            f"Expected one of: {list(SILENCE_INDICATORS)}"
        )
