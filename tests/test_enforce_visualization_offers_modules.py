"""Tests for enforce-visualization-offers hook multi-module coverage.

Verifies that the enforce-visualization-offers hook is properly configured
for use across all 4 modules it's assigned to (Modules 3, 5, 7, 8) per
hook-categories.yaml.
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
    parse_categories_yaml,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_ID = "enforce-visualization-offers"
HOOK_PATH = HOOKS_DIR / f"{HOOK_ID}.kiro.hook"
EXPECTED_MODULES = [3, 5, 7, 8]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def hook_data() -> dict:
    """Load the enforce-visualization-offers hook file."""
    assert HOOK_PATH.exists(), f"Hook file not found: {HOOK_PATH}"
    return load_hook(HOOK_PATH)


@pytest.fixture()
def hook_prompt(hook_data: dict) -> str:
    """Extract the prompt text from the hook data."""
    return hook_data["then"]["prompt"]


@pytest.fixture()
def categories() -> dict[str, list[str]]:
    """Load hook-categories.yaml."""
    return parse_categories_yaml()


# ---------------------------------------------------------------------------
# TestEnforceVisualizationOffersModules
# ---------------------------------------------------------------------------

class TestEnforceVisualizationOffersModules:
    """Verify enforce-visualization-offers hook works across all 4 assigned modules."""

    @pytest.mark.parametrize("module_num", EXPECTED_MODULES)
    def test_hook_assigned_to_module_in_categories(
        self, categories: dict[str, list[str]], module_num: int
    ) -> None:
        """Hook is listed under the expected module in hook-categories.yaml.

        Args:
            categories: Parsed hook-categories.yaml mapping.
            module_num: Module number to check.
        """
        category_key = f"module-{module_num}"
        assert category_key in categories, (
            f"Module {module_num} not found in hook-categories.yaml"
        )
        assert HOOK_ID in categories[category_key], (
            f"{HOOK_ID} not assigned to module {module_num} in hook-categories.yaml. "
            f"Found: {categories[category_key]}"
        )

    @pytest.mark.parametrize("module_num", EXPECTED_MODULES)
    def test_prompt_references_module_number(
        self, hook_prompt: str, module_num: int
    ) -> None:
        """Hook prompt references the module number for multi-module routing.

        Args:
            hook_prompt: The hook's prompt text.
            module_num: Module number that should be referenced.
        """
        assert str(module_num) in hook_prompt, (
            f"{HOOK_ID} prompt does not reference module {module_num}. "
            f"The hook is assigned to modules {EXPECTED_MODULES} but the prompt "
            f"must reference all of them for correct routing."
        )

    def test_prompt_contains_module_set(self, hook_prompt: str) -> None:
        """Hook prompt contains the complete set of visualization-capable modules."""
        # The prompt should reference the set {3, 5, 7, 8} in some form
        for module_num in EXPECTED_MODULES:
            assert str(module_num) in hook_prompt, (
                f"{HOOK_ID} prompt missing module {module_num} from the "
                f"visualization-capable module set {EXPECTED_MODULES}"
            )

    def test_hook_uses_agent_stop_event(self, hook_data: dict) -> None:
        """Hook uses agentStop event type for end-of-conversation checking."""
        event_type = hook_data.get("when", {}).get("type", "")
        assert event_type == "agentStop", (
            f"{HOOK_ID} uses event type '{event_type}', expected 'agentStop' "
            f"for end-of-conversation visualization offer checking"
        )

    def test_prompt_references_visualization_protocol(
        self, hook_prompt: str
    ) -> None:
        """Hook prompt references visualization-protocol.md for offer templates."""
        assert "visualization-protocol" in hook_prompt.lower(), (
            f"{HOOK_ID} prompt does not reference visualization-protocol.md. "
            f"The hook needs the protocol for offer templates across modules."
        )

    def test_prompt_references_tracker(self, hook_prompt: str) -> None:
        """Hook prompt references the visualization tracker for state checking."""
        assert "visualization_tracker" in hook_prompt, (
            f"{HOOK_ID} prompt does not reference visualization_tracker. "
            f"The hook needs the tracker to check which offers were made."
        )

    def test_prompt_references_progress_file(self, hook_prompt: str) -> None:
        """Hook prompt references bootcamp_progress.json for module detection."""
        assert "bootcamp_progress" in hook_prompt, (
            f"{HOOK_ID} prompt does not reference bootcamp_progress. "
            f"The hook needs progress state to determine the current module."
        )

    def test_hook_not_assigned_to_other_modules(
        self, categories: dict[str, list[str]]
    ) -> None:
        """Hook is only assigned to the expected 4 modules, not others."""
        unexpected_modules = []
        for key, hooks in categories.items():
            if not key.startswith("module-"):
                continue
            module_part = key.replace("module-", "")
            if module_part == "any":
                continue
            try:
                mod_num = int(module_part)
            except ValueError:
                continue
            if mod_num not in EXPECTED_MODULES and HOOK_ID in hooks:
                unexpected_modules.append(mod_num)

        assert unexpected_modules == [], (
            f"{HOOK_ID} unexpectedly assigned to modules {unexpected_modules}. "
            f"Expected only {EXPECTED_MODULES}."
        )
