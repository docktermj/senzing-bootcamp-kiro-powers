"""Bug condition exploration and preservation tests for module2-license-question bugfix.

Bug condition tests verify that Module 2 Step 5 (Configure License) does NOT
contain inline questions that gate license information behind conditionals.
The ask-bootcamper hook should generate the closing question; Step 5 should
present license information as unconditional content.

Preservation tests verify that license mechanics, other steps, and key content
in Step 5 remain unchanged after the fix.

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

EXPECTED OUTCOME on UNFIXED code:
- Bug condition tests FAIL (confirming the bug exists — Step 5 has inline questions)
- Preservation tests PASS (confirms baseline behavior to preserve)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_MODULE_02_FILE = _STEERING_DIR / "module-02-sdk-setup.md"

# Inline question patterns specific to Step 5's bug
_INLINE_QUESTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"Do you have a Senzing license", re.IGNORECASE),
    re.compile(r"Use this one\?", re.IGNORECASE),
    re.compile(r"I found a license at \[location\]\. Use this one\?", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Return the full text of a steering file."""
    return path.read_text(encoding="utf-8")


def _extract_step5(content: str) -> str:
    """Extract the Step 5 (Configure License) section from module-02-sdk-setup.md.

    Returns the text from '## Step 5: Configure License' up to the next
    '## Step' heading (exclusive).
    """
    pattern = re.compile(
        r"(## Step 5: Configure License.*?)(?=\n## (?:Step \d|Success Criteria|Transition|Troubleshooting|Agent Behavior))",
        re.DOTALL,
    )
    match = pattern.search(content)
    assert match is not None, "Could not find '## Step 5: Configure License' section"
    return match.group(1)


def _find_inline_questions(content: str) -> list[str]:
    """Find lines matching inline question patterns specific to Step 5."""
    matches = []
    for line in content.splitlines():
        for pattern in _INLINE_QUESTION_PATTERNS:
            if pattern.search(line):
                matches.append(line.strip())
                break
    return matches


def _extract_all_steps(content: str) -> dict[str, str]:
    """Extract all step sections from the module file.

    Returns a dict mapping step identifiers (e.g., 'Step 1', 'Step 5') to
    their full section content.
    """
    steps: dict[str, str] = {}
    # Match ## Step N: ... sections
    step_pattern = re.compile(
        r"(## (Step \d+):[^\n]*\n.*?)(?=\n## (?:Step \d|Success Criteria|Transition|Troubleshooting|Agent Behavior))",
        re.DOTALL,
    )
    for match in step_pattern.finditer(content):
        step_key = match.group(2)  # e.g., "Step 1"
        steps[step_key] = match.group(1)
    return steps


# ===========================================================================
# BUG CONDITION EXPLORATION TESTS (Task 1)
# **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2**
#
# These tests assert the EXPECTED behavior: Step 5 should NOT contain
# inline questions and SHOULD present license info unconditionally.
# On UNFIXED code, these tests FAIL — confirming the bug exists.
# ===========================================================================


