"""Bug condition exploration tests for the file-placement-conventions bugfix.

Feature: file-placement-conventions (BUGFIX)

Task 1 — Bug condition exploration test.

Property 1: Bug Condition — Misplaced Artifacts Route to Wrong Locations.

**Validates: Requirements 1.2, 1.4, 1.5, 2.2, 2.4, 2.5**

CRITICAL: These tests encode the EXPECTED (post-fix) routing behavior and MUST
FAIL on the current (unfixed) ``organize_mapping_files.py``. Their failure
confirms the routing defects exist. Once the fix (Task 7 — filename-aware
routing rules for downloaded resources and mapping/transformed data) is
implemented, these same tests validate the fix by passing.

Observed defects on unfixed code (the counterexamples this task surfaces):
  - resource scripts (``sz_*.py``) route to ``src/mapping``   (want ``src/resources``)
  - ``*_sample.jsonl`` routes to ``data``                     (want ``data/mapping``)
  - ``*_mapping_spec.json`` routes to ``config``              (want ``data/mapping``)
  - generic ``*.jsonl`` routes to ``data``                    (want ``data/transformed``)
"""

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts are not a package).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from organize_mapping_files import route

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_resource_script_name():
    """Generate filenames of resources downloaded from mcp.senzing.com/resources.

    Returns:
        A strategy over the known Senzing resource helper script names.
    """
    return st.sampled_from(
        [
            "sz_json_analyzer.py",
            "sz_verbatim_check.py",
            "sz_routing_report.py",
        ]
    )


def st_sample_jsonl_name():
    """Generate per-source sample JSONL working-data filenames.

    Returns:
        A strategy over ``{source}_sample.jsonl`` names (mapping working data).
    """
    return st.from_regex(r"[a-z]+_sample\.jsonl", fullmatch=True)


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — misplaced artifacts route to wrong locations
# ---------------------------------------------------------------------------


class TestBugConditionExploration:
    """Feature: file-placement-conventions, Property 1: Bug Condition.

    For any artifact-producing action where the bug condition holds, the fixed
    organizer SHALL route the artifact to its canonical home. These exploratory
    cases MUST FAIL on unfixed code — their failure confirms the routing defects
    exist.

    **Validates: Requirements 1.2, 1.4, 1.5, 2.2, 2.4, 2.5**
    """

    # --- Downloaded Senzing resources -> src/resources (Req 1.2, 2.2) ------

    def test_json_analyzer_routes_to_src_resources(self):
        """route("sz_json_analyzer.py") -> "src/resources" (unfixed: "src/mapping")."""
        assert route("sz_json_analyzer.py") == "src/resources"

    def test_verbatim_check_routes_to_src_resources(self):
        """route("sz_verbatim_check.py") -> "src/resources" (unfixed: "src/mapping")."""
        assert route("sz_verbatim_check.py") == "src/resources"

    def test_routing_report_routes_to_src_resources(self):
        """route("sz_routing_report.py") -> "src/resources" (unfixed: "src/mapping")."""
        assert route("sz_routing_report.py") == "src/resources"

    @given(name=st_resource_script_name())
    def test_resource_scripts_route_to_src_resources(self, name):
        """Every downloaded resource script routes to "src/resources" (Req 2.2)."""
        assert route(name) == "src/resources"

    # --- Mapping working data -> data/mapping (Req 1.4, 2.4) ---------------

    def test_customers_sample_routes_to_data_mapping(self):
        """route("customers_sample.jsonl") -> "data/mapping" (unfixed: "data")."""
        assert route("customers_sample.jsonl") == "data/mapping"

    def test_transactions_sample_routes_to_data_mapping(self):
        """route("transactions_sample.jsonl") -> "data/mapping" (unfixed: "data")."""
        assert route("transactions_sample.jsonl") == "data/mapping"

    def test_mapping_spec_routes_to_data_mapping(self):
        """route("customers_mapping_spec.json") -> "data/mapping" (unfixed: "config")."""
        assert route("customers_mapping_spec.json") == "data/mapping"

    @given(name=st_sample_jsonl_name())
    def test_sample_jsonl_routes_to_data_mapping(self, name):
        """Every "{source}_sample.jsonl" routes to "data/mapping" (Req 2.4)."""
        assert route(name) == "data/mapping"

    # --- Transformed deliverable -> data/transformed (Req 1.5, 2.5) --------

    def test_transformed_jsonl_routes_to_data_transformed(self):
        """route("customers.jsonl") -> "data/transformed" (unfixed: "data")."""
        assert route("customers.jsonl") == "data/transformed"


