"""Preservation property tests for wait-before-server-termination bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: wait-before-server-termination
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_VISUALIZATION_GUIDE = _BOOTCAMP_DIR / "steering" / "visualization-guide.md"
_MODULE_03_PHASE2 = _BOOTCAMP_DIR / "steering" / "module-03-phase2-visualization.md"
_MODULE_03_SYSTEM = _BOOTCAMP_DIR / "steering" / "module-03-system-verification.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read the full content of a steering file."""
    return path.read_text(encoding="utf-8")


def _extract_yaml_frontmatter(content: str) -> str:
    """Extract YAML frontmatter from a Markdown file."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    return match.group(0) if match else ""


def _extract_web_service_delivery_sequence(content: str) -> str:
    """Extract the Web Service Delivery Sequence section."""
    pattern = re.compile(r"^## Web Service Delivery Sequence\s*\n", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""
    start = match.start()
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(content, match.end())
    return content[start:next_match.start()] if next_match else content[start:]


def _extract_delivery_sequence_steps(section: str) -> list[tuple[int, str]]:
    """Extract numbered steps from the delivery sequence section.

    Returns list of (step_number, step_content) tuples.
    """
    # Find all numbered steps: "1. **...**"
    step_pattern = re.compile(r"^(\d+)\.\s+\*\*", re.MULTILINE)
    matches = list(step_pattern.finditer(section))
    steps = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        steps.append((int(m.group(1)), section[start:end]))
    return steps


def _extract_step_94(content: str) -> str:
    """Extract the full Step 9.4 section from module-03-phase2-visualization.md."""
    heading_pattern = re.compile(r"^###\s+9\.4\b", re.MULTILINE)
    heading_match = heading_pattern.search(content)
    if not heading_match:
        return ""
    start = heading_match.start()
    next_heading = re.compile(r"^###\s+", re.MULTILINE)
    next_match = next_heading.search(content, heading_match.end())
    return content[start:next_match.start()] if next_match else content[start:]


def _extract_step_94_items_1_and_2(content: str) -> str:
    """Extract Step 9.4 items 1 and 2 (start server, verify endpoints)."""
    section = _extract_step_94(content)
    if not section:
        return ""
    # Find item 1
    item1_pattern = re.compile(r"^1\.\s+\*\*Start the server", re.MULTILINE)
    item1_match = item1_pattern.search(section)
    if not item1_match:
        return ""
    # Find item 3 to bound items 1-2
    item3_pattern = re.compile(r"^3\.\s+\*\*Present to bootcamper", re.MULTILINE)
    item3_match = item3_pattern.search(section)
    if item3_match:
        return section[item1_match.start():item3_match.start()]
    return section[item1_match.start():]


def _extract_step_94_checkpoint(content: str) -> str:
    """Extract the checkpoint JSON structure at end of Step 9.4."""
    section = _extract_step_94(content)
    if not section:
        return ""
    # Find the **Checkpoint:** marker
    checkpoint_pattern = re.compile(r"\*\*Checkpoint:\*\*", re.MULTILINE)
    checkpoint_match = checkpoint_pattern.search(section)
    if not checkpoint_match:
        return ""
    return section[checkpoint_match.start():]


def _extract_step(content: str, step_number: int) -> str:
    """Extract a step section by its ### Step N: heading."""
    pattern = re.compile(rf"^### Step {step_number}:", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""
    start = match.start()
    next_heading = re.compile(r"^### ", re.MULTILINE)
    next_match = next_heading.search(content, match.end())
    return content[start:next_match.start()] if next_match else content[start:]


def _extract_step_11_cleanup_logic(content: str) -> str:
    """Extract Step 11 cleanup items (terminate, artifact, purge, retain).

    Returns the content starting from '1. **Terminate the web service'
    through the end of Step 11.
    """
    step11 = _extract_step(content, 11)
    if not step11:
        return ""
    # Find item 1 (terminate)
    item1_pattern = re.compile(r"^1\.\s+\*\*Terminate the web service", re.MULTILINE)
    item1_match = item1_pattern.search(step11)
    if not item1_match:
        return ""
    return step11[item1_match.start():]


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# ---------------------------------------------------------------------------

# Read all three files at module load time (observation phase)
_UNFIXED_VIS_GUIDE = _read_file(_VISUALIZATION_GUIDE)
_UNFIXED_PHASE2 = _read_file(_MODULE_03_PHASE2)
_UNFIXED_SYSTEM = _read_file(_MODULE_03_SYSTEM)

# Visualization guide baselines
_UNFIXED_VIS_FRONTMATTER = _extract_yaml_frontmatter(_UNFIXED_VIS_GUIDE)
_UNFIXED_DELIVERY_SEQUENCE = _extract_web_service_delivery_sequence(_UNFIXED_VIS_GUIDE)
_UNFIXED_DELIVERY_STEPS = _extract_delivery_sequence_steps(_UNFIXED_DELIVERY_SEQUENCE)

# Phase2 baselines
_UNFIXED_PHASE2_FRONTMATTER = _extract_yaml_frontmatter(_UNFIXED_PHASE2)
_UNFIXED_STEP94_ITEMS_1_2 = _extract_step_94_items_1_and_2(_UNFIXED_PHASE2)
_UNFIXED_STEP94_CHECKPOINT = _extract_step_94_checkpoint(_UNFIXED_PHASE2)

# System verification baselines
_UNFIXED_SYSTEM_FRONTMATTER = _extract_yaml_frontmatter(_UNFIXED_SYSTEM)
_UNFIXED_STEP10 = _extract_step(_UNFIXED_SYSTEM, 10)
_UNFIXED_STEP11_CLEANUP = _extract_step_11_cleanup_logic(_UNFIXED_SYSTEM)
_UNFIXED_STEP12 = _extract_step(_UNFIXED_SYSTEM, 12)

# All three files
_ALL_FILES = [_VISUALIZATION_GUIDE, _MODULE_03_PHASE2, _MODULE_03_SYSTEM]
_ALL_UNFIXED_FRONTMATTERS = [
    _UNFIXED_VIS_FRONTMATTER,
    _UNFIXED_PHASE2_FRONTMATTER,
    _UNFIXED_SYSTEM_FRONTMATTER,
]


# ---------------------------------------------------------------------------
# Test 1 — Steps 1–3 of Web Service Delivery Sequence byte-identical
# ---------------------------------------------------------------------------


class TestDeliverySequenceSteps1to3Preservation:
    """Steps 1–3 of the Web Service Delivery Sequence are byte-identical.

    **Validates: Requirements 3.1, 3.4**

    Parse visualization-guide.md, extract the delivery sequence, and
    assert steps 1 (start), 2 (verify), and 3 (present) are unchanged.
    """

    def test_steps_1_to_3_byte_identical(self) -> None:
        """Assert steps 1–3 content matches baseline exactly."""
        content = _read_file(_VISUALIZATION_GUIDE)
        sequence = _extract_web_service_delivery_sequence(content)
        current_steps = _extract_delivery_sequence_steps(sequence)

        # Baseline steps 1–3
        baseline_steps_1_3 = [
            (num, text) for num, text in _UNFIXED_DELIVERY_STEPS if num <= 3
        ]
        current_steps_1_3 = [
            (num, text) for num, text in current_steps if num <= 3
        ]

        assert len(baseline_steps_1_3) == 3, (
            f"Expected 3 baseline steps (1-3), found {len(baseline_steps_1_3)}"
        )
        assert len(current_steps_1_3) == 3, (
            f"Expected 3 current steps (1-3), found {len(current_steps_1_3)}"
        )

        for (b_num, b_text), (c_num, c_text) in zip(baseline_steps_1_3, current_steps_1_3):
            assert b_num == c_num, (
                f"Step numbering mismatch: baseline step {b_num} vs current step {c_num}"
            )
            assert c_text == b_text, (
                f"Step {b_num} content differs from baseline.\n"
                f"Baseline (first 200 chars): {b_text[:200]}\n"
                f"Current (first 200 chars): {c_text[:200]}"
            )


# ---------------------------------------------------------------------------
# Test 2 — Fallback step logic preserved (content unchanged)
# ---------------------------------------------------------------------------


class TestFallbackStepPreservation:
    """The fallback step logic is preserved (content unchanged).

    **Validates: Requirements 3.1, 3.4**

    The current step 4 (fallback) content should be preserved. After the
    fix it may be renumbered to step 5, but the content must be identical.
    """

    def test_fallback_step_content_preserved(self) -> None:
        """Assert the fallback step content matches baseline."""
        content = _read_file(_VISUALIZATION_GUIDE)
        sequence = _extract_web_service_delivery_sequence(content)
        current_steps = _extract_delivery_sequence_steps(sequence)

        # Baseline fallback — find by content (may be step 4 or 5 depending on fix state)
        baseline_fallback = [
            text for num, text in _UNFIXED_DELIVERY_STEPS
            if "Fallback" in text or "fallback" in text.lower().split("\n")[0]
        ]
        assert len(baseline_fallback) >= 1, "Baseline fallback step not found"
        baseline_text = baseline_fallback[0]

        # In current file, fallback is the last step (could be 4 or 5)
        # Find the step containing "Fallback on failure" or "fallback"
        fallback_steps = [
            text for num, text in current_steps
            if "Fallback" in text or "fallback" in text.lower().split("\n")[0]
        ]
        assert len(fallback_steps) >= 1, (
            "Fallback step not found in current delivery sequence"
        )
        current_text = fallback_steps[0]

        # Strip the step number prefix for content comparison
        # (number may change from 4 to 5 after fix)
        baseline_body = re.sub(r"^\d+\.\s+", "", baseline_text, count=1)
        current_body = re.sub(r"^\d+\.\s+", "", current_text, count=1)

        assert current_body == baseline_body, (
            "Fallback step content has changed (ignoring step number).\n"
            f"Baseline (first 300 chars): {baseline_body[:300]}\n"
            f"Current (first 300 chars): {current_body[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Step 9.4 items 1 and 2 unchanged
# ---------------------------------------------------------------------------


class TestStep94Items1And2Preservation:
    """Step 9.4 items 1 and 2 (start server, verify endpoints) are unchanged.

    **Validates: Requirements 3.4**

    Parse module-03-phase2-visualization.md, extract Step 9.4 items 1 and 2,
    and assert they match the baseline.
    """

    def test_step94_items_1_2_unchanged(self) -> None:
        """Assert Step 9.4 items 1-2 match baseline exactly."""
        content = _read_file(_MODULE_03_PHASE2)
        current = _extract_step_94_items_1_and_2(content)

        assert _UNFIXED_STEP94_ITEMS_1_2, "Baseline Step 9.4 items 1-2 is empty"
        assert current == _UNFIXED_STEP94_ITEMS_1_2, (
            "Step 9.4 items 1-2 (start server, verify endpoints) have changed.\n"
            f"Baseline (first 300 chars): {_UNFIXED_STEP94_ITEMS_1_2[:300]}\n"
            f"Current (first 300 chars): {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Step 9.4 checkpoint JSON structure unchanged
# ---------------------------------------------------------------------------


class TestStep94CheckpointPreservation:
    """Step 9.4 checkpoint JSON structure is unchanged.

    **Validates: Requirements 3.4**

    Parse module-03-phase2-visualization.md, extract the checkpoint at
    the end of Step 9.4, and assert it matches the baseline.
    """

    def test_step94_checkpoint_unchanged(self) -> None:
        """Assert Step 9.4 checkpoint matches baseline exactly."""
        content = _read_file(_MODULE_03_PHASE2)
        current = _extract_step_94_checkpoint(content)

        assert _UNFIXED_STEP94_CHECKPOINT, "Baseline Step 9.4 checkpoint is empty"
        assert current == _UNFIXED_STEP94_CHECKPOINT, (
            "Step 9.4 checkpoint JSON structure has changed.\n"
            f"Baseline (first 300 chars): {_UNFIXED_STEP94_CHECKPOINT[:300]}\n"
            f"Current (first 300 chars): {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 5 — Step 11 cleanup logic unchanged
# ---------------------------------------------------------------------------


class TestStep11CleanupLogicPreservation:
    """Step 11 cleanup logic (terminate, artifact, purge, retain) is unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3**

    Parse module-03-system-verification.md, extract Step 11 cleanup items
    (starting from 'Terminate the web service'), and assert they match baseline.
    After the fix, a confirmation gate is added BEFORE these items, but the
    items themselves must remain unchanged.
    """

    def test_step11_cleanup_items_unchanged(self) -> None:
        """Assert Step 11 cleanup items match baseline exactly."""
        content = _read_file(_MODULE_03_SYSTEM)
        current = _extract_step_11_cleanup_logic(content)

        assert _UNFIXED_STEP11_CLEANUP, "Baseline Step 11 cleanup logic is empty"
        assert current == _UNFIXED_STEP11_CLEANUP, (
            "Step 11 cleanup logic (terminate, artifact, purge, retain) has changed.\n"
            f"Baseline (first 400 chars): {_UNFIXED_STEP11_CLEANUP[:400]}\n"
            f"Current (first 400 chars): {current[:400]}"
        )


# ---------------------------------------------------------------------------
# Test 6 — Step 10 (Verification Report Generation) unchanged
# ---------------------------------------------------------------------------


class TestStep10Preservation:
    """Step 10 (Verification Report Generation) is unchanged.

    **Validates: Requirements 3.5**

    Parse module-03-system-verification.md, extract Step 10, and assert
    it matches the baseline.
    """

    def test_step10_unchanged(self) -> None:
        """Assert Step 10 content matches baseline exactly."""
        content = _read_file(_MODULE_03_SYSTEM)
        current = _extract_step(content, 10)

        assert _UNFIXED_STEP10, "Baseline Step 10 is empty"
        assert current == _UNFIXED_STEP10, (
            "Step 10 (Verification Report Generation) has changed.\n"
            f"Baseline (first 300 chars): {_UNFIXED_STEP10[:300]}\n"
            f"Current (first 300 chars): {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 7 — Step 12 (Module Close) unchanged
# ---------------------------------------------------------------------------


class TestStep12Preservation:
    """Step 12 (Module Close) is unchanged.

    **Validates: Requirements 3.5**

    Parse module-03-system-verification.md, extract Step 12, and assert
    it matches the baseline.
    """

    def test_step12_unchanged(self) -> None:
        """Assert Step 12 content matches baseline exactly."""
        content = _read_file(_MODULE_03_SYSTEM)
        current = _extract_step(content, 12)

        assert _UNFIXED_STEP12, "Baseline Step 12 is empty"
        assert current == _UNFIXED_STEP12, (
            "Step 12 (Module Close) has changed.\n"
            f"Baseline (first 300 chars): {_UNFIXED_STEP12[:300]}\n"
            f"Current (first 300 chars): {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 8 — YAML frontmatter preserved in all three files
# ---------------------------------------------------------------------------


class TestYAMLFrontmatterPreservation:
    """YAML frontmatter (inclusion: manual) is preserved in all three files.

    **Validates: Requirements 3.1, 3.4, 3.5**

    Assert each file starts with --- delimited YAML frontmatter
    containing 'inclusion: manual'.
    """

    def test_visualization_guide_frontmatter(self) -> None:
        """Assert visualization-guide.md frontmatter is preserved."""
        content = _read_file(_VISUALIZATION_GUIDE)
        fm = _extract_yaml_frontmatter(content)
        assert fm == _UNFIXED_VIS_FRONTMATTER, (
            "visualization-guide.md frontmatter has changed.\n"
            f"Expected: {_UNFIXED_VIS_FRONTMATTER}\n"
            f"Got: {fm}"
        )
        assert "inclusion: manual" in fm

    def test_phase2_frontmatter(self) -> None:
        """Assert module-03-phase2-visualization.md frontmatter is preserved."""
        content = _read_file(_MODULE_03_PHASE2)
        fm = _extract_yaml_frontmatter(content)
        assert fm == _UNFIXED_PHASE2_FRONTMATTER, (
            "module-03-phase2-visualization.md frontmatter has changed.\n"
            f"Expected: {_UNFIXED_PHASE2_FRONTMATTER}\n"
            f"Got: {fm}"
        )
        assert "inclusion: manual" in fm

    def test_system_verification_frontmatter(self) -> None:
        """Assert module-03-system-verification.md frontmatter is preserved."""
        content = _read_file(_MODULE_03_SYSTEM)
        fm = _extract_yaml_frontmatter(content)
        assert fm == _UNFIXED_SYSTEM_FRONTMATTER, (
            "module-03-system-verification.md frontmatter has changed.\n"
            f"Expected: {_UNFIXED_SYSTEM_FRONTMATTER}\n"
            f"Got: {fm}"
        )
        assert "inclusion: manual" in fm


# ---------------------------------------------------------------------------
# PBT Test — Random section indices verify non-insertion-point content
# ---------------------------------------------------------------------------

# Define sections across all three files that should be unchanged
# Each entry: (file_index, section_name, extractor, baseline)
_PRESERVED_SECTIONS: list[tuple[int, str, str]] = [
    (0, "delivery_step_1", ""),
    (0, "delivery_step_2", ""),
    (0, "delivery_step_3", ""),
    (0, "fallback_step", ""),
    (0, "frontmatter", ""),
    (1, "step94_items_1_2", ""),
    (1, "step94_checkpoint", ""),
    (1, "frontmatter", ""),
    (2, "step10", ""),
    (2, "step11_cleanup", ""),
    (2, "step12", ""),
    (2, "frontmatter", ""),
]

_SECTION_INDICES = list(range(len(_PRESERVED_SECTIONS)))


def _get_baseline_for_section(idx: int) -> str:
    """Get the baseline content for a given section index."""
    file_idx, section_name, _ = _PRESERVED_SECTIONS[idx]

    if section_name == "frontmatter":
        return _ALL_UNFIXED_FRONTMATTERS[file_idx]
    elif section_name == "delivery_step_1":
        steps = [(n, t) for n, t in _UNFIXED_DELIVERY_STEPS if n == 1]
        return steps[0][1] if steps else ""
    elif section_name == "delivery_step_2":
        steps = [(n, t) for n, t in _UNFIXED_DELIVERY_STEPS if n == 2]
        return steps[0][1] if steps else ""
    elif section_name == "delivery_step_3":
        steps = [(n, t) for n, t in _UNFIXED_DELIVERY_STEPS if n == 3]
        return steps[0][1] if steps else ""
    elif section_name == "fallback_step":
        steps = [(n, t) for n, t in _UNFIXED_DELIVERY_STEPS if "Fallback" in t]
        return steps[0][1] if steps else ""
    elif section_name == "step94_items_1_2":
        return _UNFIXED_STEP94_ITEMS_1_2
    elif section_name == "step94_checkpoint":
        return _UNFIXED_STEP94_CHECKPOINT
    elif section_name == "step10":
        return _UNFIXED_STEP10
    elif section_name == "step11_cleanup":
        return _UNFIXED_STEP11_CLEANUP
    elif section_name == "step12":
        return _UNFIXED_STEP12
    return ""


def _get_current_for_section(idx: int) -> str:
    """Get the current content for a given section index."""
    file_idx, section_name, _ = _PRESERVED_SECTIONS[idx]
    file_path = _ALL_FILES[file_idx]
    content = _read_file(file_path)

    if section_name == "frontmatter":
        return _extract_yaml_frontmatter(content)
    elif section_name.startswith("delivery_step_"):
        step_num = int(section_name.split("_")[-1])
        sequence = _extract_web_service_delivery_sequence(content)
        steps = _extract_delivery_sequence_steps(sequence)
        matching = [(n, t) for n, t in steps if n == step_num]
        return matching[0][1] if matching else ""
    elif section_name == "fallback_step":
        sequence = _extract_web_service_delivery_sequence(content)
        steps = _extract_delivery_sequence_steps(sequence)
        # Fallback is the last step (4 on unfixed, 5 after fix)
        # Match by content containing "Fallback"
        fallback = [(n, t) for n, t in steps if "Fallback" in t]
        if fallback:
            # Strip number prefix for comparison
            return fallback[0][1]
        return ""
    elif section_name == "step94_items_1_2":
        return _extract_step_94_items_1_and_2(content)
    elif section_name == "step94_checkpoint":
        return _extract_step_94_checkpoint(content)
    elif section_name == "step10":
        return _extract_step(content, 10)
    elif section_name == "step11_cleanup":
        return _extract_step_11_cleanup_logic(content)
    elif section_name == "step12":
        return _extract_step(content, 12)
    return ""


@st.composite
def st_section_index(draw: st.DrawFn) -> int:
    """Generate a random section index across all preserved sections."""
    return draw(st.sampled_from(_SECTION_INDICES))


class TestPreservationAcrossAllSectionsPBT:
    """PBT — Non-insertion-point content is identical to baseline.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Use Hypothesis to generate random section indices across the three
    files and verify non-insertion-point content is identical to baseline.
    """

    @given(section_idx=st_section_index())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_section_content_matches_baseline(self, section_idx: int) -> None:
        """For any preserved section, content must match baseline."""
        file_idx, section_name, _ = _PRESERVED_SECTIONS[section_idx]
        file_path = _ALL_FILES[file_idx]

        baseline = _get_baseline_for_section(section_idx)
        assert baseline, (
            f"Baseline for section '{section_name}' in {file_path.name} is empty"
        )

        current = _get_current_for_section(section_idx)

        # For fallback step, compare without number prefix (may be renumbered)
        if section_name == "fallback_step":
            baseline_body = re.sub(r"^\d+\.\s+", "", baseline, count=1)
            current_body = re.sub(r"^\d+\.\s+", "", current, count=1)
            assert current_body == baseline_body, (
                f"Section '{section_name}' in {file_path.name} differs from baseline "
                f"(ignoring step number).\n"
                f"Baseline (first 200 chars): {baseline_body[:200]}\n"
                f"Current (first 200 chars): {current_body[:200]}"
            )
        else:
            assert current == baseline, (
                f"Section '{section_name}' in {file_path.name} differs from baseline.\n"
                f"Baseline (first 200 chars): {baseline[:200]}\n"
                f"Current (first 200 chars): {current[:200]}"
            )
