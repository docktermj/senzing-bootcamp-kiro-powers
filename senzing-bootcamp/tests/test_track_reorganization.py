"""Property-based and unit tests for track reorganization.

Validates that the two-track model (core_bootcamp, advanced_topics)
is correctly implemented and that all legacy track identifiers have been removed
from the bootcamp codebase.

Uses Hypothesis for property-based testing across 5 correctness properties,
plus unit tests asserting the Track_Registry structure and POWER.md content.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from export_results import (
    ArtifactManifest,
    ExportMetrics,
    ProgressData,
    SummaryGenerator,
    TRACK_DISPLAY_NAMES,
)
from validate_dependencies import (
    validate_no_legacy_identifiers,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BOOTCAMP_ROOT = Path(__file__).resolve().parent.parent

_VALID_TRACK_IDS = {"core_bootcamp", "advanced_topics"}

_LEGACY_TRACK_IDS = {
    "fast_track", "complete_beginner", "full_production",
    "A", "B", "C", "D",
    "Path A", "Path B", "Path C", "Path D",
    "Track A", "Track B", "Track C", "Track D",
}

# ---------------------------------------------------------------------------
# Task 8.1 — Hypothesis strategies for track identifiers
# ---------------------------------------------------------------------------


@st.composite
def st_valid_track_id(draw: st.DrawFn) -> str:
    """Strategy that samples from the set of valid track identifiers."""
    return draw(st.sampled_from(sorted(_VALID_TRACK_IDS)))


@st.composite
def st_legacy_track_id(draw: st.DrawFn) -> str:
    """Strategy that samples from the set of legacy track identifiers."""
    return draw(st.sampled_from(sorted(_LEGACY_TRACK_IDS)))


# Legacy identifiers safe for word-boundary file scanning (snake_case identifiers
# that are unambiguous track references — phrase-based identifiers like "Path A"
# and "Track A" appear in too many non-track contexts across steering/test files)
_LEGACY_SCANNABLE_IDS = {
    "fast_track", "complete_beginner", "full_production",
}


@st.composite
def st_legacy_scannable_id(draw: st.DrawFn) -> str:
    """Strategy for legacy identifiers safe to scan with word-boundary regex."""
    return draw(st.sampled_from(sorted(_LEGACY_SCANNABLE_IDS)))


# ===========================================================================
# Task 8.2 — Property 1: No legacy identifiers in bootcamp files
# ===========================================================================


class TestProperty1NoLegacyIdentifiersInFiles:
    """Feature: track-reorganization, Property 1: No legacy identifiers in bootcamp files

    For any legacy identifier, scanning all files under config/, steering/,
    docs/, scripts/, and tests/ SHALL find no word-boundary match.
    Files that define legacy identifiers for detection/validation purposes
    are excluded (validate_dependencies.py, test_track_reorganization.py).

    **Validates: Requirements 2.1, 9.5**
    """

    # Files that intentionally define legacy identifiers for detection purposes
    _EXCLUDED_FILES = {
        "scripts/validate_dependencies.py",
        "tests/test_track_reorganization.py",
    }

    @given(legacy_id=st_legacy_scannable_id())
    @settings(max_examples=10)
    def test_no_legacy_id_in_bootcamp_files(self, legacy_id: str) -> None:
        """For any legacy identifier, no bootcamp file contains it."""
        pattern = re.compile(rf"\b{re.escape(legacy_id)}\b")
        scan_dirs = [
            _BOOTCAMP_ROOT / "config",
            _BOOTCAMP_ROOT / "steering",
            _BOOTCAMP_ROOT / "docs",
            _BOOTCAMP_ROOT / "scripts",
            _BOOTCAMP_ROOT / "tests",
        ]

        for scan_dir in scan_dirs:
            if not scan_dir.is_dir():
                continue
            for dirpath, _dirs, files in os.walk(scan_dir):
                for fname in files:
                    fpath = Path(dirpath) / fname
                    # Skip files that define legacy identifiers for detection
                    rel_path = str(fpath.relative_to(_BOOTCAMP_ROOT))
                    if rel_path in self._EXCLUDED_FILES:
                        continue
                    # Skip binary files
                    try:
                        content = fpath.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        continue
                    match = pattern.search(content)
                    assert match is None, (
                        f"Legacy identifier {legacy_id!r} found in "
                        f"{rel_path} at position {match.start()}"
                    )


# ===========================================================================
# Task 8.3 — Property 2: Legacy track identifiers rejected at runtime
# ===========================================================================


class TestProperty2LegacyRejectedAtRuntime:
    """Feature: track-reorganization, Property 2: Legacy track identifiers rejected at runtime

    For any legacy identifier, passing it as the track field to ProgressData
    SHALL raise ValueError.

    **Validates: Requirements 2.4, 8.2**
    """

    @given(legacy_id=st_legacy_track_id())
    @settings(max_examples=10)
    def test_legacy_id_raises_value_error(self, legacy_id: str) -> None:
        """ProgressData rejects any legacy track identifier."""
        with pytest.raises(ValueError, match="Unrecognized track identifier"):
            ProgressData(modules_completed=[], track=legacy_id)


# ===========================================================================
# Task 8.4 — Property 3: Track module lists respect topological ordering
# ===========================================================================


class TestProperty3TopologicalOrdering:
    """Feature: track-reorganization, Property 3: Track module lists respect topological ordering

    For any track in the Track_Registry, for any module in that track's module
    list that declares a prerequisite, every declared prerequisite that is also
    in the track's module list SHALL appear at an earlier index.

    **Validates: Requirements 4.3, 4.4**
    """

    @given(track_id=st_valid_track_id())
    @settings(max_examples=10)
    def test_prerequisites_appear_before_dependents(self, track_id: str) -> None:
        """All prerequisites appear before their dependents in the track module list."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        tracks = graph["tracks"]
        modules_section = graph["modules"]
        track_data = tracks[track_id]
        module_list: list[int] = track_data["modules"]

        # Build position map
        position: dict[int, int] = {mod: idx for idx, mod in enumerate(module_list)}

        for mod_num in module_list:
            mod_data = modules_section.get(mod_num)
            if mod_data is None:
                continue
            requires = mod_data.get("requires", [])
            for req in requires:
                if req in position:
                    assert position[req] < position[mod_num], (
                        f"Track {track_id!r}: module {mod_num} at index "
                        f"{position[mod_num]} appears before its prerequisite "
                        f"{req} at index {position[req]}"
                    )


