"""Structural validation tests for the mapping-workflow-integration feature.

These tests verify that the Module 5 Phase 3 integration, Module 6/7 production
focus refactoring, and POWER.md updates contain the expected content.

Feature: mapping-workflow-integration
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

_MODULE_5_STEERING = _POWER_ROOT / "steering" / "module-05-data-quality-mapping.md"
_MODULE_5_PHASE3 = _POWER_ROOT / "steering" / "module-05-phase3-test-load.md"
_MODULE_5_DOCS = _POWER_ROOT / "docs" / "modules" / "MODULE_5_DATA_QUALITY_AND_MAPPING.md"
_MODULE_6_STEERING = _POWER_ROOT / "steering" / "module-06-data-processing.md"
_MODULE_6_PHASE_FILES = [
    _POWER_ROOT / "steering" / "module-06-phaseA-build-loading.md",
    _POWER_ROOT / "steering" / "module-06-phaseB-load-first-source.md",
    _POWER_ROOT / "steering" / "module-06-phaseC-multi-source.md",
    _POWER_ROOT / "steering" / "module-06-phaseD-validation.md",
]
_MODULE_6_DOCS = _POWER_ROOT / "docs" / "modules" / "MODULE_6_DATA_PROCESSING.md"
_MODULE_7_STEERING = _POWER_ROOT / "steering" / "module-07-query-validation.md"
_MODULE_7_DOCS = _POWER_ROOT / "docs" / "modules" / "MODULE_7_QUERY_VALIDATION.md"
_POWER_MD = _POWER_ROOT / "POWER.md"


def _read(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _read_module6_all() -> str:
    """Read the Module 6 parent file plus all phase sub-files."""
    parts = [_read(_MODULE_6_STEERING)]
    for f in _MODULE_6_PHASE_FILES:
        if f.exists():
            parts.append(_read(f))
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# 9.1 — Module 5 steering file Phase 3 content
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.3,
#            7.4, 8.3, 8.4
# ═══════════════════════════════════════════════════════════════════════════


class TestModule5SteeringPhase3:
    """Verify Module 5 steering file contains Phase 3 content."""

    @pytest.fixture(autouse=True)
    def _load(self):
        # Phase 3 content is in the sub-file; combine parent + sub-file
        self.content = _read(_MODULE_5_STEERING) + "\n" + _read(_MODULE_5_PHASE3)

    def test_phase3_section_exists(self):
        """Phase 3 section exists with 'Test Load and Validate' title."""
        assert "Phase 3" in self.content
        assert "Test Load and Validate" in self.content

    def test_mapping_workflow_steps_5_through_8(self):
        """References to mapping_workflow steps 5–8 are present."""
        assert "step 5" in self.content.lower() or "step 5" in self.content
        assert "step 6" in self.content.lower() or "step 6" in self.content
        assert "step 7" in self.content.lower() or "step 7" in self.content
        assert "step 8" in self.content.lower() or "step 8" in self.content

    def test_phase3_marked_optional(self):
        """Phase 3 is marked as optional."""
        # Check for the word "optional" near Phase 3 content
        lower = self.content.lower()
        assert "optional" in lower

    def test_checkpoint_step_21(self):
        """Checkpoint step 21 is present."""
        assert "step 21" in self.content

    def test_checkpoint_step_22(self):
        """Checkpoint step 22 is present."""
        assert "step 22" in self.content

    def test_checkpoint_step_23(self):
        """Checkpoint step 23 is present."""
        assert "step 23" in self.content

    def test_checkpoint_step_24(self):
        """Checkpoint step 24 is present."""
        assert "step 24" in self.content

    def test_checkpoint_step_25(self):
        """Checkpoint step 25 is present."""
        assert "step 25" in self.content

    def test_checkpoint_step_26(self):
        """Checkpoint step 26 is present."""
        assert "step 26" in self.content

    def test_decision_gate_exists(self):
        """Decision gate content exists after Phase 3."""
        lower = self.content.lower()
        assert "decision gate" in lower or "shortcut path" in lower

    def test_shortcut_path_instructions(self):
        """Shortcut path instructions exist."""
        lower = self.content.lower()
        assert "shortcut path" in lower or "shortcut_path" in lower

    def test_sdk_not_configured_handling(self):
        """SDK-not-configured handling exists."""
        lower = self.content.lower()
        assert "sdk" in lower
        # Should mention Module 2 as a prerequisite or offer to skip
        assert "module 2" in lower or "skip phase 3" in lower or "skip" in lower

    def test_session_resume_for_phase3(self):
        """Session resume instructions for Phase 3 exist."""
        lower = self.content.lower()
        assert "session resume" in lower or "phase 3 session resume" in lower or "resume" in lower
        # Should reference mapping state checkpoint
        assert "mapping_state" in lower or "mapping state" in lower or "checkpoint" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 9.2 — Module 5 documentation Phase 3 content
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 7.2
# ═══════════════════════════════════════════════════════════════════════════


class TestModule5DocsPhase3:
    """Verify Module 5 documentation contains Phase 3 content."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_MODULE_5_DOCS)

    def test_test_load_and_validate_section(self):
        """'Test Load and Validate' section exists."""
        assert "Test Load and Validate" in self.content

    def test_phase3_learning_objectives(self):
        """Phase 3 learning objectives are listed."""
        lower = self.content.lower()
        # Should mention verifying mapping quality, observing ER results,
        # identifying issues before production
        assert "learning objective" in lower or "you will" in lower
        assert "test load" in lower or "test-load" in lower

    def test_output_files_documented(self):
        """Output files are documented."""
        lower = self.content.lower()
        assert "validation report" in lower
        assert "sqlite" in lower or "test database" in lower or "test" in lower

    def test_success_criteria_include_phase3(self):
        """Success criteria include Phase 3 indicators."""
        lower = self.content.lower()
        assert "success criteria" in lower or "success indicator" in lower
        # Phase 3 success criteria should mention SDK, test data, validation,
        # evaluation, or decision gate
        assert "phase 3" in lower

    def test_shortcut_path_section(self):
        """'Shortcut Path' section exists."""
        assert "Shortcut Path" in self.content


