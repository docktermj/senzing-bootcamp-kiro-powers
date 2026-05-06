"""Tests for the Guided Rollback with Diff Preview feature.

Validates that rollback_module.py supports --preview/--dry-run and --yes/-y flags,
and that module-completion.md instructs the agent to run preview before rollback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _ROOT / "senzing-bootcamp" / "scripts"
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"


class TestRollbackPreviewFlags:
    """Verify rollback_module.py supports --preview and --yes flags."""

    def test_preview_flag_accepted(self) -> None:
        """--preview flag is accepted by argparse."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
             "--preview", "--module", "3"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        assert result.returncode == 0

    def test_dry_run_flag_accepted(self) -> None:
        """--dry-run flag is accepted by argparse (original name)."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
             "--dry-run", "--module", "3"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        assert result.returncode == 0

    def test_yes_flag_accepted(self) -> None:
        """--yes flag is accepted by argparse."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
             "--yes", "--module", "3", "--dry-run"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        assert result.returncode == 0

    def test_y_short_flag_accepted(self) -> None:
        """-y short flag is accepted by argparse."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
             "-y", "--module", "3", "--dry-run"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        assert result.returncode == 0

    def test_preview_always_exits_zero(self) -> None:
        """--preview always exits with code 0 regardless of module state."""
        for mod in [1, 5, 11]:
            result = subprocess.run(
                [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
                 "--preview", "--module", str(mod)],
                capture_output=True, text=True, cwd=str(_ROOT),
            )
            assert result.returncode == 0, f"Module {mod} preview failed"


class TestRollbackPreviewOutput:
    """Verify preview output contains expected elements."""

    def test_preview_contains_no_changes_made(self) -> None:
        """Preview output contains 'No changes made' or 'Nothing to roll back'."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "rollback_module.py"),
             "--preview", "--module", "3"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        output = result.stdout
        assert "No changes made" in output or "Nothing to roll back" in output


class TestModuleCompletionSteering:
    """Verify module-completion.md instructs agent to run preview before rollback."""

    @pytest.fixture()
    def module_completion(self) -> str:
        path = _STEERING_DIR / "module-completion.md"
        return path.read_text(encoding="utf-8")

    def test_contains_preview_instruction(self, module_completion: str) -> None:
        """module-completion.md instructs running --preview before rollback."""
        assert "--preview" in module_completion

    def test_contains_confirmation_instruction(self, module_completion: str) -> None:
        """module-completion.md requires confirmation before executing rollback."""
        assert "confirmation" in module_completion.lower() or \
               "after explicit confirmation" in module_completion.lower()

    def test_contains_safety_assessment_mention(self, module_completion: str) -> None:
        """module-completion.md mentions safety assessment in preview context."""
        assert "safety assessment" in module_completion.lower()


class TestRollbackSafetyAssessment:
    """Verify the format_dry_run_report includes safety assessment."""

    def test_safety_assessment_in_format(self) -> None:
        """format_dry_run_report includes Safety Assessment section."""
        sys.path.insert(0, str(_SCRIPTS_DIR))
        try:
            from rollback_module import format_dry_run_report, ModuleArtifacts
            artifacts = ModuleArtifacts(
                files=["src/load/load.py", "docs/loading_strategy.md"],
                directories=["src/load"],
                modifies_database=True,
            )
            report = format_dry_run_report(
                module=6,
                artifacts=artifacts,
                existing_files=["src/load/load.py"],
                existing_dirs=["src/load"],
                missing_items=["docs/loading_strategy.md"],
                backup_path="/backups/backup_2026.zip",
                downstream_completed=[7],
                progress_changes={"modules_completed": "remove 6"},
            )
            assert "Safety Assessment" in report
            assert "Backed up:" in report
            assert "Fully reversible:" in report
        finally:
            sys.path.pop(0)
