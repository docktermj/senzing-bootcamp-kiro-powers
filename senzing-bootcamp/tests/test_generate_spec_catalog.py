"""Property-based and unit tests for generate_spec_catalog.py using Hypothesis.

Feature: spec-catalog-index.

Validates the Spec_Catalog_Generator: catalog discovery, status derivation,
relationship resolution, index/summary rendering, deterministic and read-only
operation, drift detection, and error handling. Tests follow the conventions of
test_generate_docs_index.py: sys.path import of the script, class-based
organization, Hypothesis @given with @settings, and st_-prefixed strategies.
"""

import sys
from pathlib import Path

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hashlib  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

import pytest  # noqa: E402
from hypothesis import HealthCheck, assume, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from generate_spec_catalog import (  # noqa: E402
    CONFIG_FILENAME,
    DEFAULT_INDEX_PATH,
    DEFAULT_METADATA_PATH,
    DEFAULT_SPECS_ROOT,
    SPEC_DOCUMENTS,
    STATUS_ORDER,
    Catalog,
    CatalogError,
    CatalogMetadata,
    SpecConfig,
    SpecEntry,
    SpecRecord,
    SpecRelationships,
    build_catalog,
    count_task_checkboxes,
    derive_status,
    discover_specs,
    load_metadata,
    main,
    read_config,
    render_index,
    render_summary,
    resolve_relationships,
    validate_metadata_refs,
)

_MISSING_FIELD = "unknown"


class TestSkeleton:
    """Smoke tests confirming the script skeleton imports and is well-formed.

    These guard the constants and data models established in Task 1 so later
    tasks build on a stable foundation.
    """

    def test_constants_have_expected_values(self):
        """Constants match the design's documented defaults."""
        assert DEFAULT_SPECS_ROOT == Path(".kiro/specs")
        assert DEFAULT_INDEX_PATH == Path(".kiro/SPEC_CATALOG.md")
        assert DEFAULT_METADATA_PATH == Path(".kiro/spec-catalog.yaml")
        assert CONFIG_FILENAME == ".config.kiro"
        assert SPEC_DOCUMENTS == ("requirements.md", "design.md", "tasks.md")
        assert STATUS_ORDER == (
            "in-progress",
            "implemented",
            "superseded",
            "abandoned",
            "unknown",
        )

    def test_catalog_error_is_exception(self):
        """CatalogError is an Exception subclass usable for error reporting."""
        assert issubclass(CatalogError, Exception)

    def test_spec_config_fields(self):
        """SpecConfig carries workflow_type and spec_type."""
        config = SpecConfig(workflow_type="requirements-first", spec_type="feature")
        assert config.workflow_type == "requirements-first"
        assert config.spec_type == "feature"

    def test_spec_record_fields(self):
        """SpecRecord captures discovery signals for one spec directory."""
        record = SpecRecord(
            identifier="adaptive-pacing",
            has_requirements=True,
            has_design=True,
            has_tasks=False,
            config=None,
            task_total=0,
            task_complete=0,
        )
        assert record.identifier == "adaptive-pacing"
        assert record.has_requirements is True
        assert record.config is None

    def test_spec_relationships_defaults_empty(self):
        """SpecRelationships defaults to empty tuples."""
        rels = SpecRelationships()
        assert rels.supersedes == ()
        assert rels.superseded_by == ()
        assert rels.related == ()

    def test_catalog_metadata_empty_classmethod(self):
        """CatalogMetadata.empty() yields no overrides or relationships."""
        meta = CatalogMetadata.empty()
        assert meta.status_overrides == {}
        assert meta.supersessions == ()
        assert meta.related == ()

    def test_spec_entry_and_catalog_compose(self):
        """SpecEntry and Catalog compose the resolved, ordered model."""
        record = SpecRecord(
            identifier="example",
            has_requirements=True,
            has_design=False,
            has_tasks=True,
            config=SpecConfig(workflow_type="design-first", spec_type="bugfix"),
            task_total=3,
            task_complete=3,
        )
        entry = SpecEntry(
            record=record,
            status="implemented",
            relationships=SpecRelationships(),
        )
        catalog = Catalog(entries=(entry,), status_counts={"implemented": 1})
        assert catalog.entries[0].status == "implemented"
        assert catalog.status_counts["implemented"] == 1
        assert catalog.entries[0].record.identifier == "example"


class TestReadConfig:
    """Unit tests for read_config (Requirements 1.4, 8.7)."""

    def test_returns_none_when_absent(self, tmp_path):
        """A missing Config_File yields None."""
        assert read_config(tmp_path / CONFIG_FILENAME) is None

    def test_reads_workflow_and_spec_type(self, tmp_path):
        """Valid JSON config yields the workflowType and specType values."""
        config_path = tmp_path / CONFIG_FILENAME
        config_path.write_text(
            json.dumps(
                {
                    "specId": "example",
                    "workflowType": "requirements-first",
                    "specType": "feature",
                }
            ),
            encoding="utf-8",
        )
        config = read_config(config_path)
        assert config == SpecConfig(
            workflow_type="requirements-first", spec_type="feature"
        )

    def test_missing_keys_become_none(self, tmp_path):
        """Absent workflowType/specType keys resolve to None."""
        config_path = tmp_path / CONFIG_FILENAME
        config_path.write_text(json.dumps({"specId": "example"}), encoding="utf-8")
        config = read_config(config_path)
        assert config == SpecConfig(workflow_type=None, spec_type=None)

    def test_invalid_json_raises_catalog_error_naming_spec_dir(self, tmp_path):
        """Non-JSON content raises CatalogError naming the offending spec dir."""
        spec_dir = tmp_path / "broken-spec"
        spec_dir.mkdir()
        config_path = spec_dir / CONFIG_FILENAME
        config_path.write_text("{ not valid json", encoding="utf-8")
        with pytest.raises(CatalogError) as exc_info:
            read_config(config_path)
        assert "broken-spec" in str(exc_info.value)

    def test_non_object_json_raises_catalog_error(self, tmp_path):
        """Valid JSON that is not an object raises CatalogError."""
        spec_dir = tmp_path / "list-spec"
        spec_dir.mkdir()
        config_path = spec_dir / CONFIG_FILENAME
        config_path.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(CatalogError) as exc_info:
            read_config(config_path)
        assert "list-spec" in str(exc_info.value)


class TestCountTaskCheckboxes:
    """Unit tests for count_task_checkboxes (Requirements 2.4, 2.5, 2.6)."""

    def test_absent_file_returns_zero(self, tmp_path):
        """A missing tasks.md yields (0, 0)."""
        assert count_task_checkboxes(tmp_path / "tasks.md") == (0, 0)

    def test_counts_incomplete_and_complete(self, tmp_path):
        """Mixed checkbox states are counted in total and complete."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text(
            "# Tasks\n\n- [ ] one\n- [x] two\n- [X] three\n", encoding="utf-8"
        )
        assert count_task_checkboxes(tasks_md) == (3, 2)

    def test_all_complete(self, tmp_path):
        """All-complete checkboxes report total == complete."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("- [x] a\n- [X] b\n", encoding="utf-8")
        assert count_task_checkboxes(tasks_md) == (2, 2)

    def test_indented_checkboxes_counted(self, tmp_path):
        """Indented (nested) checkbox lines are recognized after stripping."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("- [ ] parent\n  - [x] child\n", encoding="utf-8")
        assert count_task_checkboxes(tasks_md) == (2, 1)

    def test_prose_with_brackets_ignored(self, tmp_path):
        """Prose containing brackets is not counted as a checkbox."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text(
            "This mentions [ ] and array[0] and a [x] in text.\n"
            "See item [1] for details.\n"
            "- [ ] real task\n",
            encoding="utf-8",
        )
        assert count_task_checkboxes(tasks_md) == (1, 0)

    def test_no_checkboxes_returns_zero(self, tmp_path):
        """A tasks.md with prose but no checkboxes yields (0, 0)."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("# Plan\n\nSome description only.\n", encoding="utf-8")
        assert count_task_checkboxes(tasks_md) == (0, 0)


# Text values for config string fields: non-empty, exclude control chars that
# would not appear in real workflow/spec type values.
st_config_value = st.text(
    alphabet=st.characters(
        min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="\x7f"
    ),
    min_size=1,
    max_size=40,
)


@st.composite
def st_config(draw):
    """Generate a valid ``.config.kiro`` JSON object.

    The object always carries a ``specId`` and optionally carries
    ``workflowType`` and/or ``specType`` as string values. Omitting a key models
    an absent value, which read_config must surface as None.

    Returns:
        A dict suitable for JSON serialization into a ``.config.kiro`` file.
    """
    obj: dict[str, str] = {"specId": draw(st_config_value)}
    if draw(st.booleans()):
        obj["workflowType"] = draw(st_config_value)
    if draw(st.booleans()):
        obj["specType"] = draw(st_config_value)
    return obj


class TestConfigFaithfulRead:
    """Property 2: Config values are read faithfully (Requirements 1.4)."""

    # Feature: spec-catalog-index, Property 2: Config values are read faithfully
    @settings(max_examples=100)
    @given(config_obj=st_config())
    def test_config_values_read_faithfully(self, config_obj):
        """Parsed workflowType/specType equal the written values; absence is None."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / CONFIG_FILENAME
            config_path.write_text(json.dumps(config_obj), encoding="utf-8")

            config = read_config(config_path)

        assert config is not None
        assert config.workflow_type == config_obj.get("workflowType")
        assert config.spec_type == config_obj.get("specType")

    # Feature: spec-catalog-index, Property 2: Config values are read faithfully
    def test_absent_config_yields_none(self, tmp_path):
        """An absent Config_File yields None (the absence case of Property 2)."""
        assert read_config(tmp_path / CONFIG_FILENAME) is None


