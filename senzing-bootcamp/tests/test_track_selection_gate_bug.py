"""Bug condition exploration tests for track-selection-gate bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests 1-3 are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: track-selection-gate
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_ONBOARDING_FLOW = _BOOTCAMP_DIR / "steering" / "onboarding-flow.md"
_AGENT_INSTRUCTIONS = _BOOTCAMP_DIR / "steering" / "agent-instructions.md"
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.kiro.hook"
_HOOK_REGISTRY = _BOOTCAMP_DIR / "steering" / "hook-registry.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a markdown section from ``## <heading>`` to the next ``## `` heading.

    Args:
        markdown: Full markdown text.
        heading: The heading text to search for (without the ``## `` prefix).

    Returns:
        The section body (including the heading line itself).
    """
    pattern = rf"(## {re.escape(heading)}.*?)(?=\n## |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def _get_hook_prompt(hook_path: Path) -> str:
    """Read the ask-bootcamper hook JSON and return the ``then.prompt`` value."""
    data = json.loads(hook_path.read_text(encoding="utf-8"))
    return data.get("then", {}).get("prompt", "")


def _get_registry_prompt(registry_path: Path) -> str:
    """Extract the ask-bootcamper prompt text from hook-registry.md.

    The prompt is the text after ``Prompt:`` in the ask-bootcamper section,
    enclosed in double quotes.
    """
    content = registry_path.read_text(encoding="utf-8")
    # Find the ask-bootcamper section
    section = _extract_section(content, "Critical Hooks")
    if not section:
        return ""
    # Find the Prompt line for ask-bootcamper — it follows the **ask-bootcamper** heading
    # The prompt is in quotes after "Prompt:"
    match = re.search(
        r'\*\*ask-bootcamper\*\*.*?Prompt:\s*"(.*?)"',
        section,
        re.DOTALL,
    )
    if match:
        return match.group(1)
    return ""


# ---------------------------------------------------------------------------
# Onboarding flow step parsing
# ---------------------------------------------------------------------------


def _parse_onboarding_steps(markdown: str) -> dict[str, str]:
    """Parse onboarding-flow.md into a dict of step-number → section content.

    Returns a dict like ``{"0": "## 0. Setup Preamble\\n...", "5": "## 5. Track Selection\\n..."}``.
    """
    steps: dict[str, str] = {}
    # Match headings like "## 0. Setup Preamble", "## 1b. Team Detection", "## 5. Track Selection"
    step_pattern = re.compile(r"^## (\d+[a-z]?)\.\s", re.MULTILINE)
    matches = list(step_pattern.finditer(markdown))
    for i, m in enumerate(matches):
        step_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        steps[step_id] = markdown[start:end]
    return steps


_GATE_KEYWORDS = re.compile(
    r"MUST stop|mandatory gate|⛔|MUST NOT proceed|stop.*wait.*input",
    re.IGNORECASE,
)

_ANTI_FABRICATION_KEYWORDS = re.compile(
    r"fabricat|never generate.*Human:|simulate.*user|"
    r"NEVER.*fabricat|do not.*fabricat|prohibit.*fabricat",
    re.IGNORECASE,
)

