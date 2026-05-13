"""Example-based unit tests for hook-gaps-modules-1-and-3 feature.

Validates the two new hook files (validate-business-problem, verify-demo-results),
their registration in hook-categories.yaml, and the updated hook count.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup for importing sync_hook_registry helpers
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    CATEGORIES_PATH,
    HOOKS_DIR,
    discover_hook_files,
    load_category_mapping,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALIDATE_HOOK_PATH = HOOKS_DIR / "validate-business-problem.kiro.hook"
VERIFY_HOOK_PATH = HOOKS_DIR / "verify-demo-results.kiro.hook"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validate_hook_data() -> dict:
    """Load and parse validate-business-problem.kiro.hook."""
    with open(VALIDATE_HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def verify_hook_data() -> dict:
    """Load and parse verify-demo-results.kiro.hook."""
    with open(VERIFY_HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


# ===========================================================================
# Task 5.1: Both hook files parse as valid JSON with correct field values
# ===========================================================================

class TestHookFileStructure:
    """Verify both hook files parse as valid JSON with correct field values."""

    def test_validate_hook_is_valid_json(self):
        """validate-business-problem.kiro.hook parses as valid JSON."""
        with open(VALIDATE_HOOK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_verify_hook_is_valid_json(self):
        """verify-demo-results.kiro.hook parses as valid JSON."""
        with open(VERIFY_HOOK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_validate_hook_name(self, validate_hook_data: dict):
        """validate-business-problem has correct name field."""
        assert validate_hook_data["name"] == "Validate Business Problem"

    def test_validate_hook_version(self, validate_hook_data: dict):
        """validate-business-problem has version 1.0.0."""
        assert validate_hook_data["version"] == "1.0.0"

    def test_validate_hook_has_description(self, validate_hook_data: dict):
        """validate-business-problem has a non-empty description."""
        assert len(validate_hook_data["description"]) > 0

    def test_validate_hook_when_type(self, validate_hook_data: dict):
        """validate-business-problem uses postTaskExecution event."""
        assert validate_hook_data["when"]["type"] == "postTaskExecution"

    def test_validate_hook_then_type(self, validate_hook_data: dict):
        """validate-business-problem uses askAgent action."""
        assert validate_hook_data["then"]["type"] == "askAgent"

    def test_validate_hook_has_prompt(self, validate_hook_data: dict):
        """validate-business-problem has a non-empty prompt."""
        assert len(validate_hook_data["then"]["prompt"]) > 20

    def test_verify_hook_name(self, verify_hook_data: dict):
        """verify-demo-results has correct name field."""
        assert verify_hook_data["name"] == "Verify Demo Results"

    def test_verify_hook_version(self, verify_hook_data: dict):
        """verify-demo-results has version 1.0.0."""
        assert verify_hook_data["version"] == "1.0.0"

    def test_verify_hook_has_description(self, verify_hook_data: dict):
        """verify-demo-results has a non-empty description."""
        assert len(verify_hook_data["description"]) > 0

    def test_verify_hook_when_type(self, verify_hook_data: dict):
        """verify-demo-results uses postTaskExecution event."""
        assert verify_hook_data["when"]["type"] == "postTaskExecution"

    def test_verify_hook_then_type(self, verify_hook_data: dict):
        """verify-demo-results uses askAgent action."""
        assert verify_hook_data["then"]["type"] == "askAgent"

    def test_verify_hook_has_prompt(self, verify_hook_data: dict):
        """verify-demo-results has a non-empty prompt."""
        assert len(verify_hook_data["then"]["prompt"]) > 20


# ===========================================================================
# Task 5.2: Prompt content for validate-business-problem
# ===========================================================================

class TestValidateBusinessProblemPrompt:
    """Verify prompt content for validate-business-problem hook."""

    def test_module_guard_reads_progress(self, validate_hook_data: dict):
        """Prompt instructs reading config/bootcamp_progress.json."""
        prompt = validate_hook_data["then"]["prompt"]
        assert "config/bootcamp_progress.json" in prompt

    def test_module_guard_checks_module_1(self, validate_hook_data: dict):
        """Prompt checks current_module is 1."""
        prompt = validate_hook_data["then"]["prompt"]
        assert "current_module" in prompt

    def test_silent_when_not_module_1(self, validate_hook_data: dict):
        """Prompt instructs producing no output when module is not 1."""
        prompt = validate_hook_data["then"]["prompt"].lower()
        assert "produce no output" in prompt

    def test_checks_data_sources(self, validate_hook_data: dict):
        """Prompt verifies data sources are identified."""
        prompt = validate_hook_data["then"]["prompt"].lower()
        assert "data source" in prompt

    def test_checks_matching_criteria(self, validate_hook_data: dict):
        """Prompt verifies matching criteria are defined."""
        prompt = validate_hook_data["then"]["prompt"].lower()
        assert "matching criteria" in prompt

    def test_checks_success_metrics(self, validate_hook_data: dict):
        """Prompt verifies success metrics are documented."""
        prompt = validate_hook_data["then"]["prompt"].lower()
        assert "success metrics" in prompt

    def test_reports_incomplete_fields(self, validate_hook_data: dict):
        """Prompt instructs reporting incomplete fields."""
        prompt = validate_hook_data["then"]["prompt"].lower()
        assert "incomplete" in prompt or "missing" in prompt

    def test_confirms_readiness_for_module_2(self, validate_hook_data: dict):
        """Prompt confirms readiness to proceed to Module 2."""
        prompt = validate_hook_data["then"]["prompt"]
        assert "Module 2" in prompt


# ===========================================================================
# Task 5.3: Prompt content for verify-demo-results
# ===========================================================================

class TestVerifyDemoResultsPrompt:
    """Verify prompt content for verify-demo-results hook."""

    def test_module_guard_reads_progress(self, verify_hook_data: dict):
        """Prompt instructs reading config/bootcamp_progress.json."""
        prompt = verify_hook_data["then"]["prompt"]
        assert "config/bootcamp_progress.json" in prompt

    def test_module_guard_checks_module_3(self, verify_hook_data: dict):
        """Prompt checks current_module is 3."""
        prompt = verify_hook_data["then"]["prompt"]
        assert "current_module" in prompt

    def test_silent_when_not_module_3(self, verify_hook_data: dict):
        """Prompt instructs producing no output when module is not 3."""
        prompt = verify_hook_data["then"]["prompt"].lower()
        assert "produce no output" in prompt

    def test_checks_entities_resolved(self, verify_hook_data: dict):
        """Prompt verifies entities were resolved."""
        prompt = verify_hook_data["then"]["prompt"].lower()
        assert "entities were resolved" in prompt or "resolved entities" in prompt

    def test_checks_matches_found(self, verify_hook_data: dict):
        """Prompt verifies matches were found."""
        prompt = verify_hook_data["then"]["prompt"].lower()
        assert "matches" in prompt

    def test_reports_singleton_results(self, verify_hook_data: dict):
        """Prompt reports singleton-only results."""
        prompt = verify_hook_data["then"]["prompt"].lower()
        assert "singleton" in prompt

    def test_confirms_demo_success(self, verify_hook_data: dict):
        """Prompt confirms successful demo completion."""
        prompt = verify_hook_data["then"]["prompt"]
        assert "Module 4" in prompt or "success" in prompt.lower()


# ===========================================================================
# Task 5.4: hook-categories.yaml contains module 1 and 3 entries
# ===========================================================================

class TestHookCategoriesRegistration:
    """Verify hook-categories.yaml contains module 1 and module 3 entries."""

    def test_module_1_entry_exists(self):
        """hook-categories.yaml has a module 1 entry."""
        mapping = load_category_mapping(CATEGORIES_PATH)
        assert "validate-business-problem" in mapping
        cat = mapping["validate-business-problem"]
        assert cat.module_number == 1

    def test_module_3_entry_exists(self):
        """hook-categories.yaml has a module 3 entry."""
        mapping = load_category_mapping(CATEGORIES_PATH)
        assert "verify-demo-results" in mapping
        cat = mapping["verify-demo-results"]
        assert cat.module_number == 3

    def test_module_1_hook_id_correct(self):
        """Module 1 lists validate-business-problem."""
        mapping = load_category_mapping(CATEGORIES_PATH)
        assert mapping["validate-business-problem"].hook_id == "validate-business-problem"

    def test_module_3_hook_id_correct(self):
        """Module 3 lists verify-demo-results."""
        mapping = load_category_mapping(CATEGORIES_PATH)
        assert mapping["verify-demo-results"].hook_id == "verify-demo-results"


# ===========================================================================
# Task 5.5: Total hook count is 25
# ===========================================================================

class TestHookCount:
    """Verify total hook count is 24."""

    def test_total_hook_file_count_is_24(self):
        """There are exactly 24 .kiro.hook files."""
        hook_files = discover_hook_files(HOOKS_DIR)
        assert len(hook_files) == 24

    def test_both_new_hooks_exist(self):
        """Both new hook files exist on disk."""
        assert VALIDATE_HOOK_PATH.is_file(), "validate-business-problem.kiro.hook missing"
        assert VERIFY_HOOK_PATH.is_file(), "verify-demo-results.kiro.hook missing"