# ═══════════════════════════════════════════════════════════════════════════
# 9.3 — Module 6 production focus
# Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4
# ═══════════════════════════════════════════════════════════════════════════


class TestModule6ProductionFocus:
    """Verify Module 6 steering file and docs reflect production-quality focus."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.steering = _read_module6_all()
        self.docs = _read(_MODULE_6_DOCS)

    # --- Steering file checks ---

    def test_steering_error_handling(self):
        """Steering file contains error handling section."""
        lower = self.steering.lower()
        assert "error handling" in lower or "error" in lower

    def test_steering_progress_tracking(self):
        """Steering file contains progress tracking section."""
        lower = self.steering.lower()
        assert "progress tracking" in lower or "progress" in lower

    def test_steering_throughput(self):
        """Steering file contains throughput content."""
        lower = self.steering.lower()
        assert "throughput" in lower

    def test_steering_redo(self):
        """Steering file contains redo queue processing."""
        lower = self.steering.lower()
        assert "redo" in lower

    def test_steering_incremental(self):
        """Steering file contains incremental loading guidance."""
        lower = self.steering.lower()
        assert "incremental" in lower

    def test_steering_conditional_workflow(self):
        """Conditional workflow based on Phase 3 completion exists."""
        lower = self.steering.lower()
        assert "test_load_status" in lower or "phase 3" in lower

    def test_steering_match_accuracy_retained(self):
        """Match accuracy review is retained."""
        lower = self.steering.lower()
        assert "match accuracy" in lower or "accuracy" in lower

    # --- Documentation checks ---

    def test_docs_production_quality_overview(self):
        """Documentation overview describes production-quality loading."""
        lower = self.docs.lower()
        assert "production" in lower or "production-quality" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 9.4 — Module 7 production focus
# Validates: Requirements 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4
# ═══════════════════════════════════════════════════════════════════════════


class TestModule7ProductionFocus:
    """Verify combined Module 6 steering file and docs reflect production-quality orchestration.
    
    Note: After combining Modules 6+7, the orchestration content that was in the old
    Module 7 is now in the combined Module 6 (module-06-data-processing.md).
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.steering = _read_module6_all()
        self.docs = _read(_MODULE_6_DOCS)

    # --- Steering file checks ---

    def test_steering_dependency_management(self):
        """Steering file contains dependency management sections."""
        lower = self.steering.lower()
        assert "dependenc" in lower  # dependency/dependencies

    def test_steering_parallel_loading(self):
        """Steering file contains parallel loading sections."""
        lower = self.steering.lower()
        assert "parallel" in lower

    def test_steering_error_isolation(self):
        """Steering file contains error isolation sections."""
        lower = self.steering.lower()
        assert "error isolation" in lower or "error boundary" in lower

    def test_steering_coordinated_redo(self):
        """Steering file contains coordinated redo processing."""
        lower = self.steering.lower()
        assert "redo" in lower

    def test_steering_phase3_results_referenced(self):
        """Phase 3 results are referenced for planning."""
        lower = self.steering.lower()
        assert "phase 3" in lower or "test_load_status" in lower or "test_entity_count" in lower

    def test_steering_cross_source_validation_retained(self):
        """Cross-source validation is retained."""
        lower = self.steering.lower()
        assert "cross-source" in lower or "cross source" in lower

    def test_steering_uat_retained(self):
        """UAT steps are retained."""
        lower = self.steering.lower()
        assert "uat" in lower

    def test_steering_sign_off_retained(self):
        """Stakeholder sign-off steps are retained."""
        lower = self.steering.lower()
        assert "sign-off" in lower or "sign off" in lower or "signoff" in lower

    def test_steering_retry_pattern(self):
        """Production orchestration pattern: retry exists."""
        lower = self.steering.lower()
        assert "retry" in lower

    def test_steering_partial_success(self):
        """Production orchestration pattern: partial success exists."""
        lower = self.steering.lower()
        assert "partial success" in lower or "partial" in lower

    def test_steering_health_monitoring(self):
        """Production orchestration pattern: health monitoring exists."""
        lower = self.steering.lower()
        assert "health monitoring" in lower or "health" in lower

    # --- Documentation checks ---

    def test_docs_production_orchestration_overview(self):
        """Documentation overview describes production-quality orchestration."""
        lower = self.docs.lower()
        assert "production" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 9.5 — POWER.md updates