class TestDiscoverSpecs:
    """Unit tests for discover_specs (Requirements 1.1, 1.2, 1.3, 1.5, 1.6)."""

    def _make_spec(self, root, name, *, documents=(), config=None):
        """Materialize a spec directory with optional documents and config.

        Args:
            root: The specs root directory under which to create the spec.
            name: The spec directory name (identifier).
            documents: Iterable of Spec_Document filenames to create.
            config: Optional dict written as ``.config.kiro`` JSON.

        Returns:
            The created spec directory Path.
        """
        spec_dir = root / name
        spec_dir.mkdir()
        for doc in documents:
            (spec_dir / doc).write_text(f"# {doc}\n", encoding="utf-8")
        if config is not None:
            (spec_dir / CONFIG_FILENAME).write_text(
                json.dumps(config), encoding="utf-8"
            )
        return spec_dir

    def test_identifies_every_immediate_subdirectory(self, tmp_path):
        """Every immediate subdirectory becomes one SpecRecord (Req 1.1)."""
        self._make_spec(tmp_path, "alpha")
        self._make_spec(tmp_path, "beta")
        self._make_spec(tmp_path, "gamma")
        records = discover_specs(tmp_path)
        assert [r.identifier for r in records] == ["alpha", "beta", "gamma"]

    def test_ignores_loose_files(self, tmp_path):
        """Non-directory entries in the specs root are not treated as specs."""
        self._make_spec(tmp_path, "alpha")
        (tmp_path / "README.md").write_text("not a spec\n", encoding="utf-8")
        records = discover_specs(tmp_path)
        assert [r.identifier for r in records] == ["alpha"]

    def test_records_identifier_as_directory_name(self, tmp_path):
        """The identifier equals the directory name (Req 1.2)."""
        self._make_spec(tmp_path, "adaptive-pacing")
        records = discover_specs(tmp_path)
        assert records[0].identifier == "adaptive-pacing"

    def test_records_document_presence_flags(self, tmp_path):
        """Presence flags reflect exactly which documents exist (Req 1.3)."""
        self._make_spec(
            tmp_path, "full", documents=("requirements.md", "design.md", "tasks.md")
        )
        self._make_spec(tmp_path, "partial", documents=("requirements.md",))
        self._make_spec(tmp_path, "empty")
        records = {r.identifier: r for r in discover_specs(tmp_path)}

        full = records["full"]
        assert (full.has_requirements, full.has_design, full.has_tasks) == (
            True,
            True,
            True,
        )

        partial = records["partial"]
        assert (partial.has_requirements, partial.has_design, partial.has_tasks) == (
            True,
            False,
            False,
        )

        empty = records["empty"]
        assert (empty.has_requirements, empty.has_design, empty.has_tasks) == (
            False,
            False,
            False,
        )

    def test_records_parsed_config(self, tmp_path):
        """A present config is parsed into the record (Req 1.4 wiring)."""
        self._make_spec(
            tmp_path,
            "configured",
            config={
                "specId": "configured",
                "workflowType": "requirements-first",
                "specType": "feature",
            },
        )
        records = discover_specs(tmp_path)
        assert records[0].config == SpecConfig(
            workflow_type="requirements-first", spec_type="feature"
        )

    def test_config_absent_yields_none(self, tmp_path):
        """A spec without a config records None for config."""
        self._make_spec(tmp_path, "no-config", documents=("requirements.md",))
        records = discover_specs(tmp_path)
        assert records[0].config is None

    def test_records_task_checkbox_counts(self, tmp_path):
        """Task checkbox counts are captured from tasks.md."""
        spec_dir = self._make_spec(tmp_path, "with-tasks")
        (spec_dir / "tasks.md").write_text(
            "- [ ] one\n- [x] two\n- [X] three\n", encoding="utf-8"
        )
        records = discover_specs(tmp_path)
        assert records[0].task_total == 3  # brittle-allow: domain count, not suite count
        assert records[0].task_complete == 2

    def test_includes_empty_directory(self, tmp_path):
        """A directory with no documents and no config is still included (Req 1.5)."""
        self._make_spec(tmp_path, "barren")
        records = discover_specs(tmp_path)
        assert len(records) == 1
        record = records[0]
        assert record.identifier == "barren"
        assert record.config is None
        assert (record.has_requirements, record.has_design, record.has_tasks) == (
            False,
            False,
            False,
        )
        assert (record.task_total, record.task_complete) == (0, 0)

    def test_case_insensitive_ascending_order(self, tmp_path):
        """Records are sorted case-insensitively by identifier (Req 1.6)."""
        for name in ["Banana", "apple", "Cherry", "date"]:
            self._make_spec(tmp_path, name)
        records = discover_specs(tmp_path)
        assert [r.identifier for r in records] == [
            "apple",
            "Banana",
            "Cherry",
            "date",
        ]

    def test_raw_identifier_tiebreaker(self, tmp_path):
        """Identifiers equal under casefold sort by raw identifier (Req 1.6)."""
        # 'Spec' and 'spec' share a casefold key; raw ordering puts 'Spec' first
        # because uppercase letters sort before lowercase in code-point order.
        self._make_spec(tmp_path, "spec")
        self._make_spec(tmp_path, "Spec")
        records = discover_specs(tmp_path)
        assert [r.identifier for r in records] == ["Spec", "spec"]

    def test_propagates_invalid_json_config_error(self, tmp_path):
        """An invalid .config.kiro raises CatalogError naming the spec (Req 8.7)."""
        spec_dir = self._make_spec(tmp_path, "broken")
        (spec_dir / CONFIG_FILENAME).write_text("{ not json", encoding="utf-8")
        with pytest.raises(CatalogError) as exc_info:
            discover_specs(tmp_path)
        assert "broken" in str(exc_info.value)


# Identifiers for spec directory names: filesystem-safe, unique under casefold so
# distinct directories never collide on a case-insensitive filesystem.
st_spec_identifier = st.from_regex(r"[a-z][a-z0-9_-]{0,15}", fullmatch=True)


@st.composite
def st_spec_tree(draw):
    """Generate a plan for a random spec directory tree.

    The plan describes a set of spec directories (unique identifiers), the
    subset of ``SPEC_DOCUMENTS`` present in each, and a set of stray files
    placed at the specs root. The plan is later materialized into a temp dir
    and torn down with ``shutil.rmtree``.

    Returns:
        A dict mapping each spec identifier to the set of present document
        filenames, plus a ``_stray_root`` key listing loose filenames placed
        directly under the specs root (which must never be discovered as specs).
    """
    identifiers = draw(
        st.lists(st_spec_identifier, min_size=0, max_size=8, unique_by=str.casefold)
    )
    plan: dict[str, set[str]] = {}
    for identifier in identifiers:
        present = draw(
            st.sets(st.sampled_from(SPEC_DOCUMENTS), min_size=0, max_size=3)
        )
        plan[identifier] = present
    # Stray files at the specs root: loose files that are not directories and
    # therefore must be ignored by discovery.
    stray = draw(
        st.lists(
            st.from_regex(r"[a-z][a-z0-9_.-]{0,15}\.md", fullmatch=True),
            min_size=0,
            max_size=4,
            unique=True,
        )
    )
    plan["_stray_root"] = set(stray)
    return plan


def _materialize_spec_tree(specs_root: Path, plan: dict[str, set[str]]) -> set[str]:
    """Create the spec tree described by ``plan`` under ``specs_root``.

    Args:
        specs_root: The directory under which to create spec directories.
        plan: The plan produced by ``st_spec_tree`` (identifier -> doc filenames,
            plus ``_stray_root`` for loose root-level files).

    Returns:
        The set of spec identifiers (directory names) that should be discovered.
    """
    expected_ids: set[str] = set()
    for identifier, documents in plan.items():
        if identifier == "_stray_root":
            continue
        spec_dir = specs_root / identifier
        spec_dir.mkdir()
        expected_ids.add(identifier)
        for doc in documents:
            (spec_dir / doc).write_text(f"# {doc}\n", encoding="utf-8")
    # Stray files directly under the specs root must not be treated as specs.
    for stray_name in plan["_stray_root"]:
        # Skip a stray file whose name collides with a spec directory name.
        if (specs_root / stray_name).exists():
            continue
        (specs_root / stray_name).write_text("stray\n", encoding="utf-8")
    return expected_ids


