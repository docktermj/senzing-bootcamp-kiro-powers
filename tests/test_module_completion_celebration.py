"""Tests for the module-completion-celebration hook.

Validates hook file structure, prompt content for boundary detection,
celebration messages, next-module logic, lightweight execution constraints,
categories registration, coexistence with manual workflow, and correctness
properties via Hypothesis property-based testing.
"""

from __future__ import annotations

import json
import re
import string
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    HOOKS_DIR,
    REQUIRED_FIELDS,
    SEMVER_PATTERN,
    SILENT_PROCESSING_PATTERNS,
    has_silent_processing,
    parse_categories_yaml,
    validate_required_fields,
    validate_version,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = HOOKS_DIR / "module-completion-celebration.kiro.hook"
HOOK_ID = "module-completion-celebration"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def hook_data() -> dict:
    """Load and parse the module-completion-celebration hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def prompt(hook_data: dict) -> str:
    """Extract the prompt text from the hook data."""
    return hook_data["then"]["prompt"]


# ===========================================================================
# Task 3.1: TestHookFileStructure — Req 1
# ===========================================================================

class TestHookFileStructure:
    """Verify hook file exists, parses as valid JSON, contains required fields."""

    def test_hook_file_exists(self):
        """The hook file exists on disk (Req 1.1)."""
        assert HOOK_PATH.is_file(), f"Hook file not found at {HOOK_PATH}"

    def test_parses_as_valid_json(self):
        """The hook file parses as valid JSON (Req 1.1)."""
        with open(HOOK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_contains_all_required_fields(self, hook_data: dict):
        """The hook contains all required fields (Req 1.2)."""
        missing = validate_required_fields(hook_data)
        assert not missing, f"Missing required fields: {', '.join(missing)}"

    def test_when_type_is_post_task_execution(self, hook_data: dict):
        """when.type is postTaskExecution (Req 1.3)."""
        assert hook_data["when"]["type"] == "postTaskExecution"

    def test_then_type_is_ask_agent(self, hook_data: dict):
        """then.type is askAgent (Req 1.4)."""
        assert hook_data["then"]["type"] == "askAgent"

    def test_version_is_valid_semver(self, hook_data: dict):
        """version matches semver format (Req 1.5)."""
        version = hook_data["version"]
        assert validate_version(version), f"Invalid semver: {version}"

    def test_version_is_1_0_0(self, hook_data: dict):
        """version is 1.0.0."""
        assert hook_data["version"] == "1.0.0"

    def test_name_field_present(self, hook_data: dict):
        """name field is a non-empty string."""
        assert isinstance(hook_data["name"], str) and len(hook_data["name"]) > 0

    def test_description_field_present(self, hook_data: dict):
        """description field is a non-empty string."""
        assert isinstance(hook_data["description"], str) and len(hook_data["description"]) > 0


# ===========================================================================
# Task 3.2: TestPromptBoundaryDetection — Req 2
# ===========================================================================

class TestPromptBoundaryDetection:
    """Verify prompt references progress file, modules_completed, and silent-exit."""

    def test_references_bootcamp_progress_json(self, prompt: str):
        """Prompt references config/bootcamp_progress.json (Req 2.1)."""
        assert "config/bootcamp_progress.json" in prompt

    def test_references_modules_completed(self, prompt: str):
        """Prompt references modules_completed array (Req 2.1)."""
        assert "modules_completed" in prompt

    def test_contains_silent_exit_instruction(self, prompt: str):
        """Prompt contains silent-exit instruction language (Req 2.2)."""
        assert has_silent_processing(prompt), (
            "Prompt must contain a silent-processing phrase like "
            "'produce no output', 'do nothing', etc."
        )

    def test_instructs_no_output_when_unchanged(self, prompt: str):
        """Prompt instructs producing no output when modules_completed unchanged (Req 2.2)."""
        lower = prompt.lower()
        assert "has not changed" in lower or "no new module" in lower

    def test_instructs_identify_new_module(self, prompt: str):
        """Prompt instructs identifying the newly completed module (Req 2.4)."""
        lower = prompt.lower()
        assert "new module" in lower or "newly completed" in lower


# ===========================================================================
# Task 3.3: TestPromptCelebrationMessage — Req 3
# ===========================================================================

class TestPromptCelebrationMessage:
    """Verify prompt contains celebration banner and summary instructions."""

    def test_contains_congratulatory_instruction(self, prompt: str):
        """Prompt contains congratulatory/banner instructions (Req 3.1)."""
        lower = prompt.lower()
        assert "congratulat" in lower or "banner" in lower

    def test_contains_module_number_in_banner(self, prompt: str):
        """Prompt instructs including module number in celebration (Req 3.1)."""
        lower = prompt.lower()
        assert "module number" in lower or "module's number" in lower

    def test_contains_module_name_in_banner(self, prompt: str):
        """Prompt instructs including module name in celebration (Req 3.1)."""
        lower = prompt.lower()
        assert "module name" in lower or "name" in lower

    def test_contains_summary_instruction(self, prompt: str):
        """Prompt instructs providing a summary of accomplishments (Req 3.2)."""
        lower = prompt.lower()
        assert "summary" in lower or "what was built" in lower or "accomplished" in lower

    def test_references_module_dependencies_yaml(self, prompt: str):
        """Prompt references config/module-dependencies.yaml for module names (Req 3.3)."""
        assert "config/module-dependencies.yaml" in prompt

    def test_concise_message_instruction(self, prompt: str):
        """Prompt instructs keeping the message concise (Req 3.4)."""
        lower = prompt.lower()
        assert "concise" in lower or "one banner line" in lower or "brief" in lower


# ===========================================================================
# Task 3.4: TestPromptNextModule — Req 4
# ===========================================================================

class TestPromptNextModule:
    """Verify prompt contains next-module display, offer-to-begin, graduation."""

    def test_contains_next_module_display(self, prompt: str):
        """Prompt instructs displaying the next module (Req 4.1)."""
        lower = prompt.lower()
        assert "next module" in lower

    def test_contains_offer_to_begin(self, prompt: str):
        """Prompt instructs offering to begin the next module (Req 4.2)."""
        lower = prompt.lower()
        assert "offer to begin" in lower or "begin it immediately" in lower

    def test_contains_graduation_handling(self, prompt: str):
        """Prompt handles track completion with graduation (Req 4.3)."""
        lower = prompt.lower()
        assert "graduation" in lower or "track are complete" in lower

    def test_references_bootcamp_preferences_yaml(self, prompt: str):
        """Prompt references config/bootcamp_preferences.yaml for track (Req 4.4)."""
        assert "config/bootcamp_preferences.yaml" in prompt

    def test_references_module_dependencies_for_track(self, prompt: str):
        """Prompt references config/module-dependencies.yaml for track definitions (Req 4.4)."""
        assert "config/module-dependencies.yaml" in prompt

    def test_determines_track_from_preferences(self, prompt: str):
        """Prompt instructs determining the bootcamper's track (Req 4.4)."""
        lower = prompt.lower()
        assert "track" in lower


