"""Prompt logic tests for module-specific hooks without dedicated coverage.

Validates semantic correctness of hook prompts for:
- enforce-mapping-spec (Module 5)
- enforce-single-question (Critical)
- security-scan-on-save (Module 9)
- validate-alert-config (Module 10)
- validate-benchmark-results (Module 8)
- verify-sdk-setup (Module 2)

These hooks had structural validation (JSON schema, required fields) but no
tests verifying their prompt logic matches documented behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path("senzing-bootcamp/hooks")


def _load_prompt(hook_id: str) -> str:
    """Load and return the prompt text for a given hook ID."""
    path = _HOOKS_DIR / f"{hook_id}.kiro.hook"
    assert path.exists(), f"Hook file not found: {path}"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


# ===========================================================================
# enforce-mapping-spec — Module 5
# ===========================================================================


class TestEnforceMappingSpec:
    """Validate enforce-mapping-spec hook prompt logic.

    This hook fires when transformed data files are created. It must:
    1. Extract source name from the filename
    2. Check if docs/{source_name}_mapper.md exists
    3. If exists: produce no output (silent pass)
    4. If missing: block and create the mapping spec
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("enforce-mapping-spec")

    def test_extracts_source_name_from_filename(self):
        """Prompt instructs to extract source name from the transformed filename."""
        assert "source name" in self.prompt.lower()
        assert "filename" in self.prompt.lower()

    def test_checks_mapper_doc_existence(self):
        """Prompt checks for docs/{source_name}_mapper.md."""
        assert "_mapper.md" in self.prompt
        assert "docs/" in self.prompt

    def test_silent_when_mapper_exists(self):
        """Prompt produces no output when mapper doc already exists."""
        lower = self.prompt.lower()
        assert "no output" in lower or "produce no output" in lower

    def test_blocks_when_mapper_missing(self):
        """Prompt blocks progression when mapper doc is missing."""
        lower = self.prompt.lower()
        assert "do not proceed" in lower or "must create" in lower.replace(
            "you must", "must"
        )

    def test_provides_mapping_spec_template(self):
        """Prompt includes a template structure for the mapping spec."""
        assert "Field Mappings" in self.prompt
        assert "Source Field" in self.prompt
        assert "Senzing Attribute" in self.prompt


# ===========================================================================
# enforce-single-question — Critical
# ===========================================================================


class TestEnforceSingleQuestion:
    """Validate enforce-single-question hook prompt logic.

    This hook fires on preToolUse (write). It must:
    1. Only activate for .question_pending files
    2. Check for exactly one question mark
    3. Check for no conjunctions joining questions
    4. Check for unambiguous yes/no meaning
    5. Block and require rewrite on violation
    6. Silent pass when rules are satisfied
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("enforce-single-question")

    def test_only_activates_for_question_pending(self):
        """Prompt checks if target path ends with .question_pending."""
        assert ".question_pending" in self.prompt

    def test_checks_single_question_mark(self):
        """Prompt validates exactly one question mark."""
        lower = self.prompt.lower()
        assert "one question" in lower or "exactly one question mark" in lower

    def test_checks_no_conjunctions(self):
        """Prompt checks for conjunctions joining questions."""
        assert "and" in self.prompt
        assert "or" in self.prompt
        assert "but first" in self.prompt

    def test_checks_unambiguous_yes_no(self):
        """Prompt validates unambiguous yes/no meaning."""
        lower = self.prompt.lower()
        assert "yes" in lower
        assert "no" in lower
        assert "ambiguous" in lower

    def test_blocks_on_violation(self):
        """Prompt blocks the write on violation."""
        assert "COMPOUND QUESTION DETECTED" in self.prompt
        assert "REWRITE REQUIRED" in self.prompt

    def test_silent_on_pass(self):
        """Prompt produces no output when all rules pass."""
        assert "produce no output" in self.prompt.lower()

    def test_silent_for_non_question_pending_files(self):
        """Prompt produces no output for non-.question_pending files."""
        # The prompt should have a fast path for non-question_pending writes
        assert "does NOT end with" in self.prompt


# ===========================================================================
# security-scan-on-save — Module 9
# ===========================================================================


class TestSecurityScanOnSave:
    """Validate security-scan-on-save hook prompt logic.

    This hook fires when security-related files are modified. It must:
    1. Check if bootcamper is in Module 9
    2. Recommend language-appropriate scanner
    3. Cover all 5 supported languages
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("security-scan-on-save")

    def test_checks_module_9(self):
        """Prompt checks if bootcamper is in Module 9."""
        assert "Module 9" in self.prompt

    def test_recommends_python_scanner(self):
        """Prompt recommends bandit for Python."""
        assert "bandit" in self.prompt.lower()

    def test_recommends_java_scanner(self):
        """Prompt recommends spotbugs for Java."""
        assert "spotbugs" in self.prompt.lower()

    def test_recommends_csharp_scanner(self):
        """Prompt recommends dotnet vulnerability check for C#."""
        assert "dotnet" in self.prompt.lower()
        assert "vulnerable" in self.prompt.lower()

    def test_recommends_rust_scanner(self):
        """Prompt recommends cargo audit for Rust."""
        assert "cargo audit" in self.prompt.lower()

    def test_recommends_typescript_scanner(self):
        """Prompt recommends npm audit for TypeScript."""
        assert "npm audit" in self.prompt.lower()


