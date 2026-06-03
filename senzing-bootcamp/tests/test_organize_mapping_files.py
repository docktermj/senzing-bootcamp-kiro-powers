"""Property-based and unit tests for organize_mapping_files.py using Hypothesis.

Feature: mapping-file-organization
"""

import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from organize_mapping_files import (
    ROUTING_RULES,
    execute_moves,
    main,
    plan_moves,
    print_summary,
    scan_source,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_RECOGNIZED_EXTENSIONS = list(ROUTING_RULES.keys())
_UNRECOGNIZED_EXTENSIONS = [".txt", ".csv", ".xml", ".yaml", ".log", ".dat"]


def st_basename():
    """Generate valid file basenames (no extension)."""
    return st.from_regex(r"[a-z][a-z0-9_]{1,12}", fullmatch=True)


def st_recognized_files():
    """Generate a list of filenames with recognized extensions."""
    return st.lists(
        st.tuples(st_basename(), st.sampled_from(_RECOGNIZED_EXTENSIONS)),
        min_size=1,
        max_size=8,
        unique=True,
    ).map(lambda pairs: [f"{name}{ext}" for name, ext in pairs])


def st_unrecognized_files():
    """Generate a list of filenames with unrecognized extensions."""
    return st.lists(
        st.tuples(st_basename(), st.sampled_from(_UNRECOGNIZED_EXTENSIONS)),
        min_size=1,
        max_size=5,
        unique=True,
    ).map(lambda pairs: [f"{name}{ext}" for name, ext in pairs])


# ---------------------------------------------------------------------------
# Property 1: Extension-based routing correctness
# ---------------------------------------------------------------------------


class TestProperty1ExtensionBasedRouting:
    """Feature: mapping-file-organization, Property 1: Extension-based routing correctness

    For any set of files with recognized extensions (.py, .md, .jsonl, .json)
    placed in a source directory, after running the organizer, each file lands
    in the correct target subdirectory and no longer exists in source.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(filenames=st_recognized_files())
    @settings(max_examples=20)
    def test_files_routed_to_correct_subdirectory(self, filenames):
        """Each recognized file moves to the correct target subdirectory."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            files = scan_source(source)
            plan = plan_moves(files, project_root)
            execute_moves(plan)

            for fname in filenames:
                ext = Path(fname).suffix.lower()
                target_subdir = ROUTING_RULES[ext]
                expected_dest = project_root / target_subdir / fname

                assert expected_dest.exists(), (
                    f"{fname} not found at expected destination {expected_dest}"
                )
                assert not (source / fname).exists(), (
                    f"{fname} still exists in source directory"
                )
                assert expected_dest.read_text() == f"content of {fname}"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 2: Unrecognized extensions remain in place
# ---------------------------------------------------------------------------


class TestProperty2UnrecognizedExtensions:
    """Feature: mapping-file-organization, Property 2: Unrecognized extensions remain in place

    For any file with an extension not in the routing table, after running
    the organizer, the file still exists at its original location and stderr
    contains a warning.

    **Validates: Requirements 1.5**
    """

    @given(filenames=st_unrecognized_files())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_unrecognized_files_stay_in_source(self, filenames, capsys):
        """Files with unrecognized extensions remain in source with stderr warning."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            files = scan_source(source)
            plan = plan_moves(files, project_root)
            execute_moves(plan)
            print_summary(plan, dry_run=False)

            captured = capsys.readouterr()

            for fname in filenames:
                assert (source / fname).exists(), (
                    f"{fname} was moved but should have stayed in source"
                )
                assert fname in captured.err, (
                    f"Warning for {fname} not found in stderr"
                )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 3: Conflict detection prevents overwrite
# ---------------------------------------------------------------------------


class TestProperty3ConflictDetection:
    """Feature: mapping-file-organization, Property 3: Conflict detection prevents overwrite

    Pre-populate target directory with same-named files, run organizer,
    assert neither source nor target is modified.

    **Validates: Requirements 2.1**
    """

    @given(filenames=st_recognized_files())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_conflict_prevents_overwrite(self, filenames, capsys):
        """Files with conflicts at destination are not moved or overwritten."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"source content of {fname}")
                ext = Path(fname).suffix.lower()
                target_subdir = ROUTING_RULES[ext]
                dest_dir = project_root / target_subdir
                dest_dir.mkdir(parents=True, exist_ok=True)
                (dest_dir / fname).write_text(f"existing content of {fname}")

            files = scan_source(source)
            plan = plan_moves(files, project_root)
            execute_moves(plan)
            print_summary(plan, dry_run=False)

            captured = capsys.readouterr()

            for fname in filenames:
                ext = Path(fname).suffix.lower()
                target_subdir = ROUTING_RULES[ext]
                dest_file = project_root / target_subdir / fname

                assert (source / fname).exists(), (
                    f"{fname} was removed from source despite conflict"
                )
                assert (source / fname).read_text() == f"source content of {fname}", (
                    f"Source file {fname} was modified"
                )
                assert dest_file.read_text() == f"existing content of {fname}", (
                    f"Destination file {fname} was overwritten"
                )
                assert fname in captured.err, (
                    f"Skip notice for {fname} not found in stderr"
                )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 4: Idempotence
# ---------------------------------------------------------------------------


class TestProperty4Idempotence:
    """Feature: mapping-file-organization, Property 4: Idempotence

    Run organizer twice on same file set, assert second run produces no
    additional changes.

    **Validates: Requirements 2.3**
    """

    @given(filenames=st_recognized_files())
    @settings(max_examples=20)
    def test_second_run_produces_no_changes(self, filenames):
        """Running organizer twice produces same result as running once."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            # First run
            files = scan_source(source)
            plan = plan_moves(files, project_root)
            execute_moves(plan)

            # Snapshot state after first run
            state_after_first = {}
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                target_subdir = ROUTING_RULES[ext]
                dest = project_root / target_subdir / fname
                if dest.exists():
                    state_after_first[fname] = dest.read_text()

            # Second run on same source (now empty of recognized files)
            files2 = scan_source(source)
            plan2 = plan_moves(files2, project_root)
            execute_moves(plan2)

            # Verify no additional changes
            moved_in_second = [r for r in plan2 if r.status == "moved"]
            assert len(moved_in_second) == 0, (
                f"Second run moved {len(moved_in_second)} files"
            )

            # Verify state unchanged
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                target_subdir = ROUTING_RULES[ext]
                dest = project_root / target_subdir / fname
                if fname in state_after_first:
                    assert dest.read_text() == state_after_first[fname], (
                        f"File {fname} was modified by second run"
                    )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 5: Non-existent source exits with error
# ---------------------------------------------------------------------------


class TestProperty5NonExistentSource:
    """Feature: mapping-file-organization, Property 5: Non-existent source exits with error

    Generate non-existent paths, invoke main, assert exit code 1 and stderr output.

    **Validates: Requirements 4.6**
    """

    @given(path_suffix=st_basename())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_nonexistent_source_exits_with_error(self, path_suffix, capsys):
        """Non-existent source path causes exit code 1 and stderr message."""
        tmp = Path(tempfile.mkdtemp())
        try:
            nonexistent = str(tmp / f"does_not_exist_{path_suffix}")

            exit_code = main(["--source", nonexistent, "--project-root", str(tmp)])

            captured = capsys.readouterr()
            assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
            assert "error" in captured.err.lower() or "does not exist" in captured.err.lower(), (
                f"Expected error message in stderr, got: {captured.err!r}"
            )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 6: Dry-run preserves file system
# ---------------------------------------------------------------------------


class TestProperty6DryRunPreservesFileSystem:
    """Feature: mapping-file-organization, Property 6: Dry-run preserves file system

    Run with --dry-run, assert no files moved, planned moves printed to stdout.

    **Validates: Requirements 5.1, 5.2**
    """

    @given(filenames=st_recognized_files())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_dry_run_does_not_move_files(self, filenames, capsys):
        """Dry-run leaves all files in place and prints planned moves."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            exit_code = main([
                "--source", str(source),
                "--project-root", str(project_root),
                "--dry-run",
            ])

            captured = capsys.readouterr()

            assert exit_code == 0, f"Expected exit code 0, got {exit_code}"

            # All files still in source
            for fname in filenames:
                assert (source / fname).exists(), (
                    f"{fname} was moved despite --dry-run"
                )

            # No target directories created with files
            for subdir in ROUTING_RULES.values():
                target_dir = project_root / subdir
                if target_dir.exists():
                    assert not list(target_dir.iterdir()), (
                        f"Files found in {target_dir} despite --dry-run"
                    )

            # Planned moves printed to stdout
            for fname in filenames:
                assert fname in captured.out, (
                    f"Planned move for {fname} not found in stdout"
                )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 7: Summary reporting completeness
