"""Property-based, unit, and integration tests for rollback verification.

Tests the post-rollback verification feature: VerificationResult dataclass,
verify_rollback function, updated RollbackLogEntry/build_log_entry, and
integration with the main rollback flow.

Uses Hypothesis for property-based tests and pytest for example-based tests.
"""

import dataclasses
import json
import sys
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from rollback_module import (
    ARTIFACT_MANIFEST,
    MODULE_NAMES,
    RemovalResult,
    RollbackLogEntry,
    VerificationResult,
    build_log_entry,
    format_dry_run_report,
    main,
    serialize_log_entry,
    verify_rollback,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies (Task 4.1)
# ---------------------------------------------------------------------------


def _module_numbers():
    """Strategy producing valid module numbers 1-11."""
    return st.integers(min_value=1, max_value=11)


def _check_description():
    """Strategy producing non-empty text for check descriptions."""
    return st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Z"),
                               whitelist_characters=" _-/."),
        min_size=1, max_size=60,
    ).filter(lambda s: s.strip())


def _check_detail():
    """Strategy producing text for check detail strings."""
    return st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Z"),
                               whitelist_characters=" _-/."),
        min_size=0, max_size=60,
    )


def _all_false_check_tuples():
    """Strategy producing lists of (ok=False, description, detail) tuples."""
    return st.lists(
        st.tuples(st.just(False), _check_description(), _check_detail()),
        min_size=0, max_size=8,
    )


def _some_true_check_tuples():
    """Strategy producing lists of check tuples with at least one ok=True."""
    return st.lists(
        st.tuples(st.booleans(), _check_description(), _check_detail()),
        min_size=1, max_size=8,
    ).filter(lambda checks: any(ok for ok, _, _ in checks))


def _any_check_tuples():
    """Strategy producing arbitrary lists of check tuples."""
    return st.lists(
        st.tuples(st.booleans(), _check_description(), _check_detail()),
        min_size=0, max_size=8,
    )


def _removal_result():
    """Strategy producing a minimal RemovalResult for log entry tests."""
    return st.builds(
        RemovalResult,
        removed_files=st.just([]),
        removed_dirs=st.just([]),
        skipped_missing=st.just([]),
        failed_items=st.just([]),
    )


# ---------------------------------------------------------------------------
# Task 4.2: Property 1 — Validator Invocation with Correct Module
# ---------------------------------------------------------------------------


class TestProperty1ValidatorInvocation:
    """Feature: rollback-verification, Property 1: Validator Invocation with Correct Module

    For any module number in [1, 11], verify_rollback calls the validator
    for exactly that module number (mock VALIDATORS to track calls).

    **Validates: Requirements 1.1**
    """

    @given(module=_module_numbers())
    @settings(max_examples=100)
    def test_verify_rollback_calls_correct_validator(self, module):
        """Feature: rollback-verification, Property 1: Validator Invocation with Correct Module"""
        called_with = []

        def fake_validator():
            called_with.append(module)
            return [(False, "check", "detail")]

        fake_validators = {module: fake_validator}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(module)

        assert len(called_with) == 1
        assert called_with[0] == module
        assert isinstance(result, VerificationResult)


# ---------------------------------------------------------------------------
# Task 4.3: Property 2 — Verification Passed Output and Log
# ---------------------------------------------------------------------------


class TestProperty2VerificationPassed:
    """Feature: rollback-verification, Property 2: Verification Passed Output and Log

    For any list of check tuples where all ok=False, verify_rollback returns
    status="passed" with empty leftover_checks, and the resulting log entry
    contains "verification": "passed".

    **Validates: Requirements 1.2, 3.1**
    """

    @given(checks=_all_false_check_tuples(), module=_module_numbers())
    @settings(max_examples=100)
    def test_all_false_returns_passed(self, checks, module):
        """Feature: rollback-verification, Property 2: Verification Passed Output and Log"""
        fake_validators = {module: lambda: checks}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(module)

        assert result.status == "passed"
        assert result.leftover_checks == []

        # Verify log entry records the verification outcome
        removal = RemovalResult([], [], [], [])
        entry = build_log_entry(module, removal, None, None, [],
                                verification=result.status,
                                leftover_checks=result.leftover_checks)
        assert entry.verification == "passed"
        assert entry.leftover_checks == []

        # Verify serialized JSON
        parsed = json.loads(serialize_log_entry(entry))
        assert parsed["verification"] == "passed"
        assert parsed["leftover_checks"] == []


# ---------------------------------------------------------------------------
# Task 4.4: Property 3 — Verification Failed Output and Log
# ---------------------------------------------------------------------------