class TestProperty1DiscoveryCompletenessAndFidelity:
    """Property 1: Discovery completeness and fidelity (Req 1.1, 1.2, 1.3).

    For any directory tree, the set of discovered spec identifiers equals
    exactly the names of the immediate subdirectories of the specs root, each
    record's identifier equals its source directory name, and each record's
    requirements/design/tasks presence flags match exactly which of those
    documents exist in that directory.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    # Feature: spec-catalog-index, Property 1: Discovery completeness and fidelity
    @given(plan=st_spec_tree())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_discovery_completeness_and_fidelity(self, plan):
        """Discovered ids and presence flags match the materialized tree exactly."""
        tmp = Path(tempfile.mkdtemp())
        try:
            specs_root = tmp / "specs"
            specs_root.mkdir()
            expected_ids = _materialize_spec_tree(specs_root, plan)

            records = discover_specs(specs_root)

            # Completeness: discovered identifiers equal exactly the immediate
            # subdirectory names (Req 1.1) and stray files are excluded.
            discovered_ids = {record.identifier for record in records}
            assert discovered_ids == expected_ids
            assert len(records) == len(expected_ids)

            # Fidelity: each record's identifier is its source directory name
            # (Req 1.2) and presence flags match exactly which docs exist (Req 1.3).
            for record in records:
                present = plan[record.identifier]
                assert (specs_root / record.identifier).is_dir()
                assert record.has_requirements is ("requirements.md" in present)
                assert record.has_design is ("design.md" in present)
                assert record.has_tasks is ("tasks.md" in present)
        finally:
            shutil.rmtree(tmp)


def _is_invalid_json(text: str) -> bool:
    """Return True when ``text`` is not parseable as JSON.

    Args:
        text: Candidate Config_File content.

    Returns:
        True when ``json.loads`` raises, i.e. the text is malformed JSON.
    """
    try:
        json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return True
    return False


# Text guaranteed (via filter) to be invalid JSON, used as malformed
# ``.config.kiro`` content. The explicit malformed templates seed common failure
# shapes; random text is filtered down to the invalid cases.
st_invalid_json_text = st.one_of(
    st.just("{ not valid json"),
    st.just("[1, 2,"),
    st.just("}{"),
    st.just("'single quotes only'"),
    st.just("{'key': 'value'}"),  # single quotes are not valid JSON
    st.just("{key: value}"),  # unquoted key
    st.just(""),  # empty file is not a JSON document
    st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),
        min_size=0,
        max_size=30,
    ),
).filter(_is_invalid_json)


@st.composite
def st_invalid_json_config(draw):
    """Generate a malformed ``.config.kiro`` placed in a named spec directory.

    Produces a plan describing one Spec_Directory whose Config_File holds invalid
    JSON, plus zero or more sibling specs whose configs are valid. The malformed
    config must drive a CatalogError naming the offending Spec_Directory even
    though the sibling specs would otherwise process cleanly.

    Returns:
        A ``(broken_id, broken_text, valid_ids)`` tuple where ``broken_id`` is
        the directory name carrying the malformed ``broken_text`` config and
        ``valid_ids`` are sibling spec directory names with no config file.
    """
    broken_id = draw(st_spec_identifier)
    broken_text = draw(st_invalid_json_text)
    valid_ids = set(
        draw(
            st.lists(
                st_spec_identifier, min_size=0, max_size=4, unique_by=str.casefold
            )
        )
    )
    valid_ids = {
        identifier
        for identifier in valid_ids
        if identifier.casefold() != broken_id.casefold()
    }
    return (broken_id, broken_text, sorted(valid_ids))


@st.composite
def st_dangling_metadata(draw):
    """Generate CatalogMetadata with at least one unresolved reference.

    Builds a CatalogMetadata whose ``status_overrides``, ``supersessions``, and
    ``related`` reference a mix of discovered ("known") and undiscovered
    ("dangling") identifiers, guaranteeing at least one dangling reference so the
    error condition is always present.

    Returns:
        A ``(metadata, known_ids)`` tuple where ``metadata`` references one or
        more identifiers absent from ``known_ids``.
    """
    known = set(
        draw(
            st.lists(
                st_spec_identifier, min_size=0, max_size=6, unique_by=str.casefold
            )
        )
    )
    dangling = set(
        draw(
            st.lists(
                st_spec_identifier, min_size=1, max_size=6, unique_by=str.casefold
            )
        )
    )
    known_folds = {identifier.casefold() for identifier in known}
    dangling = {
        identifier
        for identifier in dangling
        if identifier.casefold() not in known_folds
    }
    # Ensure at least one genuinely unresolved reference survives.
    assume(dangling)

    all_ids = sorted(known | dangling)
    forced_dangling = sorted(dangling)[0]

    # Always reference a guaranteed-dangling identifier via an override.
    overrides: dict[str, str] = {forced_dangling: "implemented"}
    extra_override_ids = draw(
        st.sets(st.sampled_from(all_ids), min_size=0, max_size=len(all_ids))
    )
    for identifier in extra_override_ids:
        overrides.setdefault(identifier, draw(st.sampled_from(STATUS_ORDER)))

    supersessions = tuple(
        draw(
            st.lists(
                st.tuples(st.sampled_from(all_ids), st.sampled_from(all_ids)),
                min_size=0,
                max_size=4,
            )
        )
    )
    related = tuple(
        draw(
            st.lists(
                st.tuples(st.sampled_from(all_ids), st.sampled_from(all_ids)),
                min_size=0,
                max_size=4,
            )
        )
    )

    metadata = CatalogMetadata(
        status_overrides=overrides,
        supersessions=supersessions,
        related=related,
    )
    return (metadata, known)


class TestProperty13DetectedErrorsForceExit1:
    """Property 13: Detected errors force exit code 1 (Req 3.5, 8.5, 8.7).

    Two independent error conditions must always be surfaced rather than
    silently swallowed: an invalid-JSON ``.config.kiro`` raises a CatalogError
    naming the offending Spec_Directory (the error report that drives exit 1,
    Req 8.7/8.5), and a metadata file with dangling references yields a
    non-empty unresolved-reference list (which drives exit 1, Req 3.5). Both
    hold even when the rest of the catalog could process cleanly.

    **Validates: Requirements 3.5, 8.5, 8.7**
    """

    # Feature: spec-catalog-index, Property 13: Detected errors force exit code 1
    @given(plan=st_invalid_json_config())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_invalid_json_config_raises_catalog_error_naming_spec(self, plan):
        """An invalid-JSON config raises CatalogError naming its spec directory."""
        broken_id, broken_text, valid_ids = plan
        tmp = Path(tempfile.mkdtemp())
        try:
            specs_root = tmp / "specs"
            specs_root.mkdir()

            # Sibling specs that would otherwise process cleanly.
            for valid_id in valid_ids:
                (specs_root / valid_id).mkdir()

            broken_dir = specs_root / broken_id
            broken_dir.mkdir()
            (broken_dir / CONFIG_FILENAME).write_text(broken_text, encoding="utf-8")

            # read_config surfaces the error naming the offending directory.
            with pytest.raises(CatalogError) as direct_exc:
                read_config(broken_dir / CONFIG_FILENAME)
            assert broken_id in str(direct_exc.value)

            # discover_specs propagates the same error even though valid sibling
            # specs could complete processing (the error forces the exit-1 path).
            with pytest.raises(CatalogError) as discover_exc:
                discover_specs(specs_root)
            assert broken_id in str(discover_exc.value)
        finally:
            shutil.rmtree(tmp)

    # Feature: spec-catalog-index, Property 13: Detected errors force exit code 1
    @settings(max_examples=100)
    @given(case=st_dangling_metadata())
    def test_dangling_metadata_refs_are_detected(self, case):
        """Dangling metadata references yield a non-empty unresolved list."""
        metadata, known_ids = case

        unresolved = validate_metadata_refs(metadata, known_ids)

        # Recompute the referenced identifiers the same way the generator does so
        # the assertion is independent of the function under test.
        referenced: set[str] = set(metadata.status_overrides)
        for superseding, superseded in metadata.supersessions:
            referenced.add(superseding)
            referenced.add(superseded)
        for first, second in metadata.related:
            referenced.add(first)
            referenced.add(second)
        expected = sorted(referenced - known_ids)

        # The error condition is detected (non-empty) and reported exactly: this
        # non-empty list is what drives the caller's exit-code-1 contract.
        assert unresolved == expected
        assert unresolved, "expected at least one unresolved reference"
        assert all(identifier not in known_ids for identifier in unresolved)


# Status_Value drawn from the enumerated STATUS_ORDER, used both for status
# overrides (which must be valid statuses) and for assertions.
st_status_value = st.sampled_from(STATUS_ORDER)


@st.composite
def st_spec_config(draw):
    """Generate a ``SpecConfig`` or ``None``.

    Each of ``workflow_type``/``spec_type`` is independently either a short
    string or ``None``, and the whole config is occasionally absent (``None``)
    to model a spec without a ``.config.kiro`` file.

    Returns:
        A ``SpecConfig`` instance, or ``None`` to model an absent config.
    """
    if draw(st.booleans()):
        return None
    workflow_type = draw(st.none() | st_config_value)
    spec_type = draw(st.none() | st_config_value)
    return SpecConfig(workflow_type=workflow_type, spec_type=spec_type)


@st.composite
def st_record(draw):
    """Generate an arbitrary ``SpecRecord``.

    Document-presence flags are independent booleans, and task-checkbox counts
    are constrained so ``task_complete`` never exceeds ``task_total`` (the
    realistic invariant emitted by ``count_task_checkboxes``), while still
    spanning the zero-total and all-complete edges that drive status derivation.

    Returns:
        A ``SpecRecord`` covering the full space of discovery signals.
    """
    task_total = draw(st.integers(min_value=0, max_value=12))
    task_complete = draw(st.integers(min_value=0, max_value=task_total))
    return SpecRecord(
        identifier=draw(st_spec_identifier),
        has_requirements=draw(st.booleans()),
        has_design=draw(st.booleans()),
        has_tasks=draw(st.booleans()),
        config=draw(st_spec_config()),
        task_total=task_total,
        task_complete=task_complete,
    )


@st.composite
def st_metadata(draw):
    """Generate arbitrary ``CatalogMetadata``.

    ``status_overrides`` maps identifiers to valid Status_Values (drawn from
    ``STATUS_ORDER``, as a real metadata file would supply), and supersession
    and related pairs reference random identifiers. The generated identifiers
    overlap the ``st_record`` identifier space, so overrides and supersessions
    sometimes apply to a generated record and sometimes do not.

    Returns:
        A ``CatalogMetadata`` instance with overrides, supersessions, and
        related pairs.
    """
    overrides = draw(
        st.dictionaries(
            keys=st_spec_identifier,
            values=st_status_value,
            min_size=0,
            max_size=4,
        )
    )
    supersessions = tuple(
        draw(
            st.lists(
                st.tuples(st_spec_identifier, st_spec_identifier),
                min_size=0,
                max_size=4,
            )
        )
    )
    related = tuple(
        draw(
            st.lists(
                st.tuples(st_spec_identifier, st_spec_identifier),
                min_size=0,
                max_size=4,
            )
        )
    )
    return CatalogMetadata(
        status_overrides=overrides,
        supersessions=supersessions,
        related=related,
    )


class TestProperty4StatusIsSingleEnumeratedValue:
    """Property 4: Status is exactly one enumerated value (Req 2.1).

    For any spec record and any metadata, status derivation assigns exactly one
    Status_Value drawn from {in-progress, implemented, superseded, abandoned,
    unknown}.

    **Validates: Requirements 2.1**
    """

    # Feature: spec-catalog-index, Property 4: Status is exactly one enumerated value
    @settings(max_examples=100)
    @given(record=st_record(), metadata=st_metadata())
    def test_status_is_always_in_status_order(self, record, metadata):
        """derive_status always returns a single value from STATUS_ORDER."""
        status = derive_status(record, metadata)
        assert status in STATUS_ORDER


# Tasks.md checkbox states that drive the level-3 precedence signal. Each state
# maps to the Status_Value derive_status produces when tasks.md is the deciding
# signal: empty -> unknown, complete -> implemented, incomplete -> in-progress.
_TASK_STATES = ("absent", "empty", "incomplete", "complete")


@st.composite
def st_status_scenario(draw):
    """Generate a status-derivation scenario with deliberately conflicting signals.

    Each precedence level is toggled independently so higher- and
    lower-precedence signals frequently coexist on the same spec (for example an
    explicit override AND a recorded supersession AND complete tasks AND present
    documents). Metadata also carries noise overrides/supersessions referencing
    other identifiers that must never apply to this spec. The expected status is
    computed from the fixed precedence ladder so the property can assert that the
    highest-precedence applicable signal always wins.

    Returns:
        A ``(record, metadata, expected_status)`` tuple where ``expected_status``
        is the Status_Value mandated by the fixed precedence ladder.
    """
    identifier = draw(st_spec_identifier)

    # Level 1 signal: optional explicit override for this spec (Req 2.2).
    has_override = draw(st.booleans())
    override_value = draw(st_status_value)

    # Level 2 signal: optional recorded supersession targeting this spec (Req 2.3).
    has_supersession = draw(st.booleans())

    # Level 3 signal: tasks.md presence and checkbox state (Req 2.4, 2.5).
    task_state = draw(st.sampled_from(_TASK_STATES))
    has_tasks = task_state != "absent"
    if task_state in ("absent", "empty"):
        task_total, task_complete = 0, 0
    elif task_state == "complete":
        task_total = draw(st.integers(min_value=1, max_value=12))
        task_complete = task_total
    else:  # incomplete
        task_total = draw(st.integers(min_value=1, max_value=12))
        task_complete = draw(st.integers(min_value=0, max_value=task_total - 1))

    # Level 4 signal: requirements.md / design.md presence (Req 2.7).
    has_requirements = draw(st.booleans())
    has_design = draw(st.booleans())

    record = SpecRecord(
        identifier=identifier,
        has_requirements=has_requirements,
        has_design=has_design,
        has_tasks=has_tasks,
        config=None,
        task_total=task_total,
        task_complete=task_complete,
    )

    # Build metadata carrying the chosen high-precedence signals for this spec,
    # plus noise referencing OTHER identifiers that must never apply to it.
    overrides: dict[str, str] = {}
    if has_override:
        overrides[identifier] = override_value
    supersessions: list[tuple[str, str]] = []
    if has_supersession:
        superseding = draw(st_spec_identifier)
        supersessions.append((superseding, identifier))

    noise_ids = draw(
        st.lists(st_spec_identifier, min_size=0, max_size=4, unique_by=str.casefold)
    )
    for noise_id in noise_ids:
        if noise_id.casefold() != identifier.casefold() and draw(st.booleans()):
            overrides.setdefault(noise_id, draw(st_status_value))
        # A noise supersession must never target this spec, or it would become a
        # genuine (rather than noise) signal and invalidate the expected status.
        target = draw(st_spec_identifier)
        if target.casefold() != identifier.casefold() and draw(st.booleans()):
            supersessions.append((noise_id, target))

    metadata = CatalogMetadata(
        status_overrides=overrides,
        supersessions=tuple(supersessions),
        related=(),
    )

    # Expected winner by the fixed precedence ladder (Req 2.8).
    if has_override:
        expected = override_value
    elif has_supersession:
        expected = "superseded"
    elif has_tasks:
        if task_total == 0:
            expected = "unknown"
        elif task_complete >= task_total:
            expected = "implemented"
        else:
            expected = "in-progress"
    elif has_requirements or has_design:
        expected = "in-progress"
    else:
        expected = "unknown"

    return (record, metadata, expected)


class TestProperty5StatusPrecedence:
    """Property 5: Status precedence (Req 2.2, 2.3, 2.4, 2.5, 2.7, 2.8).

    For any spec record and metadata, the derived status is determined by the
    highest-precedence applicable signal in the fixed order — explicit override,
    then recorded supersession, then tasks.md checkbox state (all complete ->
    implemented; any incomplete -> in-progress; present with no checkbox ->
    unknown), then document presence (requirements.md or design.md present ->
    in-progress), otherwise unknown — and a higher-precedence signal always
    overrides every lower-precedence one.

    **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7, 2.8**
    """

    # Feature: spec-catalog-index, Property 5: Status precedence
    @settings(max_examples=100)
    @given(scenario=st_status_scenario())
    def test_highest_precedence_signal_wins(self, scenario):
        """With conflicting signals present, the highest-precedence one wins."""
        record, metadata, expected = scenario
        assert derive_status(record, metadata) == expected

    # Feature: spec-catalog-index, Property 5: Status precedence
    @settings(max_examples=100)
    @given(scenario=st_status_scenario(), override_value=st_status_value)
    def test_override_dominates_every_lower_signal(self, scenario, override_value):
        """An explicit override wins regardless of supersession/task/doc signals."""
        record, metadata, _expected = scenario
        overrides = dict(metadata.status_overrides)
        overrides[record.identifier] = override_value
        forced = CatalogMetadata(
            status_overrides=overrides,
            supersessions=metadata.supersessions,
            related=metadata.related,
        )
        assert derive_status(record, forced) == override_value

    # Feature: spec-catalog-index, Property 5: Status precedence
    @settings(max_examples=100)
    @given(scenario=st_status_scenario())
    def test_supersession_dominates_task_and_document_signals(self, scenario):
        """A supersession wins over task/doc signals when no override applies."""
        record, metadata, _expected = scenario
        # Drop any override for this spec so the supersession is highest-precedence.
        overrides = {
            key: value
            for key, value in metadata.status_overrides.items()
            if key.casefold() != record.identifier.casefold()
        }
        supersessions = metadata.supersessions + (
            ("some-superseding-spec", record.identifier),
        )
        forced = CatalogMetadata(
            status_overrides=overrides,
            supersessions=supersessions,
            related=metadata.related,
        )
        assert derive_status(record, forced) == "superseded"


# A pool of distinct known spec identifiers over which the relationship
# strategies draw. Drawing endpoints from a fixed pool guarantees every
# referenced identifier is "known" and keeps relationship graphs dense enough to
# exercise reciprocity and symmetry. Uniqueness under casefold mirrors the
# discovery invariant (distinct directories never collide case-insensitively).
st_known_id_pool = st.lists(
    st_spec_identifier, min_size=2, max_size=8, unique_by=str.casefold
)


@st.composite
def st_supersessions(draw):
    """Generate directional supersession pairs over a pool of known ids.

    Each pair ``(superseding, superseded)`` has distinct endpoints drawn from a
    shared ``known`` pool, so every reciprocity assertion (the superseding spec
    lists the superseded under ``supersedes``; the superseded lists the
    superseding under ``superseded_by``) is unambiguous.

    Returns:
        A ``(supersessions, known_ids)`` tuple where ``supersessions`` is a tuple
        of directional ``(superseding, superseded)`` pairs with distinct
        endpoints and ``known_ids`` is the pool they were drawn from.
    """
    known = draw(st_known_id_pool)
    pairs = draw(
        st.lists(
            st.tuples(st.sampled_from(known), st.sampled_from(known)),
            min_size=0,
            max_size=8,
        )
    )
    supersessions = tuple(
        (superseding, superseded)
        for superseding, superseded in pairs
        if superseding != superseded
    )
    return (supersessions, known)


@st.composite
def st_related_groups(draw):
    """Generate mutually-related groups of known ids and their flattened pairs.

    Each group is a list of two or more distinct identifiers drawn from a shared
    ``known`` pool whose members are meant to be mutually related. The groups are
    flattened into unordered member pairs the way the curated metadata file
    stores related links, so the resolved relationships can be asserted both
    per-pair and as full per-group symmetry.

    Returns:
        A ``(groups, related_pairs, known_ids)`` tuple where ``groups`` is a list
        of distinct-member identifier groups, ``related_pairs`` is the flattened
        tuple of unordered ``(a, b)`` member pairs fed to
        ``CatalogMetadata.related``, and ``known_ids`` is the source pool.
    """
    known = draw(st_known_id_pool)
    groups = draw(
        st.lists(
            st.lists(
                st.sampled_from(known),
                min_size=2,
                max_size=len(known),
                unique=True,
            ),
            min_size=0,
            max_size=4,
        )
    )
    related_pairs: list[tuple[str, str]] = []
    for group in groups:
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                related_pairs.append((group[i], group[j]))
    return (groups, tuple(related_pairs), known)


class TestProperty6RelationshipReciprocityAndSymmetry:
    """Property 6: Relationship reciprocity and symmetry (Req 3.1, 3.2, 3.3, 3.4).

    For any metadata, every directional supersession from A to B causes A's entry
    to list B under ``supersedes`` and B's entry to list A under
    ``superseded_by``, and every related grouping causes each member to list
    every other member of the group as related. Relationship lists are sorted and
    deduplicated for determinism, and identifiers participating in no
    relationship are absent from the resolved mapping.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    # Feature: spec-catalog-index, Property 6: Relationship reciprocity and symmetry
    @settings(max_examples=100)
    @given(case=st_supersessions())
    def test_supersession_reciprocity(self, case):
        """Each A->B supersession lists B under A.supersedes and A under B.superseded_by."""
        supersessions, _known = case
        metadata = CatalogMetadata(
            status_overrides={},
            supersessions=supersessions,
            related=(),
        )

        result = resolve_relationships(metadata)

        for superseding, superseded in supersessions:
            assert superseding in result
            assert superseded in result
            assert superseded in result[superseding].supersedes
            assert superseding in result[superseded].superseded_by

        # Only participating identifiers appear in the mapping (Req 3.1, 3.2):
        # specs in no relationship are absent.
        participating = {a for a, _ in supersessions} | {b for _, b in supersessions}
        assert set(result) == participating

        # Determinism (Req 3.3): each list is sorted and deduplicated, and no
        # spurious related links are introduced by supersessions.
        for rels in result.values():
            assert list(rels.supersedes) == sorted(set(rels.supersedes))
            assert list(rels.superseded_by) == sorted(set(rels.superseded_by))
            assert rels.related == ()

    # Feature: spec-catalog-index, Property 6: Relationship reciprocity and symmetry
    @settings(max_examples=100)
    @given(case=st_related_groups())
    def test_related_group_symmetry(self, case):
        """Every related pair is symmetric and each group is fully connected."""
        groups, related_pairs, _known = case
        metadata = CatalogMetadata(
            status_overrides={},
            supersessions=(),
            related=related_pairs,
        )

        result = resolve_relationships(metadata)

        # Per-pair symmetry (Req 3.4): each member lists the other as related.
        for first, second in related_pairs:
            assert second in result[first].related
            assert first in result[second].related

        # Full group symmetry (Req 3.4): every member lists every other member.
        for group in groups:
            for member in group:
                for other in group:
                    if other != member:
                        assert other in result[member].related

        # Determinism (Req 3.3): related lists are sorted and deduplicated, and
        # supersession lists are untouched by related links.
        for rels in result.values():
            assert list(rels.related) == sorted(set(rels.related))
            assert rels.supersedes == ()
            assert rels.superseded_by == ()

        # Only participating identifiers appear in the mapping.
        participating = {a for a, _ in related_pairs} | {b for _, b in related_pairs}
        assert set(result) == participating


