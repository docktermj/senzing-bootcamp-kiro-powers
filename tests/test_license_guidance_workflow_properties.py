"""Property-based tests for license guidance workflow bugfix.

Bug condition exploration tests that encode the EXPECTED (fixed) behavior.
These tests are designed to FAIL on the current unfixed steering file,
confirming the bug exists: Module 1 Step 6 has no conditional logic for
record counts > 500 and provides no license guidance workflow.

**Validates: Requirements 1.1, 1.2, 1.3**
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

STEERING_DIR = Path("senzing-bootcamp/steering")
MODULE_01 = STEERING_DIR / "module-01-business-problem.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_module_01_content() -> str:
    """Load the full content of module-01-business-problem.md."""
    return MODULE_01.read_text(encoding="utf-8")


def _extract_step_6_and_transition(content: str) -> str:
    """Extract Step 6 content and everything between Step 6 and Step 7.

    This captures the region where the license guidance workflow should exist.
    Step 6 starts at the '6. **Infer details from response**' heading and
    ends where Step 7 begins ('7. **Confirm inferred details').
    """
    # Match from Step 6 heading up to (but not including) Step 7 heading
    match = re.search(
        r"(6\.\s+\*\*Infer details from response\*\*.*?)(?=7\.\s+\*\*Confirm inferred details)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate Step 6 in module-01-business-problem.md"
    return match.group(1)


# ===========================================================================
# Bug Condition Exploration Tests
# Property 1: Bug Condition — Missing License Guidance Workflow for
#   Record Count > 500
#
# These tests MUST FAIL on unfixed code — failure confirms the bug exists.
# DO NOT attempt to fix the test or the code when they fail.
#
# Validates: Requirements 1.1, 1.2, 1.3
# ===========================================================================


class TestBugConditionLicenseGuidance:
    """Bug condition exploration: license guidance workflow must exist between
    Step 6 and Step 7 for record counts exceeding 500.

    All tests in this class encode EXPECTED behavior and will FAIL on unfixed
    code, confirming the bug exists.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @pytest.fixture
    def step_6_content(self) -> str:
        """Extract Step 6 and the transition region to Step 7."""
        content = _load_module_01_content()
        return _extract_step_6_and_transition(content)

    # -------------------------------------------------------------------
    # Test 1 — Missing Threshold Check
    # -------------------------------------------------------------------

    def test_threshold_check_for_500_records(self, step_6_content: str):
        """Step 6 (or a sub-step between 6 and 7) must contain conditional
        logic checking whether total record count exceeds 500.

        Will FAIL on unfixed code — no threshold check exists.
        """
        # Look for any reference to a 500-record threshold conditional
        has_threshold = bool(re.search(
            r"(exceed|greater\s+than|more\s+than|>\s*500|over\s+500|above\s+500|"
            r"500.record|500.record\s+limit|evaluation\s+limit|"
            r"total\s+record.*500|record\s+count.*500|500.*threshold)",
            step_6_content,
            re.IGNORECASE,
        ))
        assert has_threshold, (
            "Step 6 has no conditional logic checking whether total record "
            "count exceeds 500. The bug condition is confirmed: no threshold "
            "check exists between Step 6 and Step 7."
        )

    # -------------------------------------------------------------------
    # Test 2 — Missing License Question
    # -------------------------------------------------------------------

    def test_license_question_with_stop(self, step_6_content: str):
        """A step between 6 and 7 must ask 'Do you already have a Senzing
        license?' with a 👉 marker and STOP instruction.

        Will FAIL on unfixed code — no license question exists.
        """
        has_license_question = bool(re.search(
            r"Do you already have a Senzing license\?",
            step_6_content,
            re.IGNORECASE,
        ))
        has_pointer_marker = "👉" in step_6_content
        has_stop_after_question = bool(re.search(
            r"(Do you already have a Senzing license|license).*STOP",
            step_6_content,
            re.IGNORECASE | re.DOTALL,
        ))

        assert has_license_question, (
            "No 'Do you already have a Senzing license?' question found "
            "between Step 6 and Step 7. Bug confirmed: no license question exists."
        )
        assert has_pointer_marker, (
            "No 👉 marker found in the license guidance section."
        )
        assert has_stop_after_question, (
            "No STOP instruction found after the license question."
        )

    # -------------------------------------------------------------------
    # Test 3 — Missing "Has License" Branch
    # -------------------------------------------------------------------

    def test_has_license_branch(self, step_6_content: str):
        """A step must contain guidance for bootcampers who already have a
        license: Base64 decode instructions, licenses/g2.lic path, and
        LICENSEFILE engine config reference.

        Will FAIL on unfixed code — no branch exists.
        """
        has_base64 = bool(re.search(
            r"(base64|Base64)", step_6_content
        ))
        has_lic_path = bool(re.search(
            r"licenses/g2\.lic", step_6_content
        ))
        has_licensefile = bool(re.search(
            r"LICENSEFILE", step_6_content
        ))

        assert has_base64, (
            "No Base64 decode instructions found between Step 6 and Step 7. "
            "Bug confirmed: no 'has license' branch exists."
        )
        assert has_lic_path, (
            "No 'licenses/g2.lic' path reference found between Step 6 and Step 7."
        )
        assert has_licensefile, (
            "No LICENSEFILE engine config reference found between Step 6 and Step 7."
        )

    # -------------------------------------------------------------------
    # Test 4 — Missing "No License" Branch
    # -------------------------------------------------------------------

    def test_no_license_branch(self, step_6_content: str):
        """A step must contain guidance for bootcampers who need a license:
        contact support@senzing.com, turnaround expectations, and
        configuration instructions once received.

        Will FAIL on unfixed code — no branch exists.
        """
        has_support_email = bool(re.search(
            r"support@senzing\.com", step_6_content
        ))
        has_turnaround = bool(re.search(
            r"(1.2\s+business\s+day|turnaround|business\s+day)",
            step_6_content,
            re.IGNORECASE,
        ))
        has_config_instructions = bool(re.search(
            r"(configure|configuration).*once\s+(received|you\s+have)",
            step_6_content,
            re.IGNORECASE,
        ))

        assert has_support_email, (
            "No 'support@senzing.com' contact found between Step 6 and Step 7. "
            "Bug confirmed: no 'no license' branch exists."
        )
        assert has_turnaround, (
            "No turnaround expectations found between Step 6 and Step 7."
        )
        assert has_config_instructions, (
            "No configuration instructions for received license found."
        )

    # -------------------------------------------------------------------
    # Test 5 — Missing Deferral Option
    # -------------------------------------------------------------------

    def test_deferral_option(self, step_6_content: str):
        """A step must offer to defer license configuration to Module 2.

        Will FAIL on unfixed code — no deferral option exists.
        """
        has_deferral = bool(re.search(
            r"(defer|later|Module\s+2|continue.*without.*licens|"
            r"proceed.*Module\s+1.*license\s+later)",
            step_6_content,
            re.IGNORECASE,
        ))
        assert has_deferral, (
            "No deferral option found between Step 6 and Step 7. "
            "Bug confirmed: no option to defer license configuration to Module 2."
        )

    # -------------------------------------------------------------------
    # PBT Test — Bug Condition Identification
    # -------------------------------------------------------------------

    @given(record_count=st.integers(min_value=501, max_value=100000))
    @settings(max_examples=20)
    def test_bug_condition_threshold_content_present(self, record_count: int):
        """For any record count > 500, the steering file should contain
        license guidance logic with threshold-based conditional content
        referencing the 500-record limit.

        Uses Hypothesis to generate record counts (501–100000) and verify
        that the steering file contains conditional content for the
        500-record evaluation limit.

        Bug_Condition: isBugCondition(input) where input.totalRecords > 500
        AND input.currentModule = "Module 1" AND input.currentStep = "Step 6"
        AND licenseGuidanceNotProvided(input) = true

        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # The bug condition holds for any record_count > 500
        assert record_count > 500, "Precondition: record count must exceed 500"

        content = _load_module_01_content()
        step_6_region = _extract_step_6_and_transition(content)

        # For any count > 500, the steering file MUST contain:
        # 1. A reference to the 500-record threshold/limit
        has_500_reference = bool(re.search(
            r"500", step_6_region
        ))
        # 2. Conditional logic that triggers license guidance
        has_conditional_logic = bool(re.search(
            r"(exceed|greater\s+than|more\s+than|>\s*500|over\s+500|"
            r"if.*record.*500|when.*record.*500|total.*exceed)",
            step_6_region,
            re.IGNORECASE,
        ))
        # 3. License guidance content
        has_license_guidance = bool(re.search(
            r"(license|Senzing\s+license)",
            step_6_region,
            re.IGNORECASE,
        ))

        assert has_500_reference and has_conditional_logic and has_license_guidance, (
            f"Bug condition confirmed for record_count={record_count}: "
            f"Step 6 has no threshold-based conditional content referencing "
            f"the 500-record limit. has_500_reference={has_500_reference}, "
            f"has_conditional_logic={has_conditional_logic}, "
            f"has_license_guidance={has_license_guidance}. "
            f"The steering file provides no license guidance workflow for "
            f"record counts exceeding 500."
        )


# ===========================================================================
# Preservation Property Tests
# Property 2: Preservation — Non-License-Trigger Behavior Unchanged
#
# These tests MUST PASS on unfixed code — they lock down existing behavior
# so we can detect regressions after the fix is applied.
#
# Validates: Requirements 3.1, 3.3, 3.4
# ===========================================================================

# ---------------------------------------------------------------------------
# Additional Constants for Preservation Tests
# ---------------------------------------------------------------------------

MODULE_02 = STEERING_DIR / "module-02-sdk-setup.md"

# SHA-256 hash of module-02-sdk-setup.md at the time preservation tests were written.
# Used to verify byte-identical content (Module 2 Step 5 independence).
MODULE_02_SHA256 = "548b94e501110e4d058af391292bfc81a8f7a5e0b3fcd194c2fa4ee6bca1d5a0"

# The five inference categories in Step 6 (labeled A–F in the steering file,
# but the task spec lists five named categories plus INTEGRATION TARGETS).
STEP_6_INFERENCE_CATEGORIES = [
    "RECORD TYPES",
    "SOURCE COUNT AND NAMES",
    "PROBLEM CATEGORY",
    "MATCHING CRITERIA",
    "DESIRED OUTCOME",
    "INTEGRATION TARGETS",
]

# Phase 2 reference line expected verbatim in the steering file.
PHASE_2_REFERENCE = (
    "**Phase 2 (Steps 10–18):** Loaded from "
    "`module-01-phase2-document-confirm.md` via the phase system."
)

# License guidance trigger phrases that should NOT appear in the ≤ 500 path.
LICENSE_GUIDANCE_TRIGGERS = [
    "Do you already have a Senzing license?",
    "LICENSESTRINGBASE64",
]


# ---------------------------------------------------------------------------
# Preservation Helpers
# ---------------------------------------------------------------------------


def _extract_step_6_section(content: str) -> str:
    """Extract Step 6 content only (from heading to Step 7 heading)."""
    match = re.search(
        r"(6\.\s+\*\*Infer details from response\*\*.*?)(?=7\.\s+\*\*Confirm inferred details)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate Step 6 in module-01-business-problem.md"
    return match.group(1)


def _extract_step_7_section(content: str) -> str:
    """Extract Step 7 content (7, 7a, 7b, 7c, 7d) up to Step 8."""
    match = re.search(
        r"(7\.\s+\*\*Confirm inferred details.*?)(?=8\.\s+\*\*Ask about software integration)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate Step 7 in module-01-business-problem.md"
    return match.group(1)


def _extract_steps_1_to_5(content: str) -> str:
    """Extract Steps 1–5 content."""
    match = re.search(
        r"(1\.\s+\*\*Initialize version control\*\*.*?)(?=6\.\s+\*\*Infer details from response\*\*)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate Steps 1–5 in module-01-business-problem.md"
    return match.group(1)


def _extract_steps_8_to_9(content: str) -> str:
    """Extract Steps 8–9 content."""
    match = re.search(
        r"(8\.\s+\*\*Ask about software integration\*\*.*?)(?=\*\*Success indicator:\*\*)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate Steps 8–9 in module-01-business-problem.md"
    return match.group(1)


class TestPreservationLicenseGuidance:
    """Preservation property tests: verify that non-license-trigger behavior
    is unchanged on the current (unfixed) code.

    All tests in this class MUST PASS on unfixed code. They lock down existing
    behavior so regressions can be detected after the fix is applied.

    **Validates: Requirements 3.1, 3.3, 3.4**
    """

    @pytest.fixture
    def module_01_content(self) -> str:
        """Load the full module-01-business-problem.md content."""
        return _load_module_01_content()

    # -------------------------------------------------------------------
    # Test 1 — Step 6 Five-Category Inference Preservation
    # -------------------------------------------------------------------

    def test_step_6_inference_categories_present(self, module_01_content: str):
        """Step 6 must contain all six inference categories (A–F) with their
        content unchanged: RECORD TYPES, SOURCE COUNT AND NAMES,
        PROBLEM CATEGORY, MATCHING CRITERIA, DESIRED OUTCOME,
        INTEGRATION TARGETS.

        **Validates: Requirements 3.3**
        """
        step_6 = _extract_step_6_section(module_01_content)

        for category in STEP_6_INFERENCE_CATEGORIES:
            assert category in step_6, (
                f"Step 6 inference category '{category}' is missing. "
                f"The five-category inference logic must be preserved."
            )

        # Verify the section headers use the expected bold format
        assert "**A. RECORD TYPES**" in step_6
        assert "**B. SOURCE COUNT AND NAMES**" in step_6
        assert "**C. PROBLEM CATEGORY**" in step_6
        assert "**D. MATCHING CRITERIA**" in step_6
        assert "**E. DESIRED OUTCOME**" in step_6
        assert "**F. INTEGRATION TARGETS**" in step_6

    # -------------------------------------------------------------------
    # Test 2 — Step 7 Gap-Filling Preservation
    # -------------------------------------------------------------------

    def test_step_7_gap_filling_preserved(self, module_01_content: str):
        """Steps 7a–7d must preserve the one-question-per-turn pattern,
        STOP markers, and checkpoint writes.

        **Validates: Requirements 3.3**
        """
        step_7 = _extract_step_7_section(module_01_content)

        # Verify sub-steps 7a–7d exist
        assert "7a." in step_7, "Step 7a is missing"
        assert "7b." in step_7, "Step 7b is missing"
        assert "7c." in step_7, "Step 7c is missing"
        assert "7d." in step_7, "Step 7d is missing"

        # Verify one-question-per-turn pattern: "Ask about only one undetermined item per turn"
        assert "one undetermined item per turn" in step_7, (
            "One-question-per-turn pattern is missing from Step 7"
        )

        # Verify STOP markers are present in sub-steps
        stop_count = step_7.count("STOP")
        assert stop_count >= 4, (
            f"Expected at least 4 STOP markers in Step 7 (one per sub-step), "
            f"found {stop_count}"
        )

        # Verify checkpoint writes
        assert "bootcamp_progress.json" in step_7, (
            "Checkpoint writes to bootcamp_progress.json missing from Step 7"
        )

    # -------------------------------------------------------------------
    # Test 3 — Steps 1–5 and 8–9 Preservation
    # -------------------------------------------------------------------

    def test_steps_1_to_5_preserved(self, module_01_content: str):
        """Steps 1–5 content must be present and unchanged.

        **Validates: Requirements 3.3**
        """
        steps_1_5 = _extract_steps_1_to_5(module_01_content)

        # Verify key content from each step
        assert "Initialize version control" in steps_1_5, "Step 1 heading missing"
        assert "Data privacy reminder" in steps_1_5, "Step 2 heading missing"
        assert "Offer design pattern gallery" in steps_1_5, "Step 3 heading missing"
        assert "If user wants to see patterns" in steps_1_5, "Step 4 heading missing"
        assert "Open-ended discovery prompt" in steps_1_5, "Step 5 heading missing"

        # Verify Step 1 git check content
        assert "git rev-parse --git-dir" in steps_1_5, (
            "Step 1 git repository check is missing"
        )

        # Verify Step 5 open-ended question
        assert "Tell me about the problem you're trying to solve" in steps_1_5, (
            "Step 5 open-ended discovery question is missing"
        )

    def test_steps_8_to_9_preserved(self, module_01_content: str):
        """Steps 8–9 content must be present and unchanged.

        **Validates: Requirements 3.3**
        """
        steps_8_9 = _extract_steps_8_to_9(module_01_content)

        # Verify Step 8 content
        assert "Ask about software integration" in steps_8_9, "Step 8 heading missing"
        assert "CRM, search engine, data warehouse" in steps_8_9, (
            "Step 8 integration question content missing"
        )

        # Verify Step 9 content
        assert "Ask about deployment target" in steps_8_9, "Step 9 heading missing"
        assert "advanced_topics" in steps_8_9, (
            "Step 9 advanced topics track check missing"
        )

    # -------------------------------------------------------------------
    # Test 4 — Phase 2 Reference Preservation
    # -------------------------------------------------------------------

    def test_phase_2_reference_present(self, module_01_content: str):
        """The Phase 2 reference line must be present and unchanged.

        **Validates: Requirements 3.3**
        """
        assert PHASE_2_REFERENCE in module_01_content, (
            f"Phase 2 reference line is missing or changed. Expected:\n"
            f"  {PHASE_2_REFERENCE}"
        )

    # -------------------------------------------------------------------
    # Test 5 — YAML Frontmatter Preservation
    # -------------------------------------------------------------------

    def test_yaml_frontmatter_present(self, module_01_content: str):
        """The file must begin with YAML frontmatter containing
        'inclusion: manual'.

        **Validates: Requirements 3.3**
        """
        assert module_01_content.startswith("---\n"), (
            "File does not begin with YAML frontmatter delimiter '---'"
        )

        # Extract frontmatter
        frontmatter_match = re.match(
            r"^---\n(.*?)\n---", module_01_content, re.DOTALL
        )
        assert frontmatter_match, (
            "Could not parse YAML frontmatter (missing closing '---')"
        )

        frontmatter = frontmatter_match.group(1)
        assert "inclusion: manual" in frontmatter, (
            "YAML frontmatter does not contain 'inclusion: manual'"
        )

    # -------------------------------------------------------------------
    # Test 6 — Module 2 Step 5 Independence
    # -------------------------------------------------------------------

    def test_module_2_byte_identical(self):
        """Module 2 steering file (module-02-sdk-setup.md) must be
        byte-identical to its original content. The license gate in
        Module 2 Step 5 must be unaffected by any changes.

        **Validates: Requirements 3.4**
        """
        import hashlib

        content = MODULE_02.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()

        assert actual_hash == MODULE_02_SHA256, (
            f"module-02-sdk-setup.md has been modified!\n"
            f"  Expected SHA-256: {MODULE_02_SHA256}\n"
            f"  Actual SHA-256:   {actual_hash}\n"
            f"Module 2 Step 5 (Configure License) must remain unchanged."
        )

    # -------------------------------------------------------------------
    # Test 7 — Record Count ≤ 500 No License Mention
    # -------------------------------------------------------------------

    def test_no_license_guidance_for_small_datasets(self, module_01_content: str):
        """For record counts ≤ 500, the Step 6 inference logic (A–F categories)
        must not contain any license guidance triggers, and the conditional
        gating in Step 6a must explicitly skip license steps for ≤ 500.

        The preservation requirement (Req 3.1) states: when a bootcamper's
        record count is 500 or fewer, the system shall continue through
        Module 1 without mentioning license requirements. This is achieved
        via the Step 6a threshold check which skips Steps 6b–6e.

        **Validates: Requirements 3.1**
        """
        step_6 = _extract_step_6_section(module_01_content)

        # Extract only the inference section (A–F categories) — this is the
        # content that executes for ALL record counts including ≤ 500.
        # The inference section ends at the Step 6 checkpoint or Step 6a.
        inference_match = re.search(
            r"(\*\*A\. RECORD TYPES\*\*.*?)(?=\*\*(?:6a\.|Checkpoint)|\*\*Checkpoint\*\*)",
            step_6,
            re.DOTALL,
        )
        if inference_match:
            inference_section = inference_match.group(1)
        else:
            # Fallback: extract from **A. RECORD TYPES** to **F. INTEGRATION TARGETS** end
            inference_match = re.search(
                r"(\*\*A\. RECORD TYPES\*\*.*?\*\*F\. INTEGRATION TARGETS\*\*.*?)(?=\n\s*\*\*Checkpoint)",
                step_6,
                re.DOTALL,
            )
            assert inference_match, "Could not extract Step 6 inference section (A–F)"
            inference_section = inference_match.group(1)

        # The inference section (A–F) must not contain license triggers
        for trigger in LICENSE_GUIDANCE_TRIGGERS:
            assert trigger not in inference_section, (
                f"License guidance trigger '{trigger}' found in Step 6 "
                f"inference section (A–F categories). For record counts ≤ 500, "
                f"no license guidance should be present in the inference path."
            )

        # Verify the conditional gating exists: Step 6a must skip license
        # steps for ≤ 500 records
        has_skip_for_small = bool(re.search(
            r"(500 or fewer.*skip|skip.*6b.*6e.*proceed.*Step 7|"
            r"total is 500 or fewer.*skip)",
            step_6,
            re.IGNORECASE,
        ))
        assert has_skip_for_small, (
            "Step 6a must contain conditional logic that skips license "
            "guidance (Steps 6b–6e) when record count is ≤ 500."
        )

    # -------------------------------------------------------------------
    # PBT Test — Small Dataset Preservation
    # -------------------------------------------------------------------

    @given(record_count=st.integers(min_value=1, max_value=500))
    @settings(max_examples=20)
    def test_small_dataset_no_license_triggers(self, record_count: int):
        """For any record count from 1 to 500, the steering file's Step 6
        inference path (A–F categories) must contain no license guidance
        triggers, and the conditional gating in Step 6a must ensure the
        ≤ 500 path skips license steps.

        The preservation requirement (Req 3.1) is satisfied because Step 6a
        explicitly directs ≤ 500 records to skip Steps 6b–6e. This test
        verifies the inference section is clean and the gating is correct.

        **Validates: Requirements 3.1, 3.3**
        """
        assert 1 <= record_count <= 500, "Precondition: record count must be ≤ 500"

        content = _load_module_01_content()
        step_6 = _extract_step_6_section(content)

        # Extract only the inference section (A–F categories) — this is the
        # content that executes for ALL record counts including ≤ 500.
        inference_match = re.search(
            r"(\*\*A\. RECORD TYPES\*\*.*?)(?=\*\*(?:6a\.|Checkpoint)|\*\*Checkpoint\*\*)",
            step_6,
            re.DOTALL,
        )
        if inference_match:
            inference_section = inference_match.group(1)
        else:
            # Fallback: extract from **A. to **F. end
            inference_match = re.search(
                r"(\*\*A\. RECORD TYPES\*\*.*?\*\*F\. INTEGRATION TARGETS\*\*.*?)(?=\n\s*\*\*Checkpoint)",
                step_6,
                re.DOTALL,
            )
            assert inference_match, "Could not extract Step 6 inference section (A–F)"
            inference_section = inference_match.group(1)

        # For any count ≤ 500, the Step 6 inference section (A–F) must NOT
        # contain license guidance triggers.
        for trigger in LICENSE_GUIDANCE_TRIGGERS:
            assert trigger not in inference_section, (
                f"License guidance trigger '{trigger}' found in Step 6 "
                f"inference section for record_count={record_count}. For "
                f"counts ≤ 500, the inference path must not contain license "
                f"guidance."
            )

        # Verify the conditional gating: Step 6a must skip license steps
        # for ≤ 500 records (this ensures the runtime path is correct)
        has_skip_for_small = bool(re.search(
            r"(500 or fewer.*skip|skip.*6b.*6e.*proceed.*Step 7|"
            r"total is 500 or fewer.*skip)",
            step_6,
            re.IGNORECASE,
        ))
        assert has_skip_for_small, (
            f"Step 6a must contain conditional logic that skips license "
            f"guidance (Steps 6b–6e) when record count is ≤ 500. "
            f"Tested with record_count={record_count}."
        )