# ---------------------------------------------------------------------------
# Task 2 — Preservation property tests
# ---------------------------------------------------------------------------
#
# Property 2: Preservation — Non-Affected Artifacts Route Unchanged.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
#
# Observation-first methodology: these tests capture the CURRENT (baseline)
# routing behavior for artifact kinds the fix does NOT touch, and they MUST
# PASS on the unfixed ``organize_mapping_files.py``. Once the fix lands they act
# as regression guards — the same assertions must keep holding.
#
# Baseline observed on unfixed code (``route()`` over ``ROUTING_RULE_LIST``):
#   - route("senzing_entity_specification.md") -> "docs/reference"
#   - route("customers_mapper.md")             -> "docs/mapping"
#   - route("any_report.md")                   -> "docs/mapping"
#   - route("transform_customers.py")          -> "src/mapping"
#   - route("bootcamp_progress.json")          -> "config"
#
# Strategy design note (special-cased names): the only filename-specific rules
# are ``match_name("senzing_entity_specification.md")`` (an ``.md`` file) and
# ``match_suffix("_mapper.md")``. There is NO name-specific ``.json`` rule, so
# the ``.json`` strategy only needs to exclude ``_mapping_spec.json`` (the
# suffix the fix will re-route). Each strategy below is constrained so its
# property stays valid before AND after the fix:
#   - ``.py`` names exclude the ``sz_`` prefix (the fix routes ``sz_*`` resource
#     scripts to ``src/resources``).
#   - ``.json`` names exclude the ``_mapping_spec.json`` suffix (the fix routes
#     those to ``data/mapping``).
#   - generic ``.md`` names exclude the entity-spec name and the ``_mapper.md``
#     suffix so the generic ``.md`` rule is the one under test.

# Extensions the routing rules know about; anything else must route to None.
_KNOWN_EXTENSIONS: tuple[str, ...] = (".md", ".py", ".jsonl", ".json")

# A spread of extensions that appear in no routing rule.
_UNKNOWN_EXTENSIONS: tuple[str, ...] = (
    ".txt",
    ".csv",
    ".yaml",
    ".yml",
    ".log",
    ".db",
    ".png",
    ".pdf",
    ".html",
    ".sh",
    ".cfg",
    ".toml",
    ".xml",
)


def st_non_resource_py():
    """Generate ``.py`` filenames that do NOT start with ``sz_``.

    These are ordinary transformation/mapper scripts. The fix reroutes only the
    ``sz_*`` downloaded-resource scripts, so excluding the ``sz_`` prefix keeps
    this preservation property valid before and after the fix.

    Returns:
        A strategy over ``.py`` filenames whose stem never begins with ``sz_``.
    """
    return st.from_regex(r"[a-z][a-z0-9_]*\.py", fullmatch=True).filter(
        lambda name: not name.startswith("sz_")
    )


def st_non_sample_non_mapping_spec_json():
    """Generate ``.json`` filenames that do NOT end in ``_mapping_spec.json``.

    Ordinary config JSON (e.g. ``bootcamp_progress.json``) routes to ``config``.
    The fix reroutes only ``*_mapping_spec.json``; there is no name-specific
    ``.json`` rule to avoid, so excluding that one suffix is sufficient.

    Returns:
        A strategy over ``.json`` filenames not ending in ``_mapping_spec.json``.
    """
    return st.from_regex(r"[a-z][a-z0-9_]*\.json", fullmatch=True).filter(
        lambda name: not name.endswith("_mapping_spec.json")
    )


def st_mapper_md():
    """Generate ``*_mapper.md`` mapper-spec filenames.

    Every generated name ends in ``_mapper.md`` (matched by the dedicated suffix
    rule) and can never equal the ``senzing_entity_specification.md`` special
    case, so the mapper rule is the one exercised.

    Returns:
        A strategy over ``{stem}_mapper.md`` filenames.
    """
    return st.from_regex(r"[a-z][a-z0-9_]*_mapper\.md", fullmatch=True)


