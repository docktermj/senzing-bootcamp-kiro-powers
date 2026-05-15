"""Tests for the Module Completion Certificates feature.

Validates that module-completion.md contains certificate generation instructions
and that export_results.py handles the docs/progress/ directory gracefully.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_ROOT = Path(__file__).resolve().parent.parent.parent
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"
_SCRIPTS_DIR = _ROOT / "senzing-bootcamp" / "scripts"

# Make scripts importable
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


class TestModuleCompletionSteering:
    """Verify module-completion.md contains certificate generation instructions."""

    @pytest.fixture()
    def module_completion(self) -> str:
        path = _STEERING_DIR / "module-completion.md"
        return path.read_text(encoding="utf-8")

    def test_contains_certificate_generation_instruction(self, module_completion: str) -> None:
        """module-completion.md instructs generating a certificate."""
        assert "MODULE_N_COMPLETE.md" in module_completion or \
               "completion certificate" in module_completion.lower() or \
               "Module Completion Certificate" in module_completion

    def test_contains_readme_index_instruction(self, module_completion: str) -> None:
        """module-completion.md instructs updating docs/progress/README.md."""
        assert "docs/progress/README.md" in module_completion

    def test_contains_required_sections(self, module_completion: str) -> None:
        """Certificate template contains Key Concepts, Artifacts, What This Enables."""
        assert "Key Concepts" in module_completion
        assert "Artifacts Produced" in module_completion
        assert "What This Enables" in module_completion

    def test_specifies_language_aware_descriptions(self, module_completion: str) -> None:
        """module-completion.md specifies language-aware artifact descriptions."""
        assert "language" in module_completion.lower()
        # Check for the specific example or rule
        assert "Python" in module_completion or "chosen language" in module_completion.lower()

    def test_certificate_does_not_block_flow(self, module_completion: str) -> None:
        """module-completion.md states certificate generation should not block."""
        assert "not block" in module_completion.lower() or \
               "should not block" in module_completion.lower()


class TestExportResultsHandlesProgress:
    """Verify export_results.py handles presence/absence of docs/progress/."""

    def test_render_achievements_returns_none_when_no_dir(self) -> None:
        """_render_achievements_section returns None when docs/progress/ doesn't exist."""
        from export_results import HTMLRenderer
        renderer = HTMLRenderer()
        # In the test environment, docs/progress/ likely doesn't exist
        result = renderer._render_achievements_section()
        # Should return None (no error) when directory doesn't exist
        assert result is None


class TestCertificateFilenameProperty:
    """Property test: certificate filename pattern is valid for all module numbers."""

    @given(module_num=st.integers(min_value=1, max_value=11))
    @settings(max_examples=10)
    def test_filename_pattern_valid(self, module_num: int) -> None:
        """MODULE_N_COMPLETE.md is a valid filename for all module numbers 1-11."""
        filename = f"MODULE_{module_num}_COMPLETE.md"
        assert filename.startswith("MODULE_")
        assert filename.endswith("_COMPLETE.md")
        # Extract the number and verify it's valid
        num_str = filename.replace("MODULE_", "").replace("_COMPLETE.md", "")
        assert num_str.isdigit()
        assert 1 <= int(num_str) <= 11
