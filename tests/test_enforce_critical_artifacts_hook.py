"""Schema and prompt-logic verification for the enforce-critical-artifacts hook.

Validates that the new ``agentStop`` enforcement hook is a well-formed Kiro hook
and that its prompt implements the required gate logic:

1. Valid JSON schema — ``name``, ``version``, ``when``, ``then`` present.
2. ``when.type == "agentStop"`` (the enforcement trigger).
3. ``then.type == "askAgent"`` (the blocking-message action).
4. The ``config/.question_pending`` deferral clause (defer to ``ask-bootcamper``).
5. The stopping-point gate (Core Module 7 / Advanced Module 11 in
   ``modules_completed``, or graduation complete).
6. The mandatory-gate blocking marker naming each missing artifact.

**Validates: Requirements 2.1, 2.3, 2.6, 2.7, 6.4**
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    HOOKS_DIR,
    load_hook,
    required_fields_for_action,
    validate_event_type,
    validate_version,
)

HOOK_ID = "enforce-critical-artifacts"
HOOK_FILE = HOOKS_DIR / f"{HOOK_ID}.kiro.hook"


@pytest.fixture(scope="module")
def hook_data() -> dict:
    """Load and parse the enforce-critical-artifacts hook JSON."""
    assert HOOK_FILE.exists(), f"Hook file not found: {HOOK_FILE}"
    return load_hook(HOOK_FILE)


@pytest.fixture(scope="module")
def prompt(hook_data: dict) -> str:
    """Return the then.prompt text from the hook."""
    return hook_data["then"]["prompt"]


class TestEnforceCriticalArtifactsSchema:
    """Verify the hook is a well-formed Kiro hook JSON file.

    **Validates: Requirements 2.6, 6.4**
    """

    def test_hook_file_exists(self) -> None:
        """The hook file exists on disk."""
        assert HOOK_FILE.exists(), f"Hook file not found at {HOOK_FILE}"

    def test_required_fields_present(self, hook_data: dict) -> None:
        """name, version, when.type, then.type, then.prompt are all present."""
        missing = required_fields_for_action(hook_data)
        assert not missing, f"Hook missing required fields: {missing}"

    def test_top_level_schema_fields(self, hook_data: dict) -> None:
        """The hook contains the four Kiro schema fields name/version/when/then."""
        for field in ("name", "version", "when", "then"):
            assert field in hook_data, f"Hook missing top-level field '{field}'"

    def test_version_is_valid_semver(self, hook_data: dict) -> None:
        """The version is a valid semver string."""
        assert validate_version(hook_data["version"]), (
            f'Invalid semver version: "{hook_data["version"]}"'
        )

    def test_when_type_is_agent_stop(self, hook_data: dict) -> None:
        """when.type is the agentStop enforcement trigger (Req 2.9)."""
        when_type = hook_data["when"]["type"]
        assert validate_event_type(when_type), f"Invalid event type: {when_type}"
        assert when_type == "agentStop", (
            f'Expected when.type == "agentStop", got "{when_type}"'
        )

    def test_then_type_is_ask_agent(self, hook_data: dict) -> None:
        """then.type is askAgent (the blocking-message action)."""
        assert hook_data["then"]["type"] == "askAgent", (
            f'Expected then.type == "askAgent", got "{hook_data["then"]["type"]}"'
        )


class TestEnforceCriticalArtifactsPromptLogic:
    """Verify the prompt implements the required gate logic.

    **Validates: Requirements 2.1, 2.3, 2.7**
    """

    def test_defers_on_question_pending(self, prompt: str) -> None:
        """The prompt defers entirely when config/.question_pending exists."""
        assert "config/.question_pending" in prompt, (
            "Prompt does not reference the config/.question_pending deferral file"
        )
        prompt_lower = prompt.lower()
        assert "produce no output" in prompt_lower or "do nothing" in prompt_lower, (
            "Prompt does not instruct to produce no output on the deferral path"
        )
        assert "ask-bootcamper" in prompt_lower, (
            "Prompt does not defer to ask-bootcamper on the .question_pending path"
        )

    def test_stopping_point_gate_reads_progress(self, prompt: str) -> None:
        """The stopping-point check reads bootcamp_progress.json / modules_completed."""
        assert "bootcamp_progress.json" in prompt, (
            "Prompt does not read config/bootcamp_progress.json for the gate"
        )
        assert "modules_completed" in prompt, (
            "Prompt does not reference the modules_completed array"
        )

    def test_stopping_point_gate_covers_track_ends(self, prompt: str) -> None:
        """The gate detects Core (Module 7) and Advanced (Module 11) track ends."""
        assert "7" in prompt, "Prompt does not reference Core track end (Module 7)"
        assert "11" in prompt, (
            "Prompt does not reference Advanced track end (Module 11)"
        )
        assert "graduation" in prompt.lower(), (
            "Prompt does not reference graduation as a stopping point"
        )

    def test_no_output_when_not_stopping_point(self, prompt: str) -> None:
        """The prompt produces no output when it is not a stopping point."""
        prompt_lower = prompt.lower()
        assert "not a stopping point" in prompt_lower or "none of these" in prompt_lower, (
            "Prompt does not describe the non-stopping-point (no-op) branch"
        )

    def test_runs_ensure_orchestrator(self, prompt: str) -> None:
        """The prompt runs ensure_graduation_artifacts.py --json to verify."""
        assert "ensure_graduation_artifacts.py" in prompt, (
            "Prompt does not invoke ensure_graduation_artifacts.py"
        )
        assert "--json" in prompt, (
            "Prompt does not request the --json machine-readable report"
        )
        assert "all_satisfied" in prompt, (
            "Prompt does not consult the all_satisfied report field"
        )

    def test_silent_when_satisfied(self, prompt: str) -> None:
        """The prompt is silent (no output) when all_satisfied is true (Req 2.6)."""
        prompt_lower = prompt.lower()
        # There must be a satisfied branch that produces no output.
        assert "true" in prompt_lower, (
            "Prompt does not describe the all_satisfied == true branch"
        )
        assert "produce no output" in prompt_lower or "do nothing" in prompt_lower, (
            "Prompt does not go silent when the invariant already holds"
        )

    def test_blocks_with_mandatory_gate_marker(self, prompt: str) -> None:
        """On failure the prompt blocks with the mandatory-gate marker (Req 2.3)."""
        assert "MANDATORY GATE VIOLATION" in prompt, (
            "Prompt does not contain the 'MANDATORY GATE VIOLATION' blocking marker"
        )
        assert "⛔" in prompt, "Prompt does not contain the ⛔ violation marker"
        prompt_lower = prompt.lower()
        assert "done" in prompt_lower, (
            "Prompt does not reference blocking the 'done' state"
        )

    def test_blocking_message_names_missing_artifacts(self, prompt: str) -> None:
        """The blocking message names each missing artifact by identity + path."""
        # It must consult the report's `missing` array and name the artifacts.
        assert "missing" in prompt, (
            "Prompt does not reference the report's `missing` array"
        )
        for key in ("transcript", "recap_md", "rendered_recap"):
            assert key in prompt, (
                f"Prompt does not name the '{key}' guaranteed artifact"
            )
        for path in (
            "docs/bootcamp_transcript.md",
            "docs/bootcamp_recap.md",
        ):
            assert path in prompt, (
                f"Prompt does not name the artifact path '{path}'"
            )
        # The rendered recap must be named as PDF or HTML fallback (Req 2.7).
        assert "docs/bootcamp_recap.pdf" in prompt, (
            "Prompt does not name the rendered-recap PDF path"
        )
        assert "docs/bootcamp_recap.html" in prompt, (
            "Prompt does not name the rendered-recap HTML fallback path"
        )
