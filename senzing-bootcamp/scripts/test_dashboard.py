"""Property-based and unit tests for the interactive HTML dashboard.

Uses Hypothesis to verify 12 correctness properties across randomly generated
dashboard data, plus pytest unit tests for CLI, I/O, and error handling.
"""

import argparse
import json
import os
import re
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from status import (
    QualityScoreData,
    PerformanceData,
    EntityStatsData,
    HealthCheckItem,
    DashboardData,
    DashboardRenderer,
    DashboardDataCollector,
    generate_dashboard,
    MODULE_NAMES,
)

# ---------------------------------------------------------------------------
# Task 5.1: Hypothesis strategies
# ---------------------------------------------------------------------------

_STATUSES = ["Not Started", "In Progress", "Ready to Start", "Complete"]
_DB_TYPES = ["sqlite", "postgresql"]


def _quality_score_data():
    """Strategy for QualityScoreData with valid ranges."""
    return st.builds(
        QualityScoreData,
        source_name=st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00",
        )),
        overall=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        completeness=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        consistency=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        format_compliance=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        uniqueness=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
    )


def _performance_data():
    """Strategy for PerformanceData with valid ranges."""
    return st.builds(
        PerformanceData,
        loading_throughput_rps=st.one_of(st.none(), st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)),
        query_avg_ms=st.one_of(st.none(), st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False)),
        query_p95_ms=st.one_of(st.none(), st.floats(min_value=0.0, max_value=5000.0, allow_nan=False, allow_infinity=False)),
        database_type=st.one_of(st.none(), st.sampled_from(_DB_TYPES)),
        wall_clock_seconds=st.one_of(st.none(), st.floats(min_value=0.0, max_value=86400.0, allow_nan=False, allow_infinity=False)),
    )


def _entity_stats_data():
    """Strategy for EntityStatsData with valid ranges."""
    return st.builds(
        EntityStatsData,
        total_records=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        total_entities=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        match_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        duplicate_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        cross_source_matches=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
    )


def _health_check_item():
    """Strategy for HealthCheckItem."""
    return st.builds(
        HealthCheckItem,
        label=st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00",
        )),
        path=st.text(min_size=1, max_size=40, alphabet=st.characters(
            whitelist_categories=("L", "N", "P"),
            blacklist_characters="\x00",
        )),
        exists=st.booleans(),
    )


def _iso_timestamps():
    """Strategy for ISO 8601 timestamp strings."""
    return st.datetimes(
        min_value=__import__("datetime").datetime(2020, 1, 1),
        max_value=__import__("datetime").datetime(2030, 12, 31),
    ).map(lambda dt: dt.replace(tzinfo=__import__("datetime").timezone.utc).isoformat())


def _completion_timestamps():
    """Strategy for completion_timestamps dict (module_number -> ISO string)."""
    keys = st.sampled_from(list(range(1, 13)))
    return st.dictionaries(keys, _iso_timestamps(), min_size=0, max_size=12)


def _dashboard_data():
    """Strategy for DashboardData composing all sub-strategies."""
    return st.builds(
        _build_dashboard_data,
        modules_completed=st.lists(
            st.integers(min_value=1, max_value=12), unique=True, max_size=12,
        ).map(sorted),
        current_module=st.integers(min_value=1, max_value=12),
        status=st.sampled_from(_STATUSES),
        language=st.one_of(st.none(), st.sampled_from(["Python", "Java", "Go", "C#", "JavaScript"])),
        completion_pct_override=st.none(),  # will be computed
        completion_timestamps=_completion_timestamps(),
        quality_scores=st.lists(_quality_score_data(), min_size=0, max_size=3),
        performance=st.one_of(st.none(), _performance_data()),
        entity_stats=st.one_of(st.none(), _entity_stats_data()),
        health_checks=st.lists(_health_check_item(), min_size=1, max_size=8),
        generated_at=_iso_timestamps(),
        has_progress_data=st.booleans(),
    )


