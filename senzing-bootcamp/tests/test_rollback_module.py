"""Property-based and unit tests for module rollback.

Uses Hypothesis to verify correctness properties across randomly generated
inputs, plus pytest unit tests for specific examples and edge cases.
"""

import dataclasses
import importlib
import json
import os
import sys
import tempfile
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure scripts dir is on sys.path so we can import rollback_module
_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from rollback_module import (
    ARTIFACT_MANIFEST,
    MODULE_NAMES,
    PREREQUISITES,
    ModuleArtifacts,
    RemovalResult,
    RollbackLogEntry,
    build_log_entry,
    compute_progress_update,
    find_latest_backup,
    format_dry_run_report,
    get_completed_downstream,
    get_downstream_modules,
    main,
    parse_args,
    read_progress_file,
    remove_artifacts,
    restore_database_from_backup,
    serialize_log_entry,
    write_progress_file,
)

# ---------------------------------------------------------------------------
# Task 7.2: Hypothesis strategies
# ---------------------------------------------------------------------------


def _valid_module_numbers():
    """Strategy producing valid module numbers 1-11."""
    return st.integers(min_value=1, max_value=11)


def _any_module_numbers():
    """Strategy producing any integer, including out-of-range values."""
    return st.integers(min_value=-100, max_value=200)


def _modules_completed_lists():
    """Strategy producing sorted unique subsets of modules 1-11."""
    return st.lists(
        st.integers(min_value=1, max_value=11), unique=True, max_size=11
    ).map(sorted)


def _progress_states():
    """Strategy producing valid progress dicts with all expected fields."""
    return st.fixed_dictionaries({
        "modules_completed": _modules_completed_lists(),
        "current_module": st.integers(min_value=1, max_value=11),
        "current_step": st.one_of(st.none(), st.integers(min_value=1, max_value=20)),
        "step_history": st.dictionaries(
            st.sampled_from([str(i) for i in range(1, 12)]),
            st.fixed_dictionaries({
                "last_completed_step": st.integers(min_value=1, max_value=20),
                "updated_at": st.just("2026-05-12T09:15:00+00:00"),
            }),
            min_size=0,
            max_size=6,
        ),
        "data_sources": st.just([]),
        "database_type": st.sampled_from(["sqlite", "postgresql"]),
        "language": st.just("python"),
    })


def _removal_results():
    """Strategy producing RemovalResult instances."""
    path_strat = st.text(
        alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="/_-."),
        min_size=1, max_size=40,
    )
    return st.builds(
        RemovalResult,
        removed_files=st.lists(path_strat, max_size=5),
        removed_dirs=st.lists(path_strat, max_size=3),
        skipped_missing=st.lists(path_strat, max_size=3),
        failed_items=st.lists(
            st.tuples(path_strat, st.text(min_size=1, max_size=30)),
            max_size=2,
        ),
    )


def _rollback_log_entries():
    """Strategy producing RollbackLogEntry instances."""
    path_strat = st.text(
        alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="/_-."),
        min_size=1, max_size=40,
    )
    return st.builds(
        RollbackLogEntry,
        timestamp=st.just("2026-05-14T10:00:00+00:00"),
        module=_valid_module_numbers(),
        removed_files=st.lists(path_strat, max_size=5),
        removed_dirs=st.lists(path_strat, max_size=3),
        skipped_missing=st.lists(path_strat, max_size=3),
        failed_items=st.lists(path_strat, max_size=2),
        database_restored=st.one_of(st.none(), st.booleans()),
        backup_used=st.one_of(st.none(), path_strat),
        warnings=st.lists(st.text(min_size=0, max_size=50), max_size=3),
        verification=st.one_of(st.none(), st.sampled_from(["passed", "failed"])),
        leftover_checks=st.lists(st.text(min_size=1, max_size=50), max_size=3),
    )


def _backup_zip_filenames():
    """Strategy producing timestamped backup ZIP filenames."""
    return st.tuples(
        st.integers(min_value=2020, max_value=2030),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=0, max_value=23),
        st.integers(min_value=0, max_value=59),
        st.integers(min_value=0, max_value=59),
    ).map(lambda t: f"backup_{t[0]:04d}{t[1]:02d}{t[2]:02d}_{t[3]:02d}{t[4]:02d}{t[5]:02d}.zip")


