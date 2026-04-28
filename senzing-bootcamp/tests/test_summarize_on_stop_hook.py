"""Property-based tests for the summarize-on-stop hook prompt.

Bug condition exploration: verifies the hook prompt contains instructions
for detecting pending questions (👉 prefix / WAIT pattern) and reordering
the summary before the question.

Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3
"""

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers — locate and parse the two source-of-truth files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

HOOK_FILE = _REPO_ROOT / "hooks" / "summarize-on-stop.kiro.hook"
REGISTRY_FILE = _REPO_ROOT / "steering" / "hook-registry.md"


def _read_hook_prompt() -> str:
    """Return the ``then.prompt`` value from the hook JSON file."""
    data = json.loads(HOOK_FILE.read_text(encoding="utf-8"))
    return data["then"]["prompt"]


def _read_registry_prompt() -> str:
    """Extract the Prompt field for ``summarize-on-stop`` from hook-registry.md."""
    text = REGISTRY_FILE.read_text(encoding="utf-8")
    # The registry uses the pattern:
    #   **summarize-on-stop** (agentStop → askAgent)
    #   Prompt: "..."
    match = re.search(
        r"\*\*summarize-on-stop\*\*.*?\nPrompt:\s*\"(.*?)\"",
        text,
        re.DOTALL,
    )
    assert match, "Could not find summarize-on-stop Prompt in hook-registry.md"
    return match.group(1)


# ---------------------------------------------------------------------------
# Strategies — generate question markers the prompt should handle
# ---------------------------------------------------------------------------

# Random strings prefixed with 👉 (the pending-question marker)
pointing_question_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=80,
).map(lambda s: f"👉 {s.strip() or 'question'}?")

# Random strings containing a WAIT pattern
wait_pattern_st = st.sampled_from([
    "WAIT for the bootcamper's response",
    "WAIT for response",
    "WAIT for the user",
    "WAIT",
]).flatmap(
    lambda prefix: st.text(min_size=0, max_size=40).map(
        lambda suffix: f"{prefix} {suffix}".strip()
    )
)

# Combined strategy: either a 👉 question or a WAIT pattern
question_marker_st = st.one_of(pointing_question_st, wait_pattern_st)


# ---------------------------------------------------------------------------
# Bug Condition Exploration Property Test
# ---------------------------------------------------------------------------


