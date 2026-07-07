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
        assert (project_root / "src" / "mapping" / "test_file.py").exists()

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
        assert (
            "not a directory" in captured.err.lower()
            or "does not exist" in captured.err.lower()
        ), (
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


# ===========================================================================
# Feature: docs-file-placement (BUGFIX)
# Task 1 — Bug condition exploration tests
#
# Property 1: Bug Condition — Conventional Placement Of Routed And Generated Files
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4** (1.5 lives in
# test_generate_docs_index.py)
#
# CRITICAL: These tests encode the EXPECTED (fixed) behavior and MUST FAIL on
# the current (unfixed) code. Their failure confirms the defects exist. They
# will pass once the fix (Change 1: filename-aware `route()`, Change 3: hook
# Check 4 `.py` fallback -> src/scripts/) is implemented.
#
# `route()` does not yet exist on the unfixed organizer, so it is imported
# lazily inside each test: on unfixed code the import raises ImportError, which
# registers as the expected failure for that case without breaking the other
# (preservation) tests in this module.
# ===========================================================================

import json  # noqa: E402

_HOOK_PATH = (
    Path(__file__).resolve().parent.parent / "hooks" / "write-policy-gate.kiro.hook"
)


def _load_hook_prompt() -> str:
    """Return the askAgent prompt text from the write-policy-gate hook."""
    data = json.loads(_HOOK_PATH.read_text(encoding="utf-8"))
    return data["then"]["prompt"]


class TestBugConditionConventionalPlacement:
    """Feature: docs-file-placement, Property 1: Bug Condition — Conventional Placement.

    For any file write where the bug condition holds, the fixed power SHALL route
    the file to its conventional location. These exploratory cases MUST FAIL on
    unfixed code (failure confirms defects 1.1-1.4 exist).

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    # --- Case 1 — Python helper routing (defect 1.1) -----------------------

    def test_python_helper_routes_to_src_mapping(self):
        """route("sz_json_analyzer.py") -> "src/mapping" (unfixed: "scripts")."""
        from organize_mapping_files import route

        assert route("sz_json_analyzer.py") == "src/mapping"

    @given(base=st_basename())
    @settings(max_examples=20)
    def test_any_python_file_routes_to_src_mapping(self, base):
        """For any basename, route("{base}.py") -> "src/mapping" (defect 1.1)."""
        from organize_mapping_files import route

        assert route(f"{base}.py") == "src/mapping"

    # --- Case 2 — Mapper spec routing (defect 1.2) -------------------------

    def test_mapper_spec_routes_to_docs_mapping(self):
        """route("playpalace_mapper.md") -> "docs/mapping" (unfixed: "docs")."""
        from organize_mapping_files import route

        assert route("playpalace_mapper.md") == "docs/mapping"

    @given(base=st_basename())
    @settings(max_examples=20)
    def test_any_mapper_spec_routes_to_docs_mapping(self, base):
        """For any basename, route("{base}_mapper.md") -> "docs/mapping" (defect 1.2)."""
        from organize_mapping_files import route

        assert route(f"{base}_mapper.md") == "docs/mapping"

    # --- Case 3 — Entity-spec routing (defect 1.3) -------------------------

    def test_entity_spec_routes_to_docs_reference(self):
        """route("senzing_entity_specification.md") -> "docs/reference" (unfixed: "docs")."""
        from organize_mapping_files import route

        assert route("senzing_entity_specification.md") == "docs/reference"

    # --- Case 4 — Utility-script fallback in hook (defect 1.4) -------------

    def test_hook_py_fallback_routes_to_src_scripts(self):
        """Check 4 `.py` fallback routes non-typed `.py` to src/scripts/.

        On unfixed code the prompt offers root `scripts/{filename}` -> FAILS.
        """
        prompt = _load_hook_prompt()

        # The corrected fallback must target src/scripts/ for utility/CLI .py.
        assert "src/scripts/{filename}" in prompt, (
            "Hook Check 4 .py fallback should route utility scripts to "
            "src/scripts/{filename}"
        )

    def test_hook_py_fallback_has_no_root_scripts_option(self):
        """Check 4 `.py` fallback must NOT offer a root `scripts/{filename}` option.

        On unfixed code the prompt still contains the root fallback -> FAILS.
        """
        prompt = _load_hook_prompt()

        # The root-scripts fallback line uses the arrow + "scripts/{filename}"
        # form. Note: the fixed form "arrow + src/scripts/{filename}" is allowed.
        assert "\u2192 scripts/{filename}" not in prompt, (
            "Hook Check 4 .py fallback still offers a root scripts/{filename} "
            "destination (src/-or-scripts/ ambiguity must be removed)"
        )


# ===========================================================================
# Feature: docs-file-placement (BUGFIX)
# Task 2 — Preservation property tests
#
# Property 2: Preservation — Non-Buggy Writes Are Unchanged
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
#
# These tests capture behavior that MUST remain byte-for-byte unchanged after
# the fix so it cannot regress. They are written against the stable public
# organizer API (plan_moves / execute_moves / main) and the hook prompt text,
# rather than route() (which does not exist on the unfixed organizer), so they
# PASS on the current (unfixed) code AND continue to guard the preserved
# behavior once the fix introduces route().
# ===========================================================================


def _routed_subdir(filename: str, project_root: Path) -> str | None:
    """Return the POSIX relative subdir the organizer routes a filename to.

    Uses the stable plan_moves() public API (rather than route(), which does
    not exist on unfixed code) so the assertion is valid both before and after
    the fix. plan_moves() only inspects the file name/suffix and whether the
    destination exists, so a non-existent placeholder path is sufficient.

    Args:
        filename: The file name to route (e.g. "foo.jsonl").
        project_root: Base directory used to resolve the destination.

    Returns:
        The POSIX-style relative subdirectory (e.g. "data"), or None when the
        file is unrouted.
    """
    plan = plan_moves([Path(filename)], project_root)
    destination = plan[0].destination
    if destination is None:
        return None
    return destination.parent.relative_to(project_root).as_posix()


class TestPreservationDataConfigRouting:
    """Feature: docs-file-placement, Property 2: Preservation — data/config routing.

    The organizer's `.jsonl -> data` and `.json -> config` routing is unchanged
    by the fix. These pass on unfixed code and must keep passing afterward.

    **Validates: Requirements 3.3, 3.5**
    """

    _PROJECT_ROOT = Path("/__preservation_project__")

    @given(base=st_basename())
    @settings(max_examples=20)
    def test_jsonl_routes_to_data(self, base):
        """For any basename, a .jsonl file routes to the data/ subdir (3.5)."""
        assert _routed_subdir(f"{base}.jsonl", self._PROJECT_ROOT) == "data"

    @given(base=st_basename())
    @settings(max_examples=20)
    def test_json_routes_to_config(self, base):
        """For any basename, a .json file routes to the config/ subdir (3.5)."""
        assert _routed_subdir(f"{base}.json", self._PROJECT_ROOT) == "config"

    def test_identifier_crosswalk_json_routes_to_config(self):
        """identifier_crosswalk.json -> config/ is a permitted, unchanged dest (3.3)."""
        assert _routed_subdir("identifier_crosswalk.json", self._PROJECT_ROOT) == "config"


class TestPreservationConflictSkip:
    """Feature: docs-file-placement, Property 2: Preservation — conflict-skip.

    A same-named NON-canonical file already at the destination is skipped (not
    overwritten), exactly as today.

    **Validates: Requirements 3.6**
    """

    @given(
        names=st.lists(
            st.tuples(st_basename(), st.sampled_from([".jsonl", ".json"])),
            min_size=1,
            max_size=6,
            unique=True,
        ).map(lambda pairs: [f"{n}{e}" for n, e in pairs])
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_non_canonical_conflict_is_skipped(self, names, capsys):
        """Pre-existing non-canonical destinations are skipped, never overwritten."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in names:
                (source / fname).write_text(f"source content of {fname}")
                subdir = _routed_subdir(fname, project_root)
                dest_dir = project_root / subdir
                dest_dir.mkdir(parents=True, exist_ok=True)
                (dest_dir / fname).write_text(f"existing content of {fname}")

            files = scan_source(source)
            plan = plan_moves(files, project_root)
            execute_moves(plan)
            print_summary(plan, dry_run=False)
            captured = capsys.readouterr()

            for result in plan:
                assert result.status == "skipped", (
                    f"{result.source.name} expected 'skipped', got {result.status!r}"
                )

            for fname in names:
                subdir = _routed_subdir(fname, project_root)
                dest_file = project_root / subdir / fname
                assert (source / fname).read_text() == f"source content of {fname}"
                assert dest_file.read_text() == f"existing content of {fname}"
                assert fname in captured.err
        finally:
            shutil.rmtree(tmp)


class TestPreservationIdempotence:
    """Feature: docs-file-placement, Property 2: Preservation — idempotence.

    Running the organizer twice produces zero moves on the second run.

    **Validates: Requirements 3.5, 3.6**
    """

    @given(filenames=st_recognized_files())
    @settings(max_examples=20)
    def test_second_run_produces_zero_moves(self, filenames):
        """A second organizer run over the same source moves nothing."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            execute_moves(plan_moves(scan_source(source), project_root))

            plan2 = plan_moves(scan_source(source), project_root)
            execute_moves(plan2)

            moved_second = [r for r in plan2 if r.status == "moved"]
            assert moved_second == [], (
                f"Second run unexpectedly moved {len(moved_second)} file(s)"
            )
        finally:
            shutil.rmtree(tmp)


class TestPreservationCorrectPlacementUntouched:
    """Feature: docs-file-placement, Property 2: Preservation — correct placement.

    Files already under docs/mapping/, docs/reference/, docs/progress/, and
    docs/feedback/ are never moved or modified by an organizer run.

    **Validates: Requirements 3.6**
    """

    _CORRECT_SUBDIRS = ["docs/mapping", "docs/reference", "docs/progress", "docs/feedback"]

    @given(base=st_basename())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_already_placed_docs_are_untouched(self, base, capsys):
        """Documents already in their correct docs/ subdir are left in place."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            placed: dict[Path, str] = {}
            for subdir in self._CORRECT_SUBDIRS:
                dest_dir = project_root / subdir
                dest_dir.mkdir(parents=True, exist_ok=True)
                doc = dest_dir / f"{base}.md"
                content = f"# {base} in {subdir}"
                doc.write_text(content)
                placed[doc] = content

            exit_code = main([
                "--source", str(source),
                "--project-root", str(project_root),
            ])
            capsys.readouterr()

            assert exit_code == 0
            for doc, content in placed.items():
                assert doc.exists(), f"{doc} was removed by the organizer"
                assert doc.read_text() == content, f"{doc} content was modified"
        finally:
            shutil.rmtree(tmp)


class TestPreservationDryRun:
    """Feature: docs-file-placement, Property 2: Preservation — dry-run.

    Dry-run plans moves without touching the filesystem (unchanged).

    **Validates: Requirements 3.5, 3.6**
    """

    @given(filenames=st_recognized_files())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_dry_run_plans_without_moving(self, filenames, capsys):
        """Dry-run leaves source untouched and prints the planned moves."""
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

            assert exit_code == 0
            for fname in filenames:
                assert (source / fname).exists(), f"{fname} moved despite --dry-run"
                assert fname in captured.out, f"planned move for {fname} not printed"
        finally:
            shutil.rmtree(tmp)


class TestPreservationHookNonPlacementChecks:
    """Feature: docs-file-placement, Property 2: Preservation — hook checks intact.

    The write-policy-gate hook's non-placement checks (Check 1 Senzing SQL
    blocking, Check 2 single-question enforcement, Check 3 feedback append-only
    guard) and the root whitelist are unchanged by the fix.

    **Validates: Requirements 3.2, 3.4**
    """

    _ROOT_WHITELIST = [
        ".gitignore",
        ".env",
        ".env.example",
        "README.md",
        "requirements.txt",
        "pom.xml",
        ".csproj",
        "Cargo.toml",
        "package.json",
    ]

    def test_check1_senzing_sql_blocking_present(self):
        """Check 1 (Senzing SQL blocking) prompt section is present verbatim (3.4)."""
        prompt = _load_hook_prompt()
        assert "CHECK 1: SENZING SQL BLOCKING" in prompt
        assert (
            "SQL PATTERNS TO DETECT: SELECT, INSERT, UPDATE, DELETE, "
            "CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA" in prompt
        )
        assert "direct SQL against the Senzing database is prohibited" in prompt

    def test_check2_single_question_enforcement_present(self):
        """Check 2 (single-question for .question_pending) is present verbatim (3.4)."""
        prompt = _load_hook_prompt()
        assert "CHECK 2: SINGLE-QUESTION ENFORCEMENT" in prompt
        assert ".question_pending" in prompt
        assert (
            "EXACTLY ONE QUESTION: The content must contain exactly one question mark"
            in prompt
        )

    def test_check3_feedback_append_only_present(self):
        """Check 3 (feedback append-only guard) is present verbatim (3.4)."""
        prompt = _load_hook_prompt()
        assert "CHECK 3: FILE PATH POLICIES" in prompt
        assert "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" in prompt
        assert "APPEND-ONLY GUARD" in prompt
        assert "is append-only" in prompt

    def test_root_whitelist_entries_unchanged(self):
        """Every root whitelist entry remains permitted at the project root (3.2)."""
        prompt = _load_hook_prompt()
        assert "ROOT WHITELIST" in prompt
        for entry in self._ROOT_WHITELIST:
            assert entry in prompt, f"root whitelist entry {entry!r} missing from hook"


class TestPreservationHookTransformLoadQueryBranches:
    """Feature: docs-file-placement, Property 2: Preservation — typed .py routing.

    Check 4's `.py` routing still sends transform/load/query code to
    src/transform/, src/load/, and src/query/ (unchanged by the fix).

    **Validates: Requirements 3.1**
    """

    def test_transform_load_query_branches_present(self):
        """The three typed .py destinations are present verbatim in Check 4 (3.1)."""
        prompt = _load_hook_prompt()
        assert "src/transform/{filename}" in prompt
        assert "src/load/{filename}" in prompt
        assert "src/query/{filename}" in prompt


# ===========================================================================
# Feature: docs-file-placement (BUGFIX)
# Task 3.7 — Fix-checking and new property tests for the organizer
#
# These exercise the implemented filename-aware route() rework (Change 1) and
# the entity-spec deduplication outcome (Change 2). They validate the
# correctness properties from the design (Properties 1, 3, 4, 5) plus a unit
# route() table and a hook JSON schema-validity check.
# ===========================================================================

from organize_mapping_files import route  # noqa: E402


class TestProperty3RoutingDeterminism:
    """Feature: docs-file-placement, Property 3: Routing Determinism.

    For any generated filename, route() returns exactly one target (a str) or
    None, and is pure/stable — calling it twice yields the same value.

    **Validates: Requirements 2.4**
    """

    @given(
        filename=st.one_of(
            st.tuples(st_basename(), st.sampled_from(_RECOGNIZED_EXTENSIONS)).map(
                lambda pair: f"{pair[0]}{pair[1]}"
            ),
            st.tuples(st_basename(), st.sampled_from(_UNRECOGNIZED_EXTENSIONS)).map(
                lambda pair: f"{pair[0]}{pair[1]}"
            ),
            st_basename().map(lambda base: f"{base}_mapper.md"),
            st.just("senzing_entity_specification.md"),
        )
    )
    @settings(max_examples=20)
    def test_route_returns_single_stable_target(self, filename):
        """route() returns a str or None and is stable across repeated calls."""
        first = route(filename)
        second = route(filename)

        assert first is None or isinstance(first, str), (
            f"route({filename!r}) returned {first!r}, expected str | None"
        )
        assert first == second, (
            f"route({filename!r}) not stable: {first!r} != {second!r}"
        )


class TestProperty4MapperEntityRouting:
    """Feature: docs-file-placement, Property 4: Mapper/Entity routing.

    For any basename, "{base}_mapper.md" routes to docs/mapping; the entity
    specification routes to docs/reference.

    **Validates: Requirements 2.2, 2.3**
    """

    @given(base=st_basename())
    @settings(max_examples=20)
    def test_mapper_spec_routes_to_docs_mapping(self, base):
        """Any *_mapper.md filename routes to docs/mapping (2.2)."""
        assert route(f"{base}_mapper.md") == "docs/mapping"

    def test_entity_spec_routes_to_docs_reference(self):
        """The entity specification routes to docs/reference (2.3)."""
        assert route("senzing_entity_specification.md") == "docs/reference"


class TestProperty1ConventionalPlacement:
    """Feature: docs-file-placement, Property 1: Conventional placement.

    Recognized files land under their conventional subdir after execute_moves
    and never at the project root or directly under the docs/ root.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    @given(filenames=st_recognized_files())
    @settings(max_examples=20)
    def test_recognized_files_land_in_conventional_subdir(self, filenames):
        """Each recognized file lands under route()'s subdir, never at root."""
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            for fname in filenames:
                (source / fname).write_text(f"content of {fname}")

            execute_moves(plan_moves(scan_source(source), project_root))

            for fname in filenames:
                subdir = route(fname)
                assert subdir is not None, f"{fname} unexpectedly unrouted"
                expected_dest = project_root / subdir / fname
                assert expected_dest.exists(), (
                    f"{fname} not at conventional destination {expected_dest}"
                )

                # Never left at the project root.
                assert not (project_root / fname).exists(), (
                    f"{fname} left at project root"
                )
                # Never placed directly under the docs/ root.
                assert not (project_root / "docs" / fname).exists(), (
                    f"{fname} placed directly under docs/ root"
                )

                # The destination is genuinely nested below the conventional
                # subdir, which is itself below the project root.
                rel = expected_dest.parent.relative_to(project_root).as_posix()
                assert rel == subdir, f"{fname} parent {rel!r} != subdir {subdir!r}"
                assert rel not in ("", "docs"), (
                    f"{fname} routed to a bare root/docs location: {rel!r}"
                )
        finally:
            shutil.rmtree(tmp)


class TestProperty5EntitySpecDeduplication:
    """Feature: docs-file-placement, Property 5: Entity-spec deduplication.

    With a pre-existing docs/reference/senzing_entity_specification.md AND a
    misplaced source copy, after the organizer run exactly one copy exists under
    docs/reference/ and stderr reports the dedup.

    **Validates: Requirements 2.3**
    """

    @given(canonical_body=st.text(alphabet="abcdefghij \n#", min_size=1, max_size=40))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_entity_spec_deduplicated_to_single_copy(self, canonical_body, capsys):
        """A misplaced entity-spec source is removed, leaving one canonical copy."""
        entity_spec = "senzing_entity_specification.md"
        tmp = Path(tempfile.mkdtemp())
        try:
            source = tmp / "source"
            source.mkdir()
            project_root = tmp / "project"
            project_root.mkdir()

            # Misplaced source copy.
            (source / entity_spec).write_text("misplaced source copy")

            # Pre-existing canonical copy under docs/reference/.
            reference_dir = project_root / "docs" / "reference"
            reference_dir.mkdir(parents=True, exist_ok=True)
            canonical = reference_dir / entity_spec
            canonical.write_text(canonical_body)

            plan = plan_moves(scan_source(source), project_root)
            execute_moves(plan)
            print_summary(plan, dry_run=False)
            captured = capsys.readouterr()

            # The misplaced source copy is gone.
            assert not (source / entity_spec).exists(), (
                "misplaced entity-spec source copy was not removed"
            )

            # Exactly one copy exists anywhere under docs/reference/.
            copies = list((project_root / "docs" / "reference").rglob(entity_spec))
            assert len(copies) == 1, (
                f"expected exactly one entity-spec under docs/reference/, found {copies}"
            )
            # The canonical copy is preserved byte-for-byte (not overwritten).
            assert canonical.read_text() == canonical_body

            # The dedup is reported on stderr.
            assert entity_spec in captured.err
            statuses = {r.status for r in plan if r.source.name == entity_spec}
            assert statuses == {"deduplicate"}, (
                f"expected deduplicate status, got {statuses}"
            )
        finally:
            shutil.rmtree(tmp)


class TestRouteUnitTable:
    """Feature: docs-file-placement, Property 4 / unit route() table.

    Exact route() outputs for representative filenames covering every rule and
    an unrouted extension.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """

    def test_python_helper_routes_to_src_mapping(self):
        """A Python helper (.py) routes to src/mapping."""
        assert route("sz_json_analyzer.py") == "src/mapping"

    def test_mapper_spec_routes_to_docs_mapping(self):
        """A mapper spec (*_mapper.md) routes to docs/mapping."""
        assert route("playpalace_mapper.md") == "docs/mapping"

    def test_entity_spec_routes_to_docs_reference(self):
        """The entity spec routes to docs/reference."""
        assert route("senzing_entity_specification.md") == "docs/reference"

    def test_generic_reference_md_routes_to_docs_mapping(self):
        """A generic reference .md routes to docs/mapping."""
        assert route("profile_report.md") == "docs/mapping"

    def test_jsonl_routes_to_data(self):
        """A .jsonl file routes to data."""
        assert route("customers.jsonl") == "data"

    def test_json_routes_to_config(self):
        """A .json file routes to config."""
        assert route("identifier_crosswalk.json") == "config"

    def test_unrouted_extension_returns_none(self):
        """An unrouted extension (.txt) returns None."""
        assert route("notes.txt") is None


class TestHookSchemaValidity:
    """Feature: docs-file-placement, hook JSON schema validity.

    The write-policy-gate hook parses as JSON and carries the required schema
    fields with a preToolUse write trigger.

    **Validates: Requirements 2.4**
    """

    def test_hook_is_valid_json_with_required_schema(self):
        """name/version/when/then present; when targets preToolUse writes."""
        data = json.loads(_HOOK_PATH.read_text(encoding="utf-8"))

        for field in ("name", "version", "when", "then"):
            assert field in data, f"hook missing required field {field!r}"

        assert data["when"]["type"] == "preToolUse"
        assert data["when"]["toolTypes"] == ["write"]


# ===========================================================================
# Feature: docs-file-placement (BUGFIX)
# Task 4 — Integration test: full mapping-output sweep + docs index
#
# A mixed source directory (helper .py, *_mapper.md, entity spec, generic
# reference .md, .jsonl, .json) organizes into its conventional subdirs in a
# single run, then the docs-index generator produces a complete docs/README.md
# listing every doc under docs/. Re-running the sweep is idempotent (no spurious
# moves) and regenerating the index yields byte-identical content (stable, no
# diff).
#
# **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.5, 3.6**
# ===========================================================================

import generate_docs_index  # noqa: E402


class TestIntegrationFullSweepAndIndex:
    """Feature: docs-file-placement, Task 4 integration — sweep + docs index.

    End-to-end: organize a mixed mapping-output directory into conventional
    locations, generate a complete docs index, then confirm idempotence of the
    sweep and byte-identical stability of the regenerated index.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.5, 3.6**
    """

    # Source filename -> file content for the mixed mapping-output directory.
    _SOURCE_FILES: dict[str, str] = {
        "sz_json_analyzer.py": "# helper analyzer\nprint('analyze')\n",
        "playpalace_mapper.md": "# PlayPalace Mapper\n\nPer-source mapping spec.\n",
        "senzing_entity_specification.md": "# Senzing Entity Specification\n\nReference.\n",
        "profile_report.md": "# Profile Report\n\nGeneric mapping reference doc.\n",
        "customers.jsonl": '{"name": "Acme"}\n',
        "identifier_crosswalk.json": '{"id": "crosswalk"}\n',
    }

    # Source filename -> conventional destination subdirectory.
    _EXPECTED_PLACEMENT: dict[str, str] = {
        "sz_json_analyzer.py": "src/mapping",
        "playpalace_mapper.md": "docs/mapping",
        "senzing_entity_specification.md": "docs/reference",
        "profile_report.md": "docs/mapping",
        "customers.jsonl": "data",
        "identifier_crosswalk.json": "config",
    }

    def test_mixed_sweep_places_files_and_builds_stable_index(self, tmp_path, capsys):
        """Mixed sources land in conventional subdirs; index is complete and stable."""
        source = tmp_path / "source"
        source.mkdir()
        project_root = tmp_path / "project"
        project_root.mkdir()

        for name, content in self._SOURCE_FILES.items():
            (source / name).write_text(content)

        # --- First organizer sweep -----------------------------------------
        plan = plan_moves(scan_source(source), project_root)
        execute_moves(plan)
        print_summary(plan, dry_run=False)
        capsys.readouterr()

        # Each file lands at its conventional destination with content intact
        # and is removed from the flat source directory.
        for name, subdir in self._EXPECTED_PLACEMENT.items():
            dest = project_root / subdir / name
            assert dest.exists(), f"{name} not placed under {subdir}/"
            assert dest.read_text() == self._SOURCE_FILES[name], (
                f"{name} content changed during the sweep"
            )
            assert not (source / name).exists(), (
                f"{name} still present in the flat source directory"
            )

        # --- Docs index generation -----------------------------------------
        docs_root = project_root / "docs"
        assert generate_docs_index.main(["--docs-root", str(docs_root)]) == 0
        capsys.readouterr()

        readme = docs_root / "README.md"
        assert readme.exists(), "docs/README.md was not generated"
        index_text = readme.read_text()

        # The docs index enumerates the depth-1 contents of docs/: each
        # immediate subdirectory appears exactly once as a single entry (with a
        # trailing "/" indicator). The nested docs live under mapping/ and
        # reference/, so both subdirectory entries must be listed.
        for entry in ("mapping/", "reference/"):
            assert entry in index_text, f"{entry} missing from generated docs index"
        # Depth-1 enumeration never recurses, so nested file names do not appear
        # as their own index entries.
        for nested in (
            "playpalace_mapper.md",
            "senzing_entity_specification.md",
            "profile_report.md",
        ):
            assert nested not in index_text, (
                f"{nested} should not be listed; the index enumerates depth-1 only"
            )

        # The freshly written index is reported in sync by --check.
        assert (
            generate_docs_index.main(["--docs-root", str(docs_root), "--check"]) == 0
        ), "docs index reported out of sync immediately after generation"
        capsys.readouterr()

        # --- Idempotence: a second sweep produces no spurious moves --------
        plan2 = plan_moves(scan_source(source), project_root)
        execute_moves(plan2)
        capsys.readouterr()
        assert [r for r in plan2 if r.status == "moved"] == [], (
            "second organizer sweep produced spurious moves"
        )

        # --- Stability: regenerated index is byte-identical ----------------
        regenerated = generate_docs_index.generate_index(docs_root)
        assert regenerated == index_text, (
            "regenerated docs index drifted from the first generation"
        )
        assert generate_docs_index.main(["--docs-root", str(docs_root)]) == 0
        capsys.readouterr()
        assert readme.read_text() == index_text, (
            "rewriting docs/README.md changed its bytes (unstable output)"
        )