@st.composite
def st_catalog(draw):
    """Generate a fully-resolved, internally consistent ``Catalog``.

    Produces a random set of discovered ``SpecRecord``s (unique identifiers
    under casefold, mirroring the discovery invariant that distinct directories
    never collide case-insensitively) plus a ``CatalogMetadata`` whose status
    overrides, supersessions, and related pairs all reference those generated
    identifiers, then composes them through ``build_catalog``. Building via
    ``build_catalog`` guarantees the result is internally consistent — entries
    are ordered, ``status_counts`` is keyed over ``STATUS_ORDER`` and totals the
    records, and relationships are the reciprocal, sorted links that
    ``render_index``/``render_summary`` expect. Because metadata only references
    real identifiers, every override and relationship actually attaches to an
    entry, exercising the rendering paths densely.

    This strategy is reused by the rendering, status-count, summary, and drift
    properties (Properties 7, 8, 9, 12).

    Returns:
        A ``Catalog`` built from generated records and metadata.
    """
    identifiers = draw(
        st.lists(st_spec_identifier, min_size=0, max_size=8, unique_by=str.casefold)
    )

    records: list[SpecRecord] = []
    for identifier in identifiers:
        task_total = draw(st.integers(min_value=0, max_value=12))
        task_complete = draw(st.integers(min_value=0, max_value=task_total))
        records.append(
            SpecRecord(
                identifier=identifier,
                has_requirements=draw(st.booleans()),
                has_design=draw(st.booleans()),
                has_tasks=draw(st.booleans()),
                config=draw(st_spec_config()),
                task_total=task_total,
                task_complete=task_complete,
            )
        )

    if identifiers:
        overrides = draw(
            st.dictionaries(
                keys=st.sampled_from(identifiers),
                values=st_status_value,
                min_size=0,
                max_size=min(4, len(identifiers)),
            )
        )
        supersessions = tuple(
            (superseding, superseded)
            for superseding, superseded in draw(
                st.lists(
                    st.tuples(
                        st.sampled_from(identifiers), st.sampled_from(identifiers)
                    ),
                    min_size=0,
                    max_size=6,
                )
            )
            if superseding != superseded
        )
        related = tuple(
            (first, second)
            for first, second in draw(
                st.lists(
                    st.tuples(
                        st.sampled_from(identifiers), st.sampled_from(identifiers)
                    ),
                    min_size=0,
                    max_size=6,
                )
            )
            if first != second
        )
    else:
        overrides, supersessions, related = {}, (), ()

    metadata = CatalogMetadata(
        status_overrides=overrides,
        supersessions=supersessions,
        related=related,
    )
    return build_catalog(records, metadata)