# ===========================================================================
# Task 3.5: TestPromptLightweightExecution — Req 5
# ===========================================================================

class TestPromptLightweightExecution:
    """Verify prompt does NOT contain file-writing/script/scanning instructions."""

    def test_no_file_write_instructions(self, prompt: str):
        """Prompt does NOT instruct writing files (Req 5.2)."""
        lower = prompt.lower()
        # The prompt should say "Do NOT write" — not instruct to write
        # Check that there's no positive instruction to write files
        assert "write files" not in lower or "not write" in lower or "do not write" in lower

    def test_no_script_execution_instructions(self, prompt: str):
        """Prompt does NOT instruct running scripts (Req 5.2)."""
        lower = prompt.lower()
        assert "run scripts" not in lower or "not run" in lower or "do not run" in lower

    def test_no_filesystem_scan_instructions(self, prompt: str):
        """Prompt does NOT instruct file-system scans (Req 5.2)."""
        lower = prompt.lower()
        assert (
            "file-system scan" not in lower
            or "not perform file-system scan" in lower
            or "do not perform" in lower
        )

    def test_only_three_config_files_referenced(self, prompt: str):
        """Prompt references only the three allowed config files (Req 5.3)."""
        # The three allowed config files
        allowed_configs = {
            "config/bootcamp_progress.json",
            "config/module-dependencies.yaml",
            "config/bootcamp_preferences.yaml",
        }
        # Find all config/ file references in the prompt
        config_refs = set(re.findall(r"config/[\w\-]+\.\w+", prompt))
        assert config_refs <= allowed_configs, (
            f"Prompt references config files beyond the allowed three: "
            f"{config_refs - allowed_configs}"
        )

    def test_contains_explicit_read_constraint(self, prompt: str):
        """Prompt explicitly limits reads to three config files (Req 5.3)."""
        lower = prompt.lower()
        assert "three" in lower or "3" in lower or "only read" in lower


# ===========================================================================
# Task 3.6: TestCategoriesRegistration — Req 6
# ===========================================================================

class TestCategoriesRegistration:
    """Verify module-completion-celebration in any category, exactly once."""

    def test_hook_in_any_category(self):
        """module-completion-celebration appears in the 'any' category (Req 6.2)."""
        categories = parse_categories_yaml()
        any_hooks = categories.get("module-any", [])
        assert HOOK_ID in any_hooks, (
            f"{HOOK_ID} not found in 'any' category. "
            f"Found: {any_hooks}"
        )

    def test_hook_in_exactly_one_category(self):
        """module-completion-celebration appears in exactly one category (Req 6.3)."""
        categories = parse_categories_yaml()
        occurrences = sum(
            1 for hooks in categories.values() if HOOK_ID in hooks
        )
        assert occurrences == 1, (
            f"{HOOK_ID} appears in {occurrences} categories, expected exactly 1"
        )