class TestBugConditionStep5:
    """Assert that Step 5 does NOT contain inline questions that gate
    license information behind conditionals.

    On unfixed code these assertions will FAIL, confirming the bug exists."""

    def test_step5_no_inline_question_do_you_have(self) -> None:
        """**Validates: Requirements 1.1, 1.2**

        Step 5 should NOT contain 'Do you have a Senzing license' inline question."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        pattern = re.compile(r"Do you have a Senzing license", re.IGNORECASE)
        matches = [line.strip() for line in step5.splitlines() if pattern.search(line)]
        assert len(matches) == 0, (
            f"Step 5 contains inline question 'Do you have a Senzing license':\n"
            + "\n".join(f"  - {m}" for m in matches)
        )

    def test_step5_no_inline_question_use_this_one(self) -> None:
        """**Validates: Requirements 1.3, 2.2**

        Step 5 should NOT contain 'Use this one?' inline question."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        pattern = re.compile(r"Use this one\?", re.IGNORECASE)
        matches = [line.strip() for line in step5.splitlines() if pattern.search(line)]
        assert len(matches) == 0, (
            f"Step 5 contains inline question 'Use this one?':\n"
            + "\n".join(f"  - {m}" for m in matches)
        )

    def test_step5_no_inline_questions_combined(self) -> None:
        """**Validates: Requirements 1.1, 1.2, 1.3, 2.2**

        Step 5 should NOT contain any inline question patterns."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        questions = _find_inline_questions(step5)
        assert len(questions) == 0, (
            f"Step 5 contains {len(questions)} inline question(s):\n"
            + "\n".join(f"  - {q}" for q in questions)
        )

    def test_step5_presents_evaluation_license_info_unconditionally(self) -> None:
        """**Validates: Requirements 2.1**

        Step 5 should present evaluation license info (500 records) as
        unconditional content, not gated behind a question."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        # The evaluation license info (500 records) should be presented as
        # standalone content, not embedded inside a question string.
        # On unfixed code, "500 records" appears only inside the question text:
        #   "Do you have a Senzing license file or BASE64 key? If not, the SDK
        #    works with evaluation limits (500 records)."
        # We check that 500-record info exists AND is NOT inside a question line.
        has_500_records = "500 record" in step5.lower() or "500-record" in step5.lower()
        assert has_500_records, "Step 5 does not mention evaluation license 500-record limit"

        # Check that the 500-record info is NOT only inside a question line
        lines_with_500 = [
            line.strip()
            for line in step5.splitlines()
            if "500 record" in line.lower() or "500-record" in line.lower()
        ]
        question_lines_with_500 = [
            line for line in lines_with_500
            if any(p.search(line) for p in _INLINE_QUESTION_PATTERNS)
        ]
        non_question_lines_with_500 = [
            line for line in lines_with_500
            if not any(p.search(line) for p in _INLINE_QUESTION_PATTERNS)
        ]
        assert len(non_question_lines_with_500) > 0, (
            "Evaluation license info (500 records) only appears inside inline "
            "question text — it should be presented as unconditional content.\n"
            f"Question lines with 500-record info:\n"
            + "\n".join(f"  - {q}" for q in question_lines_with_500)
        )

    def test_step5_presents_custom_license_instructions_unconditionally(self) -> None:
        """**Validates: Requirements 2.1**

        Step 5 should present custom license instructions as unconditional
        content (how to provide a file or BASE64 key)."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        # Custom license instructions should mention providing a license file
        # or BASE64 key as standalone informational content
        has_custom_info = (
            "license file" in step5.lower()
            or "base64 key" in step5.lower()
            or "base64" in step5.lower()
        )
        assert has_custom_info, (
            "Step 5 does not present custom license instructions as content"
        )

    def test_step5_presents_acquisition_contacts_unconditionally(self) -> None:
        """**Validates: Requirements 2.1**

        Step 5 should present license acquisition contacts as unconditional content."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "support@senzing.com" in step5, (
            "Step 5 does not contain support@senzing.com contact"
        )
        assert "sales@senzing.com" in step5, (
            "Step 5 does not contain sales@senzing.com contact"
        )


# ---------------------------------------------------------------------------
# Property-Based Bug Condition Test
# **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2**
# ---------------------------------------------------------------------------

_BUG_CONDITION_CHECKS = [
    "no_inline_questions",
    "evaluation_info_unconditional",
    "custom_license_unconditional",
    "acquisition_contacts_unconditional",
]


