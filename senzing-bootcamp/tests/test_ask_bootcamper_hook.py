"""Property-based and example-based tests for the ask-bootcamper hook.

Validates the renamed hook's metadata, prompt content, registry sync,
steering rules, and removal of the old summarize-on-stop artefacts.

Correctness Properties (from design.md):
  1. Hook Prompt Contains Recap Instructions (PBT)
  2. Hook Prompt Contains 👉 Question Instructions (PBT)
  3. Hook Metadata Stability (Example)
  4. Registry-Hook Prompt Synchronization (Example)
  5. No-Op Turn Skip Instructions (Example)
  6. Steering File Contains Closing Question Rule (Example)
  7. Old Hook Removed (Example)
"""

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers — locate and parse source-of-truth files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

HOOK_FILE = _REPO_ROOT / "hooks" / "ask-bootcamper.kiro.hook"
REGISTRY_FILE = _REPO_ROOT / "steering" / "hook-registry.md"
STEERING_FILE = _REPO_ROOT / "steering" / "agent-instructions.md"
OLD_HOOK_FILE = _REPO_ROOT / "hooks" / "summarize-on-stop.kiro.hook"


def _read_hook_json() -> dict:
    """Return the full parsed JSON from the hook file."""
    return json.loads(HOOK_FILE.read_text(encoding="utf-8"))


def _read_hook_prompt() -> str:
    """Return the ``then.prompt`` value from the hook JSON file."""
    return _read_hook_json()["then"]["prompt"]


def _read_registry_prompt() -> str:
    """Extract the Prompt field for ``ask-bootcamper`` from hook-registry.md."""
    text = REGISTRY_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"\*\*ask-bootcamper\*\*.*?\nPrompt:\s*\"(.*?)\"",
        text,
        re.DOTALL,
    )
    assert match, "Could not find ask-bootcamper Prompt in hook-registry.md"
    return match.group(1)


# ---------------------------------------------------------------------------
# Strategies — generate inputs for property-based tests
# ---------------------------------------------------------------------------

# Random agent output strings (for Property 1)
_AGENT_OUTPUT_ALPHABET = st.characters(
    whitelist_categories=("L", "N", "P", "Z"),
)

agent_output_st = st.text(
    alphabet=_AGENT_OUTPUT_ALPHABET,
    min_size=1,
    max_size=200,
)

# Random strings prefixed with 👉 (for Property 2)
pointing_question_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=80,
).map(lambda s: f"👉 {s.strip() or 'question'}?")

# Random strings containing a WAIT pattern (for Property 2)
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
# Property 1: Hook Prompt Contains Recap Instructions (PBT)
# Validates: Requirements 2.1, 2.2
# ---------------------------------------------------------------------------