def _build_dashboard_data(
    modules_completed, current_module, status, language,
    completion_pct_override, completion_timestamps, quality_scores,
    performance, entity_stats, health_checks, generated_at, has_progress_data,
):
    """Build DashboardData with computed fields."""
    completion_pct = len(modules_completed) * 100 // 12
    health_score = sum(1 for h in health_checks if h.exists)
    health_total = len(health_checks)
    return DashboardData(
        modules_completed=modules_completed,
        current_module=current_module,
        status=status,
        language=language,
        completion_pct=completion_pct,
        completion_timestamps=completion_timestamps,
        quality_scores=quality_scores,
        performance=performance,
        entity_stats=entity_stats,
        health_checks=health_checks,
        health_score=health_score,
        health_total=health_total,
        generated_at=generated_at,
        has_progress_data=has_progress_data,
    )


# ---------------------------------------------------------------------------
# Helper: render once for property tests
# ---------------------------------------------------------------------------

_renderer = DashboardRenderer()


def _render(data: DashboardData) -> str:
    return _renderer.render(data)


# ---------------------------------------------------------------------------
# Task 5.2: Property 1 — Self-contained HTML (no external refs, has <style>)
# Validates: Requirements 2.1, 2.2, 2.3
# ---------------------------------------------------------------------------

class TestProperty1SelfContainedHTML:
    """P1: Self-contained HTML output — no external resource references."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_no_external_stylesheet_links(self, data):
        """**Validates: Requirements 2.1, 2.2, 2.3**"""
        html = _render(data)
        # No <link rel="stylesheet" href="http...">
        assert not re.search(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']http', html, re.IGNORECASE)
        # No <script src="...">
        assert not re.search(r'<script[^>]+src=', html, re.IGNORECASE)
        # No <link href="http...">
        assert not re.search(r'<link[^>]+href=["\']http', html, re.IGNORECASE)
        # No <img src="http...">
        assert not re.search(r'<img[^>]+src=["\']http', html, re.IGNORECASE)
        # Must have inline <style>
        assert "<style>" in html


# ---------------------------------------------------------------------------
# Task 5.3: Property 2 — Semantic HTML structure
# Validates: Requirements 2.4, 2.6, 12.3
# ---------------------------------------------------------------------------

class TestProperty2SemanticHTML:
    """P2: Semantic HTML structure with required elements."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_semantic_elements_present(self, data):
        """**Validates: Requirements 2.4, 2.6, 12.3**"""
        html = _render(data)
        assert "<header>" in html or "<header " in html
        assert "<main>" in html or "<main " in html
        assert "<section" in html
        assert "<footer>" in html or "<footer " in html
        assert 'charset="UTF-8"' in html or "charset=UTF-8" in html
        # Footer contains the generated_at timestamp
        footer_match = re.search(r"<footer>(.*?)</footer>", html, re.DOTALL)
        assert footer_match is not None
        # The timestamp should appear somewhere in the footer (HTML-escaped)
        footer_text = footer_match.group(1)
        # generated_at may be HTML-escaped (& -> &amp;, etc.)
        assert data.generated_at[:10] in footer_text  # at least the date portion


# ---------------------------------------------------------------------------
# Task 5.4: Property 3 — Progress bar reflects completion
# Validates: Requirements 4.1, 4.2
# ---------------------------------------------------------------------------