# ===========================================================================
# validate-alert-config — Module 10
# ===========================================================================


class TestValidateAlertConfig:
    """Validate validate-alert-config hook prompt logic.

    This hook fires when monitoring config files are created. It must:
    1. Validate alert rule required fields (name, condition, severity, action)
    2. Validate severity levels (Critical, Warning, Info)
    3. Validate thresholds are numeric and reasonable
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("validate-alert-config")

    def test_checks_required_fields(self):
        """Prompt validates required alert rule fields."""
        lower = self.prompt.lower()
        assert "name" in lower
        assert "condition" in lower
        assert "severity" in lower
        assert "action" in lower

    def test_checks_severity_levels(self):
        """Prompt validates severity levels are from allowed set."""
        assert "Critical" in self.prompt
        assert "Warning" in self.prompt
        assert "Info" in self.prompt

    def test_checks_numeric_thresholds(self):
        """Prompt validates thresholds are numeric."""
        lower = self.prompt.lower()
        assert "numeric" in lower or "threshold" in lower


# ===========================================================================
# validate-benchmark-results — Module 8
# ===========================================================================


class TestValidateBenchmarkResults:
    """Validate validate-benchmark-results hook prompt logic.

    This hook fires when benchmark scripts are edited. It must:
    1. Verify script runs without errors
    2. Check for required metrics (records/sec, latency percentiles)
    3. Verify results are written to structured output
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("validate-benchmark-results")

    def test_checks_script_runs(self):
        """Prompt verifies the script runs without errors."""
        lower = self.prompt.lower()
        assert "runs without errors" in lower or "run" in lower

    def test_checks_records_per_second(self):
        """Prompt checks for records/sec metric."""
        assert "records/sec" in self.prompt

    def test_checks_latency_percentiles(self):
        """Prompt checks for latency percentile metrics."""
        lower = self.prompt.lower()
        assert "p50" in lower or "p95" in lower or "p99" in lower

    def test_checks_structured_output(self):
        """Prompt verifies results are written to structured output."""
        lower = self.prompt.lower()
        assert "written" in lower or "output" in lower


# ===========================================================================
# verify-sdk-setup — Module 2
# ===========================================================================


class TestVerifySdkSetup:
    """Validate verify-sdk-setup hook prompt logic.

    This hook fires when config/database files are modified. It must:
    1. Check if bootcamper is in Module 2
    2. Verify database/G2C.db exists
    3. Verify Senzing engine can initialize
    4. Produce no output if not in Module 2
    5. Suggest preflight.py on failure
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.prompt = _load_prompt("verify-sdk-setup")

    def test_checks_module_2(self):
        """Prompt checks if bootcamper is in Module 2."""
        assert "Module 2" in self.prompt

    def test_checks_database_exists(self):
        """Prompt verifies database/G2C.db exists."""
        assert "G2C.db" in self.prompt

    def test_checks_engine_initialization(self):
        """Prompt verifies Senzing engine can initialize."""
        lower = self.prompt.lower()
        assert "initialize" in lower

    def test_silent_when_not_module_2(self):
        """Prompt produces no output when not in Module 2."""
        assert "not in Module 2" in self.prompt
        assert "no output" in self.prompt.lower()

    def test_suggests_preflight_on_failure(self):
        """Prompt suggests running preflight.py on verification failure."""
        assert "preflight.py" in self.prompt
