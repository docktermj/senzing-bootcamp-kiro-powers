"""Property-based and unit tests for export_results.py.

Uses Hypothesis to verify 12 correctness properties and pytest for 6 unit-test
groups covering CLI parsing, journal handling, HTML structure, and ZIP output.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from export_results import (
    ArtifactDiscovery,
    ArtifactEntry,
    ArtifactManifest,
    EntityStatistics,
    ExportMetrics,
    HTMLRenderer,
    MetricsExtractor,
    ModuleFilter,
    PerformanceMetrics,
    ProgressData,
    QualityScore,
    SummaryGenerator,
    VALID_ARTIFACT_TYPES,
    ZIPAssembler,
    _parse_args,
    main,
)

# ---------------------------------------------------------------------------
# Task 8.1 — Hypothesis strategies for all data types
# ---------------------------------------------------------------------------

_ARTIFACT_TYPES = sorted(VALID_ARTIFACT_TYPES)
_LANGUAGES = ["python", "java", "csharp", "rust", "typescript", None]
_TRACKS = ["core_bootcamp", "advanced_topics", None]


def st_artifact_entry() -> st.SearchStrategy[ArtifactEntry]:
    """Strategy producing random ArtifactEntry instances."""
    return st.builds(
        ArtifactEntry,
        path=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_-/."),
            min_size=3, max_size=60,
        ).filter(lambda p: p.strip() != "" and "/" not in p[:1]),
        artifact_type=st.sampled_from(_ARTIFACT_TYPES),
        module=st.one_of(st.none(), st.integers(min_value=1, max_value=12)),
        file_size=st.integers(min_value=0, max_value=10_000_000),
        description=st.text(min_size=1, max_size=120),
    )


def st_artifact_manifest() -> st.SearchStrategy[ArtifactManifest]:
    """Strategy producing random ArtifactManifest instances."""
    return st.builds(
        ArtifactManifest,
        artifacts=st.lists(st_artifact_entry(), min_size=0, max_size=30),
        scan_timestamp=st.just("2025-01-15T10:30:00+00:00"),
    )


def st_progress_data() -> st.SearchStrategy[ProgressData]:
    """Strategy producing random ProgressData instances."""
    return st.builds(
        ProgressData,
        modules_completed=st.lists(
            st.integers(min_value=1, max_value=12), unique=True, max_size=12,
        ),
        current_module=st.one_of(st.none(), st.integers(min_value=1, max_value=12)),
        language=st.sampled_from(_LANGUAGES),
        data_sources=st.just([]),
        track=st.sampled_from(_TRACKS),
    )


def st_quality_score() -> st.SearchStrategy[QualityScore]:
    """Strategy producing random QualityScore instances."""
    return st.builds(
        QualityScore,
        source_name=st.text(min_size=1, max_size=30),
        overall=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        completeness=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        consistency=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        format_compliance=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        uniqueness=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
    )


def st_performance_metrics() -> st.SearchStrategy[PerformanceMetrics]:
    """Strategy producing random PerformanceMetrics instances."""
    return st.builds(
        PerformanceMetrics,
        loading_throughput_rps=st.one_of(st.none(), st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)),
        query_response_ms=st.one_of(st.none(), st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False)),
        database_type=st.one_of(st.none(), st.sampled_from(["sqlite", "postgresql"])),
    )


def st_entity_statistics() -> st.SearchStrategy[EntityStatistics]:
    """Strategy producing random EntityStatistics instances."""
    return st.builds(
        EntityStatistics,
        total_records=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        total_entities=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        match_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        cross_source_matches=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        duplicate_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
    )


def st_export_metrics() -> st.SearchStrategy[ExportMetrics]:
    """Strategy producing random ExportMetrics instances."""
    return st.builds(
        ExportMetrics,
        quality_scores=st.lists(st_quality_score(), min_size=0, max_size=5),
        performance=st.one_of(st.none(), st_performance_metrics()),
        entity_stats=st.one_of(st.none(), st_entity_statistics()),
    )


def st_module_numbers() -> st.SearchStrategy[list[int]]:
    """Strategy producing lists of integers for module validation testing."""
    return st.lists(st.integers(min_value=-5, max_value=20), max_size=20)



# ===========================================================================
# Task 8.2 — PBT Property 1: Module number validation partitions correctly
# ===========================================================================


class TestProperty1ModuleValidation:
    """Feature: export-results, Property 1: Module number validation partitions correctly

    For any list of integers, ModuleFilter.validate_modules SHALL return a
    (valid, invalid) tuple where every integer in valid is in 1–12, every
    integer in invalid is outside 1–12, and the union equals the original list.

    **Validates: Requirements 1.6, 10.3**
    """

    @given(modules=st_module_numbers())
    @settings(max_examples=10)
    def test_partition_is_correct(self, modules: list[int]):
        """Feature: export-results, Property 1: Module number validation partitions correctly"""
        valid, invalid = ModuleFilter.validate_modules(modules)

        # Every valid is in 1-12
        for v in valid:
            assert 1 <= v <= 12, f"{v} should be in 1-12"

        # Every invalid is outside 1-12
        for i in invalid:
            assert not (1 <= i <= 12), f"{i} should be outside 1-12"

        # Union preserves multiplicity
        assert sorted(valid + invalid) == sorted(modules)


# ===========================================================================
# Task 8.3 — PBT Property 2: Artifact discovery finds matching files
# ===========================================================================


class TestProperty2ArtifactDiscovery:
    """Feature: export-results, Property 2: Artifact discovery finds all matching files

    For any project directory containing files in data/transformed/,
    data/raw/, src/, and docs/, scan() SHALL contain an ArtifactEntry for
    every file matching expected patterns.

    **Validates: Requirements 2.3, 2.5, 2.7**
    """

    @given(
        jsonl_names=st.lists(
            st.from_regex(r"[a-z]{3,10}\.jsonl", fullmatch=True),
            min_size=0, max_size=5, unique=True,
        ),
        raw_names=st.lists(
            st.from_regex(r"[a-z]{3,10}\.csv", fullmatch=True),
            min_size=0, max_size=5, unique=True,
        ),
        py_names=st.lists(
            st.from_regex(r"[a-z]{3,10}\.py", fullmatch=True),
            min_size=0, max_size=5, unique=True,
        ),
        doc_names=st.lists(
            st.from_regex(r"[a-z]{3,10}\.md", fullmatch=True),
            min_size=0, max_size=5, unique=True,
        ),
    )
    @settings(max_examples=10)
    def test_discovery_finds_matching_files(
        self, jsonl_names, raw_names, py_names, doc_names,
    ):
        """Feature: export-results, Property 2: Artifact discovery finds all matching files"""
        tmp_path = Path(tempfile.mkdtemp())
        try:
            # Create project structure
            (tmp_path / "data" / "transformed").mkdir(parents=True, exist_ok=True)
            (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
            (tmp_path / "src").mkdir(parents=True, exist_ok=True)
            (tmp_path / "docs").mkdir(parents=True, exist_ok=True)

            # Write progress so language is known
            (tmp_path / "config").mkdir(parents=True, exist_ok=True)
            (tmp_path / "config" / "bootcamp_progress.json").write_text(
                json.dumps({"language": "python"}), encoding="utf-8",
            )

            for name in jsonl_names:
                (tmp_path / "data" / "transformed" / name).write_text("data", encoding="utf-8")
            for name in raw_names:
                (tmp_path / "data" / "raw" / name).write_text("data", encoding="utf-8")
            for name in py_names:
                (tmp_path / "src" / name).write_text("# code", encoding="utf-8")
            for name in doc_names:
                (tmp_path / "docs" / name).write_text("# doc", encoding="utf-8")

            discovery = ArtifactDiscovery(str(tmp_path))
            manifest = discovery.scan()
            paths = {a.path for a in manifest.artifacts}

            for name in jsonl_names:
                expected = str(Path("data") / "transformed" / name)
                assert expected in paths, f"Missing transformed: {expected}"
            for name in raw_names:
                expected = str(Path("data") / "raw" / name)
                assert expected in paths, f"Missing raw: {expected}"
            for name in py_names:
                expected = str(Path("src") / name)
                assert expected in paths, f"Missing source: {expected}"
            for name in doc_names:
                expected = str(Path("docs") / name)
                assert expected in paths, f"Missing doc: {expected}"
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)


# ===========================================================================
# Task 8.4 — PBT Property 3: Visualization detection is content-based
# ===========================================================================


class TestProperty3VisualizationDetection:
    """Feature: export-results, Property 3: Visualization detection is content-based

    For any HTML file, ArtifactDiscovery SHALL classify it as a visualization
    if and only if its content contains entity graph or dashboard markers.

    **Validates: Requirements 2.4**
    """

    @given(
        has_marker=st.booleans(),
        marker=st.sampled_from(["d3", "force", "graph", "dashboard", "entity", "svg"]),
        filler=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz \n<>"),
            min_size=10, max_size=200,
        ),
    )
    @settings(max_examples=10)
    def test_viz_detection_is_content_based(self, has_marker, marker, filler):
        """Feature: export-results, Property 3: Visualization detection is content-based"""
        tmp_path = Path(tempfile.mkdtemp())
        try:
            # Build HTML content
            if has_marker:
                content = f"<html><body>{filler} {marker} {filler}</body></html>"
            else:
                # Ensure no markers appear in filler
                safe_filler = re.sub(r"\b(d3|force|graph|dashboard|entity|svg)\b", "xxxx", filler, flags=re.IGNORECASE)
                content = f"<html><body>{safe_filler}</body></html>"

            (tmp_path / "test_viz.html").write_text(content, encoding="utf-8")

            discovery = ArtifactDiscovery(str(tmp_path))
            manifest = discovery.scan()
            viz_paths = {a.path for a in manifest.artifacts if a.artifact_type == "visualization"}

            if has_marker:
                assert "test_viz.html" in viz_paths, "File with marker should be a visualization"
            else:
                assert "test_viz.html" not in viz_paths, "File without marker should not be a visualization"
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)


# ===========================================================================
# Task 8.5 — PBT Property 4: Manifest entries have complete metadata
# ===========================================================================


class TestProperty4ManifestMetadata:
    """Feature: export-results, Property 4: Manifest entries have complete metadata

    For any ArtifactManifest, every ArtifactEntry SHALL have a non-empty path,
    a valid artifact_type, a non-negative file_size, and a non-empty description.

    **Validates: Requirements 2.8**
    """

    @given(manifest=st_artifact_manifest())
    @settings(max_examples=10)
    def test_manifest_entries_complete(self, manifest: ArtifactManifest):
        """Feature: export-results, Property 4: Manifest entries have complete metadata"""
        for entry in manifest.artifacts:
            assert entry.path, "path must be non-empty"
            assert entry.artifact_type in VALID_ARTIFACT_TYPES, f"invalid type: {entry.artifact_type}"
            assert entry.file_size >= 0, "file_size must be non-negative"
            assert entry.description, "description must be non-empty"

        # type_counts matches actual counts
        tc = manifest.type_counts()
        for atype in VALID_ARTIFACT_TYPES:
            actual = len([a for a in manifest.artifacts if a.artifact_type == atype])
            assert tc.get(atype, 0) == actual

        # total_size matches sum
        assert manifest.total_size() == sum(a.file_size for a in manifest.artifacts)


# ===========================================================================
# Task 8.6 — PBT Property 5: Module completion table reflects progress state
# ===========================================================================


class TestProperty5ModuleCompletionTable:
    """Feature: export-results, Property 5: Module completion table reflects progress state

    For any ProgressData, the rendered module completion table SHALL contain
    exactly 12 rows, mark completed/in-progress/not-started correctly,
    display progress percentage, and display language if provided.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """

    @given(progress=st_progress_data())
    @settings(max_examples=10)
    def test_module_table_reflects_progress(self, progress: ProgressData):
        """Feature: export-results, Property 5: Module completion table reflects progress state"""
        renderer = HTMLRenderer()
        html = renderer._render_module_table(progress)

        # Exactly 12 <tr> data rows in tbody (exclude header row)
        rows = re.findall(r"<tr><td>.*?</td></tr>", html, re.DOTALL)
        assert len(rows) == 12, f"Expected 12 rows, got {len(rows)}"

        # Each completed module marked
        for m in progress.modules_completed:
            assert "Completed" in html or "✅" in html

        # Current module (if not completed) marked in progress
        if (progress.current_module is not None
                and progress.current_module not in progress.modules_completed):
            assert "In Progress" in html or "🔄" in html

        # Progress percentage
        n = len(progress.modules_completed)
        pct = n * 100 / 12
        assert f"{pct:.0f}%" in html

        # Language displayed if provided
        if progress.language:
            assert progress.language in html


# ===========================================================================
# Task 8.7 — PBT Property 6: Metric sections appear iff data exists
# ===========================================================================


class TestProperty6MetricSections:
    """Feature: export-results, Property 6: Metric sections appear iff data exists

    For any ExportMetrics, the rendered HTML SHALL contain the quality section
    iff quality_scores is non-empty, performance section iff performance is
    not None, and entity stats section iff entity_stats is not None.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """

    @given(
        metrics=st_export_metrics(),
        progress=st_progress_data(),
        manifest=st_artifact_manifest(),
    )
    @settings(max_examples=10)
    def test_metric_sections_conditional(
        self, metrics: ExportMetrics, progress: ProgressData, manifest: ArtifactManifest,
    ):
        """Feature: export-results, Property 6: Metric sections appear iff data exists"""
        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        has_quality = 'id="quality-scores"' in html
        has_perf = 'id="performance"' in html
        has_entity = 'id="entity-stats"' in html

        if metrics.quality_scores:
            assert has_quality, "Quality section should be present"
        else:
            assert not has_quality, "Quality section should be absent"

        if metrics.performance is not None:
            assert has_perf, "Performance section should be present"
        else:
            assert not has_perf, "Performance section should be absent"

        if metrics.entity_stats is not None:
            assert has_entity, "Entity stats section should be present"
        else:
            assert not has_entity, "Entity stats section should be absent"


# ===========================================================================
# Task 8.8 — PBT Property 7: Executive summary contains required info
# ===========================================================================


class TestProperty7ExecutiveSummary:
    """Feature: export-results, Property 7: Executive summary contains required information

    For any ProgressData with a track and completed modules, the executive
    summary SHALL contain the track letter and module count.

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
    """

    @given(
        progress=st_progress_data(),
        metrics=st_export_metrics(),
        manifest=st_artifact_manifest(),
    )
    @settings(max_examples=10)
    def test_executive_summary_content(
        self, progress: ProgressData, metrics: ExportMetrics, manifest: ArtifactManifest,
    ):
        """Feature: export-results, Property 7: Executive summary contains required information"""
        summary = SummaryGenerator.generate(progress, metrics, manifest)

        # Module count always present
        n = len(progress.modules_completed)
        assert str(n) in summary, f"Module count {n} not in summary"

        # Track display name present when set
        if progress.track:
            from export_results import TRACK_DISPLAY_NAMES
            display_name = TRACK_DISPLAY_NAMES.get(progress.track, progress.track)
            assert display_name in summary, f"Track display name {display_name} not in summary"

        # Quality band present when scores exist
        for qs in metrics.quality_scores:
            band_word = {"green": "high", "yellow": "moderate", "red": "low"}.get(qs.band)
            assert band_word in summary.lower() or qs.band in summary.lower()

        # Entity stats present when both total_records and total_entities available
        if (metrics.entity_stats
                and metrics.entity_stats.total_records is not None
                and metrics.entity_stats.total_entities is not None):
            tr = str(metrics.entity_stats.total_records)
            # Check the raw number appears (with or without comma formatting)
            formatted = f"{metrics.entity_stats.total_records:,}"
            plain_summary = summary.replace(",", "").replace("&nbsp;", " ")
            assert tr in plain_summary or formatted in summary

        # Summary appears before module table in full render
        renderer = HTMLRenderer()
        full_html = renderer.render(progress, metrics, manifest, None, None)
        summary_pos = full_html.find('id="executive-summary"')
        table_pos = full_html.find('id="module-completion"')
        assert summary_pos < table_pos, "Summary must appear before module table"


# ===========================================================================
# Task 8.9 — PBT Property 8: HTML report is self-contained
# ===========================================================================


class TestProperty8SelfContainedHTML:
    """Feature: export-results, Property 8: HTML report is self-contained

    For any rendered HTML report, the output SHALL contain a <style> tag and
    SHALL NOT contain external resource references.

    **Validates: Requirements 8.1, 8.2**
    """

    @given(
        progress=st_progress_data(),
        metrics=st_export_metrics(),
        manifest=st_artifact_manifest(),
    )
    @settings(max_examples=10)
    def test_html_is_self_contained(
        self, progress: ProgressData, metrics: ExportMetrics, manifest: ArtifactManifest,
    ):
        """Feature: export-results, Property 8: HTML report is self-contained"""
        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        # Must have inline styles
        assert "<style>" in html, "Missing <style> tag"

        # Must NOT have external references
        assert '<link rel="stylesheet"' not in html, "External stylesheet found"
        assert '<script src=' not in html, "External script found"
        assert not re.search(r'<link[^>]+href=["\']https?://', html), "External link found"


# ===========================================================================
# Task 8.10 — PBT Property 9: Module filter returns correct artifact subset
# ===========================================================================


class TestProperty9ModuleFilter:
    """Feature: export-results, Property 9: Module filter returns correct artifact subset

    For any ArtifactManifest and any subset of module numbers,
    ModuleFilter.filter() SHALL return exactly the artifacts whose module is
    in the set OR whose module is None.

    **Validates: Requirements 10.1, 10.2**
    """

    @given(
        manifest=st_artifact_manifest(),
        modules=st.one_of(
            st.none(),
            st.lists(st.integers(min_value=1, max_value=12), unique=True, max_size=12),
        ),
    )
    @settings(max_examples=10)
    def test_filter_returns_correct_subset(
        self, manifest: ArtifactManifest, modules: list[int] | None,
    ):
        """Feature: export-results, Property 9: Module filter returns correct artifact subset"""
        filtered = ModuleFilter.filter(manifest, modules)

        if modules is None:
            # Full manifest returned
            assert len(filtered.artifacts) == len(manifest.artifacts)
        else:
            keep = set(modules)
            for art in filtered.artifacts:
                assert art.module is None or art.module in keep, \
                    f"Artifact module {art.module} not in {keep} and not None"
            # All matching artifacts are included
            expected = [a for a in manifest.artifacts if a.module is None or a.module in keep]
            assert len(filtered.artifacts) == len(expected)


# ===========================================================================
# Task 8.11 — PBT Property 10: ZIP archive contains correct structure
# ===========================================================================


class TestProperty10ZIPStructure:
    """Feature: export-results, Property 10: ZIP archive contains correct structure

    For any HTML content and ArtifactManifest, the ZIP archive SHALL contain
    bootcamp_report.html, manifest.json, and artifacts in correct subdirs.

    **Validates: Requirements 9.1, 9.2, 9.3, 6.2**
    """

    @given(
        html_content=st.text(min_size=10, max_size=500),
        manifest=st_artifact_manifest(),
    )
    @settings(max_examples=10)
    def test_zip_structure_correct(self, html_content: str, manifest: ArtifactManifest):
        """Feature: export-results, Property 10: ZIP archive contains correct structure"""
        assembler = ZIPAssembler()

        # Build a file_reader that returns bytes for any path
        def file_reader(path: str) -> bytes:
            return b"file content for " + path.encode()

        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "test.zip")
            size = assembler.assemble(html_content, manifest, out_path, file_reader)

            assert size > 0
            assert os.path.isfile(out_path)

            with zipfile.ZipFile(out_path, "r") as zf:
                names = set(zf.namelist())

                # HTML report at root
                assert "bootcamp_report.html" in names
                assert zf.read("bootcamp_report.html").decode("utf-8") == html_content

                # manifest.json present and valid
                assert "manifest.json" in names
                mdata = json.loads(zf.read("manifest.json"))
                assert "generated_at" in mdata
                assert "version" in mdata
                assert "artifact_count" in mdata
                assert "artifacts" in mdata

                # Each non-excluded artifact in correct subdir
                for art in manifest.artifacts:
                    if ZIPAssembler.should_exclude(art.path):
                        continue
                    dest_dir = ZIPAssembler.TYPE_TO_DIR.get(art.artifact_type, "artifacts/other")
                    expected_name = dest_dir + "/" + Path(art.path).name
                    assert expected_name in names, f"Missing {expected_name} in ZIP"


# ===========================================================================
# Task 8.12 — PBT Property 11: ZIP exclusion patterns filter correctly
# ===========================================================================


class TestProperty11ZIPExclusion:
    """Feature: export-results, Property 11: ZIP exclusion patterns filter correctly

    For any file path, should_exclude() SHALL return True iff the path
    contains a segment matching an exclusion pattern.

    **Validates: Requirements 9.4**
    """

    @given(
        path_segment=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_-."),
            min_size=1, max_size=30,
        ),
    )
    @settings(max_examples=10)
    def test_exclusion_non_matching(self, path_segment: str):
        """Feature: export-results, Property 11: ZIP exclusion patterns filter correctly"""
        # Ensure the segment doesn't accidentally match exclusion patterns
        assume("__pycache__" not in path_segment)
        assume(".pyc" not in path_segment)
        assume(".env" not in path_segment)
        assume(".git" not in path_segment)
        assume("node_modules" not in path_segment)
        assume("database" not in path_segment)

        path = f"src/{path_segment}/file.txt"
        assert not ZIPAssembler.should_exclude(path), f"Should not exclude: {path}"

    @given(
        pattern=st.sampled_from([
            "__pycache__", "cache.pyc", ".env", ".git", "node_modules", "database",
        ]),
    )
    @settings(max_examples=10)
    def test_exclusion_matching(self, pattern: str):
        """Feature: export-results, Property 11: ZIP exclusion patterns filter correctly"""
        path = f"project/{pattern}/somefile.txt"
        assert ZIPAssembler.should_exclude(path), f"Should exclude: {path}"


# ===========================================================================
# Task 8.13 — PBT Property 12: Graceful degradation on read errors
# ===========================================================================


class TestProperty12GracefulDegradation:
    """Feature: export-results, Property 12: Graceful degradation on read errors

    For any ArtifactManifest where a subset of artifacts raise IOError when
    read, the ZIP output SHALL still contain all successfully-read artifacts.

    **Validates: Requirements 2.7, 12.6**
    """

    @given(
        manifest=st_artifact_manifest(),
        error_indices=st.lists(st.integers(min_value=0, max_value=29), unique=True, max_size=10),
    )
    @settings(max_examples=10)
    def test_graceful_degradation(self, manifest: ArtifactManifest, error_indices: list[int]):
        """Feature: export-results, Property 12: Graceful degradation on read errors"""
        error_set = {i for i in error_indices if i < len(manifest.artifacts)}
        # Build set of paths that should error
        error_paths = {manifest.artifacts[i].path for i in error_set}

        def file_reader(path: str) -> bytes:
            if path in error_paths:
                raise IOError(f"Simulated read error for {path}")
            return b"content"

        assembler = ZIPAssembler()
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "test.zip")
            assembler.assemble("<html></html>", manifest, out_path, file_reader)

            with zipfile.ZipFile(out_path, "r") as zf:
                names = set(zf.namelist())
                # bootcamp_report.html and manifest.json always present
                assert "bootcamp_report.html" in names
                assert "manifest.json" in names

                # Compute expected unique ZIP entry names for non-excluded,
                # non-errored artifacts (ZIP deduplicates by arc_name)
                expected_names: set[str] = set()
                for art in manifest.artifacts:
                    if ZIPAssembler.should_exclude(art.path):
                        continue
                    if art.path in error_paths:
                        continue
                    dest_dir = ZIPAssembler.TYPE_TO_DIR.get(art.artifact_type, "artifacts/other")
                    arc_name = dest_dir + "/" + Path(art.path).name
                    expected_names.add(arc_name)

                # Artifact files in ZIP (excluding report + manifest)
                artifact_files = names - {"bootcamp_report.html", "manifest.json"}
                assert artifact_files == expected_names


# ===========================================================================
# Task 9.1 — Unit test: CLI argument parsing
# ===========================================================================


class TestCLIArgumentParsing:
    """Unit tests for CLI argument parsing.

    **Validates: Requirements 1.5, 1.7**
    """

    def test_default_format_is_html(self):
        args = _parse_args([])
        assert args.format == "html"

    def test_format_html(self):
        args = _parse_args(["--format", "html"])
        assert args.format == "html"

    def test_format_zip(self):
        args = _parse_args(["--format", "zip"])
        assert args.format == "zip"

    def test_invalid_format_raises(self):
        with pytest.raises(SystemExit):
            _parse_args(["--format", "pdf"])

    def test_output_path(self):
        args = _parse_args(["--output", "/tmp/report.html"])
        assert args.output == "/tmp/report.html"

    def test_modules_argument(self):
        args = _parse_args(["--modules", "1,2,3"])
        assert args.modules == "1,2,3"

    def test_default_output_is_none(self):
        args = _parse_args([])
        assert args.output is None

    def test_default_modules_is_none(self):
        args = _parse_args([])
        assert args.modules is None


# ===========================================================================
# Task 9.2 — Unit test: Journal structure preservation / absent omission
# ===========================================================================


class TestJournalHandling:
    """Unit tests for journal rendering and absence handling.

    **Validates: Requirements 5.2, 5.3**
    """

    def test_journal_preserves_headings(self):
        """Journal with multi-module structure preserves headings."""
        journal_html = "<h2>Module 1</h2><p>Completed setup</p><h2>Module 2</h2><p>Loaded data</p>"
        progress = ProgressData(modules_completed=[1, 2], track="core_bootcamp")
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, journal_html, None)

        assert 'id="journal"' in html
        assert "Module 1" in html
        assert "Module 2" in html
        assert "Completed setup" in html
        assert "Loaded data" in html

    def test_journal_absent_omits_section(self):
        """When journal is None, the journal section is omitted."""
        progress = ProgressData(modules_completed=[1], track="core_bootcamp")
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        assert 'id="journal"' not in html


# ===========================================================================
# Task 9.3 — Unit test: No visualizations omits section; semantic HTML
# ===========================================================================


class TestVisualizationsAndSemanticHTML:
    """Unit tests for visualization section and semantic HTML elements.

    **Validates: Requirements 6.3, 8.3**
    """

    def test_no_visualizations_omits_section(self):
        """When no visualization artifacts exist, the section is omitted."""
        progress = ProgressData(modules_completed=[1], track="core_bootcamp")
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        assert 'id="visualizations"' not in html

    def test_semantic_html_elements_present(self):
        """Report uses semantic HTML elements: header, main, section, table, nav."""
        progress = ProgressData(modules_completed=[1, 2, 3], track="core_bootcamp")
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        assert "<header>" in html
        assert "<main>" in html
        assert "<section" in html
        assert "<table>" in html
        assert "<nav>" in html


# ===========================================================================
# Task 9.4 — Unit test: TOC anchor links; footer timestamp and version
# ===========================================================================


class TestTOCAndFooter:
    """Unit tests for table of contents and footer.

    **Validates: Requirements 8.4, 8.5**
    """

    def test_toc_contains_anchor_links(self):
        """TOC contains anchor links for each section."""
        progress = ProgressData(modules_completed=[1], track="core_bootcamp")
        metrics = ExportMetrics(
            quality_scores=[QualityScore(source_name="test", overall=85.0)],
        )
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        assert 'href="#executive-summary"' in html
        assert 'href="#module-completion"' in html
        assert 'href="#quality-scores"' in html

    def test_footer_contains_timestamp_and_version(self):
        """Footer contains generation timestamp and script version."""
        progress = ProgressData(modules_completed=[], track=None)
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(artifacts=[], scan_timestamp="2025-01-15T10:00:00Z")

        renderer = HTMLRenderer()
        html = renderer.render(progress, metrics, manifest, None, None)

        assert "<footer>" in html
        assert "Generated on" in html
        assert HTMLRenderer.VERSION in html


# ===========================================================================
# Task 9.5 — Unit test: ZIP reports path/size; no --modules includes all
# ===========================================================================


class TestZIPReportAndModuleDefault:
    """Unit tests for ZIP output reporting and default module inclusion.

    **Validates: Requirements 9.5, 10.4**
    """

    def test_zip_reports_file_path_and_size(self):
        """ZIP creation returns a positive size and creates the file."""
        manifest = ArtifactManifest(
            artifacts=[
                ArtifactEntry(
                    path="src/main.py", artifact_type="source_code",
                    module=3, file_size=100, description="Main script",
                ),
            ],
            scan_timestamp="2025-01-15T10:00:00Z",
        )
        assembler = ZIPAssembler()

        def file_reader(path: str) -> bytes:
            return b"print('hello')"

        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "report.zip")
            size = assembler.assemble("<html></html>", manifest, out_path, file_reader)

            assert size > 0
            assert os.path.isfile(out_path)
            assert os.path.getsize(out_path) == size

    def test_no_modules_includes_all_artifacts(self):
        """When modules is None, filter returns all artifacts."""
        arts = [
            ArtifactEntry(path="a.py", artifact_type="source_code", module=1, file_size=10, description="a"),
            ArtifactEntry(path="b.py", artifact_type="source_code", module=5, file_size=20, description="b"),
            ArtifactEntry(path="c.md", artifact_type="journal", module=None, file_size=30, description="c"),
        ]
        manifest = ArtifactManifest(artifacts=arts, scan_timestamp="2025-01-15T10:00:00Z")
        filtered = ModuleFilter.filter(manifest, None)

        assert len(filtered.artifacts) == 3


# ===========================================================================
# Task 9.6 — Unit test: Missing progress warning; empty project exits 1;
#             output dir auto-created
# ===========================================================================


class TestErrorHandlingAndEdgeCases:
    """Unit tests for error handling and edge cases.

    **Validates: Requirements 10.5, 12.3, 12.4, 12.5**
    """

    def test_missing_progress_warning(self, capsys):
        """Missing progress file prints a warning and returns minimal ProgressData."""
        with tempfile.TemporaryDirectory() as td:
            # No config/bootcamp_progress.json
            from export_results import _load_progress
            progress = _load_progress(Path(td))

            assert progress.modules_completed == []
            captured = capsys.readouterr()
            assert "Warning" in captured.err or "warning" in captured.err.lower()

    def test_empty_project_exits_1(self):
        """An empty project with no artifacts exits with code 1."""
        with tempfile.TemporaryDirectory() as td:
            # Create a minimal scripts dir so __file__ resolution works
            scripts_dir = Path(td) / "scripts"
            scripts_dir.mkdir()
            fake_script = scripts_dir / "export_results.py"
            fake_script.write_text("", encoding="utf-8")

            with mock.patch("export_results.__file__", str(fake_script)):
                exit_code = main([])

            assert exit_code == 1

    def test_output_dir_auto_created(self):
        """Output directory is created automatically if it doesn't exist."""
        manifest = ArtifactManifest(
            artifacts=[
                ArtifactEntry(
                    path="src/main.py", artifact_type="source_code",
                    module=3, file_size=50, description="Script",
                ),
            ],
            scan_timestamp="2025-01-15T10:00:00Z",
        )
        assembler = ZIPAssembler()

        def file_reader(path: str) -> bytes:
            return b"content"

        with tempfile.TemporaryDirectory() as td:
            nested = os.path.join(td, "deep", "nested", "dir", "report.zip")
            assembler.assemble("<html></html>", manifest, nested, file_reader)

            assert os.path.isfile(nested)