def _confirmation_strings():
    """Strategy producing arbitrary strings for confirmation input testing."""
    return st.text(min_size=0, max_size=20)


# ---------------------------------------------------------------------------
# Task 7.3: Property 1 — Module number validation
# ---------------------------------------------------------------------------


class TestProperty1ModuleNumberValidation:
    """Feature: module-rollback, Property 1: Module number validation

    For any integer, the CLI argument parser SHALL accept it if and only if
    it is in the range 1-11.

    **Validates: Requirements 1.2, 11.2**
    """

    @given(n=st.integers(min_value=1, max_value=11))
    @settings(max_examples=100)
    def test_valid_modules_accepted(self, n):
        """Feature: module-rollback, Property 1: Module number validation — valid range"""
        args = parse_args(["--module", str(n)])
        assert args.module == n

    @given(n=_any_module_numbers())
    @settings(max_examples=100)
    def test_invalid_modules_rejected(self, n):
        """Feature: module-rollback, Property 1: Module number validation — invalid range"""
        assume(n < 1 or n > 12)
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--module", str(n)])
        assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Task 7.4: Property 2 — Manifest completeness
# ---------------------------------------------------------------------------


class TestProperty2ManifestCompleteness:
    """Feature: module-rollback, Property 2: Manifest completeness

    For any module 1-11, ARTIFACT_MANIFEST contains valid ModuleArtifacts
    with correct modifies_database flag.

    **Validates: Requirements 2.1, 2.7, 2.8**
    """

    @given(module=_valid_module_numbers())
    @settings(max_examples=100)
    def test_manifest_has_valid_entry(self, module):
        """Feature: module-rollback, Property 2: Manifest completeness"""
        assert module in ARTIFACT_MANIFEST
        entry = ARTIFACT_MANIFEST[module]
        assert isinstance(entry, ModuleArtifacts)
        assert isinstance(entry.files, list)
        assert isinstance(entry.directories, list)
        assert isinstance(entry.modifies_database, bool)

        # Only module 6 (Load Data) modifies the database
        if module == 6:
            assert entry.modifies_database is True
        else:
            assert entry.modifies_database is False


# ---------------------------------------------------------------------------
# Task 7.5: Property 3 — Rollback removes exactly manifest items
# ---------------------------------------------------------------------------


class TestProperty3RollbackRemovesExactlyManifestItems:
    """Feature: module-rollback, Property 3: Rollback removes exactly manifest items

    For any module, create manifest artifacts + extras in temp dir, run
    remove_artifacts, verify only manifest items removed.

    **Validates: Requirements 2.14, 2.15, 4.1, 4.4**
    """

    @given(module=_valid_module_numbers())
    @settings(max_examples=100)
    def test_only_manifest_items_removed(self, module):
        """Feature: module-rollback, Property 3: Rollback removes exactly manifest items"""
        artifacts = ARTIFACT_MANIFEST[module]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            # Create all manifest files
            for f in artifacts.files:
                fp = root / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("test content", encoding="utf-8")

            # Create all manifest directories with a file inside
            for d in artifacts.directories:
                dp = root / d
                dp.mkdir(parents=True, exist_ok=True)
                (dp / "sample.txt").write_text("test", encoding="utf-8")

            # Create extra files that should NOT be removed
            extras = ["extra/keep_me.txt", "docs/other_file.md"]
            for e in extras:
                ep = root / e
                ep.parent.mkdir(parents=True, exist_ok=True)
                ep.write_text("extra content", encoding="utf-8")

            result = remove_artifacts(artifacts, str(root))

            # All manifest files should be removed
            for f in artifacts.files:
                assert not (root / f).exists(), f"Manifest file {f} still exists"

            # All manifest directories should be removed
            for d in artifacts.directories:
                assert not (root / d).exists(), f"Manifest dir {d} still exists"

            # Extra files should still exist
            for e in extras:
                assert (root / e).exists(), f"Extra file {e} was incorrectly removed"

            # Result should list all removed items
            assert len(result.removed_files) == len(artifacts.files)
            assert len(result.removed_dirs) == len(artifacts.directories)


# ---------------------------------------------------------------------------
# Task 7.6: Property 4 — Removal resilience
# ---------------------------------------------------------------------------


