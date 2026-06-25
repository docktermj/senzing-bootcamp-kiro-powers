"""Tests for generate_artifact_inventory.py.

Shared test module for the graduation-artifact-inventory feature. Additional
test classes (loaders, scanning, rendering, properties) are appended here by
later tasks.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_artifact_inventory as gai


class TestParseArgs:
    """Argument parsing: defaults and per-flag overrides.

    Validates: Requirements 1.1
    """

    def test_defaults_with_no_args(self):
        args = gai.parse_args([])
        assert args.progress_file == "config/bootcamp_progress.json"
        assert args.project_root == "."
        assert args.output is None
        assert args.show_missing is False

    def test_override_progress_file(self):
        args = gai.parse_args(["--progress-file", "custom/progress.json"])
        assert args.progress_file == "custom/progress.json"
        # Other flags keep their defaults.
        assert args.project_root == "."
        assert args.output is None
        assert args.show_missing is False

    def test_override_project_root(self):
        args = gai.parse_args(["--project-root", "/tmp/my-project"])
        assert args.project_root == "/tmp/my-project"
        assert args.progress_file == "config/bootcamp_progress.json"
        assert args.output is None
        assert args.show_missing is False

    def test_override_output(self):
        args = gai.parse_args(["--output", "inventory.md"])
        assert args.output == "inventory.md"
        assert args.progress_file == "config/bootcamp_progress.json"
        assert args.project_root == "."
        assert args.show_missing is False

    def test_show_missing_flag_flips_to_true(self):
        args = gai.parse_args(["--show-missing"])
        assert args.show_missing is True
        assert args.progress_file == "config/bootcamp_progress.json"
        assert args.project_root == "."
        assert args.output is None

    def test_all_overrides_together(self):
        args = gai.parse_args(
            [
                "--progress-file",
                "p.json",
                "--project-root",
                "root",
                "--output",
                "out.md",
                "--show-missing",
            ]
        )
        assert args.progress_file == "p.json"
        assert args.project_root == "root"
        assert args.output == "out.md"
        assert args.show_missing is True


class TestLoadModulesCompleted:
    """Loading ``modules_completed`` from bootcamp_progress.json.

    Validates: Requirements 1.2, 4.2
    """

    def test_valid_json_returns_modules_and_complete(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text('{"modules_completed": [1, 2, 3]}', encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([1, 2, 3], True)

    def test_missing_file_returns_empty_incomplete(self, tmp_path):
        missing = tmp_path / "does_not_exist.json"
        assert gai.load_modules_completed(missing) == ([], False)

    def test_malformed_json_returns_empty_incomplete(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text("{not json", encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([], False)

    def test_object_without_modules_completed_key(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text('{"other_key": [1, 2]}', encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([], False)

    def test_modules_completed_not_a_list(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text('{"modules_completed": "1,2,3"}', encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([], False)

    def test_json_not_an_object(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text("[1, 2, 3]", encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([], False)

    def test_empty_list_returns_empty_but_complete(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text('{"modules_completed": []}', encoding="utf-8")
        assert gai.load_modules_completed(progress) == ([], True)

    def test_coerces_integral_floats_and_numeric_strings_excludes_bools(self, tmp_path):
        progress = tmp_path / "bootcamp_progress.json"
        progress.write_text(
            '{"modules_completed": [1, 2.0, "3", " 4 ", true, false, "abc", 5.5]}',
            encoding="utf-8",
        )
        # 1 -> 1, 2.0 -> 2, "3" -> 3, " 4 " -> 4; bools excluded; "abc" and 5.5
        # (non-integral float) skipped.
        assert gai.load_modules_completed(progress) == ([1, 2, 3, 4], True)


def _make_artifact(path: str, kind: str) -> gai.CatalogArtifact:
    """Build a CatalogArtifact for scanning tests with sensible metadata."""
    return gai.CatalogArtifact(
        path=path,
        kind=kind,
        phase="Discovery & Data Collection",
        module=1,
        classification="carry-forward",
        why_it_matters="Test artifact.",
    )


class TestArtifactScanning:
    """Disk scanning: artifact_exists and collect_present_artifacts.

    Validates: Requirements 1.3, 2.3
    """

    def test_present_file_returns_true(self, tmp_path):
        (tmp_path / "docs").mkdir()
        target = tmp_path / "docs" / "business_problem.md"
        target.write_text("content", encoding="utf-8")
        art = _make_artifact("docs/business_problem.md", "file")
        assert gai.artifact_exists(tmp_path, art) is True

    def test_absent_file_returns_false(self, tmp_path):
        art = _make_artifact("docs/business_problem.md", "file")
        assert gai.artifact_exists(tmp_path, art) is False

    def test_file_kind_against_directory_returns_false(self, tmp_path):
        # A directory at the path should not satisfy a "file" artifact.
        (tmp_path / "docs").mkdir()
        art = _make_artifact("docs", "file")
        assert gai.artifact_exists(tmp_path, art) is False

    def test_empty_dir_returns_false(self, tmp_path):
        (tmp_path / "data" / "raw").mkdir(parents=True)
        art = _make_artifact("data/raw/", "dir")
        assert gai.artifact_exists(tmp_path, art) is False

    def test_non_empty_dir_returns_true(self, tmp_path):
        raw = tmp_path / "data" / "raw"
        raw.mkdir(parents=True)
        (raw / "people.csv").write_text("a,b,c", encoding="utf-8")
        art = _make_artifact("data/raw/", "dir")
        assert gai.artifact_exists(tmp_path, art) is True

    def test_absent_dir_returns_false(self, tmp_path):
        art = _make_artifact("data/raw/", "dir")
        assert gai.artifact_exists(tmp_path, art) is False

    def test_dir_kind_against_file_returns_false(self, tmp_path):
        # A regular file at the path should not satisfy a "dir" artifact.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").write_text("not a dir", encoding="utf-8")
        art = _make_artifact("data/raw", "dir")
        assert gai.artifact_exists(tmp_path, art) is False

    def test_dir_with_only_subdir_is_non_empty(self, tmp_path):
        # A directory containing only a subdirectory still counts as non-empty.
        raw = tmp_path / "data" / "raw"
        (raw / "nested").mkdir(parents=True)
        art = _make_artifact("data/raw/", "dir")
        assert gai.artifact_exists(tmp_path, art) is True

    def test_collect_present_artifacts_returns_present_subset_in_order(self, tmp_path):
        # Catalog with a mix of present and absent artifacts.
        present_file = _make_artifact("docs/business_problem.md", "file")
        absent_file = _make_artifact("docs/missing.md", "file")
        present_dir = _make_artifact("data/raw/", "dir")
        empty_dir = _make_artifact("data/transformed/", "dir")
        absent_dir = _make_artifact("src/load/", "dir")
        catalog = [present_file, absent_file, present_dir, empty_dir, absent_dir]

        # Materialize only the two that should be present.
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "business_problem.md").write_text("x", encoding="utf-8")
        raw = tmp_path / "data" / "raw"
        raw.mkdir(parents=True)
        (raw / "people.csv").write_text("a", encoding="utf-8")
        # Create the empty dir so it exists but stays empty (must be excluded).
        (tmp_path / "data" / "transformed").mkdir(parents=True)

        result = gai.collect_present_artifacts(tmp_path, catalog)
        assert result == [present_file, present_dir]

    def test_collect_present_artifacts_empty_when_nothing_exists(self, tmp_path):
        catalog = [
            _make_artifact("docs/business_problem.md", "file"),
            _make_artifact("data/raw/", "dir"),
        ]
        assert gai.collect_present_artifacts(tmp_path, catalog) == []

    def test_collect_present_artifacts_preserves_full_catalog_when_all_present(
        self, tmp_path
    ):
        a = _make_artifact("config/data_sources.yaml", "file")
        b = _make_artifact("src/query/", "dir")
        catalog = [a, b]
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "data_sources.yaml").write_text("x", encoding="utf-8")
        query = tmp_path / "src" / "query"
        query.mkdir(parents=True)
        (query / "search.py").write_text("print()", encoding="utf-8")
        assert gai.collect_present_artifacts(tmp_path, catalog) == [a, b]


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

import tempfile  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


def _materialize(root: Path, art: gai.CatalogArtifact) -> None:
    """Create the on-disk artifact for ``art`` under ``root``.

    Files are created with their parent directories and non-empty content.
    Directories are created and seeded with a file so they count as non-empty.
    """
    target = root / art.path
    if art.kind == "file":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("content", encoding="utf-8")
    else:  # "dir"
        target.mkdir(parents=True, exist_ok=True)
        (target / ".seed").write_text("seed", encoding="utf-8")


class TestProperty1OnlyExistingListed:
    """Property 1: only existing artifacts are listed.

    For any subset of catalog paths materialized on disk, the collected
    artifacts equal exactly that subset (in catalog order) and exclude every
    catalog artifact whose path does not exist under the project root.

    Validates: Requirements 1.3, 2.3
    """

    @settings(max_examples=50)
    @given(
        selected=st.sets(
            st.integers(min_value=0, max_value=len(gai.ARTIFACT_CATALOG) - 1)
        )
    )
    def test_collected_equals_materialized_subset(self, selected: set[int]):
        catalog = gai.ARTIFACT_CATALOG
        expected = [catalog[i] for i in range(len(catalog)) if i in selected]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for art in expected:
                _materialize(root, art)

            result = gai.collect_present_artifacts(root, catalog)

        # Collected artifacts equal exactly the materialized subset, in order.
        assert result == expected
        # No absent-path artifact appears in the result.
        absent = [
            catalog[i] for i in range(len(catalog)) if i not in selected
        ]
        for art in absent:
            assert art not in result


class TestProperty5NoFabrication:
    """Property 5: no fabrication for incomplete modules.

    Inclusion is existence-based, never driven by ``modules_completed``. For any
    random set of completed modules and any random subset of catalog paths
    materialized on disk, ``collect_present_artifacts`` returns only artifacts
    that exist on disk and never an artifact whose path is absent — regardless of
    which modules are or are not marked completed.

    Validates: Requirements 2.2, 2.3
    """

    @settings(max_examples=50)
    @given(
        # Random completed-module set: modules 1-11 plus out-of-range values
        # (0 and 12) to confirm modules_completed has no effect on the output.
        modules_completed=st.sets(st.integers(min_value=0, max_value=12)),
        # Random subset of catalog indices to materialize on disk.
        materialized=st.sets(
            st.integers(min_value=0, max_value=len(gai.ARTIFACT_CATALOG) - 1)
        ),
    )
    def test_no_absent_artifact_is_ever_listed(
        self, modules_completed: set[int], materialized: set[int]
    ):
        catalog = gai.ARTIFACT_CATALOG
        present_arts = [catalog[i] for i in range(len(catalog)) if i in materialized]
        absent_arts = [catalog[i] for i in range(len(catalog)) if i not in materialized]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for art in present_arts:
                _materialize(root, art)

            result = gai.collect_present_artifacts(root, catalog)

            # Every artifact in the result actually exists on disk.
            for art in result:
                assert gai.artifact_exists(root, art) is True

            # No absent-on-disk artifact appears in the result, regardless of
            # which modules are marked completed.
            for art in absent_arts:
                assert art not in result

            # The core anti-fabrication guarantee: an artifact whose module is in
            # modules_completed but is absent on disk is still never fabricated.
            for art in absent_arts:
                if art.module is not None and art.module in modules_completed:
                    assert art not in result


class TestRenderInventory:
    """Rendering the '## Complete Artifact Inventory' Markdown section.

    Validates: Requirements 1.1, 2.1, 3.2, 3.3, 4.2
    """

    @staticmethod
    def _artifact(
        path: str,
        phase: str,
        classification: str = "carry-forward",
        why: str = "Why it matters note.",
    ) -> gai.CatalogArtifact:
        """Build a CatalogArtifact for rendering tests."""
        return gai.CatalogArtifact(
            path=path,
            kind="file",
            phase=phase,
            module=1,
            classification=classification,
            why_it_matters=why,
        )

    def test_heading_present_with_artifacts(self):
        present = [
            self._artifact("docs/business_problem.md", "Discovery & Data Collection")
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        assert out.startswith(gai.INVENTORY_HEADING)

    def test_heading_present_with_empty_present(self):
        out = gai.render_inventory(
            [],
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        # Heading is always emitted, even with no artifacts.
        assert out.startswith(gai.INVENTORY_HEADING)
        assert gai.INVENTORY_HEADING in out

    def test_phase_sub_headings_in_canonical_order(self):
        # Build artifacts spanning multiple phases, supplied out of canonical order.
        present = [
            self._artifact("docs/bootcamp_recap.md", "Bootcamp Records", "leave-behind"),
            self._artifact("src/query/main.py", "Querying & Visualization"),
            self._artifact("docs/business_problem.md", "Discovery & Data Collection"),
            self._artifact("data/transformed/out.json", "Mapping & Processing"),
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        # Collect the order of phase sub-headings as they appear in the output.
        appeared = [
            phase
            for phase in gai.PHASE_ORDER
            if f"### {phase}" in out
        ]
        # They must appear in canonical PHASE_ORDER order in the document.
        positions = [out.index(f"### {phase}") for phase in appeared]
        assert positions == sorted(positions)
        # And the appeared phases are exactly the four phases used, in canonical order.
        assert appeared == [
            "Discovery & Data Collection",
            "Mapping & Processing",
            "Querying & Visualization",
            "Bootcamp Records",
        ]

    def test_carry_forward_tag_text(self):
        present = [
            self._artifact(
                "config/engine_config.json",
                "Setup & Verification",
                "carry-forward",
            )
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        line = next(
            ln for ln in out.splitlines() if "config/engine_config.json" in ln
        )
        assert "_(carry-forward)_" in line

    def test_leave_behind_tag_text(self):
        present = [
            self._artifact(
                "config/bootcamp_progress.json",
                "Bootcamp Records",
                "leave-behind",
            )
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        line = next(
            ln for ln in out.splitlines() if "config/bootcamp_progress.json" in ln
        )
        assert "_(bootcamp record)_" in line

    def test_incompleteness_note_present_when_progress_incomplete(self):
        present = [
            self._artifact("docs/business_problem.md", "Discovery & Data Collection")
        ]
        out = gai.render_inventory(
            present,
            progress_complete=False,
            modules_completed=[],
            show_missing=False,
        )
        assert gai.INCOMPLETE_NOTE in out
        # The note follows the heading, not before it.
        assert out.index(gai.INCOMPLETE_NOTE) > out.index(gai.INVENTORY_HEADING)

    def test_incompleteness_note_absent_when_progress_complete(self):
        present = [
            self._artifact("docs/business_problem.md", "Discovery & Data Collection")
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        assert gai.INCOMPLETE_NOTE not in out

    def test_no_empty_phase_groups(self):
        # Only one phase has a present artifact; no other phase heading should appear.
        present = [
            self._artifact("src/query/main.py", "Querying & Visualization")
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        assert "### Querying & Visualization" in out
        # Phases with no present artifacts must NOT produce a sub-heading.
        for phase in gai.PHASE_ORDER:
            if phase != "Querying & Visualization":
                assert f"### {phase}" not in out

    def test_empty_present_renders_no_phase_headings(self):
        out = gai.render_inventory(
            [],
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        for phase in gai.PHASE_ORDER:
            assert f"### {phase}" not in out

    def test_artifact_line_includes_path_and_why(self):
        present = [
            self._artifact(
                "docs/deployment_plan.md",
                "Production Readiness",
                "carry-forward",
                why="Deployment plan you execute when going live.",
            )
        ]
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        line = next(
            ln for ln in out.splitlines() if "docs/deployment_plan.md" in ln
        )
        assert "`docs/deployment_plan.md`" in line
        assert "Deployment plan you execute when going live." in line


# ---------------------------------------------------------------------------
# Property 2: Every listed artifact is fully annotated
# ---------------------------------------------------------------------------

#: Alphabet for generated free-text fields. Excludes backticks plus all control
#: and line/paragraph-separator characters (Cc, Cs, Zl, Zp). This keeps every
#: generated path/note on a single logical line so the property's line-based
#: parsing (``str.splitlines()``) is not fooled by exotic line boundaries such
#: as NEL (``\x85``), vertical tab, or U+2028/U+2029.
_SAFE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_characters="`",
        blacklist_categories=("Cc", "Cs", "Zl", "Zp"),
    ),
    min_size=1,
).filter(lambda s: s.strip() != "")

#: Strategy producing a single random CatalogArtifact with a non-empty path and
#: a non-empty why-it-matters note, a valid phase, and a valid classification.
_st_artifact = st.builds(
    gai.CatalogArtifact,
    path=_SAFE_TEXT,
    kind=st.sampled_from(["file", "dir"]),
    phase=st.sampled_from(gai.PHASE_ORDER),
    module=st.one_of(st.none(), st.integers(min_value=0, max_value=12)),
    classification=st.sampled_from(["carry-forward", "leave-behind"]),
    why_it_matters=_SAFE_TEXT,
)


class TestProperty2FullyAnnotated:
    """Property 2: every listed artifact is fully annotated.

    For any rendered inventory, every artifact line contains the artifact's
    path (backtick-quoted), a non-empty why-it-matters note, and a
    classification tag (carry-forward or bootcamp-record). The number of
    artifact lines equals the number of present artifacts.

    Validates: Requirements 3.1, 3.4
    """

    @staticmethod
    def _expected_line(art: gai.CatalogArtifact) -> str:
        """The exact Markdown line render_inventory should emit for ``art``."""
        tag = gai.classification_tag(art.classification)
        return f"- `{art.path}` — {art.why_it_matters} {tag}"

    @settings(max_examples=50)
    @given(present=st.lists(_st_artifact, max_size=12))
    def test_every_listed_artifact_is_fully_annotated(
        self, present: list[gai.CatalogArtifact]
    ):
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )

        # Artifact lines are lines beginning with "- " (exclude headings/notes).
        artifact_lines = [ln for ln in out.splitlines() if ln.startswith("- ")]

        # One rendered artifact line per present artifact (no empty groups, and
        # show_missing=False means nothing extra is emitted).
        assert len(artifact_lines) == len(present)

        valid_tags = {"_(carry-forward)_", "_(bootcamp record)_"}

        # Each present artifact has a matching, fully-annotated rendered line.
        for art in present:
            expected = self._expected_line(art)
            assert expected in artifact_lines
            # Structural checks on that line: backtick-quoted path, the
            # non-empty note text, and a recognized classification tag.
            assert f"`{art.path}`" in expected
            assert art.why_it_matters in expected
            assert art.why_it_matters.strip() != ""
            assert any(tag in expected for tag in valid_tags)

        # Every rendered artifact line is fully annotated, too: it contains a
        # backtick-quoted path segment, the em-dash separator, and a tag.
        for line in artifact_lines:
            assert line.count("`") >= 2  # backtick-quoted path present
            assert " — " in line  # path/note separator
            assert any(line.endswith(tag) for tag in valid_tags)


# ---------------------------------------------------------------------------
# Property 3: Classification matches artifact role
# ---------------------------------------------------------------------------


class TestProperty3ClassificationMatches:
    """Property 3: classification matches artifact role.

    For any rendered inventory, every carry-forward artifact renders the
    carry-forward tag (``_(carry-forward)_``) and never the bootcamp-record
    tag, while every leave-behind artifact renders the bootcamp-record tag
    (``_(bootcamp record)_``) and never the carry-forward tag. Each artifact's
    rendered line is located by its backtick-quoted path; paths are constrained
    unique so the lookup is unambiguous.

    Validates: Requirements 3.2, 3.3
    """

    @settings(max_examples=50)
    @given(present=st.lists(_st_artifact, max_size=12, unique_by=lambda a: a.path))
    def test_tag_matches_classification(
        self, present: list[gai.CatalogArtifact]
    ):
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        lines = out.splitlines()

        for art in present:
            # Locate the rendered line for this artifact by its quoted path.
            quoted = f"`{art.path}`"
            line = next(ln for ln in lines if quoted in ln)

            if art.classification == "carry-forward":
                assert "_(carry-forward)_" in line
                assert "_(bootcamp record)_" not in line
            else:  # "leave-behind"
                assert "_(bootcamp record)_" in line
                assert "_(carry-forward)_" not in line


# ---------------------------------------------------------------------------
# Property 4: Artifacts are grouped by phase
# ---------------------------------------------------------------------------


class TestProperty4GroupedByPhase:
    """Property 4: artifacts are grouped by phase.

    For any rendered inventory, the ``### <phase>`` sub-headings appear in
    canonical :data:`PHASE_ORDER` order, a sub-heading is emitted for a phase if
    and only if at least one present artifact belongs to that phase (no empty
    groups), and every present artifact's rendered line falls under the section
    whose phase equals the artifact's own phase. Paths are constrained unique so
    each artifact maps to exactly one rendered line.

    Validates: Requirements 2.1, 2.2
    """

    @settings(max_examples=50)
    @given(present=st.lists(_st_artifact, max_size=12, unique_by=lambda a: a.path))
    def test_artifacts_are_grouped_by_phase(
        self, present: list[gai.CatalogArtifact]
    ):
        out = gai.render_inventory(
            present,
            progress_complete=True,
            modules_completed=[],
            show_missing=False,
        )
        lines = out.splitlines()

        # 1. Sub-headings appear in canonical PHASE_ORDER order.
        appeared = [phase for phase in gai.PHASE_ORDER if f"### {phase}" in out]
        positions = [out.index(f"### {phase}") for phase in appeared]
        assert positions == sorted(positions)

        # 2. No empty group: a phase heading appears IFF a present artifact has
        #    that phase.
        for phase in gai.PHASE_ORDER:
            heading_present = f"### {phase}" in out
            phase_has_artifact = any(art.phase == phase for art in present)
            assert heading_present == phase_has_artifact

        # Parse the output into sections: walk lines, tracking the current
        # "### <phase>" heading; every "- " line belongs to the current section.
        section_of_line: dict[str, str] = {}
        current_phase: str | None = None
        artifact_line_count = 0
        for ln in lines:
            if ln.startswith("### "):
                current_phase = ln[len("### "):]
            elif ln.startswith("- "):
                artifact_line_count += 1
                assert current_phase is not None  # no orphan artifact lines
                section_of_line[ln] = current_phase

        # Total artifact line count equals the number of present artifacts.
        assert artifact_line_count == len(present)

        # 3. Each artifact appears under exactly one phase sub-heading — its own.
        for art in present:
            tag = gai.classification_tag(art.classification)
            expected_line = f"- `{art.path}` — {art.why_it_matters} {tag}"
            assert expected_line in section_of_line
            assert section_of_line[expected_line] == art.phase


# ---------------------------------------------------------------------------
# Property 7: Inventory never duplicates the production-subset tables
# ---------------------------------------------------------------------------

#: Artifact strategy for Property 7. Reuses ``_st_artifact`` but excludes any
#: artifact whose generated path or why-it-matters note contains a pipe
#: character. The inventory section uses bullet lists exclusively (never
#: Markdown pipe tables), so the property asserts ``"|" not in out``; filtering
#: pipes out of the *inputs* keeps that assertion from producing a false
#: positive on user content rather than on a real table being emitted.
_st_artifact_no_pipe = _st_artifact.filter(
    lambda a: "|" not in a.path and "|" not in a.why_it_matters
)


class TestProperty7NoDuplicateTables:
    """Property 7: inventory never duplicates the production-subset tables.

    The graduation report already owns two production-subset tables: the
    "Files Generated" and "Files Excluded" tables. The Complete Artifact
    Inventory is a standalone, bullet-list section and must never reproduce
    those tables. For any rendered inventory this property asserts the output:

    1. always contains the inventory heading
       (``gai.INVENTORY_HEADING == "## Complete Artifact Inventory"``); and
    2. never emits the production-subset tables — it contains neither the
       "Files Generated" nor "Files Excluded" table headings (case-insensitive)
       and contains no Markdown pipe-table characters (``"|"``), since the
       inventory renders bullet lists rather than tables.

    Approach (a) from the task: generated artifacts are filtered so their path
    and note never contain ``"|"``, so the ``"|" not in out`` assertion can only
    fail if the renderer itself emitted a pipe table.

    Validates: Requirements 1.4, 4.4
    """

    @settings(max_examples=50)
    @given(
        present=st.lists(_st_artifact_no_pipe, max_size=12),
        progress_complete=st.booleans(),
        show_missing=st.booleans(),
    )
    def test_inventory_never_reproduces_production_tables(
        self,
        present: list[gai.CatalogArtifact],
        progress_complete: bool,
        show_missing: bool,
    ):
        out = gai.render_inventory(
            present,
            progress_complete=progress_complete,
            modules_completed=[],
            show_missing=show_missing,
        )

        # 1. The inventory heading is always present.
        assert gai.INVENTORY_HEADING in out
        assert out.startswith(gai.INVENTORY_HEADING)

        # 2. The production-subset table headings never appear (case-insensitive).
        lowered = out.lower()
        assert "files generated" not in lowered
        assert "files excluded" not in lowered

        # 3. No Markdown pipe-table characters: the inventory uses bullet lists.
        assert "|" not in out


# ---------------------------------------------------------------------------
# Catalog drift guard
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "module-artifacts.yaml"


def _extract_module_paths(config_path: Path) -> list[str]:
    """Extract every ``path:`` value under ``modules:`` (line-based, no PyYAML).

    Locates the top-level ``modules:`` key, then captures the value of every
    ``path:`` line that follows until a different top-level (column-0) key is
    reached. Surrounding quotes and whitespace are stripped from each value.

    Args:
        config_path: Path to ``module-artifacts.yaml``.

    Returns:
        The list of ``path:`` values declared under ``modules:``, in file order
        (duplicates preserved).
    """
    paths: list[str] = []
    in_modules = False
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        # Skip blank lines and comments without affecting section tracking.
        if not stripped or stripped.startswith("#"):
            continue
        # Detect top-level (column-0) keys to bound the modules: section.
        is_top_level = raw_line[:1] not in (" ", "\t")
        if is_top_level:
            in_modules = stripped.rstrip(":") == "modules"
            continue
        # YAML list entries appear as "- path: ...": drop a leading dash marker.
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if in_modules and stripped.startswith("path:"):
            value = stripped[len("path:") :].strip()
            value = value.strip("'\"")
            if value:
                paths.append(value)
    return paths


class TestCatalogDriftGuard:
    """Guard against drift between module-artifacts.yaml and ARTIFACT_CATALOG.

    Validates: Requirements 1.2, 2.1
    """

    def test_config_file_exists(self):
        assert _CONFIG_PATH.is_file(), f"missing config: {_CONFIG_PATH}"

    def test_extracts_expected_paths(self):
        # Sanity check the line-based parser found the module paths.
        paths = _extract_module_paths(_CONFIG_PATH)
        assert "docs/business_problem.md" in paths
        assert "src/load/" in paths
        assert "docs/deployment_plan.md" in paths
        # requires_from list entries are not `path:` keys and must be excluded.
        assert len(paths) >= 17

    def test_every_module_path_in_catalog(self):
        yaml_paths = _extract_module_paths(_CONFIG_PATH)
        catalog_paths = {art.path for art in gai.ARTIFACT_CATALOG}
        missing = sorted({p for p in yaml_paths if p not in catalog_paths})
        assert not missing, (
            "module-artifacts.yaml paths missing from ARTIFACT_CATALOG: "
            f"{missing}"
        )


# ---------------------------------------------------------------------------
# Property 6: Robust, non-blocking generation
# ---------------------------------------------------------------------------

#: Strategy for progress-file content fed to ``main()``. A value of ``None``
#: means "do not create the progress file at all" (the missing-file branch).
#: Otherwise the value is raw bytes written to the progress file, covering:
#:   - known-valid JSON (well-formed ``modules_completed``),
#:   - empty content,
#:   - malformed JSON / arbitrary text,
#:   - arbitrary binary blobs.
_st_progress_content = st.one_of(
    st.none(),
    st.sampled_from(
        [
            b'{"modules_completed": [1, 2, 3]}',
            b'{"modules_completed": []}',
            b'{"other_key": 1}',
            b"",
            b"{bad json",
            b"not json at all",
            b"[1, 2, 3]",
        ]
    ),
    st.binary(max_size=64),
    st.text(max_size=64).map(lambda s: s.encode("utf-8")),
)


class TestProperty6RobustGeneration:
    """Property 6: robust, non-blocking generation.

    For any progress-file content (valid, missing, malformed JSON, empty, or
    binary), ``main()`` never raises an unhandled exception, always emits output
    beginning with the ``## Complete Artifact Inventory`` heading, and includes
    the incompleteness note whenever the progress data is missing or unreadable.

    The progress file is written at ``<root>/config/bootcamp_progress.json`` so
    the default ``--progress-file`` resolves to it under ``--project-root``. The
    rendered Markdown is captured by directing ``--output`` to a file inside the
    temp root, then reading it back.

    Validates: Requirements 4.1, 4.2, 4.3
    """

    @settings(max_examples=50)
    @given(content=_st_progress_content)
    def test_main_is_robust_and_always_emits_heading(
        self, content: bytes | None
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            progress_path = config_dir / "bootcamp_progress.json"

            if content is not None:
                progress_path.write_bytes(content)

            out_path = root / "inventory.md"

            # 1. main() must never raise, regardless of progress content.
            rc = gai.main(
                [
                    "--project-root",
                    str(root),
                    "--output",
                    str(out_path),
                ]
            )
            assert rc == 0

            # 2. Output always begins with the inventory heading.
            rendered = out_path.read_text(encoding="utf-8")
            assert rendered.startswith(gai.INVENTORY_HEADING)

            # 3. When progress is missing/unreadable (load reports incomplete),
            #    the incompleteness note must appear; when complete, it must not.
            _, progress_complete = gai.load_modules_completed(progress_path)
            if progress_complete:
                assert gai.INCOMPLETE_NOTE not in rendered
            else:
                assert gai.INCOMPLETE_NOTE in rendered