def _entry_block(rendered: str, identifier: str) -> str:
    """Extract the rendered Spec_Index block for a single spec identifier.

    Finds the exact ``### {identifier}`` heading line and returns it together
    with every following line up to (but excluding) the next ``### `` heading.
    Exact line matching distinguishes identifiers that are substrings of one
    another (for example ``a`` versus ``ab``).

    Args:
        rendered: The full rendered Spec_Index string.
        identifier: The spec identifier whose entry block to extract.

    Returns:
        The lines of that spec's entry block joined by newlines.
    """
    lines = rendered.split("\n")
    start = None
    for index, line in enumerate(lines):
        if line == f"### {identifier}":
            start = index
            break
    assert start is not None, f"no entry heading for {identifier!r}"
    block = [lines[start]]
    for line in lines[start + 1:]:
        if line.startswith("### "):
            break
        block.append(line)
    return "\n".join(block)


class TestProperty7IndexRenderingCompleteness:
    """Property 7: Index rendering completeness (Req 4.2, 4.3, 4.5).

    For any catalog, the rendered Spec_Index contains, for every spec, an entry
    showing the spec identifier, its status, its specType, its workflowType, a
    link to its Spec_Directory, and all of its recorded supersession and related
    identifiers. Missing specType/workflowType render as the placeholder
    ``unknown``.

    **Validates: Requirements 4.2, 4.3, 4.5**
    """

    # Feature: spec-catalog-index, Property 7: Index rendering completeness
    @settings(max_examples=100)
    @given(catalog=st_catalog())
    def test_index_contains_every_spec_entry(self, catalog):
        """Each spec's identifier, status, type, workflow, link, and relationships appear."""
        rendered = render_index(catalog)

        for entry in catalog.entries:
            record = entry.record
            identifier = record.identifier
            block = _entry_block(rendered, identifier)

            # Identifier heading (Req 4.2).
            assert block.startswith(f"### {identifier}")

            # Status (Req 4.2).
            assert f"- Status: {entry.status}" in block

            # specType / workflowType, with the "unknown" placeholder when the
            # config or the field is absent (Req 4.2).
            spec_type = record.config.spec_type if record.config else None
            workflow_type = record.config.workflow_type if record.config else None
            expected_type = spec_type if spec_type else _MISSING_FIELD
            expected_workflow = workflow_type if workflow_type else _MISSING_FIELD
            assert f"- Type: {expected_type}" in block
            assert f"- Workflow: {expected_workflow}" in block

            # Link to the Spec_Directory (Req 4.5).
            directory = f".kiro/specs/{identifier}/"
            assert f"- Directory: [{directory}]({directory})" in block

            # All recorded supersession and related identifiers (Req 4.3).
            relationships = entry.relationships
            if relationships.supersedes:
                assert (
                    f"- Supersedes: {', '.join(relationships.supersedes)}" in block
                )
                for superseded in relationships.supersedes:
                    assert superseded in block
            if relationships.superseded_by:
                assert (
                    f"- Superseded by: {', '.join(relationships.superseded_by)}"
                    in block
                )
                for superseding in relationships.superseded_by:
                    assert superseding in block
            if relationships.related:
                assert f"- Related: {', '.join(relationships.related)}" in block
                for related_id in relationships.related:
                    assert related_id in block


def _status_summary_counts(rendered: str) -> dict[str, int]:
    """Parse the rendered Status Summary section into a status -> count map.

    Extracts the lines between the ``## Status Summary`` heading and the
    following ``## Specs`` heading, where each line has the form
    ``- <status>: <count>``, and returns them as a mapping. Scoping to the
    summary section avoids matching the per-entry ``- Status: <value>`` lines in
    the ``## Specs`` section.

    Args:
        rendered: The full rendered Spec_Index string.

    Returns:
        A dict mapping each Status_Value to its rendered integer count.
    """
    lines = rendered.split("\n")
    start = lines.index("## Status Summary")
    end = lines.index("## Specs", start)
    counts: dict[str, int] = {}
    for line in lines[start + 1:end]:
        if not line.startswith("- "):
            continue
        status, _, count = line[2:].partition(": ")
        counts[status] = int(count)
    return counts


class TestProperty8StatusCountsAccurateAndTotal:
    """Property 8: Status counts are accurate and total (Req 4.4).

    For any catalog, each rendered status-group count equals the actual number
    of specs with that status, and the counts sum to the total number of
    discovered specs.

    **Validates: Requirements 4.4**
    """

    # Feature: spec-catalog-index, Property 8: Status counts are accurate and total
    @settings(max_examples=100)
    @given(catalog=st_catalog())
    def test_status_counts_accurate_and_total(self, catalog):
        """Each rendered count equals the actual tally and the counts sum to total."""
        rendered = render_index(catalog)
        rendered_counts = _status_summary_counts(rendered)

        # Every Status_Value in STATUS_ORDER is rendered exactly once.
        assert set(rendered_counts) == set(STATUS_ORDER)

        # Each rendered count equals the actual number of entries with that status.
        for status in STATUS_ORDER:
            actual = sum(
                1 for entry in catalog.entries if entry.status == status
            )
            assert rendered_counts[status] == actual

        # The counts sum to the total number of discovered specs.
        assert sum(rendered_counts.values()) == len(catalog.entries)


# Mixed-case spec identifiers: like st_spec_identifier but the alphabet spans
# both cases so the list genuinely exercises case-insensitive ordering. Unique
# under casefold mirrors the discovery invariant (distinct directories never
# collide on a case-insensitive filesystem), so the sort key never ties on
# casefold alone except via the raw-identifier tiebreaker.
st_mixed_case_identifier = st.from_regex(
    r"[A-Za-z][A-Za-z0-9_-]{0,15}", fullmatch=True
)


@st.composite
def st_identifiers(draw):
    """Generate a list of mixed-case, casefold-unique spec identifiers.

    Identifiers may contain uppercase and lowercase letters so the resulting
    catalog ordering must honor a case-insensitive sort rather than a naive
    code-point sort. Uniqueness under ``str.casefold`` mirrors the discovery
    invariant that distinct spec directories never collide case-insensitively.

    Returns:
        A list of identifier strings, unique under casefold, spanning mixed case.
    """
    return draw(
        st.lists(
            st_mixed_case_identifier,
            min_size=0,
            max_size=8,
            unique_by=str.casefold,
        )
    )


def _index_heading_order(rendered: str) -> list[str]:
    """Extract the order of ``### <identifier>`` headings from a Spec_Index.

    Args:
        rendered: The full rendered Spec_Index string.

    Returns:
        The spec identifiers in the order their entry headings appear.
    """
    headings: list[str] = []
    for line in rendered.split("\n"):
        if line.startswith("### "):
            headings.append(line[len("### "):])
    return headings