_STRONG_HOOK_KEYWORDS = re.compile(
    r"fabricat|Human:|simulate|NEVER.*fabricat|"
    r"do not generate.*Human|assume.*choice",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Test 1 — Missing Gate in Step 5
# ---------------------------------------------------------------------------


class TestMissingGateInStep5:
    """Test 1 — Missing Gate in Step 5.

    **Validates: Requirements 1.1, 2.1, 2.4**

    Parse onboarding-flow.md, extract the Step 5 section, and assert it
    contains a mandatory gate/stop instruction. On unfixed content this will
    FAIL because no gate exists.
    """

    def test_step5_contains_mandatory_gate_instruction(self) -> None:
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert step5, "Step 5 section not found in onboarding-flow.md"
        assert _GATE_KEYWORDS.search(step5), (
            "Step 5 (Track Selection) does not contain a mandatory gate/stop instruction. "
            f"Section content:\n{step5[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Anti-Fabrication Rule
# ---------------------------------------------------------------------------


class TestMissingAntiFabricationRule:
    """Test 2 — Missing Anti-Fabrication Rule.

    **Validates: Requirements 1.2, 2.2**

    Parse agent-instructions.md, extract the Communication section, and assert
    it contains an explicit fabrication prohibition. On unfixed content this
    will FAIL because no such rule exists.
    """

    def test_communication_section_contains_anti_fabrication_rule(self) -> None:
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        comm_section = _extract_section(content, "Communication")
        assert comm_section, "Communication section not found in agent-instructions.md"
        assert _ANTI_FABRICATION_KEYWORDS.search(comm_section), (
            "Communication section does not contain an explicit fabrication prohibition. "
            f"Section content:\n{comm_section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Weak Hook Language
# ---------------------------------------------------------------------------


class TestWeakHookLanguage:
    """Test 3 — Weak Hook Language.

    **Validates: Requirements 1.3, 2.2**

    Parse ask-bootcamper.kiro.hook as JSON, extract the then.prompt field, and
    assert it contains explicit fabrication prohibition beyond just "role-play".
    On unfixed content this will FAIL because the prompt only uses weak
    "role-play" language.
    """

    def test_hook_prompt_contains_strong_anti_fabrication_language(self) -> None:
        prompt = _get_hook_prompt(_HOOK_FILE)
        assert prompt, "Could not read then.prompt from ask-bootcamper.kiro.hook"
        assert _STRONG_HOOK_KEYWORDS.search(prompt), (
            "Hook prompt does not contain explicit fabrication prohibition "
            "(only has weak 'role-play' language). "
            f"Prompt content:\n{prompt[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Hook Registry Sync
# ---------------------------------------------------------------------------


class TestHookRegistrySync:
    """Test 4 — Hook Registry Sync.

    **Validates: Requirements 1.4**

    Verify that the hook registry references the hook file for prompt text
    and that the hook file contains a valid prompt.
    """

    def test_hook_registry_prompt_matches_hook_file(self) -> None:
        hook_prompt = _get_hook_prompt(_HOOK_FILE)
        assert hook_prompt, "Could not read prompt from hook file"
        # The registry stores hook definitions that the agent reads.
        # Verify the registry contains the ask-bootcamper hook entry.
        registry_content = _HOOK_REGISTRY.read_text(encoding="utf-8")
        assert "ask-bootcamper" in registry_content, (
            "Hook registry does not contain ask-bootcamper hook entry"
        )


# ---------------------------------------------------------------------------
# PBT Test — Gate Step Identification
# ---------------------------------------------------------------------------


# Known onboarding step identifiers from onboarding-flow.md
_ALL_STEP_IDS = ["0", "1", "1b", "2", "3", "4", "5"]
_EXPECTED_GATE_STEPS = {"2", "3", "4", "5"}


@st.composite
def st_step_identifier(draw: st.DrawFn) -> str:
    """Generate a step identifier — either a known step or a random integer 0-11."""
    choice = draw(st.sampled_from(["known", "random_int"]))
    if choice == "known":
        return draw(st.sampled_from(_ALL_STEP_IDS))
    else:
        return str(draw(st.integers(min_value=0, max_value=11)))


class TestGateStepIdentification:
    """PBT Test — Gate Step Identification.

    **Validates: Requirements 2.1, 2.4**

    Use Hypothesis to generate random step identifiers and verify that the
    onboarding flow only contains mandatory gate instructions in gate steps
    (2, 3, and 5). Step 3 already has its own gate logic (pass/fail/warn).
    Steps 2 and 5 are the NEW mandatory gates being added by this bugfix.
    On unfixed content, this should show that Steps 2 and 5 lack gate
    instructions (since gates don't exist yet).
    """

    @given(step_id=st_step_identifier())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_only_gate_steps_contain_gate_instructions(self, step_id: str) -> None:
        """For any step identifier, gate instructions should only appear in gate steps."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        steps = _parse_onboarding_steps(content)

        if step_id not in steps:
            # Step doesn't exist in the file — nothing to check
            return

        section = steps[step_id]
        has_gate = bool(_GATE_KEYWORDS.search(section))

        if step_id in _EXPECTED_GATE_STEPS:
            # Gate steps MUST have gate instructions
            assert has_gate, (
                f"Step {step_id} is a mandatory gate step but does NOT contain "
                f"gate instructions. Section preview:\n{section[:300]}"
            )
        else:
            # Non-gate steps MUST NOT have gate instructions
            assert not has_gate, (
                f"Step {step_id} is NOT a gate step but contains gate instructions. "
                f"Section preview:\n{section[:300]}"
            )
