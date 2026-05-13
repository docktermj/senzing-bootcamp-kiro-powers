"""Unit tests for Module 3 System Verification.

Validates specific file requirements for the system verification module:
steering file content, module dependencies, onboarding flow references,
build commands, and verification report schema.

Feature: module-03-system-verification
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _BASE_DIR / "steering"
_CONFIG_DIR: Path = _BASE_DIR / "config"

_STEERING_FILE: Path = _STEERING_DIR / "module-03-system-verification.md"
_MODULE_DEPS: Path = _CONFIG_DIR / "module-dependencies.yaml"
_ONBOARDING_FLOW: Path = _STEERING_DIR / "onboarding-flow.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_steering() -> str:
    """Read the Module 3 system verification steering file.

    Returns:
        Full text content of the steering file.
    """
    return _STEERING_FILE.read_text(encoding="utf-8")


def _read_module_deps() -> dict:
    """Read and parse the module-dependencies.yaml file.

    Returns:
        Parsed YAML content as a dictionary.
    """
    return yaml.safe_load(_MODULE_DEPS.read_text(encoding="utf-8"))


def _read_onboarding_flow() -> str:
    """Read the onboarding-flow.md steering file.

    Returns:
        Full text content of the onboarding flow file.
    """
    return _ONBOARDING_FLOW.read_text(encoding="utf-8")


def _extract_json_blocks(content: str) -> list[str]:
    """Extract all JSON code blocks from markdown content.

    Args:
        content: Markdown text containing fenced code blocks.

    Returns:
        List of raw JSON strings from ```json blocks.
    """
    return re.findall(r"```json\s*\n(.*?)```", content, re.DOTALL)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestSystemVerificationUnit:
    """Example-based unit tests for Module 3 System Verification.

    Validates specific acceptance criteria for the steering file,
    module dependencies, onboarding flow, build commands, and report schema.
    """

    def test_steering_file_uses_truthset_only(self) -> None:
        """No dataset choice is offered in the steering file.

        Validates: Requirement 1.1

        The steering file may mention other dataset names in a prohibition
        context (e.g., "Do not use CORD...") but must not offer them as
        selectable options. It must explicitly state TruthSet-only usage.
        """
        content = _read_steering()

        # Should contain explicit TruthSet-only language
        assert "TruthSet" in content, (
            "Steering file should reference TruthSet"
        )

        # Should explicitly state no dataset choice is offered
        content_lower = content.lower()
        assert "no dataset choice" in content_lower or (
            "do not" in content_lower and "dataset" in content_lower
        ), "Steering file should prohibit dataset choice"

        # Should NOT contain a dataset selection prompt/menu
        # (offering a choice like "Choose from: CORD, Las Vegas...")
        choice_patterns = [
            r"choose\s+(?:from|a|your)\s+dataset",
            r"select\s+(?:a|your)\s+dataset",
            r"which\s+dataset\s+would\s+you",
        ]
        for pattern in choice_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, (
                f"Steering file should not offer dataset choice: "
                f"found pattern '{pattern}'"
            )

    def test_steering_file_has_all_verification_steps(self) -> None:
        """All 8 check types are present in the steering file.

        Validates: Requirement 10.2
        """
        content = _read_steering()

        expected_checks = [
            "mcp_connectivity",
            "truthset_acquisition",
            "sdk_initialization",
            "code_generation",
            "build_compilation",
            "data_loading",
            "results_validation",
            "database_operations",
        ]

        for check in expected_checks:
            assert check in content, (
                f"Steering file missing check type: {check}"
            )

    def test_module_dependencies_updated(self) -> None:
        """Module 3 name is 'System Verification' in dependencies.

        Validates: Requirement 11.1
        """
        deps = _read_module_deps()
        module_3 = deps["modules"][3]
        assert module_3["name"] == "System Verification", (
            f"Module 3 name should be 'System Verification', "
            f"got '{module_3['name']}'"
        )

    def test_gate_condition_updated(self) -> None:
        """Gate 3→4 references system verification.

        Validates: Requirements 11.2, 11.5
        """
        deps = _read_module_deps()
        gate_3_4 = deps["gates"]["3->4"]
        requires_text = " ".join(gate_3_4["requires"]).lower()
        assert "system verification" in requires_text or "verification" in requires_text, (
            f"Gate 3->4 should reference system verification, "
            f"got: {gate_3_4['requires']}"
        )

    def test_steering_file_has_web_service_step(self) -> None:
        """Web service generation step exists in the steering file.

        Validates: Requirement 7.1
        """
        content = _read_steering()

        assert "web_service" in content or "Web Service" in content, (
            "Steering file should contain web service step"
        )
        assert "generate_scaffold" in content, (
            "Steering file should reference generate_scaffold for web service"
        )
        assert "web_service" in content, (
            "Steering file should reference web_service workflow"
        )

    def test_steering_file_has_cleanup_step(self) -> None:
        """Cleanup and purge instructions are present.

        Validates: Requirements 13.4, 13.5
        """
        content = _read_steering()

        # Check for cleanup section
        assert "Cleanup" in content, (
            "Steering file should have a Cleanup section"
        )
        # Check for purge instructions
        assert "Purge" in content or "purge" in content, (
            "Steering file should contain purge instructions"
        )
        # Check for TruthSet purge specifics
        assert "zero TruthSet entities remain" in content, (
            "Steering file should specify zero TruthSet entities after purge"
        )
        # Check for test-only artifact message
        assert "test-only artifact" in content or "test-only" in content, (
            "Steering file should mention test-only artifacts"
        )

    def test_steering_file_references_module_completion(self) -> None:
        """Module close references module-completion.md.

        Validates: Requirement 11.4
        """
        content = _read_steering()

        assert "module-completion.md" in content, (
            "Steering file should reference module-completion.md workflow"
        )

    def test_onboarding_flow_references_updated(self) -> None:
        """Onboarding flow uses 'System Verification' name.

        Validates: Requirement 11.1
        """
        content = _read_onboarding_flow()

        assert "System Verification" in content, (
            "Onboarding flow should reference 'System Verification'"
        )
        # The old name should not appear as a track name
        # (it may appear in other contexts, so check the track section)
        lines = content.splitlines()
        track_lines = [
            line for line in lines
            if "Module" in line and "3" in line and "Quick Demo" in line
        ]
        assert len(track_lines) == 0, (
            "Onboarding flow should not reference Module 3 as 'Quick Demo'"
        )

    def test_build_commands_for_all_languages(self) -> None:
        """Build table has entries for all 5 languages.

        Validates: Requirements 4.1, 4.4
        """
        content = _read_steering()

        expected_languages = ["Python", "Java", "C#", "Rust", "TypeScript"]
        for lang in expected_languages:
            assert lang in content, (
                f"Steering file should mention language: {lang}"
            )

        # Verify specific build commands are present
        build_commands = {
            "py_compile": "Python",
            "javac": "Java",
            "dotnet build": "C#",
            "cargo build": "Rust",
            "tsc": "TypeScript",
        }
        for cmd, lang in build_commands.items():
            assert cmd in content, (
                f"Steering file should contain build command '{cmd}' for {lang}"
            )

    def test_verification_report_schema(self) -> None:
        """Report JSON structure matches expected schema.

        Validates: Requirement 10.5
        """
        content = _read_steering()

        # Find the full report schema JSON block (the one with timestamp)
        json_blocks = _extract_json_blocks(content)

        # Find the block that contains the full schema (has timestamp field)
        schema_block: str | None = None
        for block in json_blocks:
            if '"timestamp"' in block and '"module_3_verification"' in block:
                schema_block = block
                break

        assert schema_block is not None, (
            "Steering file should contain a full report schema JSON block "
            "with timestamp and module_3_verification"
        )

        # Clean up template placeholders so it parses as valid JSON
        cleaned = schema_block.replace(
            '"<ISO 8601 timestamp>"', '"2026-01-01T00:00:00Z"'
        )
        cleaned = cleaned.replace('"passed|failed"', '"passed"')
        cleaned = cleaned.replace('"verify_pipeline.[ext]"', '"verify_pipeline.py"')

        report = json.loads(cleaned)

        # Validate top-level structure
        assert "module_3_verification" in report
        verification = report["module_3_verification"]

        expected_top_keys = {"timestamp", "status", "checks", "fix_instructions"}
        assert set(verification.keys()) == expected_top_keys, (
            f"Report schema top-level keys should be {expected_top_keys}, "
            f"got {set(verification.keys())}"
        )

        # Validate all check names are present
        expected_checks = {
            "mcp_connectivity",
            "truthset_acquisition",
            "sdk_initialization",
            "code_generation",
            "build_compilation",
            "data_loading",
            "results_validation",
            "database_operations",
            "web_service",
            "web_page",
        }
        assert set(verification["checks"].keys()) == expected_checks, (
            f"Report schema check keys should be {expected_checks}, "
            f"got {set(verification['checks'].keys())}"
        )

        # Validate fix_instructions is a list
        assert isinstance(verification["fix_instructions"], list), (
            "fix_instructions should be a list"
        )