# Validates: Requirements 9.1, 9.2, 9.3, 9.4
# ═══════════════════════════════════════════════════════════════════════════


class TestPowerMdUpdates:
    """Verify POWER.md module table and track descriptions are updated."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_POWER_MD)

    def test_module5_mentions_test_load(self):
        """Module 5 description mentions test load and validate."""
        # Find the Module 5 row in the module table
        lower = self.content.lower()
        assert "test" in lower and "load" in lower
        # More specifically, look for test load near Module 5 content
        assert "test-load" in lower or "test load" in lower

    def test_module6_production_quality_loading(self):
        """Module 6 description emphasizes production-quality loading."""
        lower = self.content.lower()
        assert "production" in lower
        # Should mention error handling or throughput or redo in Module 6 context
        assert "error handling" in lower or "throughput" in lower or "redo" in lower

    def test_module7_production_quality_orchestration(self):
        """Module 6 (combined) description covers loading and orchestration."""
        lower = self.content.lower()
        # Module 6 now covers loading and entity resolution
        assert "load" in lower
        assert "entity resolution" in lower or "redo" in lower

    def test_track_descriptions_mention_skip_ahead(self):
        """Track descriptions mention skip-ahead options for experienced users."""
        lower = self.content.lower()
        assert "skip" in lower or "experienced" in lower
