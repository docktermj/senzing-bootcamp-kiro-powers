"""Preservation property tests for track-selection-gate bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: track-selection-gate
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_ONBOARDING_FLOW = _BOOTCAMP_DIR / "steering" / "onboarding-flow.md"
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.kiro.hook"
_HOOK_REGISTRY = _BOOTCAMP_DIR / "steering" / "hook-registry.md"


# ---------------------------------------------------------------------------
# Helpers (duplicated from test_track_selection_gate_bug.py for independence)
# ---------------------------------------------------------------------------


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a markdown section from ``## <heading>`` to the next heading.

    Args:
        markdown: Full markdown text.
        heading: The heading text (without the ``## `` prefix).

    Returns:
        The section body including the heading line itself.
    """
    pattern = rf"(## {re.escape(heading)}.*?)(?=\n## |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    return match.group(1) if match else ""


def _parse_onboarding_steps(markdown: str) -> dict[str, str]:
    """Parse onboarding-flow.md into a dict of step-id → section content.

    Handles both ``## N.`` and ``### Nb.`` style headings so that each
    step/sub-step gets its own section (matching ``_parse_numbered_steps``
    in ``test_comprehension_check.py``).

    Returns:
        Dict like ``{"0": "## 0. Setup …", "4b": "### 4b. Verbosity …"}``.
    """
    steps: dict[str, str] = {}
    step_pattern = re.compile(r"^(#{2,3})\s+(\d+[a-z]?)\.\s", re.MULTILINE)
    matches = list(step_pattern.finditer(markdown))
    for i, m in enumerate(matches):
        step_id = m.group(2)
        start = m.start()
        # End at the very next numbered step heading (any level)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        # Also check for non-numbered ## headings after this step
        rest = markdown[m.end():]
        non_numbered = re.search(r"^#{2}\s+(?!\d+[a-z]?\.\s)", rest, re.MULTILINE)
        if non_numbered:
            candidate = m.end() + non_numbered.start()
            if candidate < end:
                end = candidate
        steps[step_id] = markdown[start:end]
    return steps


def _get_hook_prompt(hook_path: Path) -> str:
    """Read the ask-bootcamper hook JSON and return ``then.prompt``."""
    data = json.loads(hook_path.read_text(encoding="utf-8"))
    return data.get("then", {}).get("prompt", "")


def _get_registry_prompt(registry_path: Path) -> str:
    """Extract the ask-bootcamper prompt from hook-registry.md.

    Returns:
        The prompt string found after ``Prompt:`` in the ask-bootcamper block.
    """
    content = registry_path.read_text(encoding="utf-8")
    section = _extract_section(content, "Critical Hooks")
    if not section:
        return ""
    match = re.search(
        r'\*\*ask-bootcamper\*\*.*?Prompt:\s*"(.*?)"',
        section,
        re.DOTALL,
    )
    return match.group(1) if match else ""


_GATE_KEYWORDS = re.compile(
    r"MUST stop|mandatory gate|⛔|MUST NOT proceed|stop.*wait.*input",
    re.IGNORECASE,
)

# Non-gate steps that should never contain gate instructions
_NON_GATE_STEP_IDS = ["0", "1", "1b", "4", "4c"]


# ---------------------------------------------------------------------------
# Test 1 — Steps 0, 1, 1b contain no gate/stop instructions
# ---------------------------------------------------------------------------