class TestProperty3CaseInsensitiveOrdering:
    """Property 3: Case-insensitive ascending ordering (Req 1.6, 5.4).

    For any set of mixed-case unique spec identifiers, both the rendered
    Spec_Index entry order and the machine-readable Catalog_Summary entry order
    are case-insensitive ascending by identifier, using the raw identifier as a
    deterministic tiebreaker for identifiers that are equal under casefold.

    **Validates: Requirements 1.6, 5.4**
    """

    # Feature: spec-catalog-index, Property 3: Case-insensitive ascending ordering
    @settings(max_examples=100)
    @given(identifiers=st_identifiers())
    def test_index_and_summary_orders_are_case_insensitive_ascending(
        self, identifiers
    ):
        """Index headings and summary specs follow case-insensitive ascending order."""
        records = [
            SpecRecord(
                identifier=identifier,
                has_requirements=False,
                has_design=False,
                has_tasks=False,
                config=None,
                task_total=0,
                task_complete=0,
            )
            for identifier in identifiers
        ]
        catalog = build_catalog(records, CatalogMetadata.empty())

        expected_order = sorted(
            identifiers, key=lambda identifier: (identifier.casefold(), identifier)
        )

        # Rendered index entry order (Req 1.6).
        assert _index_heading_order(render_index(catalog)) == expected_order

        # Machine-readable summary entry order (Req 5.4): specs serialize as a
        # list under the "specs" key, in catalog order.
        summary = json.loads(render_summary(catalog))
        summary_order = [spec["identifier"] for spec in summary["specs"]]
        assert summary_order == expected_order


class TestProperty9SummaryRoundTrip:
    """Property 9: Summary serialization round-trip (Req 5.2).

    For any catalog, parsing the JSON produced by ``render_summary`` back with
    ``json.loads`` yields, for every spec, fields that match the in-memory model
    exactly: identifier, status, specType (config.spec_type or null),
    workflowType (config.workflow_type or null), the document-presence flags,
    and the recorded supersedes/superseded_by/related relationships.

    **Validates: Requirements 5.2**
    """

    # Feature: spec-catalog-index, Property 9: Summary serialization round-trip
    @settings(max_examples=100)
    @given(catalog=st_catalog())
    def test_summary_round_trips_every_spec(self, catalog):
        """Parsed summary fields match the in-memory model for every spec."""
        parsed = json.loads(render_summary(catalog))

        # The parsed summary lists one spec object per catalog entry, in order.
        parsed_specs = parsed["specs"]
        assert [spec["identifier"] for spec in parsed_specs] == [
            entry.record.identifier for entry in catalog.entries
        ]

        for entry, parsed_spec in zip(catalog.entries, parsed_specs):
            record = entry.record
            config = record.config

            # Identifier and derived status (Req 5.2).
            assert parsed_spec["identifier"] == record.identifier
            assert parsed_spec["status"] == entry.status

            # specType / workflowType serialize as the config value or null
            # (parsed back as None) when the config or the field is absent.
            expected_spec_type = config.spec_type if config else None
            expected_workflow_type = config.workflow_type if config else None
            assert parsed_spec["specType"] == expected_spec_type
            assert parsed_spec["workflowType"] == expected_workflow_type

            # Document-presence flags (Req 5.2).
            assert parsed_spec["documents"] == {
                "requirements": record.has_requirements,
                "design": record.has_design,
                "tasks": record.has_tasks,
            }

            # Recorded relationships round-trip as lists (Req 5.2).
            relationships = entry.relationships
            assert parsed_spec["relationships"] == {
                "supersedes": list(relationships.supersedes),
                "superseded_by": list(relationships.superseded_by),
                "related": list(relationships.related),
            }


@pytest.mark.slow
class TestProperty10DeterministicGeneration:
    """Property 10: Deterministic, byte-identical generation (Req 7.1).

    For any spec directory tree and any metadata, generating the Spec_Index over
    unchanged inputs produces byte-identical output every time. Running the full
    pure pipeline (``discover_specs`` -> ``build_catalog`` -> ``render_index``)
    twice over the same materialized tree and the same metadata yields the exact
    same bytes, with no dependence on dictionary/set iteration order, filesystem
    enumeration order, or other run-to-run nondeterminism.

    **Validates: Requirements 7.1**
    """

    # Feature: spec-catalog-index, Property 10: Deterministic, byte-identical generation
    @given(plan=st_spec_tree(), metadata=st_metadata())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_generation_is_byte_identical_over_unchanged_inputs(self, plan, metadata):
        """Two generations over the same tree and metadata are byte-identical."""
        tmp = Path(tempfile.mkdtemp())
        try:
            specs_root = tmp / "specs"
            specs_root.mkdir()
            _materialize_spec_tree(specs_root, plan)

            # First generation over the unchanged inputs.
            first = render_index(
                build_catalog(discover_specs(specs_root), metadata)
            ).encode("utf-8")

            # Second generation over the exact same, unchanged inputs.
            second = render_index(
                build_catalog(discover_specs(specs_root), metadata)
            ).encode("utf-8")

            assert first == second
        finally:
            shutil.rmtree(tmp)


