"""Property-based and example-based tests for the merge-mapping-validation-hooks spec.

Validates that the merge of validate-senzing-json into analyze-after-mapping
was applied correctly: all 18 preserved hooks retain their category and registry
entries, README numbering is sequential, and validate-senzing-json is fully absent.

Feature: merge-mapping-validation-hooks
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_CATEGORIES_PATH = _HOOKS_DIR / "hook-categories.yaml"
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_REGISTRY_PATH = _STEERING_DIR / "hook-registry.md"
_README_PATH = _HOOKS_DIR / "README.md"
_INSTALL_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "install_hooks.py"
_POWER_MD_PATH = Path(__file__).resolve().parent.parent / "POWER.md"

# The 18 hook IDs preserved after both merges (validate-senzing-json and
# enforce-wait-after-question were removed).
PRESERVED_HOOK_IDS: list[str] = sorted([
    "analyze-after-mapping",
    "ask-bootcamper",
    "backup-before-load",
    "backup-project-on-request",
    "review-bootcamper-input",
    "code-style-check",
    "commonmark-validation",
    "data-quality-check",
    "deployment-phase-gate",
    "enforce-feedback-path",
    "enforce-visualization-offers",
    "enforce-working-directory",
    "git-commit-reminder",
    "offer-visualization",
    "run-tests-after-change",
    "validate-data-files",
    "verify-generated-code",
    "verify-senzing-facts",
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_categories_yaml(path: Path) -> dict[str, str]:
    """Parse hook-categories.yaml and return {hook_id: category_label}.

    Category label is 'critical' or 'module-N' (or 'module-any').
    Uses simple text parsing — no PyYAML dependency.
    """
    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    current_category: str | None = None
    current_module: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level keys (no leading whitespace)
        if not line[0].isspace():
            key = stripped.rstrip(":")
            if key == "critical":
                current_category = "critical"
                current_module = None
            elif key == "modules":
                current_category = "modules"
                current_module = None
            continue

        # Inside critical section — list items like "  - ask-bootcamper"
        if current_category == "critical" and stripped.startswith("- "):
            hook_id = stripped[2:].strip()
            result[hook_id] = "critical"
            continue

        # Inside modules section
        if current_category == "modules":
            # Module number lines like "  5:" or "  any:"
            mod_match = re.match(r"^(\d+|any)\s*:\s*$", stripped)
            if mod_match:
                current_module = mod_match.group(1)
                continue
            # Hook list items like "    - analyze-after-mapping"
            if stripped.startswith("- ") and current_module is not None:
                hook_id = stripped[2:].strip()
                result[hook_id] = f"module-{current_module}"
                continue

    return result


def _parse_registry_hook_ids(path: Path) -> set[str]:
    """Extract all hook IDs from hook-registry.md.

    Hook entries are formatted as either:
      **hook-id** (event → action)           — critical hooks
      **hook-id** — Module N (event → action) — module hooks
    """
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"\*\*([a-z][a-z0-9-]+)\*\*", text))


def _parse_readme_section_numbers(path: Path) -> list[int]:
    """Extract all ### N. section header numbers from hooks/README.md."""
    text = path.read_text(encoding="utf-8")
    return [int(m.group(1)) for m in re.finditer(r"^### (\d+)\.", text, re.MULTILINE)]


# ===========================================================================
# Task 7.2 — Property 1: Category preservation for non-removed hooks
#
# **Validates: Requirements 3.3**
# ===========================================================================


class TestCategoryPreservation:
    """Property test: every preserved hook retains its category assignment.

    For any hook ID in the preserved set, hook-categories.yaml still
    contains that hook with a valid category.

    **Validates: Requirements 3.3**
    """

    @given(hook_id=st.sampled_from(PRESERVED_HOOK_IDS))
    @settings(max_examples=100)
    def test_preserved_hook_has_category(self, hook_id: str) -> None:
        """Each preserved hook ID must appear in hook-categories.yaml.

        **Validates: Requirements 3.3**
        """
        categories = _parse_categories_yaml(_CATEGORIES_PATH)
        assert hook_id in categories, (
            f"Hook '{hook_id}' missing from hook-categories.yaml. "
            f"Present hooks: {sorted(categories.keys())}"
        )
        cat = categories[hook_id]
        assert cat.startswith("critical") or cat.startswith("module-"), (
            f"Hook '{hook_id}' has unexpected category '{cat}'. "
            f"Expected 'critical' or 'module-N'."
        )


# ===========================================================================
# Task 7.3 — Property 2: Registry entry preservation for non-removed hooks
#
# **Validates: Requirements 4.3**
# ===========================================================================