class TestSetupStepsNoGate:
    """Steps 0, 1, 1b contain no mandatory gate instructions.

    **Validates: Requirements 3.1**

    Setup steps execute as continuous flow. They must not contain
    mandatory gate keywords.
    """

    def test_setup_steps_have_no_gate_instructions(self) -> None:
        """Assert Steps 0, 1, and 1b contain no gate keywords."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        steps = _parse_onboarding_steps(content)

        for step_id in ("0", "1", "1b"):
            assert step_id in steps, (
                f"Step {step_id} not found in onboarding-flow.md"
            )
            section = steps[step_id]
            assert not _GATE_KEYWORDS.search(section), (
                f"Step {step_id} should NOT contain gate instructions "
                f"but found a match. Preview:\n{section[:300]}"
            )


# ---------------------------------------------------------------------------
# Test 2 — Step 4 content markers present
# ---------------------------------------------------------------------------


class TestStep4ContentMarkers:
    """Step 4 contains key introduction content markers.

    **Validates: Requirements 3.2**

    Step 4 (Bootcamp Introduction) must contain the guided discovery
    framing, module overview, mock data mention, eval license info,
    and glossary reference.
    """

    def test_step4_contains_guided_discovery(self) -> None:
        """Assert Step 4 mentions guided discovery."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step4 = _extract_section(content, "4. Bootcamp Introduction")
        assert step4, "Step 4 section not found"
        assert re.search(r"guided discovery", step4, re.IGNORECASE), (
            "Step 4 missing 'guided discovery' content marker"
        )

    def test_step4_contains_module_overview(self) -> None:
        """Assert Step 4 mentions module overview table."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step4 = _extract_section(content, "4. Bootcamp Introduction")
        assert step4, "Step 4 section not found"
        assert re.search(r"[Mm]odule overview", step4, re.IGNORECASE), (
            "Step 4 missing 'module overview' content marker"
        )

    def test_step4_contains_mock_data(self) -> None:
        """Assert Step 4 mentions mock data."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step4 = _extract_section(content, "4. Bootcamp Introduction")
        assert step4, "Step 4 section not found"
        assert re.search(r"[Mm]ock data", step4, re.IGNORECASE), (
            "Step 4 missing 'mock data' content marker"
        )

    def test_step4_contains_eval_license_info(self) -> None:
        """Assert Step 4 mentions eval license or 500-record limit."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step4 = _extract_section(content, "4. Bootcamp Introduction")
        assert step4, "Step 4 section not found"
        has_eval = re.search(r"eval license", step4, re.IGNORECASE)
        has_500 = re.search(r"500-record", step4, re.IGNORECASE)
        assert has_eval or has_500, (
            "Step 4 missing eval license / 500-record content marker"
        )

    def test_step4_contains_glossary_reference(self) -> None:
        """Assert Step 4 references the glossary."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step4 = _extract_section(content, "4. Bootcamp Introduction")
        assert step4, "Step 4 section not found"
        has_glossary = re.search(r"glossary", step4, re.IGNORECASE)
        has_file = re.search(r"GLOSSARY\.md", step4)
        assert has_glossary or has_file, (
            "Step 4 missing glossary / GLOSSARY.md content marker"
        )


# ---------------------------------------------------------------------------
# Test 3 — Track mapping logic preserved
# ---------------------------------------------------------------------------


class TestTrackMappingPreserved:
    """Step 5 contains the track-to-module mapping logic.

    **Validates: Requirements 3.4**

    The "Interpreting responses" line and the A→3, B→5, C→1, D→1
    mapping must be present in Step 5.
    """

    def test_step5_contains_interpreting_responses(self) -> None:
        """Assert Step 5 has the 'Interpreting responses' text."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert step5, "Step 5 section not found"
        assert "Interpreting responses" in step5, (
            "Step 5 missing 'Interpreting responses' text"
        )

    def test_step5_maps_a_to_module3(self) -> None:
        """Assert track A maps to Module 3."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert re.search(r'"A".*Module 3|"demo".*Module 3', step5), (
            "Step 5 missing A→Module 3 mapping"
        )

    def test_step5_maps_b_to_module5(self) -> None:
        """Assert track B maps to Module 5."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert re.search(r'"B".*Module 5|"fast".*Module 5', step5), (
            "Step 5 missing B→Module 5 mapping"
        )

    def test_step5_maps_c_to_module1(self) -> None:
        """Assert track C maps to Module 1."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert re.search(r'"C".*Module 1|"beginner".*Module 1', step5), (
            "Step 5 missing C→Module 1 mapping"
        )

    def test_step5_maps_d_to_module1(self) -> None:
        """Assert track D maps to Module 1."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        step5 = _extract_section(content, "5. Track Selection")
        assert re.search(r'"D".*Module 1|"full".*Module 1', step5), (
            "Step 5 missing D→Module 1 mapping"
        )


# ---------------------------------------------------------------------------
# Test 4 — General note preserved
# ---------------------------------------------------------------------------


class TestGeneralNotePreserved:
    """The general note about no inline closing questions is preserved.

    **Validates: Requirements 3.5**

    The top of onboarding-flow.md must contain the note about not
    including inline closing questions or WAIT instructions.
    """

    def test_general_note_present(self) -> None:
        """Assert the 'Do NOT include inline closing questions' note exists."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        assert re.search(
            r"Do NOT include inline closing questions or WAIT instructions",
            content,
        ), "General note about no inline closing questions not found"


# ---------------------------------------------------------------------------
# Test 5 — Hook recap logic preserved
# ---------------------------------------------------------------------------


class TestHookRecapLogicPreserved:
    """The ask-bootcamper hook prompt preserves recap and closing logic.

    **Validates: Requirements 3.3**

    The hook prompt must contain recap keywords and the 👉 closing
    question pattern.
    """

    def test_hook_prompt_contains_recap_keywords(self) -> None:
        """Assert the hook prompt mentions recap logic."""
        prompt = _get_hook_prompt(_HOOK_FILE)
        assert prompt, "Could not read then.prompt from hook file"
        has_recap = "recap" in prompt.lower()
        has_accomplished = "accomplished" in prompt.lower()
        has_files = re.search(
            r"files created or modified", prompt, re.IGNORECASE
        )
        assert has_recap and (has_accomplished or has_files), (
            "Hook prompt missing recap logic keywords. "
            f"Prompt preview:\n{prompt[:300]}"
        )

    def test_hook_prompt_contains_closing_question_emoji(self) -> None:
        """Assert the hook prompt contains the 👉 closing question pattern."""
        prompt = _get_hook_prompt(_HOOK_FILE)
        assert prompt, "Could not read then.prompt from hook file"
        assert "👉" in prompt, (
            "Hook prompt missing 👉 closing question pattern"
        )