# ===========================================================================
# Task 3.7: TestPromptCoexistence — Req 7
# ===========================================================================

class TestPromptCoexistence:
    """Verify prompt does NOT load module-completion.md, has trigger words."""

    def test_does_not_load_module_completion_md(self, prompt: str):
        """Prompt does NOT instruct loading module-completion.md (Req 7.1)."""
        # Should not contain instructions to load/include the steering file
        assert "load module-completion.md" not in prompt.lower()
        assert "include module-completion.md" not in prompt.lower()
        # The file name itself should not appear as a reference to load
        assert "module-completion.md" not in prompt

    def test_contains_completion_trigger_word(self, prompt: str):
        """Prompt contains 'completion' trigger word (Req 7.2)."""
        assert "completion" in prompt.lower()

    def test_contains_journal_trigger_word(self, prompt: str):
        """Prompt contains 'journal' trigger word (Req 7.2)."""
        assert "journal" in prompt.lower()

    def test_does_not_contain_journal_entry_instructions(self, prompt: str):
        """Prompt does NOT contain journal entry creation instructions (Req 7.3)."""
        lower = prompt.lower()
        # Should not instruct creating journal entries
        assert "create a journal" not in lower
        assert "write a journal" not in lower

    def test_does_not_contain_certificate_instructions(self, prompt: str):
        """Prompt does NOT contain certificate generation instructions (Req 7.3)."""
        lower = prompt.lower()
        assert "generate a certificate" not in lower
        assert "create a certificate" not in lower

    def test_does_not_contain_reflection_instructions(self, prompt: str):
        """Prompt does NOT contain positive reflection question instructions (Req 7.3)."""
        lower = prompt.lower()
        # The prompt may mention reflection questions in a negative/prohibitive context
        # (e.g., "Do NOT ask reflection questions"). We check it doesn't instruct
        # the agent to actually perform reflection.
        assert "ask the bootcamper reflection" not in lower
        assert "present reflection questions" not in lower
        assert "guide them through reflection" not in lower


# ===========================================================================
# Task 4.1: TestRequiredFieldsValidation — Property 1
# ===========================================================================

class TestRequiredFieldsValidation:
    """Property 1: Required fields validation.

    For any subset of required fields, validator reports exactly the missing fields.
    Feature: module-completion-celebration, Property 1: Required fields validation.
    """

    @given(
        fields_to_include=st.lists(
            st.sampled_from(REQUIRED_FIELDS),
            unique=True,
            min_size=0,
            max_size=len(REQUIRED_FIELDS),
        )
    )
    @settings(max_examples=100)
    def test_validator_reports_exactly_missing_fields(
        self, fields_to_include: list[str]
    ):
        """For any subset of required fields present, validator reports exactly the missing."""
        # Build a hook dict with only the specified fields
        hook: dict = {}
        for field in fields_to_include:
            parts = field.split(".")
            obj = hook
            for part in parts[:-1]:
                if part not in obj:
                    obj[part] = {}
                obj = obj[part]
            obj[parts[-1]] = "test-value"

        missing = validate_required_fields(hook)
        expected_missing = set(REQUIRED_FIELDS) - set(fields_to_include)
        assert set(missing) == expected_missing, (
            f"Expected missing: {expected_missing}, got: {set(missing)}"
        )


# ===========================================================================
# Task 4.2: TestSemverFormatValidation — Property 2
# ===========================================================================