class TestRecapInstructions:
    """Property 1 — For any agent output, the prompt must contain recap keywords.

    **Validates: Requirements 2.1, 2.2**
    """

    @given(agent_output=agent_output_st)
    @settings(max_examples=50)
    def test_prompt_contains_accomplish_keyword(self, agent_output: str):
        """The hook prompt must mention what was accomplished.

        **Validates: Requirements 2.1**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_accomplish = any(
            term in prompt_lower
            for term in ["accomplish", "what you accomplished", "what was done"]
        )
        assert has_accomplish, (
            f"Prompt missing 'accomplish' recap keyword.\n"
            f"Agent output: {agent_output!r}\n"
            f"Prompt: {prompt!r}"
        )

    @given(agent_output=agent_output_st)
    @settings(max_examples=50)
    def test_prompt_contains_files_keyword(self, agent_output: str):
        """The hook prompt must mention files created or modified.

        **Validates: Requirements 2.2**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_files = any(
            term in prompt_lower
            for term in ["files", "file paths", "created or modified"]
        )
        assert has_files, (
            f"Prompt missing 'files' recap keyword.\n"
            f"Agent output: {agent_output!r}\n"
            f"Prompt: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 2: Hook Prompt Contains 👉 Question Instructions (PBT)
# Validates: Requirements 3.1, 3.4, 7.7
# ---------------------------------------------------------------------------


class TestPointingQuestionInstructions:
    """Property 2 — Prompt must handle 👉 questions and duplicate detection.

    **Validates: Requirements 3.1, 3.4, 7.7**
    """

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_prompt_mentions_pointing_emoji(self, marker: str):
        """The hook prompt must contain the 👉 character.

        **Validates: Requirements 3.1**
        """
        prompt = _read_hook_prompt()
        assert "👉" in prompt, (
            f"Prompt does not contain 👉 emoji.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt: {prompt!r}"
        )

    @given(marker=question_marker_st)
    @settings(max_examples=50)
    def test_prompt_contains_duplicate_detection(self, marker: str):
        """The prompt must instruct not to duplicate an existing 👉 question.

        **Validates: Requirements 3.4, 7.7**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_duplicate_detection = any(
            term in prompt_lower
            for term in [
                "already ends with",
                "do nothing",
                "already ended with",
                "don't add a second",
                "do not add",
                "already present",
            ]
        )
        assert has_duplicate_detection, (
            f"Prompt lacks duplicate 👉 question detection instructions.\n"
            f"Generated marker: {marker!r}\n"
            f"Prompt: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Hook Metadata Stability (Example-based)
# Validates: Requirements 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------


class TestHookMetadata:
    """Property 3 — Hook file must be valid JSON with correct metadata.

    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    def test_hook_file_is_valid_json_with_required_keys(self):
        """Hook file must be valid JSON with keys: name, version, description, when, then.

        **Validates: Requirements 5.3**
        """
        data = _read_hook_json()
        required_keys = {"name", "version", "description", "when", "then"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Hook JSON missing required keys: {missing}"

    def test_hook_event_type_is_agent_stop(self):
        """when.type must be 'agentStop'.

        **Validates: Requirements 5.1**
        """
        data = _read_hook_json()
        assert data["when"]["type"] == "agentStop", (
            f"Expected when.type='agentStop', got {data['when']['type']!r}"
        )

    def test_hook_action_type_is_ask_agent(self):
        """then.type must be 'askAgent'.

        **Validates: Requirements 5.2**
        """
        data = _read_hook_json()
        assert data["then"]["type"] == "askAgent", (
            f"Expected then.type='askAgent', got {data['then']['type']!r}"
        )

    def test_hook_name_is_ask_bootcamper(self):
        """name must be 'Ask Bootcamper'.

        **Validates: Requirements 5.3**
        """
        data = _read_hook_json()
        assert data["name"] == "Ask Bootcamper", (
            f"Expected name='Ask Bootcamper', got {data['name']!r}"
        )


# ---------------------------------------------------------------------------
# Property 4: Registry-Hook Prompt Synchronization (Example-based)
# Validates: Requirement 6.1
# ---------------------------------------------------------------------------


class TestRegistrySync:
    """Property 4 — Hook file prompt must exactly match registry prompt.

    **Validates: Requirement 6.1**
    """

    def test_registry_prompt_matches_hook_prompt(self):
        """Prompt from hook file must exactly match registry entry.

        **Validates: Requirement 6.1**
        """
        hook_prompt = _read_hook_prompt()
        registry_prompt = _read_registry_prompt()
        assert hook_prompt == registry_prompt, (
            f"Prompt mismatch between hook file and registry.\n"
            f"Hook file prompt:  {hook_prompt!r}\n"
            f"Registry prompt:   {registry_prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: No-Op Turn Skip Instructions (Example-based)
# Validates: Requirement 2.3
# ---------------------------------------------------------------------------


class TestNoOpSkip:
    """Property 5 — Prompt must instruct skipping recap on no-op turns.

    **Validates: Requirement 2.3**
    """

    def test_prompt_contains_noop_skip_instructions(self):
        """Hook prompt must contain instructions for skipping recap on no-op turns.

        **Validates: Requirement 2.3**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_skip = any(
            term in prompt_lower
            for term in [
                "skip the recap",
                "no files changed",
                "no substantive",
                "skip recap",
            ]
        )
        assert has_skip, (
            f"Prompt lacks no-op turn skip instructions.\n"
            f"Prompt: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 6: Steering File Contains Closing Question Rule (Example-based)
# Validates: Requirements 4.1, 4.2, 4.3
# ---------------------------------------------------------------------------


class TestSteeringClosingQuestionRule:
    """Property 6 — Agent instructions must contain closing-question ownership rule.

    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    def test_steering_references_ask_bootcamper_hook(self):
        """Steering file must reference the ask-bootcamper hook.

        **Validates: Requirement 4.3**
        """
        text = STEERING_FILE.read_text(encoding="utf-8")
        assert "ask-bootcamper" in text, (
            "Steering file does not reference 'ask-bootcamper' hook."
        )

    def test_steering_contains_closing_question_ownership(self):
        """Steering file must state the hook owns closing questions.

        **Validates: Requirements 4.1, 4.2**
        """
        text = STEERING_FILE.read_text(encoding="utf-8").lower()
        has_ownership = any(
            term in text
            for term in [
                "closing question",
                "closing-question",
                "owns all closing",
            ]
        )
        assert has_ownership, (
            "Steering file lacks closing-question ownership rule."
        )


# ---------------------------------------------------------------------------
# Property 7: Old Hook Removed (Example-based)
# Validates: Requirements 1.1, 1.5
# ---------------------------------------------------------------------------


class TestOldHookRemoved:
    """Property 7 — Old summarize-on-stop artefacts must not exist.

    **Validates: Requirements 1.1, 1.5**
    """

    def test_old_hook_file_does_not_exist(self):
        """summarize-on-stop.kiro.hook must not exist.

        **Validates: Requirement 1.1**
        """
        assert not OLD_HOOK_FILE.exists(), (
            f"Old hook file still exists: {OLD_HOOK_FILE}"
        )

    def test_registry_does_not_contain_old_entry(self):
        """Hook registry must not contain a summarize-on-stop entry.

        **Validates: Requirement 1.5**
        """
        text = REGISTRY_FILE.read_text(encoding="utf-8")
        match = re.search(r"\*\*summarize-on-stop\*\*", text)
        assert match is None, (
            "Hook registry still contains a 'summarize-on-stop' entry."
        )