# ---------------------------------------------------------------------------
# Test 6 — Hook JSON structure valid
# ---------------------------------------------------------------------------


class TestHookJsonStructure:
    """The ask-bootcamper.kiro.hook file is valid JSON with required keys.

    **Validates: Requirements 3.3**

    The hook file must parse as valid JSON and contain the keys:
    name, version, description, when.type, then.type, then.prompt.
    """

    def test_hook_file_is_valid_json(self) -> None:
        """Assert the hook file parses as valid JSON."""
        raw = _HOOK_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)  # Will raise if invalid
        assert isinstance(data, dict), "Hook file root is not a JSON object"

    def test_hook_file_has_required_top_level_keys(self) -> None:
        """Assert the hook file has name, version, description."""
        data = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
        for key in ("name", "version", "description"):
            assert key in data, f"Hook file missing required key: {key}"
            assert isinstance(data[key], str), (
                f"Hook file key '{key}' is not a string"
            )

    def test_hook_file_has_when_type(self) -> None:
        """Assert the hook file has when.type."""
        data = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
        assert "when" in data, "Hook file missing 'when' key"
        assert "type" in data["when"], "Hook file missing 'when.type'"

    def test_hook_file_has_then_type_and_prompt(self) -> None:
        """Assert the hook file has then.type and then.prompt."""
        data = json.loads(_HOOK_FILE.read_text(encoding="utf-8"))
        assert "then" in data, "Hook file missing 'then' key"
        assert "type" in data["then"], "Hook file missing 'then.type'"
        assert "prompt" in data["then"], "Hook file missing 'then.prompt'"


# ---------------------------------------------------------------------------
# Test 7 — Hook registry entry format preserved
# ---------------------------------------------------------------------------


class TestHookRegistryEntryFormat:
    """The hook-registry.md entry for ask-bootcamper has required fields.

    **Validates: Requirements 3.3**

    The registry entry must contain id, name, and description fields
    for the ask-bootcamper hook.
    """

    def test_registry_has_ask_bootcamper_id(self) -> None:
        """Assert the registry contains an id for ask-bootcamper."""
        content = _HOOK_REGISTRY.read_text(encoding="utf-8")
        section = _extract_section(content, "Critical Hooks")
        assert section, "Critical Hooks section not found"
        assert re.search(
            r"id:\s*`ask-bootcamper`", section
        ), "Registry missing id field for ask-bootcamper"

    def test_registry_has_ask_bootcamper_name(self) -> None:
        """Assert the registry contains a name for ask-bootcamper."""
        content = _HOOK_REGISTRY.read_text(encoding="utf-8")
        section = _extract_section(content, "Critical Hooks")
        assert section, "Critical Hooks section not found"
        assert re.search(
            r"name:\s*`Ask Bootcamper`", section
        ), "Registry missing name field for ask-bootcamper"

    def test_registry_has_ask_bootcamper_description(self) -> None:
        """Assert the registry contains a description for ask-bootcamper."""
        content = _HOOK_REGISTRY.read_text(encoding="utf-8")
        section = _extract_section(content, "Critical Hooks")
        assert section, "Critical Hooks section not found"
        assert re.search(
            r"description:\s*`[^`]+`", section
        ), "Registry missing description field for ask-bootcamper"


# ---------------------------------------------------------------------------
# Test 8 — PBT: Non-gate steps have no gate instructions
# ---------------------------------------------------------------------------


@st.composite
def st_non_gate_step(draw: st.DrawFn) -> str:
    """Generate a non-gate step identifier from Steps 0, 1, 1b, 4, 4c.

    These steps should never contain mandatory gate instructions.
    """
    return draw(st.sampled_from(_NON_GATE_STEP_IDS))


class TestNonGateStepsProperty:
    """PBT — Non-gate steps have no gate instructions.

    **Validates: Requirements 3.1, 3.5**

    Use Hypothesis to generate random non-gate step identifiers and
    verify none contain mandatory gate instructions.
    """

    @given(step_id=st_non_gate_step())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_gate_steps_never_contain_gate_instructions(
        self, step_id: str
    ) -> None:
        """For any non-gate step, no gate instructions should be present."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        steps = _parse_onboarding_steps(content)

        if step_id not in steps:
            return  # Step not in file — nothing to check

        section = steps[step_id]
        assert not _GATE_KEYWORDS.search(section), (
            f"Non-gate step {step_id} unexpectedly contains gate "
            f"instructions. Preview:\n{section[:300]}"
        )