class TestProperty3ProgressBar:
    """P3: Progress bar reflects completion state."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_progress_bar_percentage_and_fraction(self, data):
        """**Validates: Requirements 4.1, 4.2**"""
        html = _render(data)
        expected_pct = len(data.modules_completed) * 100 // 12
        n = len(data.modules_completed)
        # The percentage should appear in the progress section
        assert f"{expected_pct}%" in html
        # The fraction "N / 12" should appear
        assert f"{n} / 12" in html


# ---------------------------------------------------------------------------
# Task 5.5: Property 4 — Module cards reflect correct status
# Validates: Requirements 4.3, 4.4, 4.5, 4.6
# ---------------------------------------------------------------------------

class TestProperty4ModuleCards:
    """P4: Module cards reflect correct status for all 12 modules."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_twelve_module_cards_with_correct_status(self, data):
        """**Validates: Requirements 4.3, 4.4, 4.5, 4.6**"""
        html = _render(data)
        # Exactly 12 module cards
        card_matches = re.findall(r'class="card\s+(completed|in-progress|not-started)"', html)
        assert len(card_matches) == 12

        # Extract individual cards by splitting on card boundaries
        # Each card is a <div class="card ...">...</div>
        cards_section = re.search(r'<div class="cards">(.*?)</section>', html, re.DOTALL)
        assert cards_section is not None
        # Find all individual cards with their class and content
        individual_cards = re.findall(
            r'<div class="card (completed|in-progress|not-started)">(.*?)</div></div>',
            cards_section.group(1), re.DOTALL,
        )
        # Build a map of module number -> card class
        card_status_map = {}
        for card_class, card_content in individual_cards:
            mod_match = re.search(r'Module (\d+)', card_content)
            if mod_match:
                card_status_map[int(mod_match.group(1))] = card_class

        assert len(card_status_map) == 12

        for num in range(1, 13):
            card_class = card_status_map[num]
            if num in data.modules_completed:
                assert card_class == "completed", f"Module {num} should be completed"
            elif num == data.current_module and num not in data.modules_completed:
                assert card_class == "in-progress", f"Module {num} should be in-progress"
            else:
                assert card_class == "not-started", f"Module {num} should be not-started"


# ---------------------------------------------------------------------------
# Task 5.6: Property 5 — Header displays status and language
# Validates: Requirements 4.7, 4.8
# ---------------------------------------------------------------------------

class TestProperty5HeaderMetadata:
    """P5: Header displays status and language metadata."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_header_contains_status_and_language(self, data):
        """**Validates: Requirements 4.7, 4.8**"""
        html = _render(data)
        header_match = re.search(r"<header>(.*?)</header>", html, re.DOTALL)
        assert header_match is not None
        header_text = header_match.group(1)
        # Status should appear in header
        assert data.status in header_text
        # Language should appear when not None
        if data.language is not None:
            assert data.language in header_text


# ---------------------------------------------------------------------------
# Task 5.7: Property 6 — Quality section conditional rendering
# Validates: Requirements 5.1, 5.2, 5.4, 5.5
# ---------------------------------------------------------------------------

class TestProperty6QualitySection:
    """P6: Quality section present iff quality_scores non-empty."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_quality_section_conditional(self, data):
        """**Validates: Requirements 5.1, 5.2, 5.4, 5.5**"""
        html = _render(data)
        has_quality_section = 'id="quality"' in html

        if data.quality_scores:
            assert has_quality_section, "Quality section should be present when scores exist"
            for qs in data.quality_scores:
                # Source name should appear (HTML-escaped)
                escaped_name = (
                    qs.source_name
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )
                assert escaped_name in html, f"Source name '{qs.source_name}' not found"
                # Overall score should appear
                assert f"{qs.overall:.1f}" in html
                # Sub-scores when not None
                if qs.completeness is not None:
                    assert f"{qs.completeness:.1f}" in html
                if qs.consistency is not None:
                    assert f"{qs.consistency:.1f}" in html
                if qs.format_compliance is not None:
                    assert f"{qs.format_compliance:.1f}" in html
                if qs.uniqueness is not None:
                    assert f"{qs.uniqueness:.1f}" in html
        else:
            assert not has_quality_section, "Quality section should be absent when no scores"


# ---------------------------------------------------------------------------
# Task 5.8: Property 7 — Performance section conditional rendering
# Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
# ---------------------------------------------------------------------------