def _snapshot_tree(root: Path) -> dict[str, str]:
    """Map every file under ``root`` to the sha256 of its bytes.

    The mapping is keyed by each file's path relative to ``root`` so the
    snapshot captures both the set of files present and their exact contents.
    Comparing two snapshots therefore detects any created, deleted, or modified
    file anywhere in the tree.

    Args:
        root: The directory tree to snapshot.

    Returns:
        A dict mapping each relative file path (as a POSIX-style string) to the
        hex sha256 digest of that file's contents.
    """
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            snapshot[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


class TestProperty11StrictlyReadOnly:
    """Property 11: Strictly read-only over the spec catalog (Req 7.2-7.4, 6.1).

    The generator must never mutate the spec catalog it scans. For any spec
    directory tree, a write run leaves every spec directory and Spec_Document
    byte-identical (Req 7.2, 7.3, 7.4) and creates or modifies only the
    configured index and summary output paths. A subsequent Drift_Check_Mode
    (``--check``) run writes nothing at all (Req 6.1): neither the spec catalog
    nor the previously written index/summary files change.

    **Validates: Requirements 7.2, 7.3, 7.4, 6.1**
    """

    # Feature: spec-catalog-index, Property 11: Strictly read-only over the spec catalog
    @given(plan=st_spec_tree())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_write_and_check_runs_are_read_only_over_specs(self, plan):
        """Write and --check runs leave the spec catalog byte-identical."""
        tmp = Path(tempfile.mkdtemp())
        try:
            specs_root = tmp / "specs"
            specs_root.mkdir()
            _materialize_spec_tree(specs_root, plan)

            # Outputs live OUTSIDE the specs root so any write into the specs
            # tree would show up as a change in its snapshot. An absent metadata
            # path keeps relationships empty and avoids touching repo files.
            out_dir = tmp / "out"
            out_dir.mkdir()
            index_path = out_dir / "SPEC_CATALOG.md"
            summary_path = out_dir / "summary.json"
            metadata_path = tmp / "absent-metadata.yaml"

            specs_before = _snapshot_tree(specs_root)

            # Write run: render the index and summary outside the specs root.
            exit_code = main(
                [
                    "--specs-root",
                    str(specs_root),
                    "--output",
                    str(index_path),
                    "--summary",
                    str(summary_path),
                    "--metadata",
                    str(metadata_path),
                ]
            )
            assert exit_code == 0

            # The spec catalog is byte-identical after the write run: same set of
            # files, same contents (Req 7.2, 7.3, 7.4).
            assert _snapshot_tree(specs_root) == specs_before

            # Only the configured index and summary paths were created, and only
            # outside the specs root (Req 7.2).
            assert _snapshot_tree(out_dir) == {
                index_path.name: hashlib.sha256(
                    index_path.read_bytes()
                ).hexdigest(),
                summary_path.name: hashlib.sha256(
                    summary_path.read_bytes()
                ).hexdigest(),
            }

            # Snapshot the freshly written outputs to prove --check writes nothing.
            index_digest = hashlib.sha256(index_path.read_bytes()).hexdigest()
            summary_digest = hashlib.sha256(summary_path.read_bytes()).hexdigest()
            specs_before_check = _snapshot_tree(specs_root)

            # Drift_Check_Mode run over the in-sync index: writes nothing (Req 6.1).
            check_code = main(
                [
                    "--specs-root",
                    str(specs_root),
                    "--output",
                    str(index_path),
                    "--metadata",
                    str(metadata_path),
                    "--check",
                ]
            )
            assert check_code == 0

            # The spec catalog is still unchanged after --check (Req 7.2-7.4).
            assert _snapshot_tree(specs_root) == specs_before_check
            # --check wrote nothing: the index and summary are untouched (Req 6.1).
            assert hashlib.sha256(index_path.read_bytes()).hexdigest() == index_digest
            assert summary_path.exists()
            assert (
                hashlib.sha256(summary_path.read_bytes()).hexdigest()
                == summary_digest
            )
        finally:
            shutil.rmtree(tmp)


class TestProperty12DriftDetection:
    """Property 12: Drift detection (Req 6.2, 6.3, 6.5).

    A freshly generated Spec_Index is in sync with the catalog it was generated
    from, so Drift_Check_Mode exits 0 (Req 6.2). Once the committed index
    content is mutated, or the spec set under the Specs_Root changes (a spec
    directory is added or removed), the committed index no longer matches the
    freshly generated output, so Drift_Check_Mode reports the index as out of
    sync and exits 1 (Req 6.3, 6.5). Drift_Check_Mode itself writes nothing: the
    committed index file is byte-identical before and after the check run.

    **Validates: Requirements 6.2, 6.3, 6.5**
    """

    # Feature: spec-catalog-index, Property 12: Drift detection
    @given(
        plan=st_spec_tree(),
        mutation=st.sampled_from(("index_content", "add_spec", "remove_spec")),
        new_identifier=st_spec_identifier,
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_check_detects_index_or_spec_set_drift(
        self, plan, mutation, new_identifier
    ):
        """In-sync --check exits 0; after a mutation --check exits 1 and writes nothing."""
        tmp = Path(tempfile.mkdtemp())
        try:
            specs_root = tmp / "specs"
            specs_root.mkdir()
            expected_ids = _materialize_spec_tree(specs_root, plan)

            # Outputs live OUTSIDE the specs root; an absent metadata path keeps
            # relationships empty and avoids touching repo files.
            out_dir = tmp / "out"
            out_dir.mkdir()
            index_path = out_dir / "SPEC_CATALOG.md"
            metadata_path = tmp / "absent-metadata.yaml"

            base_args = [
                "--specs-root",
                str(specs_root),
                "--output",
                str(index_path),
                "--metadata",
                str(metadata_path),
            ]
            check_args = base_args + ["--check"]

            # Write the freshly generated index, then --check is in sync (Req 6.2).
            assert main(base_args) == 0
            assert main(check_args) == 0

            # Apply exactly one Hypothesis-chosen mutation that must induce drift.
            if mutation == "index_content":
                # Mutate the committed index content: appended bytes guarantee the
                # committed index can no longer match the freshly generated output.
                index_path.write_bytes(
                    index_path.read_bytes() + b"\n<!-- injected drift -->\n"
                )
            elif mutation == "add_spec":
                # Add a brand-new spec directory whose identifier is unique under
                # casefold so it is genuinely new to the catalog (Req 6.5).
                assume(
                    new_identifier.casefold()
                    not in {identifier.casefold() for identifier in expected_ids}
                )
                (specs_root / new_identifier).mkdir()
            else:  # remove_spec
                # Remove an existing spec directory; skip when the tree is empty
                # since there is nothing to remove (Req 6.5).
                assume(expected_ids)
                victim = sorted(expected_ids)[0]
                shutil.rmtree(specs_root / victim)

            # Snapshot the committed index immediately before the drift check to
            # prove --check writes nothing regardless of which path mutated it.
            committed_before_check = index_path.read_bytes()

            # --check now detects the drift and exits 1 (Req 6.3, 6.5).
            assert main(check_args) == 1

            # --check wrote nothing: the committed index is byte-identical (the
            # check run never writes).
            assert index_path.read_bytes() == committed_before_check
        finally:
            shutil.rmtree(tmp)


class TestEdgeCases:
    """Example-based edge-case unit tests (Req 1.5, 2.6, 3.6, 6.4).

    These complement the property suite with concrete boundary scenarios that
    pin down behavior the design calls out explicitly: an empty spec directory
    is still listed as ``unknown``, a ``tasks.md`` carrying only prose resolves
    to ``unknown``, an absent metadata file produces a derived-only catalog with
    no relationships, and ``--check`` against a missing index reports the
    missing file and exits 1.
    """

    def _make_spec(self, root, name, *, documents=(), config=None):
        """Materialize a spec directory with optional documents and config.

        Args:
            root: The specs root directory under which to create the spec.
            name: The spec directory name (identifier).
            documents: Iterable of Spec_Document filenames to create.
            config: Optional dict written as ``.config.kiro`` JSON.

        Returns:
            The created spec directory Path.
        """
        spec_dir = root / name
        spec_dir.mkdir()
        for doc in documents:
            (spec_dir / doc).write_text(f"# {doc}\n", encoding="utf-8")
        if config is not None:
            (spec_dir / CONFIG_FILENAME).write_text(
                json.dumps(config), encoding="utf-8"
            )
        return spec_dir

    def test_empty_directory_is_listed_with_unknown_status(self, tmp_path):
        """An empty spec directory is discovered and resolves to ``unknown`` (Req 1.5)."""
        self._make_spec(tmp_path, "barren")

        records = discover_specs(tmp_path)
        assert len(records) == 1
        record = records[0]
        assert record.identifier == "barren"

        # With no documents and no config, status derivation yields ``unknown``.
        assert derive_status(record, CatalogMetadata.empty()) == "unknown"

        # The empty directory still appears as an entry in the composed catalog.
        catalog = build_catalog(records, CatalogMetadata.empty())
        identifiers = [entry.record.identifier for entry in catalog.entries]
        assert identifiers == ["barren"]
        assert catalog.entries[0].status == "unknown"
        assert catalog.status_counts["unknown"] == 1

    def test_tasks_md_with_prose_only_resolves_to_unknown(self, tmp_path):
        """A ``tasks.md`` with prose but no checkbox resolves to ``unknown`` (Req 2.6)."""
        spec_dir = self._make_spec(tmp_path, "prose-only")
        (spec_dir / "tasks.md").write_text(
            "# Plan\n\nThis describes work but lists no checkboxes.\n"
            "See item [1] and array[0] for context.\n",
            encoding="utf-8",
        )

        records = discover_specs(tmp_path)
        record = records[0]

        # tasks.md is present but contains no Task_Checkbox lines.
        assert record.has_tasks is True
        assert (record.task_total, record.task_complete) == (0, 0)

        # Present tasks.md with zero checkboxes yields ``unknown`` (Req 2.6).
        assert derive_status(record, CatalogMetadata.empty()) == "unknown"

    def test_absent_metadata_yields_derived_only_empty_relationships(self, tmp_path):
        """An absent metadata file gives an empty CatalogMetadata and no links (Req 3.6)."""
        missing_metadata = tmp_path / "absent-spec-catalog.yaml"
        assert not missing_metadata.exists()

        metadata = load_metadata(missing_metadata)

        # Absent metadata is equivalent to CatalogMetadata.empty(): derived-only.
        assert metadata == CatalogMetadata.empty()
        assert metadata.status_overrides == {}
        assert metadata.supersessions == ()
        assert metadata.related == ()

        # A catalog built with absent metadata records no relationships at all.
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        self._make_spec(specs_root, "beta", documents=("tasks.md",))
        records = discover_specs(specs_root)

        catalog = build_catalog(records, metadata)
        for entry in catalog.entries:
            assert entry.relationships == SpecRelationships()
            assert entry.relationships.supersedes == ()
            assert entry.relationships.superseded_by == ()
            assert entry.relationships.related == ()

    def test_check_with_missing_index_reports_and_exits_1(self, tmp_path, capsys):
        """``--check`` with no committed index reports the missing file and exits 1 (Req 6.4)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))

        missing_index = tmp_path / "SPEC_CATALOG.md"
        missing_metadata = tmp_path / "absent-metadata.yaml"
        assert not missing_index.exists()

        exit_code = main(
            [
                "--specs-root",
                str(specs_root),
                "--output",
                str(missing_index),
                "--metadata",
                str(missing_metadata),
                "--check",
            ]
        )

        # Drift_Check_Mode against an absent index reports drift and exits 1.
        assert exit_code == 1

        # The error names the missing index and routes to standard error (Req 6.4).
        captured = capsys.readouterr()
        assert "missing" in captured.err
        assert str(missing_index) in captured.err

        # --check never writes: the index is still absent afterward.
        assert not missing_index.exists()


class TestCliAndIo:
    """CLI and I/O example unit tests (Req 4.1, 4.6, 5.1, 5.3, 5.5, 8.1, 8.2, 8.6, 8.8, 9.1, 9.2).

    These pin down the concrete I/O behavior of ``main`` that the property
    suite does not exercise directly: write mode creates the index at the
    configured path and exits 0, the provenance banner heads the file, the
    optional ``--summary`` writes valid JSON (and is absent when omitted), an
    uncollectable summary field skips the summary and exits 1, the
    ``--specs-root``/``--output``/``--check`` flags are wired through, missing or
    non-directory specs roots and malformed metadata exit 1, and the default
    index path lives under ``.kiro/`` rather than the distributed
    ``senzing-bootcamp/`` tree.

    Every ``main`` invocation points ``--metadata`` at a nonexistent path so the
    repository's real ``.kiro/spec-catalog.yaml`` is never picked up and the
    derived-only path is exercised deterministically.
    """

    _PROVENANCE_BANNER = (
        "<!-- Generated by generate_spec_catalog.py. "
        "Do not edit by hand; regenerate. -->"
    )

    def _make_spec(self, root, name, *, documents=(), config=None, tasks_text=None):
        """Materialize a spec directory with optional documents and config.

        Args:
            root: The specs root directory under which to create the spec.
            name: The spec directory name (identifier).
            documents: Iterable of Spec_Document filenames to create.
            config: Optional dict written as ``.config.kiro`` JSON.
            tasks_text: Optional explicit ``tasks.md`` content; when given, a
                ``tasks.md`` is written with this body regardless of ``documents``.

        Returns:
            The created spec directory Path.
        """
        spec_dir = root / name
        spec_dir.mkdir()
        for doc in documents:
            (spec_dir / doc).write_text(f"# {doc}\n", encoding="utf-8")
        if tasks_text is not None:
            (spec_dir / "tasks.md").write_text(tasks_text, encoding="utf-8")
        if config is not None:
            (spec_dir / CONFIG_FILENAME).write_text(
                json.dumps(config), encoding="utf-8"
            )
        return spec_dir

    def _run(self, specs_root, output, tmp_path, *, summary=None, check=False):
        """Invoke ``main`` with a nonexistent metadata path and given flags.

        Args:
            specs_root: Value for ``--specs-root``.
            output: Value for ``--output``.
            tmp_path: Test temp dir used to derive a nonexistent metadata path.
            summary: Optional value for ``--summary``.
            check: Whether to pass ``--check``.

        Returns:
            The integer exit code returned by ``main``.
        """
        missing_metadata = tmp_path / "absent-metadata.yaml"
        argv = [
            "--specs-root",
            str(specs_root),
            "--output",
            str(output),
            "--metadata",
            str(missing_metadata),
        ]
        if summary is not None:
            argv.extend(["--summary", str(summary)])
        if check:
            argv.append("--check")
        return main(argv)

    def test_write_mode_creates_index_and_exits_0(self, tmp_path):
        """Write mode writes the index to the configured path and exits 0 (Req 4.1)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(
            specs_root, "alpha", documents=("requirements.md", "design.md")
        )
        output = tmp_path / "SPEC_CATALOG.md"
        assert not output.exists()

        exit_code = self._run(specs_root, output, tmp_path)

        assert exit_code == 0
        assert output.is_file()
        assert "### alpha" in output.read_text(encoding="utf-8")

    def test_provenance_banner_is_first_line(self, tmp_path):
        """The generated index begins with the provenance banner comment (Req 4.6)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"

        assert self._run(specs_root, output, tmp_path) == 0

        first_line = output.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == self._PROVENANCE_BANNER

    def test_summary_writes_valid_json(self, tmp_path):
        """``--summary`` writes a parseable JSON Catalog_Summary (Req 5.1)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(
            specs_root,
            "alpha",
            documents=("requirements.md", "tasks.md"),
            config={"specId": "alpha", "specType": "feature"},
        )
        output = tmp_path / "SPEC_CATALOG.md"
        summary = tmp_path / "summary.json"

        exit_code = self._run(specs_root, output, tmp_path, summary=summary)

        assert exit_code == 0
        assert summary.is_file()
        parsed = json.loads(summary.read_text(encoding="utf-8"))
        identifiers = [spec["identifier"] for spec in parsed["specs"]]
        assert identifiers == ["alpha"]

    def test_omitting_summary_writes_no_summary(self, tmp_path):
        """Without ``--summary`` only the index is written (Req 5.3)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"
        summary = tmp_path / "summary.json"

        exit_code = self._run(specs_root, output, tmp_path)

        assert exit_code == 0
        assert output.is_file()
        # No summary path was requested, so no summary file is produced.
        assert not summary.exists()

    def test_render_summary_raises_for_uncollectable_field(self):
        """render_summary raises CatalogError for an unrecognized status (Req 5.5)."""
        record = SpecRecord(
            identifier="alpha",
            has_requirements=True,
            has_design=False,
            has_tasks=False,
            config=None,
            task_total=0,
            task_complete=0,
        )
        # A status outside STATUS_ORDER is an uncollectable required field.
        bad_entry = SpecEntry(
            record=record,
            status="not-a-real-status",
            relationships=SpecRelationships(),
        )
        catalog = Catalog(
            entries=(bad_entry,),
            status_counts={status: 0 for status in STATUS_ORDER},
        )
        with pytest.raises(CatalogError):
            render_summary(catalog)

    def test_uncollectable_summary_field_skips_summary_and_exits_1(
        self, tmp_path, monkeypatch
    ):
        """An uncollectable summary field skips the summary and exits 1 (Req 5.5)."""
        import generate_spec_catalog

        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"
        summary = tmp_path / "summary.json"

        def _raise(_catalog):
            raise CatalogError("cannot collect required summary field")

        monkeypatch.setattr(generate_spec_catalog, "render_summary", _raise)

        exit_code = self._run(specs_root, output, tmp_path, summary=summary)

        # render_summary fails before any file is written: exit 1, no summary.
        assert exit_code == 1
        assert not summary.exists()

    def test_specs_root_flag_is_wired(self, tmp_path):
        """``--specs-root`` selects the directory that is scanned (Req 8.1)."""
        specs_root = tmp_path / "custom-specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "only-here", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"

        assert self._run(specs_root, output, tmp_path) == 0

        rendered = output.read_text(encoding="utf-8")
        assert "### only-here" in rendered

    def test_output_flag_is_wired(self, tmp_path):
        """``--output`` selects the index destination path (Req 9.2)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "nested" / "custom-index.md"
        output.parent.mkdir()

        assert self._run(specs_root, output, tmp_path) == 0

        # The index is written to the explicitly configured path.
        assert output.is_file()
        assert self._PROVENANCE_BANNER in output.read_text(encoding="utf-8")

    def test_check_flag_is_wired_and_in_sync_exits_0(self, tmp_path):
        """``--check`` compares without writing; an in-sync index exits 0 (Req 8.2)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"

        # First write the index, then a --check run over unchanged inputs.
        assert self._run(specs_root, output, tmp_path) == 0
        before = output.read_text(encoding="utf-8")

        exit_code = self._run(specs_root, output, tmp_path, check=True)

        assert exit_code == 0
        # --check never writes: the committed index is byte-for-byte unchanged.
        assert output.read_text(encoding="utf-8") == before

    def test_missing_specs_root_exits_1(self, tmp_path, capsys):
        """A nonexistent specs root reports an error and exits 1 (Req 8.6)."""
        specs_root = tmp_path / "does-not-exist"
        output = tmp_path / "SPEC_CATALOG.md"

        exit_code = self._run(specs_root, output, tmp_path)

        assert exit_code == 1
        assert str(specs_root) in capsys.readouterr().err
        assert not output.exists()

    def test_file_specs_root_exits_1(self, tmp_path, capsys):
        """A specs root that is a file (not a directory) exits 1 (Req 8.6)."""
        specs_root = tmp_path / "specs-as-file"
        specs_root.write_text("not a directory\n", encoding="utf-8")
        output = tmp_path / "SPEC_CATALOG.md"

        exit_code = self._run(specs_root, output, tmp_path)

        assert exit_code == 1
        assert str(specs_root) in capsys.readouterr().err
        assert not output.exists()

    def test_malformed_metadata_exits_1(self, tmp_path, capsys):
        """A metadata file the parser rejects reports an error and exits 1 (Req 8.8)."""
        specs_root = tmp_path / "specs"
        specs_root.mkdir()
        self._make_spec(specs_root, "alpha", documents=("requirements.md",))
        output = tmp_path / "SPEC_CATALOG.md"

        # A top-level YAML list is outside the supported mapping subset.
        bad_metadata = tmp_path / "spec-catalog.yaml"
        bad_metadata.write_text("- a\n- b\n", encoding="utf-8")

        # Confirm the loader itself rejects this content before asserting on main.
        with pytest.raises(CatalogError):
            load_metadata(bad_metadata)

        exit_code = main(
            [
                "--specs-root",
                str(specs_root),
                "--output",
                str(output),
                "--metadata",
                str(bad_metadata),
            ]
        )

        assert exit_code == 1
        assert capsys.readouterr().err.strip() != ""
        # An all-or-nothing pipeline: the index is not written on metadata error.
        assert not output.exists()

    def test_default_index_path_under_kiro_not_distributed(self):
        """The default index path lives under ``.kiro/`` and not ``senzing-bootcamp/`` (Req 9.1)."""
        # Index of workspace-only artifacts must not ship in the distributed power.
        assert DEFAULT_INDEX_PATH.parts[0] == ".kiro"
        assert "senzing-bootcamp" not in DEFAULT_INDEX_PATH.parts


class TestCommonMarkCompliance:
    """CommonMark compliance smoke test for the rendered Spec_Index (Req 9.3).

    Task 10.3 validates that a rendered index passes CommonMark linting end to
    end, using a couple of concrete fixture catalogs rather than an iterated
    property. The check mirrors ``validate_commonmark.py``: it lints the
    generated index with ``markdownlint`` (markdownlint-cli) under the same
    lenient ruleset (``default`` on; ``MD013``/``MD033``/``MD041``/line-length
    off). ``validate_commonmark.py`` is a whole-tree CLI wrapper, not an
    importable per-string validator, so this test invokes ``markdownlint``
    directly on the single generated file.

    The tool may be absent in some environments; when ``markdownlint`` is not on
    the PATH the test skips rather than fails, matching the graceful-degradation
    posture of the validator script.
    """

    # The lenient ruleset validate_commonmark.py writes to .markdownlint.json.
    _MARKDOWNLINT_CONFIG = {
        "default": True,
        "MD013": False,
        "MD033": False,
        "MD041": False,
        "line-length": False,
    }

    def _markdownlint_cmd(self) -> str | None:
        """Return the markdownlint executable name if available, else None.

        Returns:
            The command name to invoke (``markdownlint`` or, on Windows, the
            ``.cmd`` shim) when present on the PATH; None when the tool is not
            installed.
        """
        if sys.platform == "win32" and shutil.which("markdownlint.cmd"):
            return "markdownlint.cmd"
        if shutil.which("markdownlint"):
            return "markdownlint"
        return None

    def _assert_index_is_commonmark_compliant(self, index_text: str) -> None:
        """Lint a rendered index string with markdownlint under the lenient ruleset.

        Writes the index and a temporary ``.markdownlint.json`` into a temp dir,
        runs ``markdownlint --config`` against the index file, and asserts a
        zero return code. Skips when markdownlint is not installed.

        Args:
            index_text: The rendered Spec_Index markdown to validate.
        """
        ml_cmd = self._markdownlint_cmd()
        if ml_cmd is None:
            pytest.skip("markdownlint-cli not installed")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            index_path = tmp / "SPEC_CATALOG.md"
            index_path.write_text(index_text, encoding="utf-8")
            config_path = tmp / ".markdownlint.json"
            config_path.write_text(
                json.dumps(self._MARKDOWNLINT_CONFIG, indent=2), encoding="utf-8"
            )

            result = subprocess.run(
                [ml_cmd, str(index_path), "--config", str(config_path)],
                capture_output=True,
                text=True,
            )

        assert result.returncode == 0, (
            "markdownlint reported CommonMark issues in the generated index:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_index_with_configs_and_relationships_is_commonmark_compliant(self):
        """An index for a full fixture catalog (configs + relationships) lints clean.

        The fixture exercises the rich rendering paths: a spec with a complete
        config (specType/workflowType) plus a supersession and a related link,
        the spec it supersedes, and its related peer.
        """
        records = [
            SpecRecord(
                identifier="alpha-feature",
                has_requirements=True,
                has_design=True,
                has_tasks=True,
                config=SpecConfig(
                    workflow_type="requirements-first", spec_type="feature"
                ),
                task_total=4,
                task_complete=4,
            ),
            SpecRecord(
                identifier="beta-legacy",
                has_requirements=True,
                has_design=False,
                has_tasks=True,
                config=SpecConfig(workflow_type="design-first", spec_type="bugfix"),
                task_total=3,
                task_complete=1,
            ),
            SpecRecord(
                identifier="gamma-peer",
                has_requirements=True,
                has_design=True,
                has_tasks=False,
                config=SpecConfig(
                    workflow_type="requirements-first", spec_type="feature"
                ),
                task_total=0,
                task_complete=0,
            ),
        ]
        # A supersession (alpha supersedes beta) and a related pair
        # (alpha <-> gamma) so the relationship lines are rendered.
        metadata = CatalogMetadata(
            status_overrides={},
            supersessions=(("alpha-feature", "beta-legacy"),),
            related=(("alpha-feature", "gamma-peer"),),
        )
        catalog = build_catalog(records, metadata)

        self._assert_index_is_commonmark_compliant(render_index(catalog))

    def test_index_with_unknown_placeholders_is_commonmark_compliant(self):
        """An index for a spec with no config (``unknown`` placeholders) lints clean.

        This second example covers the bare path where specType/workflowType
        render as ``unknown`` placeholders and no relationships are present.
        """
        records = [
            SpecRecord(
                identifier="barren-spec",
                has_requirements=False,
                has_design=False,
                has_tasks=False,
                config=None,
                task_total=0,
                task_complete=0,
            ),
        ]
        catalog = build_catalog(records, CatalogMetadata.empty())

        self._assert_index_is_commonmark_compliant(render_index(catalog))