class TestProperty3VerificationFailed:
    """Feature: rollback-verification, Property 3: Verification Failed Output and Log

    For any list of check tuples with at least one ok=True, verify_rollback
    returns status="failed" with leftover_checks containing exactly the
    descriptions of ok=True checks, and the resulting log entry contains
    "verification": "failed" with the correct leftover_checks.

    **Validates: Requirements 1.3, 3.2**
    """

    @given(checks=_some_true_check_tuples(), module=_module_numbers())
    @settings(max_examples=100)
    def test_some_true_returns_failed_with_correct_leftovers(self, checks, module):
        """Feature: rollback-verification, Property 3: Verification Failed Output and Log"""
        expected_leftovers = [desc for ok, desc, _ in checks if ok]
        fake_validators = {module: lambda: checks}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(module)

        assert result.status == "failed"
        assert result.leftover_checks == expected_leftovers

        # Verify log entry records the verification outcome
        removal = RemovalResult([], [], [], [])
        entry = build_log_entry(module, removal, None, None, [],
                                verification=result.status,
                                leftover_checks=result.leftover_checks)
        assert entry.verification == "failed"
        assert entry.leftover_checks == expected_leftovers

        # Verify serialized JSON
        parsed = json.loads(serialize_log_entry(entry))
        assert parsed["verification"] == "failed"
        assert parsed["leftover_checks"] == expected_leftovers


# ---------------------------------------------------------------------------
# Task 4.5: Property 4 — Dry-Run Skips Verification
# ---------------------------------------------------------------------------