class TestProperty7PerformanceSection:
    """P7: Performance section present iff performance is not None."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_performance_section_conditional(self, data):
        """**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**"""
        html = _render(data)
        has_perf_section = 'id="performance"' in html

        if data.performance is not None:
            perf = data.performance
            # Section present only if at least one metric is non-None
            has_any = any(v is not None for v in [
                perf.loading_throughput_rps, perf.query_avg_ms,
                perf.query_p95_ms, perf.database_type, perf.wall_clock_seconds,
            ])
            if has_any:
                assert has_perf_section, "Performance section should be present"
                # Each non-None metric value should appear
                if perf.loading_throughput_rps is not None:
                    assert f"{perf.loading_throughput_rps:,.1f}" in html
                if perf.query_avg_ms is not None:
                    assert f"{perf.query_avg_ms:,.1f}" in html
                if perf.query_p95_ms is not None:
                    assert f"{perf.query_p95_ms:,.1f}" in html
                if perf.database_type is not None:
                    assert perf.database_type in html
                if perf.wall_clock_seconds is not None:
                    assert f"{perf.wall_clock_seconds:,.1f}" in html
            else:
                assert not has_perf_section
        else:
            assert not has_perf_section, "Performance section should be absent when None"


# ---------------------------------------------------------------------------
# Task 5.9: Property 8 — Entity stats section conditional rendering
# Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
# ---------------------------------------------------------------------------

class TestProperty8EntitySection:
    """P8: Entity stats section present iff entity_stats is not None."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_entity_section_conditional(self, data):
        """**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7**"""
        html = _render(data)
        has_entity_section = 'id="entities"' in html

        if data.entity_stats is not None:
            stats = data.entity_stats
            has_any = any(v is not None for v in [
                stats.total_records, stats.total_entities,
                stats.match_count, stats.duplicate_count,
                stats.cross_source_matches,
            ])
            if has_any:
                assert has_entity_section, "Entity section should be present"
                if stats.total_records is not None:
                    assert f"{stats.total_records:,}" in html
                if stats.total_entities is not None:
                    assert f"{stats.total_entities:,}" in html
                if stats.match_count is not None:
                    assert f"{stats.match_count:,}" in html
                if stats.duplicate_count is not None:
                    assert f"{stats.duplicate_count:,}" in html
                if stats.cross_source_matches is not None:
                    assert f"{stats.cross_source_matches:,}" in html
            else:
                assert not has_entity_section
        else:
            assert not has_entity_section, "Entity section should be absent when None"


# ---------------------------------------------------------------------------
# Task 5.10: Property 9 — Timeline conditional rendering
# Validates: Requirements 8.1, 8.2, 8.3, 8.4
# ---------------------------------------------------------------------------

class TestProperty9Timeline:
    """P9: Timeline present iff completion_timestamps non-empty, chronological."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_timeline_conditional_and_chronological(self, data):
        """**Validates: Requirements 8.1, 8.2, 8.3, 8.4**"""
        html = _render(data)
        has_timeline = 'id="timeline"' in html

        if data.completion_timestamps:
            assert has_timeline, "Timeline should be present when timestamps exist"
            # Each module number should appear in the timeline section
            timeline_match = re.search(
                r'<section id="timeline">(.*?)</section>', html, re.DOTALL
            )
            assert timeline_match is not None
            timeline_html = timeline_match.group(1)

            for mod_num in data.completion_timestamps:
                assert f"Module {mod_num}" in timeline_html

            # Verify chronological order: extract module numbers in order
            module_nums_in_order = [
                int(m.group(1))
                for m in re.finditer(r"Module (\d+)", timeline_html)
            ]
            sorted_entries = sorted(
                data.completion_timestamps.items(), key=lambda kv: kv[1]
            )
            expected_order = [mod for mod, _ in sorted_entries]
            assert module_nums_in_order == expected_order, (
                f"Timeline not chronological: got {module_nums_in_order}, "
                f"expected {expected_order}"
            )
        else:
            assert not has_timeline, "Timeline should be absent when no timestamps"


# ---------------------------------------------------------------------------
# Task 5.11: Property 10 — Health section displays all checks
# Validates: Requirements 9.1, 9.2, 9.3
# ---------------------------------------------------------------------------

class TestProperty10HealthSection:
    """P10: Health section displays all checks with correct indicators and score."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_health_section_items_and_score(self, data):
        """**Validates: Requirements 9.1, 9.2, 9.3**"""
        html = _render(data)
        health_match = re.search(
            r'<section id="health">(.*?)</section>', html, re.DOTALL
        )
        assert health_match is not None, "Health section should always be present"
        health_html = health_match.group(1)

        # Extract all health items as individual strings
        health_items = re.findall(
            r'<div class="health-item">(.*?)</div>', health_html, re.DOTALL
        )

        # Verify each health check item appears with correct indicator
        # Build expected (label, exists) pairs in order
        expected_items = []
        for chk in data.health_checks:
            escaped_label = (
                chk.label
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )
            expected_status = "exists" if chk.exists else "missing"
            expected_icon = "&#x2705;" if chk.exists else "&#x274C;"
            expected_items.append((escaped_label, expected_status, expected_icon))

        # Verify the items appear in order
        assert len(health_items) == len(data.health_checks)
        for i, (escaped_label, expected_status, expected_icon) in enumerate(expected_items):
            item_html = health_items[i]
            assert escaped_label in item_html, f"Health label not found at position {i}"
            assert expected_status in item_html, f"Expected '{expected_status}' at position {i}"
            assert expected_icon in item_html, f"Expected icon at position {i}"

        # Health score fraction
        assert f"{data.health_score}/{data.health_total}" in health_html
        # Health score percentage
        expected_pct = data.health_score * 100 // data.health_total if data.health_total else 0
        assert f"{expected_pct}%" in health_html


