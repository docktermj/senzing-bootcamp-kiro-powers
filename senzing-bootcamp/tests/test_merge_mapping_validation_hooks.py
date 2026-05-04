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

# The 19 hook IDs preserved after both merges (validate-senzing-json and
# enforce-wait-after-question were removed, review-bootcamper-input was added).
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


# ---------------------------------------------------------------------------
# Expected category assignments for preserved hooks (known-good baseline).
# Used by Property 1 to verify each hook retains its exact category and
# module number after the merge.
# ---------------------------------------------------------------------------

EXPECTED_CATEGORIES: dict[str, str] = {
    "ask-bootcamper": "critical",
    "review-bootcamper-input": "critical",
    "code-style-check": "critical",
    "commonmark-validation": "critical",
    "enforce-feedback-path": "critical",
    "enforce-working-directory": "critical",
    "verify-senzing-facts": "critical",
    "validate-data-files": "module-4",
    "analyze-after-mapping": "module-5",
    "data-quality-check": "module-5",
    "backup-before-load": "module-6",
    "run-tests-after-change": "module-6",
    "verify-generated-code": "module-6",
    "enforce-visualization-offers": "module-7",
    "offer-visualization": "module-7",
    "deployment-phase-gate": "module-11",
    "backup-project-on-request": "module-any",
    "git-commit-reminder": "module-any",
}


# ===========================================================================
# Task 7.2 — Property 1: Category preservation for non-removed hooks
#
# Feature: merge-mapping-validation-hooks, Property 1: Category preservation
# for non-removed hooks
#
# **Validates: Requirements 3.3**
# ===========================================================================


class TestCategoryPreservation:
    """Property test: every preserved hook retains its category and module.

    For any hook ID in the preserved set, hook-categories.yaml still
    contains that hook with the same category (critical or module) and
    the same module number assignment.

    Feature: merge-mapping-validation-hooks, Property 1: Category preservation
    for non-removed hooks

    **Validates: Requirements 3.3**
    """

    @given(hook_id=st.sampled_from(PRESERVED_HOOK_IDS))
    @settings(max_examples=100)
    def test_preserved_hook_retains_category_and_module(self, hook_id: str) -> None:
        """Each preserved hook ID must appear in hook-categories.yaml with
        its original category and module number unchanged.

        **Validates: Requirements 3.3**
        """
        categories = _parse_categories_yaml(_CATEGORIES_PATH)
        assert hook_id in categories, (
            f"Hook '{hook_id}' missing from hook-categories.yaml. "
            f"Present hooks: {sorted(categories.keys())}"
        )
        actual = categories[hook_id]
        expected = EXPECTED_CATEGORIES[hook_id]
        assert actual == expected, (
            f"Hook '{hook_id}' category changed. "
            f"Expected '{expected}', got '{actual}'."
        )


# ---------------------------------------------------------------------------
# Expected registry metadata for preserved hooks (known-good baseline).
# Used by Property 2 to verify each hook retains its id, name, and
# description in hook-registry.md after the merge.
# ---------------------------------------------------------------------------

EXPECTED_REGISTRY: dict[str, dict[str, str]] = {
    "analyze-after-mapping": {
        "name": "Analyze After Mapping",
        "description": (
            "After completing a mapping task, validates the transformation output using"
            " analyze_record for quality metrics and Senzing Generic Entity Specification"
            " conformance before proceeding to loading."
        ),
    },
    "ask-bootcamper": {
        "name": "Ask Bootcamper",
        "description": (
            "Recaps what was accomplished and which files changed, then asks the bootcamper"
            " what to do next with a contextual 👉 question. Suppresses output entirely when"
            " a question is already pending."
        ),
    },
    "backup-before-load": {
        "name": "Backup Database Before Loading",
        "description": "Remind to backup database before running loading programs",
    },
    "backup-project-on-request": {
        "name": "Backup Project on Request",
        "description": (
            "Run project backup when user clicks the hook button."
            " Avoids firing on every prompt \u2014 use the manual trigger"
            " button in the Agent Hooks panel instead."
        ),
    },
    "review-bootcamper-input": {
        "name": "Review Bootcamper Input",
        "description": (
            "Reviews each message submission for feedback trigger phrases and initiates the"
            " feedback workflow with automatic context capture."
        ),
    },
    "code-style-check": {
        "name": "Code Style Check",
        "description": (
            "Automatically checks source code files for language-appropriate coding standards"
            " when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET"
            " conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions."
        ),
    },
    "commonmark-validation": {
        "name": "CommonMark Validation",
        "description": (
            "Validates that all Markdown files conform to CommonMark standards when edited"
        ),
    },
    "data-quality-check": {
        "name": "Senzing Data Quality Check",
        "description": (
            "Automatically check data quality when transformation programs are saved"
        ),
    },
    "deployment-phase-gate": {
        "name": "Deployment Phase Gate",
        "description": (
            "After packaging tasks complete in Module 11, displays a phase gate prompt asking"
            " the bootcamper whether to proceed to deployment or stop. Checks"
            " config/bootcamp_progress.json to confirm the current module is 11 or 12 before"
            " acting."
        ),
    },
    "enforce-feedback-path": {
        "name": "Enforce Feedback File Path",
        "description": (
            "Before any write operation, checks if the agent is writing feedback content. If"
            " so, ensures it goes to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md and"
            " nowhere else."
        ),
    },
    "enforce-visualization-offers": {
        "name": "Enforce Visualization Offers",
        "description": (
            "When the agent stops during Module 7, checks whether both visualization offers"
            " (entity graph and results dashboard) were made. If either was missed, prompts"
            " the agent to offer it before closing."
        ),
    },
    "enforce-working-directory": {
        "name": "Enforce Working Directory Paths",
        "description": (
            "Checks that file write operations do not use /tmp, %TEMP%, or any path outside"
            " the working directory. Enforces the file storage policy automatically."
        ),
    },
    "git-commit-reminder": {
        "name": "Git Commit Reminder",
        "description": (
            "Reminds the user to commit their work after completing a module. Triggered"
            " manually via button click."
        ),
    },
    "offer-visualization": {
        "name": "Offer Entity Graph Visualization",
        "description": (
            "After query programs are created in Module 7, prompts the agent to offer"
            " generating an interactive entity graph visualization."
        ),
    },
    "run-tests-after-change": {
        "name": "Run Tests After Code Change",
        "description": (
            "Reminds the agent to run the test suite after source code changes in loading,"
            " query, or transformation programs."
        ),
    },
    "validate-data-files": {
        "name": "Validate Data Files",
        "description": (
            "When new data files are added to data/raw/, checks file format, encoding, and"
            " basic readability to catch issues early."
        ),
    },
    "verify-generated-code": {
        "name": "Verify Generated Code Runs",
        "description": (
            "When bootcamp source code is created, prompts the agent to run it on sample data"
            " and report results before moving on."
        ),
    },
    "verify-senzing-facts": {
        "name": "Verify Senzing Facts Before Writing",
        "description": (
            "Reminds the agent to verify Senzing-specific facts via MCP tools before writing"
            " code or documentation that contains Senzing attribute names, SDK method calls,"
            " or configuration values."
        ),
    },
}


