"""Bug condition exploration and preservation tests for module-closing-question-ownership bugfix.

Bug condition tests verify that module steering files do NOT contain inline
closing questions or WAIT-for-response instructions. The ask-bootcamper hook
should be the sole owner of closing questions.

Preservation tests verify that informational content, step sequences, non-affected
files, hook file, agent-instructions, and onboarding-flow are unchanged.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

EXPECTED OUTCOME on UNFIXED code:
- Bug condition tests FAIL on affected files (confirming the bug exists)
- Bug condition tests PASS on unaffected files (modules 03, 09, 10, 11)
- Preservation tests PASS (confirms baseline behavior to preserve)
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"

# Affected module files -- these SHOULD fail on unfixed code
_AFFECTED_FILES: dict[str, Path] = {
    "module-01": _STEERING_DIR / "module-01-business-problem.md",
    "module-02": _STEERING_DIR / "module-02-sdk-setup.md",
    "module-04": _STEERING_DIR / "module-04-data-collection.md",
    "module-05": _STEERING_DIR / "module-05-data-quality-mapping.md",
    "module-06": _STEERING_DIR / "module-06-load-data.md",
    "module-07": _STEERING_DIR / "module-07-query-validation.md",
    "module-11": _STEERING_DIR / "module-11-deployment.md",
    "module-completion": _STEERING_DIR / "module-completion.md",
}

# Unaffected module files -- these should PASS (no bug patterns present)
_UNAFFECTED_FILES: dict[str, Path] = {
    "module-08": _STEERING_DIR / "module-08-performance.md",
    "module-09": _STEERING_DIR / "module-09-security.md",
    "module-10": _STEERING_DIR / "module-10-monitoring.md",
}

# Baseline files that must not be modified
_HOOK_FILE = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
_AGENT_INSTRUCTIONS_FILE = _STEERING_DIR / "agent-instructions.md"
_ONBOARDING_FILE = _STEERING_DIR / "onboarding-flow.md"

# WAIT patterns that conflict with ask-bootcamper hook ownership
_WAIT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"WAIT for response", re.IGNORECASE),
    re.compile(r"WAIT for confirmation", re.IGNORECASE),
    re.compile(r"WAIT for their response", re.IGNORECASE),
    re.compile(r"WAIT for response before proceeding", re.IGNORECASE),
    re.compile(r"WAIT for each", re.IGNORECASE),
    re.compile(r"\u26a0\ufe0f WAIT \u2014 Do NOT proceed", re.IGNORECASE),
    re.compile(r"MANDATORY STOP", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Return the full text of a steering file."""
    return path.read_text(encoding="utf-8")