# ===========================================================================
# Task 8.5 — Property 4: Executive summary renders display name for valid tracks
# ===========================================================================


class TestProperty4DisplayNameInSummary:
    """Feature: track-reorganization, Property 4: Executive summary renders display name

    For any valid track identifier, when SummaryGenerator.generate() is called
    with a ProgressData that has that track, the output SHALL contain the
    corresponding display name from TRACK_DISPLAY_NAMES.

    **Validates: Requirements 8.3**
    """

    @given(track_id=st_valid_track_id())
    @settings(max_examples=10)
    def test_summary_contains_display_name(self, track_id: str) -> None:
        """Executive summary uses the track's display name."""
        progress = ProgressData(
            modules_completed=[1, 2, 3],
            track=track_id,
        )
        metrics = ExportMetrics(quality_scores=[])
        manifest = ArtifactManifest(
            artifacts=[],
            scan_timestamp="2025-01-15T10:30:00+00:00",
        )

        summary = SummaryGenerator.generate(progress, metrics, manifest)
        expected_display_name = TRACK_DISPLAY_NAMES[track_id]
        assert expected_display_name in summary, (
            f"Display name {expected_display_name!r} not found in summary "
            f"for track {track_id!r}. Summary: {summary!r}"
        )


# ===========================================================================
# Task 8.6 — Property 5: validate_dependencies detects legacy identifiers as ERROR
# ===========================================================================


class TestProperty5ValidationDetectsLegacy:
    """Feature: track-reorganization, Property 5: validate_dependencies detects legacy as ERROR

    For any legacy identifier injected into a Track_Registry YAML structure,
    running validate_no_legacy_identifiers() SHALL report at least one
    ERROR-level violation.

    **Validates: Requirements 8.5**
    """

    @given(legacy_id=st_legacy_track_id())
    @settings(max_examples=10)
    def test_legacy_in_registry_detected_as_error(self, legacy_id: str) -> None:
        """Injecting a legacy identifier into the Track_Registry triggers ERROR."""
        # Build a minimal graph with the legacy identifier as a track key
        graph = {
            "metadata": {"version": "1.0.0", "last_updated": "2025-01-01"},
            "modules": {
                1: {"name": "Test", "requires": [], "skip_if": None},
            },
            "tracks": {
                legacy_id: {
                    "name": f"Legacy {legacy_id}",
                    "description": "A legacy track",
                    "modules": [1],
                },
            },
            "gates": {},
        }

        # Use a non-existent onboarding path so only the registry check fires
        fake_onboarding = Path(tempfile.gettempdir()) / "nonexistent_onboarding.md"
        violations = validate_no_legacy_identifiers(graph, fake_onboarding)

        error_violations = [v for v in violations if v.level == "ERROR"]
        assert len(error_violations) >= 1, (
            f"Expected at least one ERROR for legacy identifier {legacy_id!r} "
            f"in Track_Registry, got violations: {[v.format() for v in violations]}"
        )


# ===========================================================================
# Task 8.7 — Unit test: Track_Registry contains exactly two identifiers
# ===========================================================================