class TestProperty4RemovalResilience:
    """Feature: module-rollback, Property 4: Removal resilience

    For any module and random subset of existing artifacts, remove_artifacts
    correctly categorizes removed/skipped/failed.

    **Validates: Requirements 4.2, 4.3, 11.4**
    """

    @given(module=_valid_module_numbers(), data=st.data())
    @settings(max_examples=100)
    def test_partial_artifacts_categorized_correctly(self, module, data):
        """Feature: module-rollback, Property 4: Removal resilience"""
        artifacts = ARTIFACT_MANIFEST[module]
        all_items = list(artifacts.files) + list(artifacts.directories)

        # Draw a random subset of items to actually create on disk
        if all_items:
            existing_mask = data.draw(
                st.lists(st.booleans(), min_size=len(all_items), max_size=len(all_items))
            )
        else:
            existing_mask = []

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected_existing = set()

            for i, item in enumerate(all_items):
                if existing_mask[i]:
                    expected_existing.add(item)
                    p = root / item
                    if item in artifacts.files:
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text("content", encoding="utf-8")
                    else:
                        p.mkdir(parents=True, exist_ok=True)
                        (p / "file.txt").write_text("x", encoding="utf-8")

            result = remove_artifacts(artifacts, str(root))

            # Every item should be either removed or skipped
            all_accounted = (
                set(result.removed_files)
                | set(result.removed_dirs)
                | set(result.skipped_missing)
                | {p for p, _ in result.failed_items}
            )
            assert all_accounted == set(all_items), (
                f"Not all items accounted for: {set(all_items) - all_accounted}"
            )

            # Items that existed should be in removed (not skipped)
            removed_set = set(result.removed_files) | set(result.removed_dirs)
            for item in expected_existing:
                assert item in removed_set, f"Existing item {item} not in removed set"


# ---------------------------------------------------------------------------
# Task 7.7: Property 5 — Dry-run safety
# ---------------------------------------------------------------------------


class TestProperty5DryRunSafety:
    """Feature: module-rollback, Property 5: Dry-run safety

    For any module and temp filesystem, dry-run produces output but modifies
    nothing.

    **Validates: Requirements 3.1, 3.5**
    """

    @given(module=_valid_module_numbers())
    @settings(max_examples=100)
    def test_dry_run_no_modifications(self, module):
        """Feature: module-rollback, Property 5: Dry-run safety"""
        artifacts = ARTIFACT_MANIFEST[module]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            # Create manifest artifacts
            for f in artifacts.files:
                fp = root / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("content", encoding="utf-8")
            for d in artifacts.directories:
                dp = root / d
                dp.mkdir(parents=True, exist_ok=True)
                (dp / "file.txt").write_text("x", encoding="utf-8")

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

            # Snapshot filesystem state before dry-run
            before_files = set()
            for p in root.rglob("*"):
                if p.is_file():
                    before_files.add((str(p.relative_to(root)), p.read_text(encoding="utf-8")))

            # Create scripts dir so __file__ resolves
            scripts_dir = root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            fake_script = str(scripts_dir / "rollback_module.py")

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", str(module), "--dry-run"])

            assert exit_code == 0

            # Snapshot filesystem state after dry-run
            after_files = set()
            for p in root.rglob("*"):
                if p.is_file():
                    after_files.add((str(p.relative_to(root)), p.read_text(encoding="utf-8")))

            assert before_files == after_files, "Dry-run modified the filesystem"


# ---------------------------------------------------------------------------
# Task 7.8: Property 6 — Downstream dependency reporting
# ---------------------------------------------------------------------------