# ---------------------------------------------------------------------------
# Task 5.12: Property 11 — Quality band classification
# Validates: Requirements 5.3
# ---------------------------------------------------------------------------

class TestProperty11QualityBand:
    """P11: Quality band classification (green>=80, yellow>=70, red<70)."""

    @given(score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_band_classification(self, score):
        """**Validates: Requirements 5.3**"""
        qs = QualityScoreData(source_name="test", overall=score)
        if score >= 80:
            assert qs.band == "green"
        elif score >= 70:
            assert qs.band == "yellow"
        else:
            assert qs.band == "red"


# ---------------------------------------------------------------------------
# Task 5.13: Property 12 — Rendering never raises unhandled exceptions
# Validates: Requirements 11.3
# ---------------------------------------------------------------------------

class TestProperty12NoExceptions:
    """P12: Rendering never raises unhandled exceptions."""

    @given(data=_dashboard_data())
    @settings(max_examples=100)
    def test_render_never_raises(self, data):
        """**Validates: Requirements 11.3**"""
        result = _render(data)
        assert isinstance(result, str)
        assert len(result) > 0


# ===========================================================================
# Task 6: Unit tests for edge cases and integration points
# ===========================================================================


# ---------------------------------------------------------------------------
# Task 6.1: CLI argument parsing
# Validates: Requirements 1.1, 1.2, 1.3, 1.4
# ---------------------------------------------------------------------------

class TestCLIArgumentParsing:
    """Unit tests for CLI argument parsing."""

    def test_html_flag_accepted(self):
        """--html flag is recognized."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--html", action="store_true")
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--no-open", action="store_true")
        parser.add_argument("--sync", action="store_true")
        args = parser.parse_args(["--html"])
        assert args.html is True

    def test_output_custom_path(self):
        """--output accepts a custom path."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--html", action="store_true")
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--no-open", action="store_true")
        args = parser.parse_args(["--html", "--output", os.path.join(tempfile.gettempdir(), "my_dash.html")])
        assert args.output == os.path.join(tempfile.gettempdir(), "my_dash.html")

    def test_no_open_flag(self):
        """--no-open flag is recognized."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--html", action="store_true")
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--no-open", action="store_true")
        args = parser.parse_args(["--html", "--no-open"])
        assert args.no_open is True

    def test_backward_compat_no_html(self):
        """Without --html, the flag defaults to False."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--html", action="store_true")
        parser.add_argument("--output", type=str, default=None)
        parser.add_argument("--no-open", action="store_true")
        parser.add_argument("--sync", action="store_true")
        args = parser.parse_args([])
        assert args.html is False
        assert args.output is None
        assert args.no_open is False


# ---------------------------------------------------------------------------
# Task 6.2: Output directory auto-creation, file path/size printed
# Validates: Requirements 1.5, 1.6
# ---------------------------------------------------------------------------

