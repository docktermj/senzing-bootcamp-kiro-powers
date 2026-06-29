"""Property-based tests for generate_power_docs.py.

Feature: generated-power-docs

Hypothesis property tests for the POWER.md documentation generator. The shared
world generators live in ``conftest.py``: ``st_world_spec()`` draws a pure,
self-consistent description of the generator's sources and ``materialize_world``
writes that description (hook files + ``hook-categories.yaml``,
``steering-index.yaml`` + steering files, ``module-dependencies.yaml``, and a
``POWER.md`` skeleton with the four marker pairs) to a throwaway directory.

This module currently holds the scaffolding smoke property (Property 0). The
numbered correctness properties (1-11) are added by the later 12.x tasks, each
reusing ``st_world_spec`` / ``materialize_world`` from here.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_power_docs as gpd  # noqa: E402
from generate_power_docs import (  # noqa: E402
    assemble,
    build_regions,
    load_sources,
    locate_regions,
    main,
    render_all,
    verify,
)
from mcp_tool_inventory import ALL_TOOLS  # noqa: E402

# Import the shared strategies/helpers from this directory's conftest using a
# package-relative import. This test module is collected as part of the
# ``tests`` package (``senzing-bootcamp/tests/__init__.py``), so ``.conftest``
# resolves unambiguously to the sibling conftest. A bare ``from conftest import``
# is unsafe in the combined CI run (``pytest senzing-bootcamp/tests/ tests/``)
# because the repo-root ``tests/conftest.py`` registers the top-level
# ``conftest`` module name and shadows this one.
from .conftest import (  # noqa: E402
    REGION_IDS,
    disable_commonmark,
    materialize_world,
    st_world_spec,
)


class TestScaffoldingSmoke:
    """End-to-end sanity check that the world generators feed the generator.

    Validates the 12.1 scaffolding: a drawn world materializes to disk, its
    sources load without error, and a Write_Mode ``main(...)`` run over the
    skeleton returns 0. This exercises load -> render -> locate -> assemble ->
    normalize -> write for every drawn world without asserting any specific
    rendered content (that is the job of the numbered properties).
    """

    @settings(
        max_examples=25,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_world_loads_and_write_mode_succeeds(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 0: scaffolding smoke check —
        # every drawn world loads and a Write_Mode run completes cleanly.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_world_"))
        try:
            world = materialize_world(spec, base_dir)

            # load_sources succeeds and reflects the drawn world.
            sources = load_sources(world.paths)
            assert sources.total_count == len(sources.tools)
            assert {hook.hook_id for hook in sources.hooks} == set(spec.hook_ids)
            assert {hook.hook_id for hook in sources.hooks if hook.is_critical} == set(
                spec.critical_ids
            )
            assert len(sources.steering) == len(spec.steering)
            assert len(sources.modules) == len(spec.modules)

            # A full Write_Mode run over the skeleton returns success.
            exit_code = main(
                [
                    "--write",
                    "--power-md", str(world.paths.power_md),
                    "--hooks-dir", str(world.paths.hooks_dir),
                    "--hook-categories", str(world.paths.hook_categories),
                    "--steering-index", str(world.paths.steering_index),
                    "--module-deps", str(world.paths.module_deps),
                    "--repo-root", str(world.paths.repo_root),
                ]
            )
            assert exit_code == 0

            # The written document still carries all four marker pairs.
            written = world.paths.power_md.read_text(encoding="utf-8")
            for region_id in ("mcp-tools", "hooks", "steering-files", "modules"):
                assert f"<!-- BEGIN GENERATED: {region_id} -->" in written
                assert f"<!-- END GENERATED: {region_id} -->" in written
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Shared helpers for the numbered correctness properties
# ---------------------------------------------------------------------------


def _source_argv(paths) -> list[str]:
    """Return the source-path CLI flags pointing at a materialized world.

    Args:
        paths: The ``SourcePaths`` from a :class:`MaterializedWorld`.

    Returns:
        The list of ``--power-md`` / source-override flags (no mode flag).
    """
    return [
        "--power-md", str(paths.power_md),
        "--hooks-dir", str(paths.hooks_dir),
        "--hook-categories", str(paths.hook_categories),
        "--steering-index", str(paths.steering_index),
        "--module-deps", str(paths.module_deps),
        "--repo-root", str(paths.repo_root),
    ]


def _write_argv(paths) -> list[str]:
    """Return the full ``--write`` argv for a materialized world."""
    return ["--write", *_source_argv(paths)]


def _verify_argv(paths) -> list[str]:
    """Return the full ``--verify`` argv for a materialized world."""
    return ["--verify", *_source_argv(paths)]


def _region_bodies(doc: str) -> dict[str, str]:
    """Return the current body text of each generated region in ``doc``.

    Args:
        doc: A ``POWER.md`` document carrying the four marker pairs.

    Returns:
        A mapping ``region_id -> body`` for every region in :data:`REGION_IDS`.
    """
    spans = locate_regions(doc, set(REGION_IDS))
    return {rid: spans[rid].body for rid in REGION_IDS}


def _skeleton_projection(doc: str) -> str:
    """Return ``doc`` with every region body blanked, markers/prose intact.

    Splices an empty body into each region using its located span, so the
    result preserves every byte outside the region bodies (marker lines and all
    surrounding prose) while discarding the body contents. Two documents that
    differ only inside region bodies share the same projection.

    Args:
        doc: A ``POWER.md`` document carrying the four marker pairs.

    Returns:
        The document with all four region bodies replaced by the empty string.
    """
    spans = locate_regions(doc, set(REGION_IDS))
    return assemble(doc, spans, {rid: "" for rid in REGION_IDS})


_MCP_TOOL_RE = re.compile(r"^- `([a-z_]+)`", re.MULTILINE)
_HOOKS_COUNT_RE = re.compile(r"Available \((\d+) hooks\):")
_HOOK_ENTRY_RE = re.compile(r"`([a-z-]+)`( \u2b50)?")
_STEERING_ROW_RE = re.compile(r"^\| `([^`]+)` \| (\d+) \| (\w+) \|$", re.MULTILINE)
_MODULE_ROW_RE = re.compile(r"^\| (\d+) \| (.*?) \|$", re.MULTILINE)
_MODULE_COUNT_RE = re.compile(r"^Total: (\d+) modules\.$", re.MULTILINE)


class TestProperty1WriteIdempotency:
    """Property 1: two Write_Mode runs produce byte-identical POWER.md.

    Validates: Requirements 4.1, 8.1.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_write_is_idempotent(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 1: write idempotency — two
        # successive Write_Mode runs against identical sources produce
        # byte-identical POWER.md.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p1_"))
        try:
            world = materialize_world(spec, base_dir)
            assert main(_write_argv(world.paths)) == 0
            first = world.paths.power_md.read_bytes()
            assert main(_write_argv(world.paths)) == 0
            second = world.paths.power_md.read_bytes()
            assert first == second
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


class TestProperty2WriteVerifyRoundTrip:
    """Property 2: Write then Verify against unchanged sources is clean.

    Validates: Requirements 3.1, 3.3, 4.2, 6.6, 8.2.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_write_then_verify_is_clean(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 2: write-then-verify round-trip
        # is clean — Write then Verify against unchanged sources exits 0.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p2_"))
        try:
            world = materialize_world(spec, base_dir)
            assert main(_write_argv(world.paths)) == 0
            assert main(_verify_argv(world.paths)) == 0
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


class TestProperty3ProsePreservation:
    """Property 3: Write_Mode mutates only region bodies.

    Validates: Requirements 2.2, 2.3.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_only_region_bodies_change(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 3: prose preservation — every
        # byte outside the region bodies (and the marker lines) is unchanged.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p3_"))
        try:
            world = materialize_world(spec, base_dir)
            before = world.paths.power_md.read_text(encoding="utf-8")
            assert main(_write_argv(world.paths)) == 0
            after = world.paths.power_md.read_text(encoding="utf-8")

            # Blanking every region body must yield identical documents: only
            # the bodies may have changed; markers and all prose are intact.
            assert _skeleton_projection(before) == _skeleton_projection(after)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


class TestProperty4DeterminismIndependentOfEnvironment:
    """Property 4: output is independent of environment and source order.

    Validates: Requirements 4.4, 4.5, 9.2, 12.3.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_env_and_order_do_not_change_output(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 4: determinism independent of
        # environment and source order — mutated LC_ALL/TZ and a re-materialized
        # identical world both yield identical generated bodies.
        disable_commonmark(monkeypatch)

        first_dir = Path(tempfile.mkdtemp(prefix="gpd_p4a_"))
        second_dir = Path(tempfile.mkdtemp(prefix="gpd_p4b_"))
        try:
            # Run once under a baseline environment.
            monkeypatch.setenv("LC_ALL", "C")
            monkeypatch.setenv("TZ", "UTC")
            world = materialize_world(spec, first_dir)
            assert main(_write_argv(world.paths)) == 0
            bytes_a = world.paths.power_md.read_bytes()

            # Mutate the environment and rerun in the same world: byte-identical.
            monkeypatch.setenv("LC_ALL", "fr_FR.UTF-8")
            monkeypatch.setenv("TZ", "Asia/Kolkata")
            assert main(_write_argv(world.paths)) == 0
            bytes_b = world.paths.power_md.read_bytes()
            assert bytes_a == bytes_b

            # Source-enumeration-order independence: a second identical world
            # materialized into a different directory renders identical bodies
            # (the generator sorts hooks/steering/modules deterministically).
            other = materialize_world(spec, second_dir)
            assert main(_write_argv(other.paths)) == 0
            assert _region_bodies(
                world.paths.power_md.read_text(encoding="utf-8")
            ) == _region_bodies(
                other.paths.power_md.read_text(encoding="utf-8")
            )
        finally:
            shutil.rmtree(first_dir, ignore_errors=True)
            shutil.rmtree(second_dir, ignore_errors=True)


class TestProperty5PerRegionContentCorrectness:
    """Property 5: each region body matches its source of truth exactly.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 9.1, 9.3, 10.1, 10.2, 10.3,
    11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_region_bodies_reflect_sources(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 5: per-region content
        # correctness — mcp-tools/hooks/steering-files/modules bodies match
        # their sources of truth exactly.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p5_"))
        try:
            world = materialize_world(spec, base_dir)
            assert main(_write_argv(world.paths)) == 0
            bodies = _region_bodies(
                world.paths.power_md.read_text(encoding="utf-8")
            )

            # --- mcp-tools: exactly the real inventory, one bullet per tool ---
            tool_names = _MCP_TOOL_RE.findall(bodies["mcp-tools"])
            assert set(tool_names) == set(ALL_TOOLS)
            assert len(tool_names) == len(ALL_TOOLS)

            # --- hooks: count, membership, and exact critical marks ---
            hooks_body = bodies["hooks"]
            count_match = _HOOKS_COUNT_RE.search(hooks_body)
            assert count_match is not None
            assert int(count_match.group(1)) == len(spec.hook_ids)
            listed_ids: set[str] = set()
            starred_ids: set[str] = set()
            for hook_id, star in _HOOK_ENTRY_RE.findall(hooks_body):
                listed_ids.add(hook_id)
                if star:
                    starred_ids.add(hook_id)
            assert listed_ids == set(spec.hook_ids)
            assert starred_ids == set(spec.critical_ids)

            # --- steering-files: one row per entry, sorted, with footer ---
            steering_rows = _STEERING_ROW_RE.findall(bodies["steering-files"])
            expected_steering = sorted(spec.steering, key=lambda e: e.filename)
            assert len(steering_rows) == len(expected_steering)
            assert [row[0] for row in steering_rows] == [
                e.filename for e in expected_steering
            ]
            for (filename, tokens, size), entry in zip(
                steering_rows, expected_steering
            ):
                assert filename == entry.filename
                assert int(tokens) == entry.token_count
                assert size == entry.size_category
            assert (
                f"**Total budget:** {spec.budget_total} tokens"
                in bodies["steering-files"]
            )

            # --- modules: one row per module, ascending, with count line ---
            module_rows = _MODULE_ROW_RE.findall(bodies["modules"])
            expected_modules = sorted(spec.modules, key=lambda m: m.number)
            assert len(module_rows) == len(expected_modules)
            assert [int(num) for num, _ in module_rows] == [
                m.number for m in expected_modules
            ]
            for (num, name), module in zip(module_rows, expected_modules):
                assert int(num) == module.number
                assert name == module.name
            count_match = _MODULE_COUNT_RE.search(bodies["modules"])
            assert count_match is not None
            assert int(count_match.group(1)) == len(spec.modules)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


class TestProperty6DriftDetection:
    """Property 6: Verify reports exactly the regions that were changed.

    Validates: Requirements 3.1, 3.2, 3.7, 4.3.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        spec=st_world_spec(),
        victim_indices=st.sets(st.integers(min_value=0, max_value=3), min_size=1),
    )
    def test_verify_reports_exactly_the_drifted_regions(
        self, spec, victim_indices, monkeypatch
    ):
        # Feature: generated-power-docs, Property 6: drift detection reports
        # exactly the changed regions — mutating a subset of region bodies makes
        # Verify report exactly that subset and exit 1.
        disable_commonmark(monkeypatch)
        victim_ids = {REGION_IDS[i] for i in victim_indices}
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p6_"))
        try:
            world = materialize_world(spec, base_dir)
            assert main(_write_argv(world.paths)) == 0

            # Inject a DRIFT line at the top of each victim region body. Insert
            # at the highest offsets first so earlier offsets stay valid.
            doc = world.paths.power_md.read_text(encoding="utf-8")
            spans = locate_regions(doc, set(REGION_IDS))
            insert_points = sorted(
                (spans[rid].begin_marker_end for rid in victim_ids),
                reverse=True,
            )
            for offset in insert_points:
                doc = doc[:offset] + "DRIFT\n" + doc[offset:]
            world.paths.power_md.write_text(doc, encoding="utf-8")

            # CLI Verify_Mode reports drift with a non-zero exit.
            assert main(_verify_argv(world.paths)) == 1

            # Pure path: assert the drifted set is exactly the mutated subset.
            sources = load_sources(world.paths)
            regions = build_regions(world.paths)
            bodies = render_all(sources, regions)
            mutated = world.paths.power_md.read_text(encoding="utf-8")
            mutated_spans = locate_regions(mutated, set(REGION_IDS))
            result = verify(mutated, mutated_spans, bodies)
            assert set(result.drifted_region_ids) == victim_ids
            assert result.drift_count == len(victim_ids)
            assert result.missing_region_ids == ()
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


def _snapshot_tree(root: Path) -> dict[str, bytes | None]:
    """Snapshot every file's bytes and the directory structure under ``root``.

    Walks ``root`` recursively and records, for each entry relative to ``root``,
    the file's raw bytes (for files) or ``None`` (for directories). Two
    snapshots compare equal only when the set of paths is identical, every file
    holds identical bytes, and the directory tree is unchanged.

    Args:
        root: The directory to snapshot.

    Returns:
        A mapping of POSIX relative path -> file bytes (or ``None`` for a dir).
    """
    snapshot: dict[str, bytes | None] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            snapshot[rel] = None
        else:
            snapshot[rel] = path.read_bytes()
    return snapshot


class TestProperty7VerifyNeverMutatesFilesystem:
    """Property 7: Verify_Mode creates, modifies, or deletes no file.

    Validates: Requirements 3.4.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_verify_leaves_filesystem_unchanged(self, spec, monkeypatch):
        # Feature: generated-power-docs, Property 7: verify never mutates the
        # filesystem — for clean or drifted input, Verify_Mode leaves every
        # file's bytes and the directory tree identical.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p7_"))
        try:
            world = materialize_world(spec, base_dir)
            # Produce a clean, up-to-date POWER.md to verify against.
            assert main(_write_argv(world.paths)) == 0

            # --- Clean input: Verify_Mode reports success and mutates nothing.
            before_clean = _snapshot_tree(base_dir)
            assert main(_verify_argv(world.paths)) == 0
            after_clean = _snapshot_tree(base_dir)
            assert after_clean == before_clean

            # --- Drifted input: inject a DRIFT line into every region body.
            doc = world.paths.power_md.read_text(encoding="utf-8")
            spans = locate_regions(doc, set(REGION_IDS))
            insert_points = sorted(
                (spans[rid].begin_marker_end for rid in REGION_IDS),
                reverse=True,
            )
            for offset in insert_points:
                doc = doc[:offset] + "DRIFT\n" + doc[offset:]
            world.paths.power_md.write_text(doc, encoding="utf-8")

            # Verify_Mode reports drift (exit 1) yet still mutates nothing.
            before_drift = _snapshot_tree(base_dir)
            assert main(_verify_argv(world.paths)) == 1
            after_drift = _snapshot_tree(base_dir)
            assert after_drift == before_drift
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


@pytest.mark.slow
class TestProperty11WrittenOutputIsCommonMarkValid:
    """Property 11: Write_Mode output passes ``validate_commonmark.py``.

    Validates: Requirements 5.1.

    Marked ``slow``: each example shells out to the markdownlint-backed
    CommonMark validator, making this the single longest-running test in the
    suite (~28s on the fast profile, far longer on ``thorough``).
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec())
    def test_written_output_is_commonmark_valid(self, spec):
        # Feature: generated-power-docs, Property 11: written output is
        # CommonMark-valid — the POWER.md produced by Write_Mode passes the same
        # CommonMark gate that validate_commonmark.py runs in CI.
        #
        # This property deliberately does NOT call disable_commonmark: it must
        # exercise the real markdownlint-backed validation against the generated
        # document. Write_Mode validates the assembled, newline-normalized
        # candidate before the atomic write, so a successful exit already proves
        # the written POWER.md is CommonMark-valid; we then re-run the same gate
        # over the written bytes to assert it directly.
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p11_"))
        try:
            world = materialize_world(spec, base_dir)
            assert main(_write_argv(world.paths)) == 0

            written = world.paths.power_md.read_text(encoding="utf-8")
            # validate_commonmark_text raises GeneratorError on any CommonMark
            # violation (and is a silent no-op only when markdownlint is absent),
            # so a clean return proves the produced document passes the gate.
            gpd.validate_commonmark_text(written)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 8 helpers: marker-integrity violations
# ---------------------------------------------------------------------------


# The four recognized marker-integrity violations, one per acceptance criterion:
#   "missing"          -> Req 2.4 (expected region's begin/end marker missing)
#   "begin_no_end"     -> Req 2.5 (begin without a matching end)
#   "end_before_begin" -> Req 2.6 (end appears before its begin)
#   "duplicate_begin"  -> Req 2.7 (duplicated begin identifier)
_MARKER_VIOLATIONS: tuple[str, ...] = (
    "missing",
    "begin_no_end",
    "end_before_begin",
    "duplicate_begin",
)


def _corrupt_markers(doc: str, region_id: str, violation: str) -> str:
    """Return ``doc`` with ``region_id``'s markers corrupted per ``violation``.

    Operates on a freshly materialized skeleton in which each region's begin
    marker is immediately followed by its end marker (empty body), so the
    begin/end lines are adjacent and unique.

    Args:
        doc: The original POWER.md text carrying the four valid marker pairs.
        region_id: The region whose markers are corrupted.
        violation: One of :data:`_MARKER_VIOLATIONS`.

    Returns:
        The corrupted document text.
    """
    begin = f"<!-- BEGIN GENERATED: {region_id} -->\n"
    end = f"<!-- END GENERATED: {region_id} -->\n"
    assert begin in doc and end in doc

    if violation == "missing":
        # Both markers for the expected region removed entirely (Req 2.4).
        return doc.replace(begin, "").replace(end, "")
    if violation == "begin_no_end":
        # Begin retained, end removed -> begin without matching end (Req 2.5).
        return doc.replace(end, "")
    if violation == "end_before_begin":
        # Swap the adjacent begin/end pair so end precedes begin (Req 2.6).
        return doc.replace(begin + end, end + begin)
    if violation == "duplicate_begin":
        # A second begin marker carrying the same id (Req 2.7).
        return doc.replace(begin, begin + begin)
    raise AssertionError(f"unknown violation: {violation}")  # pragma: no cover


class TestProperty8MarkerIntegrityViolations:
    """Property 8: marker integrity violations abort Write_Mode without mutation.

    Validates: Requirements 2.4, 2.5, 2.6, 2.7.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        spec=st_world_spec(),
        region_index=st.integers(min_value=0, max_value=len(REGION_IDS) - 1),
        violation=st.sampled_from(_MARKER_VIOLATIONS),
    )
    def test_marker_violation_aborts_without_mutation(
        self, spec, region_index, violation, monkeypatch, capsys
    ):
        # Feature: generated-power-docs, Property 8: marker integrity violations
        # abort without mutation — any recognized marker violation reports the
        # region id, leaves POWER.md byte-for-byte unchanged, and exits non-zero.
        disable_commonmark(monkeypatch)
        region_id = REGION_IDS[region_index]
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p8_"))
        try:
            world = materialize_world(spec, base_dir)

            # Corrupt the skeleton's markers and commit the broken file to disk.
            doc = world.paths.power_md.read_text(encoding="utf-8")
            corrupted = _corrupt_markers(doc, region_id, violation)
            assert corrupted != doc
            world.paths.power_md.write_text(corrupted, encoding="utf-8")

            # Snapshot the exact bytes Write_Mode is invoked against.
            before = world.paths.power_md.read_bytes()

            # Write_Mode must abort non-zero and touch nothing.
            exit_code = main(_write_argv(world.paths))
            assert exit_code != 0

            # POWER.md is byte-for-byte unchanged.
            assert world.paths.power_md.read_bytes() == before

            # The affected region id is reported on stderr.
            captured = capsys.readouterr()
            assert region_id in captured.err

            # The pure locate path raises MarkerError naming the same region.
            with pytest.raises(gpd.MarkerError) as exc_info:
                locate_regions(corrupted, set(REGION_IDS))
            assert region_id in str(exc_info.value.args)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 10 helpers: inject arbitrary line endings into a POWER.md skeleton
# ---------------------------------------------------------------------------

# Line endings the generator must normalize away: Unix, Windows, classic-Mac.
_LINE_ENDINGS: tuple[str, ...] = ("\n", "\r\n", "\r")
# Endings that keep a line locatable by the ``^...-->\s*$`` (re.MULTILINE)
# marker regex, which anchors only on ``\n``: a marker line — and the line
# directly before it — must terminate in a ``\n`` so the marker still matches.
_LF_TERMINATED: tuple[str, ...] = ("\n", "\r\n")


def _is_marker_line(line: str) -> bool:
    """Return True when ``line`` is a generated-region begin/end marker."""
    return "GENERATED:" in line


def _reending(doc: str, draw) -> str:
    """Rewrite ``doc`` with Hypothesis-drawn line endings, markers preserved.

    The skeleton produced by ``build_power_md_skeleton`` uses ``\\n`` throughout.
    This splits it into logical lines and re-joins them with an ending drawn per
    line from CRLF / bare-CR / LF, so the surrounding prose carries arbitrary
    line endings (including carriage returns the generator must normalize away).

    To keep every Generated_Region locatable, any marker line and the line
    immediately preceding a marker line are forced to a ``\\n``-terminated ending
    (``\\n`` or ``\\r\\n``); the marker-matching regex anchors only on ``\\n``.

    Args:
        doc: The ``\\n``-terminated skeleton document.
        draw: The Hypothesis ``data.draw`` callable.

    Returns:
        The document re-joined with arbitrary, marker-safe line endings.
    """
    # doc ends in "\n", so split drops a trailing "" sentinel we re-add as "".
    lines = doc.split("\n")
    content_lines = lines[:-1]  # the real lines; lines[-1] == ""
    pieces: list[str] = []
    for index, line in enumerate(content_lines):
        next_is_marker = (
            index + 1 < len(content_lines)
            and _is_marker_line(content_lines[index + 1])
        )
        if _is_marker_line(line) or next_is_marker:
            ending = draw(st.sampled_from(_LF_TERMINATED))
        else:
            ending = draw(st.sampled_from(_LINE_ENDINGS))
        pieces.append(line + ending)
    return "".join(pieces)


class TestProperty10OutputNewlineNormalization:
    """Property 10: written POWER.md has no CR and one trailing LF.

    Validates: Requirements 5.5, 5.6.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(spec=st_world_spec(), data=st.data())
    def test_output_has_no_cr_and_single_trailing_lf(self, spec, data, monkeypatch):
        # Feature: generated-power-docs, Property 10: output newline
        # normalization — for prose with arbitrary CRLF/CR endings, the written
        # document has no carriage returns and exactly one trailing line-feed.
        disable_commonmark(monkeypatch)
        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p10_"))
        try:
            world = materialize_world(spec, base_dir)

            # Rewrite the skeleton's prose with arbitrary (CRLF/CR/LF) endings,
            # keeping marker lines locatable, then run Write_Mode over it.
            skeleton = world.paths.power_md.read_text(encoding="utf-8")
            mangled = _reending(skeleton, data.draw)
            world.paths.power_md.write_bytes(mangled.encode("utf-8"))

            assert main(_write_argv(world.paths)) == 0

            written = world.paths.power_md.read_bytes()
            # Req 5.6: no carriage-return line terminators anywhere.
            assert b"\r" not in written
            # Req 5.5: terminated by exactly one trailing line-feed.
            assert written.endswith(b"\n")
            assert not written.endswith(b"\n\n")
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 9 helpers: aborting Write_Mode error injectors
# ---------------------------------------------------------------------------
#
# Each injector takes a materialized world (and the test's monkeypatch) and
# introduces exactly one aborting Write_Mode error condition without ever
# touching POWER.md, then returns. The world is otherwise fully valid, so the
# injected condition is the sole reason the run must abort. The error kinds span
# every category named by Property 9: an unreadable source, an unparseable
# source, the MCP TOTAL_COUNT invariant, a module/steering missing-field
# invariant, a missing referenced file, and a CommonMark validation failure.

# A steering filename guaranteed not to collide with any drawn world filename
# (drawn stems are <= 12 chars of [a-z0-9-]); this name is longer and unique.
_ABSENT_STEERING_FILE = "property9-guaranteed-absent-steering-file.md"


def _inject_unparseable_source(world, monkeypatch) -> None:
    """Make ``module-dependencies.yaml`` unparseable (Req 1.5/1.6)."""
    world.paths.module_deps.write_text("{ this is : not valid : yaml\n", encoding="utf-8")


def _inject_unreadable_source(world, monkeypatch) -> None:
    """Delete ``steering-index.yaml`` so reading it raises OSError (Req 1.5/1.6)."""
    world.paths.steering_index.unlink()


def _inject_total_count_mismatch(world, monkeypatch) -> None:
    """Force ``TOTAL_COUNT`` to disagree with ``len(ALL_TOOLS)`` (Req 9.4)."""
    import mcp_tool_inventory

    monkeypatch.setattr(
        mcp_tool_inventory, "TOTAL_COUNT", len(ALL_TOOLS) + 1, raising=True
    )


def _inject_module_missing_name(world, monkeypatch) -> None:
    """Record a module with no ``name`` field (Req 12.5)."""
    world.paths.module_deps.write_text("modules:\n  7: {}\n", encoding="utf-8")


def _inject_steering_missing_field(world, monkeypatch) -> None:
    """Record a steering entry missing its ``token_count`` (Req 11.5)."""
    world.paths.steering_index.write_text(
        "file_metadata:\n"
        "  needs-token.md:\n"
        "    size_category: small\n"
        "budget:\n"
        "  total_tokens: 1\n",
        encoding="utf-8",
    )


def _inject_missing_referenced_file(world, monkeypatch) -> None:
    """Reference a steering file that does not exist on disk (Req 5.4/5.7)."""
    steering_dir = world.paths.steering_index.parent
    absent = steering_dir / _ABSENT_STEERING_FILE
    if absent.exists():
        absent.unlink()
    world.paths.steering_index.write_text(
        "file_metadata:\n"
        f"  {_ABSENT_STEERING_FILE}:\n"
        "    token_count: 5\n"
        "    size_category: small\n"
        "budget:\n"
        "  total_tokens: 1\n",
        encoding="utf-8",
    )


def _inject_commonmark_failure(world, monkeypatch) -> None:
    """Make CommonMark validation of the candidate document fail (Req 5.7)."""
    def _raise(_content: str) -> None:
        raise gpd.GeneratorError("CommonMark validation failed (injected)")

    monkeypatch.setattr(gpd, "validate_commonmark_text", _raise)


# Label -> injector. ``st.sampled_from`` over the labels drives Hypothesis to
# exercise every aborting error category across the generated examples.
_ERROR_INJECTORS: dict[str, object] = {
    "unparseable_source": _inject_unparseable_source,
    "unreadable_source": _inject_unreadable_source,
    "total_count_mismatch": _inject_total_count_mismatch,
    "module_missing_name": _inject_module_missing_name,
    "steering_missing_field": _inject_steering_missing_field,
    "missing_referenced_file": _inject_missing_referenced_file,
    "commonmark_failure": _inject_commonmark_failure,
}


class TestProperty9NoPartialWriteOnError:
    """Property 9: any aborting Write_Mode error leaves POWER.md unchanged.

    Validates: Requirements 1.5, 1.6, 5.7, 9.4, 12.5.
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        spec=st_world_spec(),
        error_kind=st.sampled_from(sorted(_ERROR_INJECTORS)),
    )
    def test_aborting_error_leaves_power_md_unchanged(
        self, spec, error_kind, monkeypatch
    ):
        # Feature: generated-power-docs, Property 9: no partial write on any
        # error — any aborting Write_Mode error (unreadable/unparseable source,
        # source invariant violation, missing referenced file, CommonMark
        # failure) leaves POWER.md byte-for-byte unchanged and exits non-zero.
        #
        # Non-CommonMark error kinds disable the markdownlint gate so the run
        # aborts solely on the injected condition; the commonmark_failure kind
        # installs its own failing validator instead.
        if error_kind != "commonmark_failure":
            disable_commonmark(monkeypatch)

        base_dir = Path(tempfile.mkdtemp(prefix="gpd_p9_"))
        try:
            world = materialize_world(spec, base_dir)

            # Inject exactly one aborting error condition. Injectors never touch
            # POWER.md, so the snapshot below captures its pre-run bytes.
            _ERROR_INJECTORS[error_kind](world, monkeypatch)

            before = world.paths.power_md.read_bytes()
            tree_before = _snapshot_tree(base_dir)

            # Write_Mode must abort with a non-zero exit status.
            exit_code = main(_write_argv(world.paths))
            assert exit_code != 0

            # POWER.md is byte-for-byte unchanged: no partial write occurred.
            after = world.paths.power_md.read_bytes()
            assert after == before

            # No partial artifact (e.g. a leftover temp file) was created and no
            # other file was mutated by the aborted run.
            assert _snapshot_tree(base_dir) == tree_before
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)