class TestRegistryPreservation:
    """Property test: every preserved hook has a registry entry.

    For any hook ID in the preserved set, hook-registry.md contains
    a section with the correct id.

    **Validates: Requirements 4.3**
    """

    @given(hook_id=st.sampled_from(PRESERVED_HOOK_IDS))
    @settings(max_examples=100)
    def test_preserved_hook_has_registry_entry(self, hook_id: str) -> None:
        """Each preserved hook ID must appear in hook-registry.md.

        **Validates: Requirements 4.3**
        """
        registry_ids = _parse_registry_hook_ids(_REGISTRY_PATH)
        assert hook_id in registry_ids, (
            f"Hook '{hook_id}' missing from hook-registry.md. "
            f"Present hooks: {sorted(registry_ids)}"
        )

        # Also verify the id field is present in the entry
        text = _REGISTRY_PATH.read_text(encoding="utf-8")
        id_pattern = rf"- id: `{re.escape(hook_id)}`"
        assert re.search(id_pattern, text), (
            f"Hook '{hook_id}' entry in hook-registry.md lacks "
            f"'- id: `{hook_id}`' field."
        )


# ===========================================================================
# Task 7.4 — Property 3: README hook numbering is sequential
#
# **Validates: Requirements 5.4**
# ===========================================================================


class TestReadmeNumbering:
    """Example-based test: README section numbers form a contiguous 1..N sequence.

    **Validates: Requirements 5.4**
    """

    def test_section_numbers_are_sequential(self) -> None:
        """README ### N. headers must form 1, 2, 3, ..., 18 with no gaps."""
        numbers = _parse_readme_section_numbers(_README_PATH)
        assert len(numbers) == 18, (
            f"Expected 18 hook sections in README, got {len(numbers)}: {numbers}"
        )
        expected = list(range(1, 19))
        assert numbers == expected, (
            f"README section numbers are not sequential.\n"
            f"Expected: {expected}\n"
            f"Got:      {numbers}"
        )


# ===========================================================================
# Task 7.5 — Example-based tests for validate-senzing-json absence
#
# **Validates: Requirements 2.1, 3.2, 4.2, 5.2, 6.2, 7.2**
# ===========================================================================


class TestValidateSenzingJsonAbsence:
    """Verify validate-senzing-json is fully removed from all artifacts.

    **Validates: Requirements 2.1, 3.2, 4.2, 5.2, 6.2, 7.2**
    """

    def test_hook_file_does_not_exist(self) -> None:
        """validate-senzing-json.kiro.hook must not exist.

        **Validates: Requirements 2.1**
        """
        hook_file = _HOOKS_DIR / "validate-senzing-json.kiro.hook"
        assert not hook_file.exists(), (
            f"Removed hook file still exists: {hook_file}"
        )

    def test_not_in_categories_yaml(self) -> None:
        """hook-categories.yaml must not reference validate-senzing-json.

        **Validates: Requirements 3.2**
        """
        text = _CATEGORIES_PATH.read_text(encoding="utf-8")
        assert "validate-senzing-json" not in text, (
            "hook-categories.yaml still contains 'validate-senzing-json'"
        )

    def test_not_in_hook_registry(self) -> None:
        """hook-registry.md must not reference validate-senzing-json.

        **Validates: Requirements 4.2**
        """
        text = _REGISTRY_PATH.read_text(encoding="utf-8")
        assert "validate-senzing-json" not in text, (
            "hook-registry.md still contains 'validate-senzing-json'"
        )

    def test_not_in_readme(self) -> None:
        """hooks/README.md must not contain a validate-senzing-json section.

        **Validates: Requirements 5.2**
        """
        text = _README_PATH.read_text(encoding="utf-8")
        assert "validate-senzing-json" not in text.lower(), (
            "hooks/README.md still contains 'validate-senzing-json'"
        )

    def test_not_in_install_script(self) -> None:
        """install_hooks.py must not reference validate-senzing-json.

        **Validates: Requirements 6.2**
        """
        text = _INSTALL_SCRIPT_PATH.read_text(encoding="utf-8")
        assert "validate-senzing-json" not in text, (
            "install_hooks.py still contains 'validate-senzing-json'"
        )

    def test_not_in_power_md(self) -> None:
        """POWER.md must not reference validate-senzing-json.

        **Validates: Requirements 7.2**
        """
        text = _POWER_MD_PATH.read_text(encoding="utf-8")
        assert "validate-senzing-json" not in text, (
            "POWER.md still contains 'validate-senzing-json'"
        )