class TestProperty6DownstreamDependencyReporting:
    """Feature: module-rollback, Property 6: Downstream dependency reporting

    For any module and progress state with completed downstream modules,
    output lists each downstream module.

    **Validates: Requirements 3.3, 3.4, 7.2**
    """

    @given(module=_valid_module_numbers(), progress=_progress_states())
    @settings(max_examples=100)
    def test_downstream_modules_listed(self, module, progress):
        """Feature: module-rollback, Property 6: Downstream dependency reporting"""
        modules_completed = progress["modules_completed"]
        downstream = get_downstream_modules(module)
        completed_downstream = get_completed_downstream(module, modules_completed)

        # Every completed downstream must be both downstream and completed
        for dm in completed_downstream:
            assert dm in downstream
            assert dm in modules_completed

        # If there are completed downstream modules, dry-run should mention them
        if completed_downstream:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                artifacts = ARTIFACT_MANIFEST[module]

                # Create at least one artifact so there's something to report
                for f in artifacts.files:
                    fp = root / f
                    fp.parent.mkdir(parents=True, exist_ok=True)
                    fp.write_text("x", encoding="utf-8")
                for d in artifacts.directories:
                    dp = root / d
                    dp.mkdir(parents=True, exist_ok=True)

                config_dir = root / "config"
                config_dir.mkdir(parents=True, exist_ok=True)
                (config_dir / "bootcamp_progress.json").write_text(
                    json.dumps(progress, indent=2), encoding="utf-8"
                )

                scripts_dir = root / "scripts"
                scripts_dir.mkdir(parents=True, exist_ok=True)
                fake_script = str(scripts_dir / "rollback_module.py")

                buf = StringIO()
                with mock.patch("rollback_module.__file__", fake_script), \
                     mock.patch("sys.stdout", buf):
                    main(["--module", str(module), "--dry-run"])

                output = buf.getvalue()
                for dm in completed_downstream:
                    assert f"Module {dm}" in output, (
                        f"Downstream module {dm} not mentioned in dry-run output"
                    )


# ---------------------------------------------------------------------------
# Task 7.9: Property 7 — Progress file update correctness
# ---------------------------------------------------------------------------


class TestProperty7ProgressFileUpdateCorrectness:
    """Feature: module-rollback, Property 7: Progress file update correctness

    For any progress state and module N, compute_progress_update produces
    correct mutations.

    **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    """

    @given(progress=_progress_states(), module=_valid_module_numbers())
    @settings(max_examples=100)
    def test_compute_progress_update_mutations(self, progress, module):
        """Feature: module-rollback, Property 7: Progress file update correctness"""
        result = compute_progress_update(progress, module)

        # (a) Module N not in modules_completed
        assert module not in result.get("modules_completed", [])

        # (b) If N was current_module, current_module is set to N
        if progress.get("current_module") == module:
            assert result["current_module"] == module

        # (c) step_history entry for module N is removed
        assert str(module) not in result.get("step_history", {})

        # (d) If current_module equals N, current_step is cleared
        if progress.get("current_module") == module:
            assert result.get("current_step") is None

        # (e) All other fields preserved
        for key in progress:
            if key not in ("modules_completed", "current_module", "current_step", "step_history"):
                assert result[key] == progress[key], f"Field {key} was modified"

        # Original dict not mutated
        assert progress == json.loads(json.dumps(progress))


# ---------------------------------------------------------------------------
# Task 7.10: Property 8 — Progress file JSON formatting
# ---------------------------------------------------------------------------


class TestProperty8ProgressFileJSONFormatting:
    """Feature: module-rollback, Property 8: Progress file JSON formatting

    For any progress dict, write then read produces identical dict with
    2-space indent and trailing newline.

    **Validates: Requirements 6.6**
    """

    @given(progress=_progress_states())
    @settings(max_examples=100)
    def test_write_read_roundtrip(self, progress):
        """Feature: module-rollback, Property 8: Progress file JSON formatting"""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "progress.json")
            write_progress_file(path, progress)

            # Read raw content to check formatting
            raw = Path(path).read_text(encoding="utf-8")
            assert raw.endswith("\n"), "File does not end with trailing newline"

            # Check 2-space indent by verifying the JSON formatting
            expected = json.dumps(progress, indent=2) + "\n"
            assert raw == expected, "JSON formatting does not match 2-space indent"

            # Round-trip: read back and compare
            loaded = read_progress_file(path)
            assert loaded == progress, "Round-trip produced different dict"


# ---------------------------------------------------------------------------
# Task 7.11: Property 9 — Confirmation input validation
# ---------------------------------------------------------------------------