class TestBugConditionExploration:
    """Property 1: Bug Condition — Prompt Lacks Pending-Question Detection and Reordering.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3**

    These tests MUST FAIL on unfixed code — failure confirms the bug exists.
    The prompt currently has NO instructions for detecting 👉/WAIT markers
    and NO instructions for reordering summary before a pending question.
    """

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_hook_prompt_contains_pending_question_detection(self, marker: str):
        """The hook prompt must contain instructions to detect pending questions.

        **Validates: Requirements 1.1, 1.2**

        For any generated question marker (👉-prefixed or WAIT pattern),
        the prompt text should mention detection of such markers.
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        # The prompt must mention detecting the 👉 marker or WAIT pattern
        has_pointing_detection = "👉" in prompt or "pointing" in prompt_lower
        has_wait_detection = "wait" in prompt_lower and (
            "pattern" in prompt_lower
            or "detect" in prompt_lower
            or "check" in prompt_lower
            or "previous output" in prompt_lower
        )
        has_pending_question = "pending question" in prompt_lower

        assert has_pointing_detection or has_wait_detection or has_pending_question, (
            f"Hook prompt lacks pending-question detection instructions.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The prompt contains no mention of 👉, WAIT detection, or 'pending question'."
        )

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_hook_prompt_contains_reordering_logic(self, marker: str):
        """The hook prompt must contain conditional handling for pending questions.

        **Validates: Requirements 2.1, 2.2, 2.3**

        When a pending question is detected, the prompt should instruct
        the agent to handle it correctly — either by reordering (summary
        before question) or by appending only the summary without repeating
        the question.
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        # The prompt must mention reordering / placing summary before question
        has_reorder = any(
            term in prompt_lower
            for term in ["reorder", "before the question", "summary first",
                         "summary before", "re-state", "restate"]
        )
        has_final_element = any(
            term in prompt_lower
            for term in ["final element", "last element", "last thing",
                         "end of the response", "very last"]
        )
        # The fix replaces reordering with "do not repeat" — the question
        # is already visible, so the prompt appends only the summary.
        has_no_repeat = any(
            term in prompt_lower
            for term in ["do not repeat the question", "don't repeat the question",
                         "already visible", "without re-stating",
                         "without restating", "append only the summary"]
        )

        assert has_reorder or has_final_element or has_no_repeat, (
            f"Hook prompt lacks pending-question handling instructions.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The prompt contains no mention of reordering, 'summary before question', "
            f"'re-state', 'do not repeat the question', or 'already visible'."
        )

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_hook_prompt_does_not_restate_question(self, marker: str):
        """The hook prompt must NOT contain instructions to re-state the pending question.

        **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

        For any generated question marker (👉-prefixed or WAIT pattern),
        the prompt text should NOT instruct the agent to re-state or restate
        the pending question — the question is already visible in the output.
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        assert "re-state the pending question" not in prompt_lower, (
            f"Hook prompt contains 're-state the pending question' instruction.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The prompt should NOT instruct re-stating the pending question — "
            f"it is already visible in the agent's output."
        )
        assert "restate the pending question" not in prompt_lower, (
            f"Hook prompt contains 'restate the pending question' instruction.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The prompt should NOT instruct restating the pending question — "
            f"it is already visible in the agent's output."
        )

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_registry_prompt_does_not_restate_question(self, marker: str):
        """The registry prompt must NOT contain instructions to re-state the pending question.

        **Validates: Requirements 2.2**

        Both the hook file and the registry must be in sync and neither should
        contain the re-statement instruction for pending questions.
        """
        prompt = _read_registry_prompt()
        prompt_lower = prompt.lower()

        assert "re-state the pending question" not in prompt_lower, (
            f"Registry prompt contains 're-state the pending question' instruction.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The registry prompt should NOT instruct re-stating the pending question — "
            f"it is already visible in the agent's output."
        )
        assert "restate the pending question" not in prompt_lower, (
            f"Registry prompt contains 'restate the pending question' instruction.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The registry prompt should NOT instruct restating the pending question — "
            f"it is already visible in the agent's output."
        )

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_registry_prompt_contains_pending_question_detection(self, marker: str):
        """The registry prompt must also contain detection instructions.

        **Validates: Requirements 2.2**

        Both the hook file and the registry must be in sync and both must
        contain the pending-question detection logic.
        """
        prompt = _read_registry_prompt()
        prompt_lower = prompt.lower()

        has_pointing_detection = "👉" in prompt or "pointing" in prompt_lower
        has_wait_detection = "wait" in prompt_lower and (
            "pattern" in prompt_lower
            or "detect" in prompt_lower
            or "check" in prompt_lower
            or "previous output" in prompt_lower
        )
        has_pending_question = "pending question" in prompt_lower

        assert has_pointing_detection or has_wait_detection or has_pending_question, (
            f"Registry prompt lacks pending-question detection instructions.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt text: {prompt!r}\n"
            f"The registry prompt contains no mention of 👉, WAIT detection, "
            f"or 'pending question'."
        )


# ---------------------------------------------------------------------------
# Strategies — generate agent output WITHOUT question markers
# ---------------------------------------------------------------------------

# Agent output strings that do NOT contain 👉 or WAIT — these represent
# the "no pending question" path where the summary should be appended at end.
_NO_QUESTION_ALPHABET = st.characters(
    whitelist_categories=("L", "N", "P", "Z"),
    # Exclude the 👉 character (U+1F449) to guarantee no pointing marker
    blacklist_characters="\U0001f449",
)

no_question_output_st = (
    st.text(alphabet=_NO_QUESTION_ALPHABET, min_size=1, max_size=200)
    .filter(lambda s: "👉" not in s)
    .filter(lambda s: "WAIT" not in s.upper())
)


# ---------------------------------------------------------------------------
# Preservation Property Tests
# ---------------------------------------------------------------------------


def _read_hook_json() -> dict:
    """Return the full parsed JSON from the hook file."""
    return json.loads(HOOK_FILE.read_text(encoding="utf-8"))


class TestPreservation:
    """Property 2: Preservation — No-Question Behavior and Hook Metadata Unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    These tests MUST PASS on unfixed code — they capture the baseline
    behavior that the fix must preserve.
    """

    # ------------------------------------------------------------------
    # Property-based test: no-question path preserves three-element summary
    # ------------------------------------------------------------------

    @given(agent_output=no_question_output_st)
    @settings(max_examples=50)
    def test_no_question_output_prompt_instructs_three_element_summary(
        self, agent_output: str
    ):
        """For any agent output WITHOUT 👉 or WAIT markers, the prompt
        still instructs the standard three-element summary.

        **Validates: Requirements 3.1, 3.2, 3.4**

        The prompt must mention all three summary elements regardless of
        what the agent output looks like, as long as it has no pending
        question markers.
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        # Element 1: what was accomplished
        has_accomplished = any(
            term in prompt_lower
            for term in ["accomplish", "what did you", "what was"]
        )
        # Element 2: files created or modified
        has_files = any(
            term in prompt_lower
            for term in ["files", "file paths", "created or modified"]
        )
        # Element 3: next step
        has_next_step = any(
            term in prompt_lower
            for term in ["next step", "what is the next", "expect when they continue"]
        )

        assert has_accomplished, (
            f"Prompt missing 'accomplished' element.\n"
            f"Agent output (no question): {agent_output!r}\n"
            f"Prompt: {prompt!r}"
        )
        assert has_files, (
            f"Prompt missing 'files' element.\n"
            f"Agent output (no question): {agent_output!r}\n"
            f"Prompt: {prompt!r}"
        )
        assert has_next_step, (
            f"Prompt missing 'next step' element.\n"
            f"Agent output (no question): {agent_output!r}\n"
            f"Prompt: {prompt!r}"
        )

    # ------------------------------------------------------------------
    # Example-based tests: hook metadata and structure
    # ------------------------------------------------------------------

    def test_hook_file_is_valid_json_with_required_keys(self):
        """The hook file must be valid JSON with all required keys.

        **Validates: Requirements 3.3**
        """
        data = _read_hook_json()
        required_keys = {"name", "version", "description", "when", "then"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Hook JSON missing required keys: {missing}"

    def test_hook_event_type_is_agent_stop(self):
        """The hook must fire on agentStop events.

        **Validates: Requirements 3.3**
        """
        data = _read_hook_json()
        assert data["when"]["type"] == "agentStop", (
            f"Expected when.type='agentStop', got {data['when']['type']!r}"
        )

    def test_hook_action_type_is_ask_agent(self):
        """The hook action must be askAgent.

        **Validates: Requirements 3.3**
        """
        data = _read_hook_json()
        assert data["then"]["type"] == "askAgent", (
            f"Expected then.type='askAgent', got {data['then']['type']!r}"
        )

    def test_hook_name_is_correct(self):
        """The hook name must be 'Summarize Progress on Stop'.

        **Validates: Requirements 3.3**
        """
        data = _read_hook_json()
        assert data["name"] == "Summarize Progress on Stop", (
            f"Expected name='Summarize Progress on Stop', got {data['name']!r}"
        )

    def test_prompt_mentions_all_three_summary_elements(self):
        """The prompt must mention accomplished, files, and next step.

        **Validates: Requirements 3.2, 3.4**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        assert any(
            t in prompt_lower for t in ["accomplish", "what did you", "what was"]
        ), f"Prompt missing 'accomplished' element: {prompt!r}"

        assert any(
            t in prompt_lower for t in ["files", "file paths", "created or modified"]
        ), f"Prompt missing 'files' element: {prompt!r}"

        assert any(
            t in prompt_lower for t in ["next step", "what is the next", "expect when they continue"]
        ), f"Prompt missing 'next step' element: {prompt!r}"

    def test_registry_prompt_matches_hook_prompt(self):
        """The prompt in hook-registry.md must match the hook file prompt.

        **Validates: Requirements 3.3**
        """
        hook_prompt = _read_hook_prompt()
        registry_prompt = _read_registry_prompt()
        assert hook_prompt == registry_prompt, (
            f"Prompt mismatch between hook file and registry.\n"
            f"Hook file prompt:  {hook_prompt!r}\n"
            f"Registry prompt:   {registry_prompt!r}"
        )