class TestBugConditionProperty:
    """Property-based test: for any bug condition check, Step 5 should
    satisfy the expected behavior (no inline questions, unconditional content).

    On unfixed code this property FAILS, surfacing counterexamples."""

    @given(check=st.sampled_from(_BUG_CONDITION_CHECKS))
    @settings(max_examples=20)
    def test_step5_satisfies_expected_behavior(self, check: str) -> None:
        """**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2**

        For any bug condition check, Step 5 should satisfy the expected behavior."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)

        if check == "no_inline_questions":
            questions = _find_inline_questions(step5)
            assert len(questions) == 0, (
                f"Bug condition: Step 5 contains {len(questions)} inline question(s):\n"
                + "\n".join(f"  - {q}" for q in questions)
            )
        elif check == "evaluation_info_unconditional":
            lines_with_500 = [
                line.strip()
                for line in step5.splitlines()
                if "500 record" in line.lower() or "500-record" in line.lower()
            ]
            non_question_lines = [
                line for line in lines_with_500
                if not any(p.search(line) for p in _INLINE_QUESTION_PATTERNS)
            ]
            assert len(non_question_lines) > 0, (
                "Bug condition: evaluation license info (500 records) only in question text"
            )
        elif check == "custom_license_unconditional":
            # Custom license info should be in non-question lines
            has_custom = "license file" in step5.lower() or "base64" in step5.lower()
            assert has_custom, "Bug condition: no custom license instructions found"
        elif check == "acquisition_contacts_unconditional":
            assert "support@senzing.com" in step5 and "sales@senzing.com" in step5, (
                "Bug condition: missing license acquisition contacts"
            )


# ===========================================================================
# PRESERVATION TESTS (Task 2)
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
#
# These tests observe the UNFIXED code baseline and assert that license
# mechanics, other steps, and key content are preserved.
# All preservation tests should PASS on UNFIXED code.
# ===========================================================================


# ---------------------------------------------------------------------------
# Baselines -- SHA-256 hashes for non-Step-5 sections (observed from UNFIXED code)
# ---------------------------------------------------------------------------

import hashlib

_STEP_HASHES: dict[str, str] = {
    "Step 1": "32e777457a1e706c4b46aed05fd48016211a61456696ab4149d804863642c4bd",
    "Step 2": "d699ce64d2b9f6f8f834466b7886611343554f5d3e7f1bf89c39ad7d58cf92a0",
    "Step 3": "d7c960e5ed8453dfda7120d9c0731f78deefea81409a87f616246486359ab800",
    "Step 4": "5ee5168b5bfe301fcf7f6841ef78f3ab334dfc1b413e7440cc598fc72d69e6be",
    "Step 6": "67f0d91f31c40a0ef08336845a0a001ab959d4dc38c8ef5864e7a0141df4837f",
    "Step 7": "e70acaae1640b0259e3cc5927f5ea27c88a98b3625cc2d5a6eca36ca367bb7a2",
    "Step 8": "fb49adcbe89176c7822c33742d1b48d44e7e411968e035a3ced5a03f2f0631e3",
    "Step 9": "88c37cc18880b31179d85efcd076ef2522b1f88ecd9a4a108f8e1f29a2f1f1fa",
}

_PREAMBLE_HASH = "d7645bfe51464bd2b52d7515a462879ff8d1398148326688fe98d4049602024f"
_POST_STEP9_HASH = "4b2fe895f0b163de379485f2e311d37273e6fd359d35efdc13d72f45341590aa"

_EXPECTED_HEADINGS = [
    "# Module 2: SDK Installation and Configuration",
    "## Step 1: Check for Existing Installation \u2014 MUST DO FIRST",
    "## Step 2: Determine Platform",
    "## Step 3: Install Senzing SDK",
    "## Step 4: Verify Installation",
    "## Step 5: Configure License",
    "## Step 6: Create Project Directory Structure",
    "## Step 7: Configure Database",
    "## Step 8: Create Engine Configuration",
    "## Step 9: Test Database Connection",
    "## Success Criteria",
    "## Transition",
    "## Troubleshooting",
    "## Agent Behavior",
]


# ---------------------------------------------------------------------------
# Helpers for preservation tests
# ---------------------------------------------------------------------------


def _sha256(content: str) -> str:
    """Return SHA-256 hex digest of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_step_section(content: str, step_num: int) -> str | None:
    """Extract a step section by number.

    Returns the text from '## Step N:' up to the next section heading.
    """
    # Determine what follows each step
    next_headings = {
        1: "Step 2:",
        2: "Step 3:",
        3: "Step 4:",
        4: "Step 5:",
        5: "Step 6:",
        6: "Step 7:",
        7: "Step 8:",
        8: "Step 9:",
        9: "Success Criteria",
    }
    next_h = next_headings.get(step_num, "Success Criteria")
    pattern = re.compile(
        rf"(## Step {step_num}:.*?)(?=\n## {re.escape(next_h)})",
        re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(1) if m else None


def _extract_preamble(content: str) -> str:
    """Extract the preamble (everything before Step 1)."""
    m = re.search(r"^(.*?)(?=\n## Step 1:)", content, re.DOTALL)
    return m.group(1) if m else ""


def _extract_post_step9(content: str) -> str:
    """Extract everything from Success Criteria onwards."""
    m = re.search(r"(## Success Criteria.*)", content, re.DOTALL)
    return m.group(1) if m else ""


def _extract_headings(content: str) -> list[str]:
    """Extract all markdown headings (# through ####) in order."""
    return re.findall(r"^(#{1,4} .+)$", content, re.MULTILINE)


# ---------------------------------------------------------------------------
# Preservation Tests -- Step 5 Key Content
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
# ---------------------------------------------------------------------------


class TestPreservationStep5Content:
    """Verify that Step 5 preserves all key mechanical content.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    def test_step5_license_check_priority_order(self) -> None:
        """**Validates: Requirements 3.1**

        Step 5 contains the license check priority order."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "project-local" in step5, "Missing 'project-local' in priority order"
        assert "SENZING_LICENSE_PATH" in step5, "Missing 'SENZING_LICENSE_PATH' in priority order"
        assert "CONFIGPATH" in step5, "Missing 'CONFIGPATH' in priority order"
        assert "built-in evaluation" in step5, "Missing 'built-in evaluation' in priority order"

    def test_step5_base64_decode_command(self) -> None:
        """**Validates: Requirements 3.2**

        Step 5 contains the BASE64 decode command."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "base64 --decode > licenses/g2.lic" in step5, (
            "Missing BASE64 decode command"
        )

    def test_step5_never_paste_warning(self) -> None:
        """**Validates: Requirements 3.2**

        Step 5 contains the 'NEVER ask the user to paste a license key into chat' warning."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "NEVER ask the user to paste a license key into chat" in step5, (
            "Missing 'NEVER paste' warning"
        )

    def test_step5_pipeline_licensefile_json(self) -> None:
        """**Validates: Requirements 3.3**

        Step 5 contains the engine config PIPELINE LICENSEFILE JSON."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "PIPELINE" in step5, "Missing PIPELINE in engine config"
        assert "LICENSEFILE" in step5, "Missing LICENSEFILE in engine config"
        assert '"licenses/g2.lic"' in step5, "Missing licenses/g2.lic path in PIPELINE config"

    def test_step5_preference_recording(self) -> None:
        """**Validates: Requirements 3.4**

        Step 5 contains preference recording instructions."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "license: custom" in step5, "Missing 'license: custom' preference"
        assert "license: evaluation" in step5, "Missing 'license: evaluation' preference"
        assert "bootcamp_preferences.yaml" in step5, "Missing bootcamp_preferences.yaml reference"

    def test_step5_acquisition_contacts(self) -> None:
        """**Validates: Requirements 3.5**

        Step 5 contains license acquisition contacts."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "support@senzing.com" in step5, "Missing support@senzing.com"
        assert "sales@senzing.com" in step5, "Missing sales@senzing.com"

    def test_step5_checkpoint(self) -> None:
        """**Validates: Requirements 3.5**

        Step 5 contains the checkpoint write instruction."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)
        assert "Checkpoint" in step5, "Missing checkpoint instruction"
        assert "step 5" in step5.lower(), "Missing 'step 5' in checkpoint"
        assert "bootcamp_progress.json" in step5, "Missing bootcamp_progress.json in checkpoint"