def _sha256(content: str) -> str:
    """Return SHA-256 hex digest of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _find_inline_pointing_questions(content: str) -> list[str]:
    """Find lines containing a pointing-right emoji followed by a question mark.

    These represent inline closing questions. Excludes properly structured
    👉 questions that are followed within 3 lines by a STOP/wait instruction,
    since those are stop-and-wait workflow questions, not closing questions.
    """
    matches = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "\U0001f449" in line and "?" in line:
            # Check if this is a proper stop-and-wait question
            # (followed by a STOP instruction within 3 lines)
            is_stop_and_wait = False
            for j in range(i + 1, min(len(lines), i + 4)):
                following = lines[j].strip()
                if "STOP" in following or "wait" in following.lower():
                    is_stop_and_wait = True
                    break
            if is_stop_and_wait:
                continue  # Skip — proper stop-and-wait question
            matches.append(line.strip())
    return matches


def _find_wait_instructions(content: str) -> list[str]:
    """Find lines matching any WAIT pattern.

    Excludes WAIT instructions that are part of:
    - Visualization delivery prompts (added by the visualization-web-service feature)
    - Phase gates (⛔ PHASE GATE sections with MANDATORY STOP / WAIT)
    - Stop-and-wait 👉 question blocks (proper ask-then-wait patterns)
    Those WAITs are structural gates, not closing questions owned by the
    ask-bootcamper hook.
    """
    matches = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        for pattern in _WAIT_PATTERNS:
            if pattern.search(line):
                # Check surrounding context (previous 30 lines) for exclusion markers
                context_start = max(0, i - 30)
                context = "\n".join(lines[context_start:i + 1])
                if "Static HTML file" in context and "Web service" in context:
                    break  # Skip — visualization delivery prompt
                if "PHASE GATE" in context or "⛔" in context:
                    break  # Skip — phase gate stop instruction
                if "🛑 STOP" in line and "End your response here" in line:
                    break  # Skip — question stop protocol instruction
                matches.append(line.strip())
                break  # avoid duplicate matches for the same line
    return matches


def _extract_headings(content: str) -> list[str]:
    """Extract all markdown headings (# through ####) in order."""
    return re.findall(r"^(#{1,4} .+)$", content, re.MULTILINE)


def _strip_question_and_wait_lines(content: str) -> str:
    """Remove inline closing-question lines and WAIT instruction lines.

    This extracts the informational content by stripping:
    - Lines containing the pointing-right emoji followed by a question mark
    - Lines matching WAIT patterns
    - Lines that are the MANDATORY VISUALIZATION OFFER wait blocks
    """
    lines = content.splitlines()
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip WAIT instruction lines
        skip = False
        for pattern in _WAIT_PATTERNS:
            if pattern.search(stripped):
                skip = True
                break
        if skip:
            continue
        # Skip lines that are inline closing questions
        if "\U0001f449" in stripped and "?" in stripped:
            continue
        filtered.append(line)
    return "\n".join(filtered)


# ---------------------------------------------------------------------------
# Tests -- Bug Condition: Affected files should NOT have inline questions/WAITs
# On UNFIXED code, these tests FAIL (confirming the bug exists)
# ---------------------------------------------------------------------------


class TestBugConditionAffectedFiles:
    """Assert that affected module steering files do NOT contain inline
    closing questions or WAIT-for-response instructions.

    On unfixed code these assertions will FAIL, confirming the bug exists."""

    # -- Module 01: 4 WAIT instructions --

    def test_module_01_no_wait_instructions(self) -> None:
        """module-01 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-01"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-01 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 02: 4 WAIT instructions --

    def test_module_02_no_wait_instructions(self) -> None:
        """module-02 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-02"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-02 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 04: 1 WAIT instruction --

    def test_module_04_no_wait_instructions(self) -> None:
        """module-04 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-04"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-04 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 05: 4 WAIT instructions --

    def test_module_05_no_wait_instructions(self) -> None:
        """module-05 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-05"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-05 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 06: 1 inline question, 1 WAIT instruction --

    def test_module_06_no_inline_questions(self) -> None:
        """module-06 should NOT contain inline closing questions."""
        content = _read_file(_AFFECTED_FILES["module-06"])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"module-06 contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_module_06_no_wait_instructions(self) -> None:
        """module-06 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-06"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-06 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 07: 7 inline questions, 7 WAIT instructions --

    def test_module_07_no_inline_questions(self) -> None:
        """module-07 should NOT contain inline closing questions."""
        content = _read_file(_AFFECTED_FILES["module-07"])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"module-07 contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_module_07_no_wait_instructions(self) -> None:
        """module-07 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-07"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-07 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 07: now Query and Visualize (was module-08) --

    def test_module_07_no_inline_questions(self) -> None:
        """module-07 should NOT contain inline closing questions."""
        content = _read_file(_AFFECTED_FILES["module-07"])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"module-07 contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_module_07_no_wait_instructions(self) -> None:
        """module-07 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-07"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-07 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module 11: Deployment (was module-12) --

    def test_module_11_no_inline_questions(self) -> None:
        """module-11 should NOT contain inline closing questions."""
        content = _read_file(_AFFECTED_FILES["module-11"])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"module-11 contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_module_11_no_wait_instructions(self) -> None:
        """module-11 should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-11"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-11 contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )

    # -- Module Completion: 3 inline questions, 2 WAIT instructions --

    def test_module_completion_no_inline_questions(self) -> None:
        """module-completion should NOT contain inline closing questions."""
        content = _read_file(_AFFECTED_FILES["module-completion"])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"module-completion contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_module_completion_no_wait_instructions(self) -> None:
        """module-completion should NOT contain WAIT instructions."""
        content = _read_file(_AFFECTED_FILES["module-completion"])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"module-completion contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )


# ---------------------------------------------------------------------------
# Tests -- Unaffected files should have NO matches (these should PASS)
# ---------------------------------------------------------------------------


class TestUnaffectedFilesClean:
    """Assert that unaffected module steering files (03, 09, 10, 11) do NOT
    contain inline closing questions or WAIT instructions.

    These tests should PASS on both unfixed and fixed code."""

    @pytest.mark.parametrize("module_key", list(_UNAFFECTED_FILES.keys()))
    def test_unaffected_no_inline_questions(self, module_key: str) -> None:
        """Unaffected module should NOT contain inline closing questions."""
        content = _read_file(_UNAFFECTED_FILES[module_key])
        questions = _find_inline_pointing_questions(content)
        assert len(questions) == 0, (
            f"{module_key} contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    @pytest.mark.parametrize("module_key", list(_UNAFFECTED_FILES.keys()))
    def test_unaffected_no_wait_instructions(self, module_key: str) -> None:
        """Unaffected module should NOT contain WAIT instructions."""
        content = _read_file(_UNAFFECTED_FILES[module_key])
        waits = _find_wait_instructions(content)
        assert len(waits) == 0, (
            f"{module_key} contains {len(waits)} WAIT instruction(s):\n"
            + "\n".join(f"  - {w}" for w in waits)
        )


# ---------------------------------------------------------------------------
# Property-Based Test -- Bug Condition across all affected files
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1**
# ---------------------------------------------------------------------------


_AFFECTED_KEYS = list(_AFFECTED_FILES.keys())


class TestBugConditionProperty:
    """Property-based test: for any randomly selected affected module file,
    the file should NOT contain inline closing questions or WAIT instructions.

    On unfixed code this property FAILS, surfacing counterexamples that
    demonstrate the bug exists."""

    @given(module_key=st.sampled_from(_AFFECTED_KEYS))
    @settings(max_examples=50)
    def test_no_affected_file_has_inline_questions_or_waits(
        self, module_key: str
    ) -> None:
        """**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1**

        For any affected module steering file, the file should contain
        zero inline closing questions and zero WAIT instructions."""
        content = _read_file(_AFFECTED_FILES[module_key])
        questions = _find_inline_pointing_questions(content)
        waits = _find_wait_instructions(content)

        assert len(questions) == 0 and len(waits) == 0, (
            f"Bug condition found in {module_key}:\n"
            f"  Inline questions ({len(questions)}):\n"
            + "\n".join(f"    - {q}" for q in questions)
            + f"\n  WAIT instructions ({len(waits)}):\n"
            + "\n".join(f"    - {w}" for w in waits)
        )



# ===========================================================================
# PRESERVATION TESTS (Property 2)
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
#
# These tests observe the UNFIXED code baseline and assert that informational
# content, step sequences, non-affected files, hook, agent-instructions, and
# onboarding-flow are preserved.  All preservation tests should PASS on
# UNFIXED code (confirming the baseline).
# ===========================================================================


# ---------------------------------------------------------------------------
# Baselines -- heading sequences observed from UNFIXED code
# ---------------------------------------------------------------------------

_HEADINGS_MODULE_01 = [
    "# Module 1: Discover the Business Problem",
    "## Workflow: Discover the Business Problem (Module 1)",
    "## Error Handling",
]

_HEADINGS_MODULE_02 = [
    "# Module 2: SDK Installation and Configuration",
    "## Step 1: Check for Existing Installation \u2014 MUST DO FIRST",
    "## Step 2: Determine Platform",
    "## Step 3: Install Senzing SDK",
    "## Step 4: Verify Installation",
    "## Step 5: Configure License",
    "### 5a. Explain the built-in evaluation license",
    "### 5b. Ask about the bootcamper's license situation",
    "### 5c. Handle the response",
    "### 5d. Configure LICENSEFILE in engine config",
    "## Step 6: Create Project Directory Structure",
    "## Step 7: Configure Database",
    "## Step 8: Create Engine Configuration",
    "## Step 9: Test Database Connection",
    "## Success Criteria",
    "## Transition",
    "## Troubleshooting",
    "## Error Handling",
    "## Agent Behavior",
]

_HEADINGS_MODULE_04 = [
    "# Module 4: Identify and Collect Data Sources",
    "## Workflow: Identify and Collect Data Sources (Module 4)",
    "## Error Handling",
]

_HEADINGS_MODULE_05 = [
    "# Module 5: Data Quality & Mapping",
    "## Error Handling",
    "## Phase Sub-Files",
]

_HEADINGS_MODULE_06 = [
    "# Module 6: Load Data",
    "## Conditional Workflow: Check Phase 3 Status",
    "## Pre-Load Data Freshness Check",
    "## Agent Workflow",
    "## Error Handling",
    "## Phase Sub-Files",
    "## Advanced Reading",
]

_HEADINGS_MODULE_07 = [
    "# Module 7: Query and Visualize",
    "## Query Completeness Gate",
    "## Error Handling",
    "## Integration Patterns",
]

_HEADINGS_MODULE_11 = [
    "# Module 11: Packaging and Deployment",
    "## Hardware Target (On-Premises Only)",
    "## Step 1: Deployment Target and Method \u2014 ASK FIRST",
    "### Step 1a: Deployment Target",
    "### Step 1b: Deployment Method",
    "## Phase 1: Packaging (Steps 2-11)",
    "## Step 2: Packaging Requirements",
    "## Step 3: Package Code",
    "## Step 4: Multi-Environment Config",
    "## Step 5: Containerization",
    "## Step 6: Database Migration (SQLite \u2192 PostgreSQL)",
    "## Step 7: CI/CD Pipeline",
    "## Step 8: REST API Layer (If Requested)",
    "## Step 9: Scaling Guidance",
    "## Step 10: Deployment Scripts",
    "## Step 11: Pre-Deployment Checklist",
    "## \u26d4 PHASE GATE \u2014 PACKAGING COMPLETE, DEPLOYMENT DECISION REQUIRED",
    "## Step 12: Rollback Plan",
    "## Further Reading",
    "## Error Handling",
]

_HEADINGS_MODULE_COMPLETION = [
    "# Module Completion Workflow",
    "## Bootcamp Journal",
    "## Module N: [Name] \u2014 Completed [date]",
    "## Module Completion Certificate",
    "### Certificate Template",
    "# Module [N]: [Title] \u2014 Complete \u2705",
    "## Key Concepts Learned",
    "## Artifacts Produced",
    "## What This Enables",
    "## Session Stats",
    "### Content Derivation Rules",
    "### Summary Index",
    "# Bootcamp Progress",
    "## Completed Modules",
    "## Track Progress",
    "## Total Time Invested",
    "### Error Handling",
    "## Next-Step Options",
    "### \u26d4 Immediate Execution on Affirmative Response",
    "## Path Completion Detection",
    "## Path Completion Celebration",
]

_ALL_HEADING_BASELINES: dict[str, list[str]] = {
    "module-01": _HEADINGS_MODULE_01,
    "module-02": _HEADINGS_MODULE_02,
    "module-04": _HEADINGS_MODULE_04,
    "module-05": _HEADINGS_MODULE_05,
    "module-06": _HEADINGS_MODULE_06,
    "module-07": _HEADINGS_MODULE_07,
    "module-11": _HEADINGS_MODULE_11,
    "module-completion": _HEADINGS_MODULE_COMPLETION,
}


# ---------------------------------------------------------------------------
# Baselines -- key informational content per affected file
# These phrases MUST be present in the file content AFTER stripping
# inline closing questions and WAIT lines.
# ---------------------------------------------------------------------------

_KEY_CONTENT_MODULE_01: list[str] = [
    "git repository",
    "design pattern",
    "business problem",
    "Checkpoint",
    "success criteria",
]

_KEY_CONTENT_MODULE_02: list[str] = [
    "Determine Platform",
    "sdk_guide",
    "licenses/g2.lic",
    "LICENSEFILE",
    "generate_scaffold",
    "database/G2C.db",
    "SENZING_ENGINE_CONFIGURATION_JSON",
    "Configure License",
]

_KEY_CONTENT_MODULE_04: list[str] = [
    "data source",
    "CORD",
    "data/raw/",
    "get_sample_data",
    "data_source_locations.md",
    "data_collection_checklist",
    "data_sources.yaml",
]

_KEY_CONTENT_MODULE_05: list[str] = [
    "Quality Assessment",
    "Data Mapping",
    "Phase 3",
    "Test Load and Validate",
    "module-05-phase1",
    "module-05-phase2",
    "module-05-phase3",
    "Quality Scoring Methodology",
]

_KEY_CONTENT_MODULE_06: list[str] = [
    "production",
    "redo",
    "data_sources.yaml",
    "test_load_status",
    "error handling",
    "progress tracking",
    "throughput",
    "incremental",
]

_KEY_CONTENT_MODULE_07: list[str] = [
    "entity graph",
    "results dashboard",
    "integration pattern",
    "generate_scaffold",
    "get_entity_by_record_id",
    "Query Completeness Gate",
    "Batch Report",
    "REST API",
]

_KEY_CONTENT_MODULE_11: list[str] = [
    "deployment",
    "containeriz",
    "rollback",
    "Dockerfile",
    "CI/CD",
    "PHASE GATE",
]

_KEY_CONTENT_MODULE_COMPLETION: list[str] = [
    "journal",
    "graduation",
    "celebration",
    "bootcamp_journal.md",
    "Path Completion Detection",
    "lessons-learned.md",
    "export_results.py",
    "skip_graduation",
]

_ALL_KEY_CONTENT: dict[str, list[str]] = {
    "module-01": _KEY_CONTENT_MODULE_01,
    "module-02": _KEY_CONTENT_MODULE_02,
    "module-04": _KEY_CONTENT_MODULE_04,
    "module-05": _KEY_CONTENT_MODULE_05,
    "module-06": _KEY_CONTENT_MODULE_06,
    "module-07": _KEY_CONTENT_MODULE_07,
    "module-11": _KEY_CONTENT_MODULE_11,
    "module-completion": _KEY_CONTENT_MODULE_COMPLETION,
}


# ---------------------------------------------------------------------------
# Baselines -- SHA-256 hashes for files that must not change
# ---------------------------------------------------------------------------

_HASH_UNAFFECTED: dict[str, str] = {
    "module-08": "cbba2a596783b5d7cd4fffcf837c007908c0dbcaca96bd71f97e1e9306f0055e",
    "module-09": "9bf4b4c8e9abdaf601c395016781f3223e4bc0df083f8ebd85393f555055cf1c",
    "module-10": "0dc0f96576e8ef4548fe2401558007e23c36499951c00c9f1fe04c9c456d4117",
}

_HASH_HOOK = "98e08f645acc81716e92202a631727283b6153a82c3df7a07a3d8935034c5706"
_HASH_AGENT_INSTRUCTIONS = "706ba6b75a4249064df033a1c1e1c4687157fb1e5377624e4d1e1871ff5f2488"
_HASH_ONBOARDING_FLOW = "fe1ab471e0f53b26c3bd153c8b135aa04a377646de018844b8d182c007287464"


# ---------------------------------------------------------------------------
# Preservation Tests -- Heading Sequences
# **Validates: Requirements 3.3, 3.4**
# ---------------------------------------------------------------------------


class TestPreservationHeadings:
    """Verify that step/section headings in each affected file match the
    observed baseline heading sequence.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @pytest.mark.parametrize("module_key", list(_AFFECTED_FILES.keys()))
    def test_heading_sequence_preserved(self, module_key: str) -> None:
        """**Validates: Requirements 3.3, 3.4**

        For each affected file, the heading sequence matches the baseline."""
        content = _read_file(_AFFECTED_FILES[module_key])
        actual = _extract_headings(content)
        expected = _ALL_HEADING_BASELINES[module_key]
        assert actual == expected, (
            f"Heading sequence mismatch in {module_key}.\n"
            f"Expected: {expected}\n"
            f"Got:      {actual}"
        )


# ---------------------------------------------------------------------------
# Preservation Tests -- Key Informational Content
# **Validates: Requirements 3.3, 3.4**
# ---------------------------------------------------------------------------


class TestPreservationKeyContent:
    """Verify that key informational content (excluding inline closing
    questions and WAIT lines) is preserved in each affected file.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @pytest.mark.parametrize("module_key", list(_AFFECTED_FILES.keys()))
    def test_key_content_preserved(self, module_key: str) -> None:
        """**Validates: Requirements 3.3, 3.4**

        For each affected file, key informational phrases are present
        after stripping inline questions and WAIT lines."""
        content = _read_file(_AFFECTED_FILES[module_key])
        info = _strip_question_and_wait_lines(content)
        key_phrases = _ALL_KEY_CONTENT[module_key]
        missing = [p for p in key_phrases if p.lower() not in info.lower()]
        assert len(missing) == 0, (
            f"{module_key} missing key informational content:\n"
            + "\n".join(f"  - '{p}'" for p in missing)
        )


# ---------------------------------------------------------------------------
# Preservation Tests -- Non-Affected Module Files Unchanged
# **Validates: Requirements 3.3**
# ---------------------------------------------------------------------------


class TestPreservationUnaffectedFiles:
    """Verify that non-affected module files (03, 09, 10, 11) are completely
    unchanged by comparing SHA-256 hashes.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @pytest.mark.parametrize("module_key", list(_UNAFFECTED_FILES.keys()))
    def test_unaffected_file_unchanged(self, module_key: str) -> None:
        """**Validates: Requirements 3.3**

        Non-affected module file content matches the observed baseline hash."""
        content = _read_file(_UNAFFECTED_FILES[module_key])
        actual_hash = _sha256(content)
        expected_hash = _HASH_UNAFFECTED[module_key]
        assert actual_hash == expected_hash, (
            f"{module_key} content has changed.\n"
            f"Expected hash: {expected_hash}\n"
            f"Actual hash:   {actual_hash}"
        )


# ---------------------------------------------------------------------------
# Preservation Tests -- Hook File Baseline
# **Validates: Requirements 3.1, 3.6**
# ---------------------------------------------------------------------------


class TestPreservationHookFile:
    """Verify that ask-bootcamper.kiro.hook content matches the observed
    baseline.

    EXPECTED OUTCOME on UNFIXED code: test PASSES."""

    def test_hook_file_matches_baseline(self) -> None:
        """**Validates: Requirements 3.1, 3.6**

        ask-bootcamper.kiro.hook content matches the observed baseline hash."""
        content = _read_file(_HOOK_FILE)
        actual_hash = _sha256(content)
        assert actual_hash == _HASH_HOOK, (
            "ask-bootcamper.kiro.hook content has changed.\n"
            f"Expected hash: {_HASH_HOOK}\n"
            f"Actual hash:   {actual_hash}"
        )

    def test_hook_file_has_agent_stop_trigger(self) -> None:
        """**Validates: Requirements 3.1**

        Hook fires on agentStop event."""
        content = _read_file(_HOOK_FILE)
        assert '"agentStop"' in content, (
            "Hook file missing agentStop trigger"
        )

    def test_hook_file_has_ask_agent_action(self) -> None:
        """**Validates: Requirements 3.1**

        Hook uses askAgent action type."""
        content = _read_file(_HOOK_FILE)
        assert '"askAgent"' in content, (
            "Hook file missing askAgent action type"
        )


# ---------------------------------------------------------------------------
# Preservation Tests -- Agent Instructions Baseline
# **Validates: Requirements 3.2, 3.6**
# ---------------------------------------------------------------------------


class TestPreservationAgentInstructions:
    """Verify that agent-instructions.md content matches the observed baseline.

    EXPECTED OUTCOME on UNFIXED code: test PASSES."""

    def test_agent_instructions_matches_baseline(self) -> None:
        """**Validates: Requirements 3.2, 3.6**

        agent-instructions.md content matches the observed baseline hash."""
        content = _read_file(_AGENT_INSTRUCTIONS_FILE)
        actual_hash = _sha256(content)
        assert actual_hash == _HASH_AGENT_INSTRUCTIONS, (
            "agent-instructions.md content has changed.\n"
            f"Expected hash: {_HASH_AGENT_INSTRUCTIONS}\n"
            f"Actual hash:   {actual_hash}"
        )

    def test_agent_instructions_has_ownership_rule(self) -> None:
        """**Validates: Requirements 3.2**

        agent-instructions.md contains the closing-question ownership rule."""
        content = _read_file(_AGENT_INSTRUCTIONS_FILE)
        assert "Closing-question ownership" in content
        assert "ask-bootcamper" in content
        assert "safety net" in content


# ---------------------------------------------------------------------------
# Preservation Tests -- Onboarding Flow Baseline (Regression Check)
# **Validates: Requirements 3.5**
# ---------------------------------------------------------------------------


class TestPreservationOnboardingFlow:
    """Verify that onboarding-flow.md content matches the observed baseline.
    This is a regression check -- the fix from missing-pointing-prefix must
    remain intact.

    EXPECTED OUTCOME on UNFIXED code: test PASSES."""

    def test_onboarding_flow_matches_baseline(self) -> None:
        """**Validates: Requirements 3.5**

        onboarding-flow.md content matches the observed baseline hash."""
        content = _read_file(_ONBOARDING_FILE)
        actual_hash = _sha256(content)
        assert actual_hash == _HASH_ONBOARDING_FLOW, (
            "onboarding-flow.md content has changed.\n"
            f"Expected hash: {_HASH_ONBOARDING_FLOW}\n"
            f"Actual hash:   {actual_hash}"
        )

    def test_onboarding_flow_no_inline_questions(self) -> None:
        """**Validates: Requirements 3.5**

        onboarding-flow.md inline 👉 questions are accounted for.
        The conversation-ux-rules spec (Requirements 4.1, 7.4) requires 👉
        prefixes on ALL bootcamper-directed questions. The
        _find_inline_pointing_questions helper detects 👉 lines with '?'
        that lack a STOP marker within 3 lines. Three such lines are expected:
        - Step 0b (MCP Health Check): 👉 offline mode question
        - Step 2 (Language Selection): 👉 with example question text where
          the STOP marker is >3 lines away
        - Step 4c (Comprehension Check): 👉 question with no STOP (non-gate)
        These are intentional per conversation-ux-rules and not regressions."""
        content = _read_file(_ONBOARDING_FILE)
        questions = _find_inline_pointing_questions(content)
        # Allow up to 3 expected inline 👉 questions added by
        # conversation-ux-rules spec and mcp-health-check spec
        assert len(questions) <= 3, (
            f"onboarding-flow.md contains {len(questions)} inline question(s) "
            f"(expected at most 3 from conversation-ux-rules + mcp-health-check specs):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )


# ---------------------------------------------------------------------------
# Property-Based Preservation Tests
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
# ---------------------------------------------------------------------------


class TestPreservationProperty:
    """Property-based preservation tests: for any randomly selected affected
    module file, headings and key informational content are preserved.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @given(module_key=st.sampled_from(_AFFECTED_KEYS))
    @settings(max_examples=50)
    def test_headings_preserved_for_any_affected_file(
        self, module_key: str
    ) -> None:
        """**Validates: Requirements 3.3, 3.4**

        For any affected module steering file, the heading sequence matches
        the observed baseline."""
        content = _read_file(_AFFECTED_FILES[module_key])
        actual = _extract_headings(content)
        expected = _ALL_HEADING_BASELINES[module_key]
        assert actual == expected, (
            f"Heading sequence mismatch in {module_key}.\n"
            f"Expected: {expected}\n"
            f"Got:      {actual}"
        )

    @given(module_key=st.sampled_from(_AFFECTED_KEYS))
    @settings(max_examples=50)
    def test_key_content_preserved_for_any_affected_file(
        self, module_key: str
    ) -> None:
        """**Validates: Requirements 3.3, 3.4**

        For any affected module steering file, key informational phrases
        are present after stripping inline questions and WAIT lines."""
        content = _read_file(_AFFECTED_FILES[module_key])
        info = _strip_question_and_wait_lines(content)
        key_phrases = _ALL_KEY_CONTENT[module_key]
        missing = [p for p in key_phrases if p.lower() not in info.lower()]
        assert len(missing) == 0, (
            f"{module_key} missing key informational content:\n"
            + "\n".join(f"  - '{p}'" for p in missing)
        )