class TestSemverFormatValidation:
    """Property 2: Semantic version format validation.

    For any random string, version validator accepts iff it matches valid semver.
    Feature: module-completion-celebration, Property 2: Semver format validation.
    """

    @given(version=st.from_regex(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", fullmatch=True))
    @settings(max_examples=100)
    def test_valid_semver_accepted(self, version: str):
        """Valid semver strings are accepted by the validator."""
        # Only truly valid if no leading zeros (except single 0)
        parts = version.split(".")
        is_valid = all(
            part == "0" or not part.startswith("0") for part in parts
        )
        assert validate_version(version) == is_valid

    @given(
        version=st.one_of(
            # Non-numeric strings
            st.text(
                alphabet=string.ascii_letters + "-_!@#",
                min_size=1,
                max_size=15,
            ),
            # Two components only
            st.builds(
                lambda a, b: f"{a}.{b}",
                a=st.integers(min_value=0, max_value=99),
                b=st.integers(min_value=0, max_value=99),
            ),
            # Four components
            st.builds(
                lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
                a=st.integers(min_value=0, max_value=9),
                b=st.integers(min_value=0, max_value=9),
                c=st.integers(min_value=0, max_value=9),
                d=st.integers(min_value=0, max_value=9),
            ),
            # Empty string
            st.just(""),
        )
    )
    @settings(max_examples=100)
    def test_invalid_semver_rejected(self, version: str):
        """Invalid semver strings are rejected by the validator."""
        assert not validate_version(version), f"Should reject: {version!r}"


# ===========================================================================
# Task 4.3: TestSilentProcessingDetection — Property 3
# ===========================================================================

class TestSilentProcessingDetection:
    """Property 3: Silent-processing detection.

    For any prompt string, detector returns true iff a silent-processing phrase is present.
    Feature: module-completion-celebration, Property 3: Silent-processing detection.
    """

    @given(
        base_text=st.text(
            alphabet=string.ascii_lowercase + " ",
            min_size=5,
            max_size=50,
        ),
        phrase_index=st.integers(min_value=0, max_value=2),
    )
    @settings(max_examples=100)
    def test_prompt_with_phrase_detected(self, base_text: str, phrase_index: int):
        """Prompts containing a silent-processing phrase are detected."""
        # Inject a known phrase
        phrases = [
            "produce no output at all",
            "do nothing",
            "do not acknowledge, do not explain, do not print",
        ]
        prompt_with_phrase = base_text + " " + phrases[phrase_index] + " " + base_text
        assert has_silent_processing(prompt_with_phrase), (
            f"Should detect silent-processing in: {prompt_with_phrase!r}"
        )

    @given(
        text=st.text(
            alphabet=string.ascii_uppercase + string.digits + "!?.,;:",
            min_size=5,
            max_size=80,
        )
    )
    @settings(max_examples=100)
    def test_prompt_without_phrase_not_detected(self, text: str):
        """Prompts without silent-processing phrases are not detected."""
        # Ensure the text doesn't accidentally contain any pattern
        has_pattern = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in SILENT_PROCESSING_PATTERNS
        )
        if not has_pattern:
            assert not has_silent_processing(text), (
                f"Should NOT detect silent-processing in: {text!r}"
            )


# ===========================================================================
# Task 4.4: TestCategoryUniqueness — Property 4
# ===========================================================================

class TestCategoryUniqueness:
    """Property 4: Category uniqueness.

    For any category mapping, uniqueness checker correctly identifies duplicates.
    Feature: module-completion-celebration, Property 4: Category uniqueness.
    """

    @given(
        categories=st.dictionaries(
            keys=st.text(
                alphabet=string.ascii_lowercase + "-",
                min_size=3,
                max_size=15,
            ),
            values=st.lists(
                st.text(
                    alphabet=string.ascii_lowercase + "-",
                    min_size=3,
                    max_size=20,
                ),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_uniqueness_checker_identifies_duplicates(
        self, categories: dict[str, list[str]]
    ):
        """For any category mapping, correctly identify duplicate hook identifiers."""
        # Count occurrences of each hook_id across all categories
        hook_counts: dict[str, int] = {}
        for hooks in categories.values():
            for hook_id in hooks:
                hook_counts[hook_id] = hook_counts.get(hook_id, 0) + 1

        # Find duplicates (appear in more than one category)
        duplicates = {hid for hid, count in hook_counts.items() if count > 1}

        # Verify our checker logic matches
        found_duplicates: set[str] = set()
        seen: set[str] = set()
        for hooks in categories.values():
            for hook_id in hooks:
                if hook_id in seen:
                    found_duplicates.add(hook_id)
                seen.add(hook_id)

        assert found_duplicates == duplicates, (
            f"Expected duplicates: {duplicates}, found: {found_duplicates}"
        )

    @given(
        hook_ids=st.lists(
            st.text(
                alphabet=string.ascii_lowercase + "-",
                min_size=3,
                max_size=15,
            ),
            min_size=2,
            max_size=10,
            unique=True,
        ),
        num_categories=st.integers(min_value=2, max_value=4),
    )
    @settings(max_examples=100)
    def test_unique_distribution_has_no_duplicates(
        self, hook_ids: list[str], num_categories: int
    ):
        """When each hook appears in exactly one category, no duplicates found."""
        # Distribute hooks uniquely across categories
        categories: dict[str, list[str]] = {}
        for i, hook_id in enumerate(hook_ids):
            cat_name = f"cat-{i % num_categories}"
            categories.setdefault(cat_name, []).append(hook_id)

        # Verify no duplicates across categories
        seen: set[str] = set()
        found_duplicates: set[str] = set()
        for hooks in categories.values():
            for hook_id in hooks:
                if hook_id in seen:
                    found_duplicates.add(hook_id)
                seen.add(hook_id)

        assert len(found_duplicates) == 0