class TestTrackRegistryStructure:
    """Unit tests asserting the Track_Registry has exactly two tracks with correct structure.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    def test_registry_has_exactly_two_tracks(self) -> None:
        """Track_Registry contains exactly core_bootcamp and advanced_topics."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        tracks = graph["tracks"]
        assert set(tracks.keys()) == {"core_bootcamp", "advanced_topics"}

    def test_each_track_has_required_fields(self) -> None:
        """Each track has name, description, modules, and recommendation fields."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        tracks = graph["tracks"]
        required_fields = {"name", "description", "modules", "recommendation"}

        for track_id, track_data in tracks.items():
            for field in required_fields:
                assert field in track_data, (
                    f"Track {track_id!r} missing required field {field!r}"
                )

    def test_quick_demo_absent_from_registry(self) -> None:
        """quick_demo track is not present in the Track_Registry."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        assert "quick_demo" not in graph["tracks"]

    def test_core_bootcamp_modules(self) -> None:
        """core_bootcamp track has modules [1, 2, 3, 4, 5, 6, 7]."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        assert graph["tracks"]["core_bootcamp"]["modules"] == [1, 2, 3, 4, 5, 6, 7]

    def test_advanced_topics_modules(self) -> None:
        """advanced_topics track has modules [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        assert graph["tracks"]["advanced_topics"]["modules"] == [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
        ]

    def test_recommendation_values(self) -> None:
        """Recommendation values are correct for each track."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        tracks = graph["tracks"]
        assert tracks["core_bootcamp"]["recommendation"] == "recommended"
        assert tracks["advanced_topics"]["recommendation"] == "not_recommended"

    def test_no_legacy_track_keys(self) -> None:
        """No legacy track identifier appears as a key in the Track_Registry."""
        yaml_path = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
        with open(yaml_path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)

        tracks = graph["tracks"]
        for legacy_id in _LEGACY_TRACK_IDS:
            assert legacy_id not in tracks, (
                f"Legacy identifier {legacy_id!r} found as track key"
            )


# ===========================================================================
# Task 7.5 — Unit tests: POWER.md lists exactly 2 tracks, Module 3 retained
# ===========================================================================


class TestPowerMdTrackContent:
    """Unit tests asserting POWER.md lists exactly 2 tracks and retains Module 3.

    **Validates: Requirements 7.1, 7.6**
    """

    def test_power_md_lists_exactly_two_tracks(self) -> None:
        """POWER.md Quick Start section lists exactly 2 track bullets."""
        power_md_path = _BOOTCAMP_ROOT / "POWER.md"
        content = power_md_path.read_text(encoding="utf-8")

        # Extract the Quick Start section
        qs_match = re.search(
            r"## Quick Start\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        assert qs_match is not None, "Quick Start section not found in POWER.md"
        qs_section = qs_match.group(1)

        # Count track bullet lines (lines starting with "- **" that describe tracks)
        track_bullets = re.findall(r"^- \*\*[^*]+\*\*", qs_section, re.MULTILINE)
        assert len(track_bullets) == 2, (
            f"Expected exactly 2 track bullets in Quick Start, "
            f"got {len(track_bullets)}: {track_bullets}"
        )

    def test_power_md_no_quick_demo_track_bullet(self) -> None:
        """POWER.md Quick Start section does not list a Quick Demo track."""
        power_md_path = _BOOTCAMP_ROOT / "POWER.md"
        content = power_md_path.read_text(encoding="utf-8")

        # Extract the Quick Start section
        qs_match = re.search(
            r"## Quick Start\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        assert qs_match is not None, "Quick Start section not found in POWER.md"
        qs_section = qs_match.group(1)

        # Ensure no "Quick Demo" track bullet exists
        assert "Quick Demo" not in qs_section, (
            "Quick Demo track bullet still present in POWER.md Quick Start section"
        )

    def test_power_md_module_3_in_bootcamp_modules_table(self) -> None:
        """POWER.md Bootcamp Modules table retains Module 3 (System Verification)."""
        power_md_path = _BOOTCAMP_ROOT / "POWER.md"
        content = power_md_path.read_text(encoding="utf-8")

        # Look for Module 3 row in the Bootcamp Modules table
        # The table has format: | 3      | System Verification ...
        module_3_pattern = re.compile(r"^\|\s*3\s*\|.*System Verification", re.MULTILINE)
        assert module_3_pattern.search(content) is not None, (
            "Module 3 (System Verification) not found in POWER.md Bootcamp Modules table"
        )

    def test_power_md_has_core_bootcamp_track(self) -> None:
        """POWER.md Quick Start section lists Core Bootcamp track."""
        power_md_path = _BOOTCAMP_ROOT / "POWER.md"
        content = power_md_path.read_text(encoding="utf-8")

        qs_match = re.search(
            r"## Quick Start\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        assert qs_match is not None
        qs_section = qs_match.group(1)

        assert "Core Bootcamp" in qs_section, (
            "Core Bootcamp track not found in POWER.md Quick Start section"
        )

    def test_power_md_has_advanced_topics_track(self) -> None:
        """POWER.md Quick Start section lists Advanced Topics track."""
        power_md_path = _BOOTCAMP_ROOT / "POWER.md"
        content = power_md_path.read_text(encoding="utf-8")

        qs_match = re.search(
            r"## Quick Start\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        assert qs_match is not None
        qs_section = qs_match.group(1)

        assert "Advanced Topics" in qs_section, (
            "Advanced Topics track not found in POWER.md Quick Start section"
        )