class TestProperty4DryRunSkipsVerification:
    """Feature: rollback-verification, Property 4: Dry-Run Skips Verification

    For any module number, when dry-run is active, the validator is not called
    and the log entry contains "verification": null.

    **Validates: Requirements 2.1, 2.2, 3.3**
    """

    @given(module=_module_numbers())
    @settings(max_examples=100)
    def test_dry_run_skips_verification(self, module):
        """Feature: rollback-verification, Property 4: Dry-Run Skips Verification"""
        import tempfile

        validator_called = []

        def tracking_validator():
            validator_called.append(True)
            return [(False, "check", "detail")]

        fake_validators = {module: tracking_validator}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifacts = ARTIFACT_MANIFEST[module]

            # Create at least one artifact so there's something to report
            for f in artifacts.files:
                fp = root / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("content", encoding="utf-8")
            for d in artifacts.directories:
                dp = root / d
                dp.mkdir(parents=True, exist_ok=True)

            # Create progress file
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            progress = {
                "modules_completed": [module],
                "current_module": module,
                "current_step": 1,
                "step_history": {},
                "data_sources": [],
                "database_type": "sqlite",
            }
            (config_dir / "bootcamp_progress.json").write_text(
                json.dumps(progress, indent=2), encoding="utf-8"
            )

            scripts_dir = root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            fake_script = str(scripts_dir / "rollback_module.py")

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("sys.stdout", buf), \
                 mock.patch.dict(
                     "sys.modules",
                     {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
                 ):
                exit_code = main(["--module", str(module), "--dry-run"])

            assert exit_code == 0
            # Validator should NOT have been called during dry-run
            assert len(validator_called) == 0

            # Dry-run output should not contain verification results
            output = buf.getvalue()
            assert "Verification passed" not in output
            assert "Verification warning" not in output


# ---------------------------------------------------------------------------
# Task 5: Example-based unit tests
# ---------------------------------------------------------------------------


class TestVerifyRollbackUnit:
    """Example-based unit tests for verify_rollback and related functions."""

    def test_all_checks_false_returns_passed(self):
        """5.1: verify_rollback with all checks returning ok=False returns
        status='passed' and empty leftover_checks."""
        checks = [
            (False, "Business problem documented", "docs/business_problem.md not found"),
        ]
        fake_validators = {1: lambda: checks}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(1)

        assert result.status == "passed"
        assert result.leftover_checks == []

    def test_mixed_checks_returns_failed(self):
        """5.2: verify_rollback with mixed checks (some ok=True) returns
        status='failed' and correct leftover_checks list."""
        checks = [
            (False, "Check A", "detail A"),
            (True, "Check B still passes", "path/b"),
            (False, "Check C", "detail C"),
            (True, "Check D still passes", "path/d"),
        ]
        fake_validators = {5: lambda: checks}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(5)

        assert result.status == "failed"
        assert result.leftover_checks == ["Check B still passes", "Check D still passes"]

    def test_validator_raises_returns_none(self):
        """5.3: verify_rollback when validator raises RuntimeError returns
        status=None and empty leftover_checks (Req 1.4)."""
        def exploding_validator():
            raise RuntimeError("Unexpected error reading file")

        fake_validators = {3: exploding_validator}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(3)

        assert result.status is None
        assert result.leftover_checks == []

    def test_empty_check_list_returns_passed(self):
        """5.4: verify_rollback when validator returns empty list returns
        status='passed'."""
        fake_validators = {2: lambda: []}

        with mock.patch.dict(
            "sys.modules",
            {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
        ):
            result = verify_rollback(2)

        assert result.status == "passed"
        assert result.leftover_checks == []

    def test_build_log_entry_verification_passed(self):
        """5.5: build_log_entry with verification='passed' produces log entry
        with verification field."""
        removal = RemovalResult(
            removed_files=["docs/business_problem.md"],
            removed_dirs=[],
            skipped_missing=[],
            failed_items=[],
        )
        entry = build_log_entry(1, removal, None, None, [],
                                verification="passed", leftover_checks=[])

        assert entry.verification == "passed"
        assert entry.leftover_checks == []

    def test_build_log_entry_verification_failed_with_leftovers(self):
        """5.6: build_log_entry with verification='failed' and leftover_checks
        produces log entry with both fields."""
        removal = RemovalResult(
            removed_files=["docs/data_source_evaluation.md"],
            removed_dirs=[],
            skipped_missing=[],
            failed_items=[],
        )
        leftovers = ["Transformation program(s) created", "Transformed JSONL file(s) created"]
        entry = build_log_entry(5, removal, None, None, [],
                                verification="failed", leftover_checks=leftovers)

        assert entry.verification == "failed"
        assert entry.leftover_checks == leftovers

    def test_build_log_entry_verification_none(self):
        """5.7: build_log_entry with verification=None produces log entry
        with null verification."""
        removal = RemovalResult(
            removed_files=[],
            removed_dirs=[],
            skipped_missing=[],
            failed_items=[],
        )
        entry = build_log_entry(1, removal, None, None, [],
                                verification=None, leftover_checks=[])

        assert entry.verification is None
        assert entry.leftover_checks == []

    def test_serialize_roundtrip_preserves_verification_fields(self):
        """5.8: serialize_log_entry round-trip preserves verification and
        leftover_checks fields."""
        removal = RemovalResult(
            removed_files=["docs/business_problem.md"],
            removed_dirs=[],
            skipped_missing=[],
            failed_items=[],
        )
        entry = build_log_entry(1, removal, None, None, [],
                                verification="failed",
                                leftover_checks=["Check A", "Check B"])
        serialized = serialize_log_entry(entry)
        parsed = json.loads(serialized)

        assert parsed["verification"] == "failed"
        assert parsed["leftover_checks"] == ["Check A", "Check B"]

        # Also test with None verification
        entry_none = build_log_entry(1, removal, None, None, [],
                                     verification=None, leftover_checks=[])
        parsed_none = json.loads(serialize_log_entry(entry_none))
        assert parsed_none["verification"] is None
        assert parsed_none["leftover_checks"] == []

    def test_dry_run_output_no_verification(self):
        """5.9: dry-run output does not mention verification results."""
        artifacts = ARTIFACT_MANIFEST[1]
        report = format_dry_run_report(
            module=1,
            artifacts=artifacts,
            existing_files=["docs/business_problem.md"],
            existing_dirs=[],
            missing_items=[],
            backup_path=None,
            downstream_completed=[],
            progress_changes={"modules_completed": "remove 1"},
        )

        assert "verification" not in report.lower()
        assert "Verification" not in report
        assert "leftover" not in report.lower()


# ---------------------------------------------------------------------------
# Task 6: Integration tests
# ---------------------------------------------------------------------------


class TestRollbackVerificationIntegration:
    """Integration tests for the full rollback + verification flow."""

    def _setup_project(self, tmp_path, module, modules_completed=None):
        """Helper: create a project root with artifacts and progress file."""
        root = tmp_path
        artifacts = ARTIFACT_MANIFEST[module]

        # Create manifest artifacts
        for f in artifacts.files:
            fp = root / f
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text("content", encoding="utf-8")
        for d in artifacts.directories:
            dp = root / d
            dp.mkdir(parents=True, exist_ok=True)
            (dp / "sample.txt").write_text("content", encoding="utf-8")

        # Create progress file
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        progress = {
            "modules_completed": modules_completed if modules_completed else [module],
            "current_module": module,
            "current_step": 1,
            "step_history": {},
            "data_sources": [],
            "database_type": "sqlite",
        }
        (config_dir / "bootcamp_progress.json").write_text(
            json.dumps(progress, indent=2), encoding="utf-8"
        )

        # Create scripts dir for __file__ resolution
        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Create logs dir
        (root / "logs").mkdir(parents=True, exist_ok=True)

        return root, str(scripts_dir / "rollback_module.py")

    def test_full_rollback_verification_passes(self, tmp_path):
        """6.1: Full rollback of a module with artifacts present — artifacts
        removed, verification passes, log entry has verification='passed'."""
        root, fake_script = self._setup_project(tmp_path, 1)

        # After removal, the validator should return all ok=False
        def post_removal_validator():
            return [(False, "Business problem documented",
                     "docs/business_problem.md not found")]

        fake_validators = {1: post_removal_validator}

        buf = StringIO()
        with mock.patch("rollback_module.__file__", fake_script), \
             mock.patch("sys.stdout", buf), \
             mock.patch.dict(
                 "sys.modules",
                 {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
             ):
            exit_code = main(["--module", "1", "--force"])

        assert exit_code == 0

        # Artifacts should be removed
        assert not (root / "docs" / "business_problem.md").exists()

        # Check stdout for verification passed message
        output = buf.getvalue()
        assert "Verification passed" in output

        # Check log entry
        log_path = root / "logs" / "rollback_log.jsonl"
        assert log_path.exists()
        log_line = log_path.read_text(encoding="utf-8").strip().split("\n")[-1]
        log_entry = json.loads(log_line)
        assert log_entry["verification"] == "passed"
        assert log_entry["leftover_checks"] == []

    def test_rollback_with_leftover_artifact(self, tmp_path):
        """6.2: Rollback with simulated leftover artifact — verification warns,
        log entry has verification='failed' and correct leftover_checks."""
        root, fake_script = self._setup_project(tmp_path, 1)

        # Simulate a validator that still finds an artifact after rollback
        def leftover_validator():
            return [
                (True, "Business problem documented", "docs/business_problem.md"),
            ]

        fake_validators = {1: leftover_validator}

        buf = StringIO()
        with mock.patch("rollback_module.__file__", fake_script), \
             mock.patch("sys.stdout", buf), \
             mock.patch.dict(
                 "sys.modules",
                 {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
             ):
            exit_code = main(["--module", "1", "--force"])

        assert exit_code == 0

        # Check stdout for verification warning
        output = buf.getvalue()
        assert "Verification warning" in output
        assert "Business problem documented" in output

        # Check log entry
        log_path = root / "logs" / "rollback_log.jsonl"
        log_line = log_path.read_text(encoding="utf-8").strip().split("\n")[-1]
        log_entry = json.loads(log_line)
        assert log_entry["verification"] == "failed"
        assert "Business problem documented" in log_entry["leftover_checks"]

    def test_dry_run_no_verification(self, tmp_path):
        """6.3: Dry-run rollback — no verification performed, log entry has
        verification=null."""
        root, fake_script = self._setup_project(tmp_path, 1)

        validator_called = []

        def tracking_validator():
            validator_called.append(True)
            return [(False, "check", "detail")]

        fake_validators = {1: tracking_validator}

        buf = StringIO()
        with mock.patch("rollback_module.__file__", fake_script), \
             mock.patch("sys.stdout", buf), \
             mock.patch.dict(
                 "sys.modules",
                 {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
             ):
            exit_code = main(["--module", "1", "--dry-run"])

        assert exit_code == 0
        assert len(validator_called) == 0

        # Artifacts should still exist (dry-run)
        assert (root / "docs" / "business_problem.md").exists()

        # Dry-run output should not mention verification
        output = buf.getvalue()
        assert "Verification passed" not in output
        assert "Verification warning" not in output

    def test_rollback_with_validator_exception(self, tmp_path):
        """6.4: Rollback with mocked validator exception — warning printed,
        rollback completes, log entry has verification=null."""
        root, fake_script = self._setup_project(tmp_path, 1)

        def exploding_validator():
            raise RuntimeError("File system error during validation")

        fake_validators = {1: exploding_validator}

        buf = StringIO()
        with mock.patch("rollback_module.__file__", fake_script), \
             mock.patch("sys.stdout", buf), \
             mock.patch.dict(
                 "sys.modules",
                 {"validate_module": mock.MagicMock(VALIDATORS=fake_validators)},
             ):
            exit_code = main(["--module", "1", "--force"])

        assert exit_code == 0

        # Artifacts should be removed despite verification failure
        assert not (root / "docs" / "business_problem.md").exists()

        # Check stdout for verification warning
        output = buf.getvalue()
        assert "Verification could not be completed" in output

        # Check log entry
        log_path = root / "logs" / "rollback_log.jsonl"
        log_line = log_path.read_text(encoding="utf-8").strip().split("\n")[-1]
        log_entry = json.loads(log_line)
        assert log_entry["verification"] is None
        assert log_entry["leftover_checks"] == []