# ---------------------------------------------------------------------------


class TestProperty7SummaryReporting:
    """Feature: mapping-file-organization, Property 7: Summary reporting completeness

    Run organizer on file sets, assert stdout contains a line per moved file
    or "no files" message when none moved.

    **Validates: Requirements 8.1, 8.2**
    """

    @given(filenames=st_recognized_files())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_summary_lists_each_moved_file(self, filenames, capsys):
        """Stdout contains a line for each moved file."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            exit_code = main([
                "--source", str(source),
                "--project-root", str(project_root),
            ])

            captured = capsys.readouterr()
            assert exit_code == 0

            for fname in filenames:
                assert fname in captured.out, (
                    f"Moved file {fname} not mentioned in stdout summary"
                )
        finally:
            shutil.rmtree(tmp)

    def test_no_files_message_when_empty(self, tmp_path, capsys):
        """Stdout contains 'no files' message when nothing to move."""
        source = tmp_path / "source"
        source.mkdir()
        project_root = tmp_path / "project"
        project_root.mkdir()

        exit_code = main([
            "--source", str(source),
            "--project-root", str(project_root),
        ])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "no files" in captured.out.lower(), (
            f"Expected 'no files' message in stdout, got: {captured.out!r}"
        )


# ---------------------------------------------------------------------------
# Task 3.8: Unit tests for CLI argument defaults and error messages
# ---------------------------------------------------------------------------


class TestCLIArgumentDefaults:
    """Unit tests for CLI argument defaults and error messages.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6**
    """

    def test_source_defaults_to_cwd(self, tmp_path, monkeypatch, capsys):
        """--source defaults to current working directory when omitted."""
        monkeypatch.chdir(tmp_path)
        # Create a recognizable file in cwd
        (tmp_path / "test_file.py").write_text("# test")
        project_root = tmp_path / "project"
        project_root.mkdir()

        exit_code = main(["--project-root", str(project_root)])

        assert exit_code == 0
        assert (project_root / "scripts" / "test_file.py").exists()

    def test_project_root_defaults_to_cwd(self, tmp_path, monkeypatch, capsys):
        """--project-root defaults to current working directory when omitted."""
        monkeypatch.chdir(tmp_path)
        source = tmp_path / "source"
        source.mkdir()
        (source / "data_file.jsonl").write_text('{"key": "value"}')

        exit_code = main(["--source", str(source)])

        assert exit_code == 0
        # File should be moved to data/ relative to cwd (tmp_path)
        assert (tmp_path / "data" / "data_file.jsonl").exists()

    def test_error_when_source_is_file(self, tmp_path, capsys):
        """Error message when --source points to a file, not a directory."""
        source_file = tmp_path / "not_a_dir.txt"
        source_file.write_text("I am a file")

        exit_code = main(["--source", str(source_file)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "not a directory" in captured.err.lower() or "does not exist" in captured.err.lower(), (
            f"Expected directory error in stderr, got: {captured.err!r}"
        )

    def test_error_when_source_does_not_exist(self, tmp_path, capsys):
        """Error message when --source path does not exist."""
        nonexistent = str(tmp_path / "no_such_dir")

        exit_code = main(["--source", nonexistent])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "does not exist" in captured.err.lower() or "error" in captured.err.lower(), (
            f"Expected error in stderr, got: {captured.err!r}"
        )