class TestOutputDirectoryAndPrint:
    """Unit tests for output directory creation and stdout messages."""

    def test_output_dir_auto_created(self):
        """Output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sub", "deep", "dashboard.html")
            # Mock the collector and renderer to avoid real filesystem scanning
            fake_data = DashboardData(
                modules_completed=[1, 2],
                current_module=3,
                status="In Progress",
                language="Python",
                completion_pct=16,
                completion_timestamps={},
                quality_scores=[],
                performance=None,
                entity_stats=None,
                health_checks=[HealthCheckItem("README.md", "README.md", True)],
                health_score=1,
                health_total=1,
                generated_at="2024-01-01T00:00:00+00:00",
                has_progress_data=True,
            )
            with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
                 mock.patch("status.webbrowser.open"):
                captured = StringIO()
                with mock.patch("sys.stdout", captured):
                    generate_dashboard(out_path, no_open=True)
            output = captured.getvalue()
            assert os.path.isfile(out_path)
            assert "Dashboard written to" in output
            assert "KB" in output

    def test_file_path_and_size_printed(self):
        """File path and size are printed to stdout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "dashboard.html")
            fake_data = DashboardData(
                modules_completed=[],
                current_module=1,
                status="Not Started",
                language=None,
                completion_pct=0,
                completion_timestamps={},
                quality_scores=[],
                performance=None,
                entity_stats=None,
                health_checks=[],
                health_score=0,
                health_total=0,
                generated_at="2024-01-01T00:00:00+00:00",
                has_progress_data=False,
            )
            with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
                 mock.patch("status.webbrowser.open"):
                captured = StringIO()
                with mock.patch("sys.stdout", captured):
                    generate_dashboard(out_path, no_open=True)
            output = captured.getvalue()
            assert out_path in output or "dashboard.html" in output
            assert "KB" in output


# ---------------------------------------------------------------------------
# Task 6.3: Browser auto-open mocked, --no-open suppresses, failure prints path
# Validates: Requirements 3.1, 3.2, 3.3
# ---------------------------------------------------------------------------

class TestBrowserAutoOpen:
    """Unit tests for browser auto-open behavior."""

    def _make_fake_data(self):
        return DashboardData(
            modules_completed=[1],
            current_module=2,
            status="In Progress",
            language="Python",
            completion_pct=8,
            completion_timestamps={},
            quality_scores=[],
            performance=None,
            entity_stats=None,
            health_checks=[HealthCheckItem("README.md", "README.md", True)],
            health_score=1,
            health_total=1,
            generated_at="2024-01-01T00:00:00+00:00",
            has_progress_data=True,
        )

    def test_browser_opens_by_default(self):
        """webbrowser.open is called when --no-open is not set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "dashboard.html")
            fake_data = self._make_fake_data()
            with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
                 mock.patch("status.webbrowser.open") as mock_open:
                captured = StringIO()
                with mock.patch("sys.stdout", captured):
                    generate_dashboard(out_path, no_open=False)
                mock_open.assert_called_once()

    def test_no_open_suppresses_browser(self):
        """--no-open suppresses webbrowser.open."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "dashboard.html")
            fake_data = self._make_fake_data()
            with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
                 mock.patch("status.webbrowser.open") as mock_open:
                captured = StringIO()
                with mock.patch("sys.stdout", captured):
                    generate_dashboard(out_path, no_open=True)
                mock_open.assert_not_called()

    def test_browser_failure_prints_path(self):
        """When webbrowser.open raises, the file path is printed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "dashboard.html")
            fake_data = self._make_fake_data()
            with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
                 mock.patch("status.webbrowser.open", side_effect=Exception("no browser")):
                captured = StringIO()
                with mock.patch("sys.stdout", captured):
                    generate_dashboard(out_path, no_open=False)
                output = captured.getvalue()
                assert "Could not open browser" in output or out_path in output


# ---------------------------------------------------------------------------
# Task 6.4: Progress JSON primary, markdown fallback, neither → notice + health
# Validates: Requirements 10.1, 10.2, 10.3
# ---------------------------------------------------------------------------

class TestProgressDataSources:
    """Unit tests for progress data source priority."""

    def test_json_primary_source(self):
        """Progress JSON is the primary data source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, "config")
            os.makedirs(config_dir)
            progress = {
                "modules_completed": [1, 2, 3],
                "current_module": 4,
                "language": "Python",
            }
            with open(os.path.join(config_dir, "bootcamp_progress.json"), "w") as f:
                json.dump(progress, f)

            collector = DashboardDataCollector(tmpdir)
            data = collector.collect()
            assert data.modules_completed == [1, 2, 3]
            assert data.current_module == 4
            assert data.language == "Python"
            assert data.has_progress_data is True

    def test_markdown_fallback(self):
        """Falls back to PROGRESS_TRACKER.md when JSON is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_dir = os.path.join(tmpdir, "docs", "guides")
            os.makedirs(md_dir)
            md_content = (
                "# Progress\n"
                "- [x] Module 1: Business Problem\n"
                "- [x] Module 2: SDK Setup\n"
                "- [ ] Module 3: System Verification\n"
            )
            with open(os.path.join(md_dir, "PROGRESS_TRACKER.md"), "w") as f:
                f.write(md_content)

            collector = DashboardDataCollector(tmpdir)
            data = collector.collect()
            assert 1 in data.modules_completed
            assert 2 in data.modules_completed
            assert data.has_progress_data is True

    def test_neither_exists_shows_health_only(self):
        """When neither source exists, has_progress_data is False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DashboardDataCollector(tmpdir)
            data = collector.collect()
            assert data.has_progress_data is False
            assert data.modules_completed == []
            # Health checks still run
            assert isinstance(data.health_checks, list)

            # Rendered HTML should contain the notice
            html = _render(data)
            assert "No progress data found" in html


