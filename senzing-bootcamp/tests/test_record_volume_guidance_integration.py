"""Integration tests for record volume guidance feature.

Tests end-to-end flow (parse → classify → persist → read back → generate guidance)
and validates steering file structure consistency (step numbering, phase ranges).

Requirements validated: 2.1, 2.2, 7.1, 7.2, 7.5
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import volume_utils  # noqa: E402


# ---------------------------------------------------------------------------
# TestEndToEndFlow
# ---------------------------------------------------------------------------


class TestEndToEndFlow:
    """Full pipeline tests: parse → classify → persist → read back → generate guidance."""

    def test_medium_tier_end_to_end(self, tmp_path: Path) -> None:
        """Parse '1M' → classify → persist → read back → verify tier=medium → generate guidance.

        Validates: Requirements 2.1, 2.2
        """
        prefs_path = tmp_path / "config" / "bootcamp_preferences.yaml"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        # Parse
        raw_value = volume_utils.parse_volume_input("1M")
        assert raw_value == 1_000_000

        # Classify
        tier = volume_utils.classify_tier(raw_value)
        assert tier == "medium"

        # Persist
        volume_utils.persist_volume_selection(
            raw_value=raw_value,
            tier=tier,
            preferences_path=str(prefs_path),
            progress_path=str(progress_path),
            step_number=1,
        )

        # Read back preferences
        prefs_content = prefs_path.read_text(encoding="utf-8")
        assert "raw_value: 1000000" in prefs_content
        assert "tier: medium" in prefs_content

        # Read back progress
        progress_data = json.loads(progress_path.read_text(encoding="utf-8"))
        assert progress_data["current_step"] == 1

        # Generate all guidance types and verify non-empty strings
        license_guidance = volume_utils.get_license_guidance(tier)
        assert isinstance(license_guidance, str)
        assert len(license_guidance) > 0

        arch_guidance = volume_utils.get_architecture_guidance(tier)
        assert isinstance(arch_guidance, str)
        assert len(arch_guidance) > 0

        db_guidance = volume_utils.get_database_guidance(tier)
        assert isinstance(db_guidance, str)
        assert len(db_guidance) > 0

        perf_guidance = volume_utils.get_performance_guidance(tier)
        assert isinstance(perf_guidance, str)
        assert len(perf_guidance) > 0

    def test_demo_tier_end_to_end(self, tmp_path: Path) -> None:
        """Parse '100' → classify → persist → verify tier=demo → license mentions evaluation.

        Validates: Requirements 2.1, 2.2
        """
        prefs_path = tmp_path / "config" / "bootcamp_preferences.yaml"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        # Parse
        raw_value = volume_utils.parse_volume_input("100")
        assert raw_value == 100

        # Classify
        tier = volume_utils.classify_tier(raw_value)
        assert tier == "demo"

        # Persist
        volume_utils.persist_volume_selection(
            raw_value=raw_value,
            tier=tier,
            preferences_path=str(prefs_path),
            progress_path=str(progress_path),
            step_number=1,
        )

        # Read back and verify
        prefs_content = prefs_path.read_text(encoding="utf-8")
        assert "raw_value: 100" in prefs_content
        assert "tier: demo" in prefs_content

        # License guidance mentions evaluation
        license_guidance = volume_utils.get_license_guidance(tier)
        assert license_guidance is not None
        assert "evaluation" in license_guidance.lower()

    def test_large_tier_end_to_end(self, tmp_path: Path) -> None:
        """Parse '50 million' → classify → persist → verify tier=large → arch mentions distributed.

        Validates: Requirements 2.1, 2.2
        """
        prefs_path = tmp_path / "config" / "bootcamp_preferences.yaml"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        # Parse
        raw_value = volume_utils.parse_volume_input("50 million")
        assert raw_value == 50_000_000

        # Classify
        tier = volume_utils.classify_tier(raw_value)
        assert tier == "large"

        # Persist
        volume_utils.persist_volume_selection(
            raw_value=raw_value,
            tier=tier,
            preferences_path=str(prefs_path),
            progress_path=str(progress_path),
            step_number=1,
        )

        # Read back and verify
        prefs_content = prefs_path.read_text(encoding="utf-8")
        assert "raw_value: 50000000" in prefs_content
        assert "tier: large" in prefs_content

        # Architecture guidance mentions distributed
        arch_guidance = volume_utils.get_architecture_guidance(tier)
        assert "distributed" in arch_guidance.lower()


# ---------------------------------------------------------------------------
# TestSteeringFileStructure
# ---------------------------------------------------------------------------


class TestSteeringFileStructure:
    """Validate steering files are consistent with the spec."""

    def test_phase_a_step_numbering(self) -> None:
        """Verify module-06-phaseA-build-loading.md has steps 1-4 in order.

        Step 1 should have 'Assess production record volume' title.
        Each step has a checkpoint line with matching step number.

        Validates: Requirements 7.1
        """
        phase_a_path = _STEERING_DIR / "module-06-phaseA-build-loading.md"
        content = phase_a_path.read_text(encoding="utf-8")

        # Verify step 1 exists with correct title
        assert re.search(
            r"^1\.\s+\*\*Assess production record volume", content, re.MULTILINE
        ), "Step 1 with 'Assess production record volume' title not found"

        # Verify steps are numbered 1, 2, 3, 4 in order
        step_pattern = re.compile(r"^(\d+)\.\s+\*\*", re.MULTILINE)
        step_numbers = [int(m.group(1)) for m in step_pattern.finditer(content)]
        assert step_numbers == [1, 2, 3, 4], (
            f"Expected steps [1, 2, 3, 4], got {step_numbers}"
        )

        # Verify each step has a checkpoint line with matching step number
        checkpoint_pattern = re.compile(
            r"\*\*Checkpoint:\*\*.*(?:Write|write)\s+step\s+(\d+)", re.MULTILINE
        )
        checkpoint_numbers = [int(m.group(1)) for m in checkpoint_pattern.finditer(content)]
        assert checkpoint_numbers == [1, 2, 3, 4], (
            f"Expected checkpoint steps [1, 2, 3, 4], got {checkpoint_numbers}"
        )

    def test_steering_index_module6_phase_ranges(self) -> None:
        """Verify steering-index.yaml Module 6 phase step_range values.

        Validates: Requirements 7.5
        """
        index_path = _STEERING_DIR / "steering-index.yaml"
        content = index_path.read_text(encoding="utf-8")

        # Parse step_range values for Module 6 phases using regex
        # Look for phase entries under module 6
        phase1_match = re.search(
            r"phase1-build-loading-program:.*?step_range:\s*\[(\d+),\s*(\d+)\]",
            content, re.DOTALL,
        )
        phase2_match = re.search(
            r"phase2-load-first-source:.*?step_range:\s*\[(\d+),\s*(\d+)\]",
            content, re.DOTALL,
        )
        phase3_match = re.search(
            r"phase3-multi-source-orchestration:.*?step_range:\s*\[(\d+),\s*(\d+)\]",
            content, re.DOTALL,
        )
        phase4_match = re.search(
            r"phase4-validation:.*?step_range:\s*\[(\d+),\s*(\d+)\]",
            content, re.DOTALL,
        )

        assert phase1_match is not None, "phase1-build-loading-program not found"
        assert phase2_match is not None, "phase2-load-first-source not found"
        assert phase3_match is not None, "phase3-multi-source-orchestration not found"
        assert phase4_match is not None, "phase4-validation not found"

        # Verify step ranges
        assert (int(phase1_match.group(1)), int(phase1_match.group(2))) == (1, 4)
        assert (int(phase2_match.group(1)), int(phase2_match.group(2))) == (5, 11)
        assert (int(phase3_match.group(1)), int(phase3_match.group(2))) == (12, 20)
        assert (int(phase4_match.group(1)), int(phase4_match.group(2))) == (21, 28)

    def test_module6_root_phase_sub_files_ranges(self) -> None:
        """Verify module-06-data-processing.md phase sub-files section mentions correct ranges.

        Validates: Requirements 7.2
        """
        root_path = _STEERING_DIR / "module-06-data-processing.md"
        content = root_path.read_text(encoding="utf-8")

        # Phase A: steps 1–4
        assert re.search(
            r"Phase A.*steps\s+1.4", content
        ), "Phase A should reference steps 1–4"

        # Phase B: steps 5–11
        assert re.search(
            r"Phase B.*steps\s+5.11", content
        ), "Phase B should reference steps 5–11"

        # Phase C: steps 12–20
        assert re.search(
            r"Phase C.*steps\s+12.20", content
        ), "Phase C should reference steps 12–20"

        # Phase D: steps 21–28
        assert re.search(
            r"Phase D.*steps\s+21.28", content
        ), "Phase D should reference steps 21–28"