def st_generic_md():
    """Generate ``.md`` filenames that are neither the entity spec nor a mapper.

    Excludes the ``senzing_entity_specification.md`` special case (routes to
    ``docs/reference``) and any ``_mapper.md`` suffix so the generic ``.md`` rule
    is the one under test.

    Returns:
        A strategy over generic ``.md`` filenames routing to ``docs/mapping``.
    """
    return st.from_regex(r"[a-z][a-z0-9_]*\.md", fullmatch=True).filter(
        lambda name: name != "senzing_entity_specification.md"
        and not name.endswith("_mapper.md")
    )


def st_unknown_ext():
    """Generate filenames whose extension appears in no routing rule.

    Pairs a lowercase stem (no dots) with an extension drawn from a set that is
    disjoint from :data:`_KNOWN_EXTENSIONS`, so ``route()`` must return None.

    Returns:
        A strategy over ``{stem}{ext}`` filenames with unrouted extensions.
    """
    stems = st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True)
    exts = st.sampled_from(_UNKNOWN_EXTENSIONS)
    return st.builds(lambda stem, ext: f"{stem}{ext}", stems, exts)


class TestPreservationProperties:
    """Feature: file-placement-conventions, Property 2: Preservation.

    For any artifact-producing action where the bug condition does NOT hold, the
    fixed organizer SHALL route the artifact exactly as the original did. These
    tests capture that baseline on unfixed code (they MUST PASS now) and guard
    against regressions once the fix is applied.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    # --- Concrete baseline observations (must hold on unfixed code) --------

    def test_entity_spec_routes_to_docs_reference(self):
        """route("senzing_entity_specification.md") -> "docs/reference"."""
        assert route("senzing_entity_specification.md") == "docs/reference"

    def test_mapper_md_routes_to_docs_mapping(self):
        """route("customers_mapper.md") -> "docs/mapping"."""
        assert route("customers_mapper.md") == "docs/mapping"

    def test_generic_md_routes_to_docs_mapping(self):
        """route("any_report.md") -> "docs/mapping"."""
        assert route("any_report.md") == "docs/mapping"

    def test_non_resource_py_routes_to_src_mapping(self):
        """route("transform_customers.py") -> "src/mapping"."""
        assert route("transform_customers.py") == "src/mapping"

    def test_config_json_routes_to_config(self):
        """route("bootcamp_progress.json") -> "config"."""
        assert route("bootcamp_progress.json") == "config"

    # --- Property: non-affected artifacts route unchanged ------------------

    @given(name=st_non_resource_py())
    def test_non_resource_py_preserved(self, name):
        """Every non-``sz_`` ``.py`` file routes to "src/mapping" (Req 3.3)."""
        assert route(name) == "src/mapping"

    @given(name=st_non_sample_non_mapping_spec_json())
    def test_non_mapping_spec_json_preserved(self, name):
        """Every ``.json`` not ending in ``_mapping_spec.json`` -> "config" (Req 3.3)."""
        assert route(name) == "config"

    @given(name=st_mapper_md())
    def test_mapper_md_preserved(self, name):
        """Every ``*_mapper.md`` file routes to "docs/mapping" (Req 3.3)."""
        assert route(name) == "docs/mapping"

    @given(name=st_generic_md())
    def test_generic_md_preserved(self, name):
        """Every generic ``.md`` file routes to "docs/mapping" (Req 3.3, 3.4)."""
        assert route(name) == "docs/mapping"

    @given(name=st_unknown_ext())
    def test_unknown_ext_preserved(self, name):
        """Every filename with an unrouted extension routes to None (Req 3.4)."""
        assert route(name) is None


# ---------------------------------------------------------------------------
# Task 8.3 — End-to-end file organization integration tests
# ---------------------------------------------------------------------------
#
# These integration tests drive the full ``organize_mapping_files.py`` CLI
# through its ``main()`` entry point over real temp directories. They confirm
# that the filename-aware routing rules land each artifact in its canonical
# subdirectory, that ``--dry-run`` reports planned moves without touching the
# filesystem, and that canonical single-copy deduplication (see
# ``CANONICAL_DEDUP_FILES``) is preserved for ``senzing_entity_specification.md``.
#
# **Validates: Requirements 2.2, 2.4, 2.5, 3.3, 3.4**

from organize_mapping_files import main

# Representative mapping-workflow artifacts mapped to their canonical
# destination subdirectory (POSIX-style, relative to the project root).
_INTEGRATION_ROUTES: dict[str, str] = {
    "sz_json_analyzer.py": "src/resources",
    "customers_sample.jsonl": "data/mapping",
    "customers.jsonl": "data/transformed",
    "customers_mapping_spec.json": "data/mapping",
    "customers_mapper.md": "docs/mapping",
    "profile_report.md": "docs/mapping",
    "bootcamp_progress.json": "config",
}


def _populate_source(source_dir: Path) -> None:
    """Write one representative file per entry in :data:`_INTEGRATION_ROUTES`.

    Args:
        source_dir: The (already-created) directory to populate with artifacts.
    """
    for filename in _INTEGRATION_ROUTES:
        (source_dir / filename).write_text(f"content {filename}\n", encoding="utf-8")


class TestFileOrganizationIntegration:
    """Feature: file-placement-conventions — end-to-end organizer integration.

    Exercises ``organize_mapping_files.main()`` over real temp directories to
    confirm the fixed routing rules place each artifact in its canonical home,
    that ``--dry-run`` is non-destructive, and that canonical deduplication for
    ``senzing_entity_specification.md`` is unchanged.

    **Validates: Requirements 2.2, 2.4, 2.5, 3.3, 3.4**
    """

    def test_end_to_end_routes_files_to_canonical_subdirs(self, tmp_path):
        """main() moves each artifact into its canonical subdirectory (exit 0)."""
        source_dir = tmp_path / "source"
        project_root = tmp_path / "project"
        source_dir.mkdir()
        project_root.mkdir()
        _populate_source(source_dir)

        exit_code = main(["--source", str(source_dir), "--project-root", str(project_root)])

        assert exit_code == 0
        for filename, subdir in _INTEGRATION_ROUTES.items():
            destination = project_root / subdir / filename
            assert destination.is_file(), f"{filename} should land in {subdir}/"
            assert not (source_dir / filename).exists(), f"{filename} should leave source"

    def test_dry_run_reports_moves_without_touching_filesystem(self, tmp_path, capsys):
        """--dry-run prints planned destinations but moves/creates nothing."""
        source_dir = tmp_path / "source"
        project_root = tmp_path / "project"
        source_dir.mkdir()
        project_root.mkdir()
        _populate_source(source_dir)

        exit_code = main(
            ["--source", str(source_dir), "--project-root", str(project_root), "--dry-run"]
        )

        assert exit_code == 0
        stdout = capsys.readouterr().out
        resolved_root = project_root.resolve()
        for filename, subdir in _INTEGRATION_ROUTES.items():
            # The planned destination is reported on stdout ...
            assert filename in stdout
            assert str(resolved_root / subdir / filename) in stdout
            # ... but nothing is actually moved and no destination is created.
            assert (source_dir / filename).is_file()
            assert not (project_root / subdir / filename).exists()
            assert not (project_root / subdir).exists()

    def test_deduplication_preserved_for_entity_spec(self, tmp_path):
        """A misplaced entity-spec source copy is removed; the canonical copy remains."""
        source_dir = tmp_path / "source"
        project_root = tmp_path / "project"
        source_dir.mkdir()
        project_root.mkdir()

        canonical = project_root / "docs" / "reference" / "senzing_entity_specification.md"
        canonical.parent.mkdir(parents=True)
        canonical.write_text("canonical entity specification\n", encoding="utf-8")

        misplaced = source_dir / "senzing_entity_specification.md"
        misplaced.write_text("misplaced duplicate copy\n", encoding="utf-8")

        exit_code = main(["--source", str(source_dir), "--project-root", str(project_root)])

        assert exit_code == 0
        assert not misplaced.exists(), "misplaced duplicate should be deduplicated (removed)"
        assert canonical.is_file(), "canonical copy must remain"
        assert canonical.read_text(encoding="utf-8") == "canonical entity specification\n"