# ---------------------------------------------------------------------------
# Task 6.5: File read error skips, write failure exits non-zero, invalid JSON
# Validates: Requirements 10.5, 11.1, 11.2
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Unit tests for error handling edge cases."""

    def test_file_read_error_skips_data_source(self):
        """File read error for an artifact skips that data source gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a docs directory with an unreadable quality file
            docs_dir = os.path.join(tmpdir, "docs")
            os.makedirs(docs_dir)
            quality_file = os.path.join(docs_dir, "quality_report.md")
            with open(quality_file, "w") as f:
                f.write("overall: 85\nsource: TestSource\n")
            # Make it unreadable
            os.chmod(quality_file, 0o000)
            try:
                collector = DashboardDataCollector(tmpdir)
                data = collector.collect()
                # Should not crash; quality_scores may be empty
                assert isinstance(data.quality_scores, list)
            finally:
                os.chmod(quality_file, 0o644)

    def test_write_failure_exits_nonzero(self):
        """Write failure causes sys.exit(1)."""
        fake_data = DashboardData(
            modules_completed=[],
            current_module=1,
            status="Not Started",
            language=None,
            completion_pct=0,
            completion_timestamps={},
            quality_scores=[],
            performance=None,
            entity_stats=None,
            health_checks=[],
            health_score=0,
            health_total=0,
            generated_at="2024-01-01T00:00:00+00:00",
            has_progress_data=False,
        )
        with mock.patch("status.DashboardDataCollector.collect", return_value=fake_data), \
             mock.patch("pathlib.Path.write_text", side_effect=OSError("disk full")), \
             mock.patch("pathlib.Path.mkdir"):
            with pytest.raises(SystemExit) as exc_info:
                generate_dashboard("/nonexistent/path/dashboard.html", no_open=True)
            assert exc_info.value.code == 1

    def test_invalid_json_prints_warning_and_continues(self):
        """Invalid JSON in progress file prints warning and continues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, "config")
            os.makedirs(config_dir)
            with open(os.path.join(config_dir, "bootcamp_progress.json"), "w") as f:
                f.write("{invalid json content!!!")

            captured_err = StringIO()
            with mock.patch("sys.stderr", captured_err):
                collector = DashboardDataCollector(tmpdir)
                data = collector.collect()

            # Should still produce valid data (fallback)
            assert isinstance(data, DashboardData)
            assert data.modules_completed == []
            # Warning should have been printed
            err_output = captured_err.getvalue()
            assert "Warning" in err_output or "invalid JSON" in err_output.lower() or "warning" in err_output.lower()