class TestProperty9ConfirmationInputValidation:
    """Feature: module-rollback, Property 9: Confirmation input validation

    For any string, confirmation proceeds iff input is "y" or "Y".

    **Validates: Requirements 8.2, 8.3**
    """

    @given(user_input=_confirmation_strings())
    @settings(max_examples=100)
    def test_confirmation_logic(self, user_input):
        """Feature: module-rollback, Property 9: Confirmation input validation"""
        should_proceed = user_input.strip() in ("y", "Y")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Use module 1 (simple, no DB)
            artifacts = ARTIFACT_MANIFEST[1]
            for f in artifacts.files:
                fp = root / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("content", encoding="utf-8")

            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            progress = {
                "modules_completed": [1],
                "current_module": 1,
                "current_step": None,
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
                 mock.patch("builtins.input", return_value=user_input), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0

            # Check if artifact was removed (proceed) or still exists (cancelled)
            artifact_path = root / artifacts.files[0]
            if should_proceed:
                assert not artifact_path.exists(), (
                    f"Artifact should be removed for input '{user_input}'"
                )
            else:
                assert artifact_path.exists(), (
                    f"Artifact should remain for input '{user_input}'"
                )


# ---------------------------------------------------------------------------
# Task 7.12: Property 10 — Latest backup selection
# ---------------------------------------------------------------------------


class TestProperty10LatestBackupSelection:
    """Feature: module-rollback, Property 10: Latest backup selection

    For any set of timestamped ZIP filenames, find_latest_backup returns
    the most recent.

    **Validates: Requirements 5.1**
    """

    @given(filenames=st.lists(_backup_zip_filenames(), min_size=1, max_size=10, unique=True))
    @settings(max_examples=100)
    def test_latest_backup_is_most_recent(self, filenames):
        """Feature: module-rollback, Property 10: Latest backup selection"""
        with tempfile.TemporaryDirectory() as td:
            backups_dir = Path(td) / "backups"
            backups_dir.mkdir()

            for name in filenames:
                # Create a valid (empty) ZIP file
                zp = backups_dir / name
                with zipfile.ZipFile(zp, "w") as zf:
                    zf.writestr("dummy.txt", "x")

            result = find_latest_backup(str(backups_dir))
            assert result is not None

            # The latest should be the lexicographically last (timestamps sort correctly)
            expected = str(sorted(backups_dir.glob("*.zip"))[-1])
            assert result == expected

    def test_no_backups_returns_none(self):
        """find_latest_backup returns None when no ZIPs exist."""
        with tempfile.TemporaryDirectory() as td:
            backups_dir = Path(td) / "backups"
            backups_dir.mkdir()
            assert find_latest_backup(str(backups_dir)) is None

    def test_missing_dir_returns_none(self):
        """find_latest_backup returns None when directory doesn't exist."""
        assert find_latest_backup("/nonexistent/path/backups") is None


# ---------------------------------------------------------------------------
# Task 7.13: Property 11 — Database restoration extracts only database/
# ---------------------------------------------------------------------------


class TestProperty11DatabaseRestorationExtractsOnlyDatabase:
    """Feature: module-rollback, Property 11: Database restoration extracts only database/

    For any ZIP with database/ and other dirs, only database/ is extracted.

    **Validates: Requirements 5.3**
    """

    @given(
        other_dirs=st.lists(
            st.sampled_from(["src/", "config/", "docs/", "tests/", "data/"]),
            min_size=1, max_size=4, unique=True,
        )
    )
    @settings(max_examples=100)
    def test_only_database_dir_extracted(self, other_dirs):
        """Feature: module-rollback, Property 11: Database restoration extracts only database/"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            # Create a ZIP with database/ and other directories
            zip_path = root / "backup.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("database/G2C.db", "db content")
                zf.writestr("database/config.json", "db config")
                for d in other_dirs:
                    zf.writestr(f"{d}file.txt", f"content of {d}")

            extract_root = root / "project"
            extract_root.mkdir()

            result = restore_database_from_backup(str(zip_path), str(extract_root))
            assert result is True

            # database/ files should exist
            assert (extract_root / "database" / "G2C.db").exists()
            assert (extract_root / "database" / "config.json").exists()

            # Other directories should NOT exist
            for d in other_dirs:
                dir_name = d.rstrip("/")
                assert not (extract_root / dir_name).exists(), (
                    f"Non-database dir {dir_name} was extracted"
                )


# ---------------------------------------------------------------------------
# Task 7.14: Property 12 — Rollback log entry round-trip
# ---------------------------------------------------------------------------


class TestProperty12RollbackLogEntryRoundTrip:
    """Feature: module-rollback, Property 12: Rollback log entry round-trip

    For any RollbackLogEntry, serialize then json.loads produces matching dict.

    **Validates: Requirements 12.3, 12.4**
    """

    @given(entry=_rollback_log_entries())
    @settings(max_examples=100)
    def test_serialize_roundtrip(self, entry):
        """Feature: module-rollback, Property 12: Rollback log entry round-trip"""
        serialized = serialize_log_entry(entry)

        # No embedded newlines (JSON Lines format)
        assert "\n" not in serialized, "Serialized entry contains newline"

        # Parse back
        parsed = json.loads(serialized)
        assert isinstance(parsed, dict)

        # All fields match
        entry_dict = dataclasses.asdict(entry)
        assert parsed == entry_dict


# ---------------------------------------------------------------------------
# Task 7.15: Property 13 — Downstream artifacts untouched
# ---------------------------------------------------------------------------


class TestProperty13DownstreamArtifactsUntouched:
    """Feature: module-rollback, Property 13: Downstream artifacts untouched

    For any module with downstream artifacts on disk, rollback only removes
    target module artifacts.

    **Validates: Requirements 7.5**
    """

    @given(module=_valid_module_numbers())
    @settings(max_examples=100)
    def test_downstream_artifacts_preserved(self, module):
        """Feature: module-rollback, Property 13: Downstream artifacts untouched"""
        downstream = get_downstream_modules(module)
        assume(len(downstream) > 0)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            # Create target module artifacts
            target_artifacts = ARTIFACT_MANIFEST[module]
            for f in target_artifacts.files:
                fp = root / f
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("target", encoding="utf-8")
            for d in target_artifacts.directories:
                dp = root / d
                dp.mkdir(parents=True, exist_ok=True)
                (dp / "file.txt").write_text("target", encoding="utf-8")

            # Create downstream module artifacts
            downstream_paths = []
            for dm in downstream:
                dm_artifacts = ARTIFACT_MANIFEST[dm]
                for f in dm_artifacts.files:
                    fp = root / f
                    fp.parent.mkdir(parents=True, exist_ok=True)
                    fp.write_text("downstream", encoding="utf-8")
                    downstream_paths.append(f)
                for d in dm_artifacts.directories:
                    dp = root / d
                    dp.mkdir(parents=True, exist_ok=True)
                    (dp / "file.txt").write_text("downstream", encoding="utf-8")
                    downstream_paths.append(d)

            # Remove only target module artifacts
            remove_artifacts(target_artifacts, str(root))

            # All downstream artifacts should still exist
            for p in downstream_paths:
                pp = root / p
                assert pp.exists(), (
                    f"Downstream artifact {p} was removed during module {module} rollback"
                )


# ===========================================================================
# Task 8: Unit tests for specific examples and edge cases
# ===========================================================================

# ---------------------------------------------------------------------------
# Task 8.1: Each module's manifest content (12 test cases)
# ---------------------------------------------------------------------------


class TestManifestContent:
    """Verify each module's manifest content matches requirements 2.2-2.13."""

    def test_module_1_manifest(self):
        a = ARTIFACT_MANIFEST[1]
        assert "docs/business_problem.md" in a.files
        assert a.modifies_database is False

    def test_module_2_manifest(self):
        a = ARTIFACT_MANIFEST[2]
        assert "database/G2C.db" in a.files
        assert "config/bootcamp_preferences.yaml" in a.files
        assert a.modifies_database is False

    def test_module_3_manifest(self):
        a = ARTIFACT_MANIFEST[3]
        assert "src/quickstart_demo" in a.directories
        assert a.modifies_database is False

    def test_module_4_manifest(self):
        a = ARTIFACT_MANIFEST[4]
        assert "docs/data_source_locations.md" in a.files
        assert "data/raw" in a.directories
        assert a.modifies_database is False

    def test_module_5_manifest(self):
        a = ARTIFACT_MANIFEST[5]
        assert "docs/data_source_evaluation.md" in a.files
        assert "docs/data_quality_report.md" in a.files
        assert "src/transform" in a.directories
        assert "data/transformed" in a.directories
        assert a.modifies_database is False

    def test_module_6_manifest(self):
        a = ARTIFACT_MANIFEST[6]
        assert "src/load" in a.directories
        assert a.modifies_database is True

    def test_module_7_manifest(self):
        a = ARTIFACT_MANIFEST[7]
        assert "docs/results_validation.md" in a.files
        assert "src/query" in a.directories
        assert a.modifies_database is False

    def test_module_8_manifest(self):
        a = ARTIFACT_MANIFEST[8]
        assert "docs/performance_requirements.md" in a.files
        assert "docs/performance_report.md" in a.files
        assert "tests/performance" in a.directories
        assert a.modifies_database is False

    def test_module_9_manifest(self):
        a = ARTIFACT_MANIFEST[9]
        assert "docs/security_checklist.md" in a.files
        assert a.modifies_database is False

    def test_module_10_manifest(self):
        a = ARTIFACT_MANIFEST[10]
        assert "docs/monitoring_setup.md" in a.files
        assert "monitoring" in a.directories
        assert a.modifies_database is False

    def test_module_11_manifest(self):
        a = ARTIFACT_MANIFEST[11]
        assert "docs/deployment_plan.md" in a.files
        assert a.modifies_database is False


# ---------------------------------------------------------------------------
# Task 8.2: Dependency map matches prerequisites
# ---------------------------------------------------------------------------


class TestDependencyMap:
    """Verify dependency map matches module-prerequisites diagram."""

    def test_prerequisites_structure(self):
        assert PREREQUISITES[3] == [2]
        assert PREREQUISITES[4] == [1]
        assert PREREQUISITES[5] == [4]
        assert set(PREREQUISITES[6]) == {2, 5}
        assert PREREQUISITES[7] == [6]
        assert PREREQUISITES[8] == [7]
        assert PREREQUISITES[9] == [8]
        assert PREREQUISITES[10] == [9]
        assert PREREQUISITES[11] == [10]

    def test_modules_1_2_have_no_prerequisites(self):
        assert 1 not in PREREQUISITES
        assert 2 not in PREREQUISITES

    def test_downstream_of_module_2(self):
        ds = get_downstream_modules(2)
        assert 3 in ds
        assert 6 in ds

    def test_downstream_of_module_1(self):
        ds = get_downstream_modules(1)
        assert 4 in ds
        assert 5 in ds

    def test_downstream_of_module_11(self):
        ds = get_downstream_modules(11)
        assert ds == []


# ---------------------------------------------------------------------------
# Task 8.3: Error scenarios
# ---------------------------------------------------------------------------


class TestErrorScenarios:
    """Unit tests for error scenarios."""

    def test_missing_module_arg(self):
        """Missing --module exits with non-zero code."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args([])
        assert exc_info.value.code != 0

    def test_out_of_range_module_zero(self):
        """Module 0 is rejected."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--module", "0"])
        assert exc_info.value.code != 0

    def test_out_of_range_module_13(self):
        """Module 13 is rejected."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--module", "13"])
        assert exc_info.value.code != 0

    def test_out_of_range_module_negative(self):
        """Negative module is rejected."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--module", "-1"])
        assert exc_info.value.code != 0

    def test_nothing_to_rollback(self):
        """Module not completed and no artifacts → nothing to roll back."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            progress = {
                "modules_completed": [],
                "current_module": 1,
                "current_step": None,
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
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert "Nothing to roll back" in buf.getvalue()

    def test_missing_progress_file(self):
        """Missing progress file prints warning and continues."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create an artifact so there's something to roll back
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "business_problem.md").write_text("x", encoding="utf-8")

            scripts_dir = root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            fake_script = str(scripts_dir / "rollback_module.py")

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "Warning" in output or "not found" in output.lower() or "not updated" in output.lower()

    def test_invalid_json_progress_file(self):
        """Invalid JSON in progress file prints warning."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "bootcamp_progress.json").write_text(
                "not valid json{{{", encoding="utf-8"
            )

            # Create an artifact
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "business_problem.md").write_text("x", encoding="utf-8")

            scripts_dir = root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            fake_script = str(scripts_dir / "rollback_module.py")

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "invalid JSON" in output or "Warning" in output


# ---------------------------------------------------------------------------
# Task 8.4: Database scenarios
# ---------------------------------------------------------------------------


class TestDatabaseScenarios:
    """Unit tests for database rollback scenarios."""

    def _setup_db_module(self, td, module=6, with_backup=True, completed=None):
        """Helper to set up a DB module rollback scenario."""
        root = Path(td)
        artifacts = ARTIFACT_MANIFEST[module]

        # Create artifacts
        for f in artifacts.files:
            fp = root / f
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text("content", encoding="utf-8")
        for d in artifacts.directories:
            dp = root / d
            dp.mkdir(parents=True, exist_ok=True)
            (dp / "loader.py").write_text("code", encoding="utf-8")

        # Create progress
        if completed is None:
            completed = [module]
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        progress = {
            "modules_completed": completed,
            "current_module": module,
            "current_step": None,
            "step_history": {},
            "data_sources": [],
            "database_type": "sqlite",
        }
        (config_dir / "bootcamp_progress.json").write_text(
            json.dumps(progress, indent=2), encoding="utf-8"
        )

        # Create backup if requested
        if with_backup:
            backups_dir = root / "backups"
            backups_dir.mkdir(parents=True, exist_ok=True)
            zip_path = backups_dir / "backup_20260514_100000.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("database/G2C.db", "backup db content")

        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        return str(scripts_dir / "rollback_module.py")

    def test_backup_found_user_confirms(self):
        """Backup found + user confirms → database restored."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_db_module(td)
            root = Path(td)

            buf = StringIO()
            # Two prompts: confirmation + db restore
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "6"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "restored" in output.lower() or "Restoring" in output

    def test_backup_found_user_declines(self):
        """Backup found + user declines → warning about records remaining."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_db_module(td)

            # The prompts in order for module 6 (no completed downstream):
            # 1. "Proceed with rollback? (y/N)" → y
            # 2. "Restore database from backup ...? (y/N)" → n
            responses = iter(["y", "n"])

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", side_effect=responses), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "6"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "remain" in output.lower() or "Warning" in output

    def test_no_backup_found(self):
        """No backup → warning about no backup available."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_db_module(td, with_backup=False)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "6"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "no backup" in output.lower() or "No backup" in output

    def test_force_with_backup(self):
        """--force with backup → auto-restores without prompt."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_db_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "6", "--force"])

            assert exit_code == 0
            output = buf.getvalue()
            assert "restored" in output.lower() or "Restoring" in output
            # Database file should be restored
            assert (root / "database" / "G2C.db").exists()


# ---------------------------------------------------------------------------
# Task 8.5: Confirmation prompt
# ---------------------------------------------------------------------------


class TestConfirmationPrompt:
    """Unit tests for confirmation prompt behavior."""

    def _setup_simple_module(self, td, module=1):
        """Helper to set up a simple module for confirmation testing."""
        root = Path(td)
        artifacts = ARTIFACT_MANIFEST[module]

        for f in artifacts.files:
            fp = root / f
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text("content", encoding="utf-8")
        for d in artifacts.directories:
            dp = root / d
            dp.mkdir(parents=True, exist_ok=True)
            (dp / "file.txt").write_text("x", encoding="utf-8")

        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        progress = {
            "modules_completed": [module],
            "current_module": module,
            "current_step": None,
            "step_history": {},
            "data_sources": [],
            "database_type": "sqlite",
        }
        (config_dir / "bootcamp_progress.json").write_text(
            json.dumps(progress, indent=2), encoding="utf-8"
        )

        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        return str(scripts_dir / "rollback_module.py")

    def test_force_skips_prompt(self):
        """--force skips confirmation prompt entirely."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("sys.stdout", buf):
                # No input mock needed — --force should skip prompts
                exit_code = main(["--module", "1", "--force"])

            assert exit_code == 0
            # Artifact should be removed
            assert not (root / "docs" / "business_problem.md").exists()

    def test_user_enters_y_proceeds(self):
        """User enters 'y' → rollback proceeds."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert not (root / "docs" / "business_problem.md").exists()

    def test_user_enters_Y_proceeds(self):
        """User enters 'Y' → rollback proceeds."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="Y"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert not (root / "docs" / "business_problem.md").exists()

    def test_user_enters_n_cancels(self):
        """User enters 'n' → rollback cancelled."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="n"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert "cancelled" in buf.getvalue().lower()
            # Artifact should still exist
            assert (root / "docs" / "business_problem.md").exists()

    def test_user_enters_empty_cancels(self):
        """User enters empty string → rollback cancelled."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value=""), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert (root / "docs" / "business_problem.md").exists()

    def test_user_enters_yes_cancels(self):
        """User enters 'yes' (not just 'y') → rollback cancelled."""
        with tempfile.TemporaryDirectory() as td:
            fake_script = self._setup_simple_module(td)
            root = Path(td)

            buf = StringIO()
            with mock.patch("rollback_module.__file__", fake_script), \
                 mock.patch("builtins.input", return_value="yes"), \
                 mock.patch("sys.stdout", buf):
                exit_code = main(["--module", "1"])

            assert exit_code == 0
            assert (root / "docs" / "business_problem.md").exists()