# ---------------------------------------------------------------------------
# Preservation Tests -- Other Steps Unchanged
# **Validates: Requirements 3.6**
# ---------------------------------------------------------------------------


class TestPreservationOtherSteps:
    """Verify that Steps 1-4 and 6-9 are unchanged by comparing SHA-256 hashes.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @pytest.mark.parametrize("step_key", list(_STEP_HASHES.keys()))
    def test_step_unchanged(self, step_key: str) -> None:
        """**Validates: Requirements 3.6**

        Non-Step-5 step content matches the observed baseline hash."""
        step_num = int(step_key.split()[1])
        content = _read_file(_MODULE_02_FILE)
        step_content = _extract_step_section(content, step_num)
        assert step_content is not None, f"Could not extract {step_key}"
        actual_hash = _sha256(step_content)
        expected_hash = _STEP_HASHES[step_key]
        assert actual_hash == expected_hash, (
            f"{step_key} content has changed.\n"
            f"Expected hash: {expected_hash}\n"
            f"Actual hash:   {actual_hash}"
        )

    def test_preamble_unchanged(self) -> None:
        """**Validates: Requirements 3.6**

        Preamble (before Step 1) matches the observed baseline hash."""
        content = _read_file(_MODULE_02_FILE)
        preamble = _extract_preamble(content)
        actual_hash = _sha256(preamble)
        assert actual_hash == _PREAMBLE_HASH, (
            f"Preamble content has changed.\n"
            f"Expected hash: {_PREAMBLE_HASH}\n"
            f"Actual hash:   {actual_hash}"
        )

    def test_post_step9_unchanged(self) -> None:
        """**Validates: Requirements 3.6**

        Post-Step-9 sections (Success Criteria, Transition, etc.) match baseline."""
        content = _read_file(_MODULE_02_FILE)
        post = _extract_post_step9(content)
        actual_hash = _sha256(post)
        assert actual_hash == _POST_STEP9_HASH, (
            f"Post-Step-9 content has changed.\n"
            f"Expected hash: {_POST_STEP9_HASH}\n"
            f"Actual hash:   {actual_hash}"
        )


# ---------------------------------------------------------------------------
# Preservation Tests -- Heading Sequence
# **Validates: Requirements 3.6**
# ---------------------------------------------------------------------------


class TestPreservationHeadings:
    """Verify that the heading sequence for the entire file is unchanged.

    EXPECTED OUTCOME on UNFIXED code: test PASSES."""

    def test_heading_sequence_preserved(self) -> None:
        """**Validates: Requirements 3.6**

        The heading sequence matches the observed baseline."""
        content = _read_file(_MODULE_02_FILE)
        actual = _extract_headings(content)
        assert actual == _EXPECTED_HEADINGS, (
            f"Heading sequence mismatch.\n"
            f"Expected: {_EXPECTED_HEADINGS}\n"
            f"Got:      {actual}"
        )


# ---------------------------------------------------------------------------
# Property-Based Preservation Tests
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
# ---------------------------------------------------------------------------

_NON_STEP5_KEYS = list(_STEP_HASHES.keys())

_STEP5_PRESERVATION_CHECKS = [
    "license_check_priority_order",
    "base64_decode_command",
    "never_paste_warning",
    "pipeline_licensefile_json",
    "preference_recording",
    "acquisition_contacts",
    "checkpoint",
]


class TestPreservationProperty:
    """Property-based preservation tests.

    EXPECTED OUTCOME on UNFIXED code: all tests PASS."""

    @given(step_key=st.sampled_from(_NON_STEP5_KEYS))
    @settings(max_examples=30)
    def test_non_step5_content_preserved(self, step_key: str) -> None:
        """**Validates: Requirements 3.6**

        For any non-Step-5 step, the content matches the observed baseline hash."""
        step_num = int(step_key.split()[1])
        content = _read_file(_MODULE_02_FILE)
        step_content = _extract_step_section(content, step_num)
        assert step_content is not None, f"Could not extract {step_key}"
        actual_hash = _sha256(step_content)
        expected_hash = _STEP_HASHES[step_key]
        assert actual_hash == expected_hash, (
            f"{step_key} content has changed.\n"
            f"Expected hash: {expected_hash}\n"
            f"Actual hash:   {actual_hash}"
        )

    @given(check=st.sampled_from(_STEP5_PRESERVATION_CHECKS))
    @settings(max_examples=30)
    def test_step5_key_content_preserved(self, check: str) -> None:
        """**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

        For any Step 5 preservation check, the key content is present."""
        content = _read_file(_MODULE_02_FILE)
        step5 = _extract_step5(content)

        if check == "license_check_priority_order":
            assert "project-local" in step5
            assert "SENZING_LICENSE_PATH" in step5
            assert "CONFIGPATH" in step5
            assert "built-in evaluation" in step5
        elif check == "base64_decode_command":
            assert "base64 --decode > licenses/g2.lic" in step5
        elif check == "never_paste_warning":
            assert "NEVER ask the user to paste a license key into chat" in step5
        elif check == "pipeline_licensefile_json":
            assert "PIPELINE" in step5
            assert "LICENSEFILE" in step5
        elif check == "preference_recording":
            assert "license: custom" in step5
            assert "license: evaluation" in step5
        elif check == "acquisition_contacts":
            assert "support@senzing.com" in step5
            assert "sales@senzing.com" in step5
        elif check == "checkpoint":
            assert "Checkpoint" in step5
            assert "bootcamp_progress.json" in step5