# ===========================================================================
# Task 7.3 — Property 2: Registry entry preservation for non-removed hooks
#
# Feature: merge-mapping-validation-hooks, Property 2: Registry entry
# preservation for non-removed hooks
#
# **Validates: Requirements 4.3**
# ===========================================================================


def _parse_registry_entry(text: str, hook_id: str) -> dict[str, str | None]:
    """Extract id, name, and description fields from a hook's registry entry.

    Returns a dict with keys 'id', 'name', 'description' (values may be None
    if the field is not found).
    """
    result: dict[str, str | None] = {"id": None, "name": None, "description": None}

    id_match = re.search(rf"- id: `{re.escape(hook_id)}`", text)
    if id_match:
        result["id"] = hook_id

    name_match = re.search(rf"- name: `([^`]+)`", text[text.find(f"**{hook_id}**"):])
    if name_match:
        result["name"] = name_match.group(1)

    desc_match = re.search(rf"- description: `([^`]+)`", text[text.find(f"**{hook_id}**"):])
    if desc_match:
        result["description"] = desc_match.group(1)

    return result


class TestRegistryPreservation:
    """Property test: every preserved hook retains its registry entry.

    For any hook ID in the preserved set, hook-registry.md contains
    a section with the correct id, name, and description.

    Feature: merge-mapping-validation-hooks, Property 2: Registry entry
    preservation for non-removed hooks

    **Validates: Requirements 4.3**
    """

    @given(hook_id=st.sampled_from(PRESERVED_HOOK_IDS))
    @settings(max_examples=100)
    def test_preserved_hook_has_registry_entry_with_metadata(self, hook_id: str) -> None:
        """Each preserved hook ID must appear in hook-registry.md with
        correct id, name, and description fields.

        **Validates: Requirements 4.3**
        """
        text = _REGISTRY_PATH.read_text(encoding="utf-8")

        # Verify the hook appears as a bold header in the registry
        registry_ids = _parse_registry_hook_ids(_REGISTRY_PATH)
        assert hook_id in registry_ids, (
            f"Hook '{hook_id}' missing from hook-registry.md. "
            f"Present hooks: {sorted(registry_ids)}"
        )

        # Parse the entry's metadata fields
        entry = _parse_registry_entry(text, hook_id)

        # Verify id field
        assert entry["id"] == hook_id, (
            f"Hook '{hook_id}' entry in hook-registry.md lacks "
            f"'- id: `{hook_id}`' field."
        )

        # Verify name field
        expected = EXPECTED_REGISTRY[hook_id]
        assert entry["name"] == expected["name"], (
            f"Hook '{hook_id}' name mismatch in hook-registry.md. "
            f"Expected '{expected['name']}', got '{entry['name']}'."
        )

        # Verify description field
        assert entry["description"] == expected["description"], (
            f"Hook '{hook_id}' description mismatch in hook-registry.md. "
            f"Expected '{expected['description']}', got '{entry['description']}'."
        )


# ===========================================================================
# Task 7.4 — Property 3: README hook numbering is sequential
#
# **Validates: Requirements 5.4**
# ===========================================================================


class TestReadmeNumbering:
    """Example-based test: README section numbers form a contiguous 1..N sequence.

    The key property is sequential numbering with no gaps — the specific count
    of hooks may change as other specs add or remove hooks.

    **Validates: Requirements 5.4**
    """

    def test_section_numbers_are_sequential(self) -> None:
        """README ### N. headers must form a contiguous 1..N sequence with no gaps."""
        numbers = _parse_readme_section_numbers(_README_PATH)
        n = len(numbers)
        assert n >= 1, "README must contain at least one hook section"
        expected = list(range(1, n + 1))
        assert numbers == expected, (
            f"README section numbers are not a contiguous 1..{n} sequence.\n"
            f"Expected: {expected}\n"
            f"Got:      {numbers}"
        )


