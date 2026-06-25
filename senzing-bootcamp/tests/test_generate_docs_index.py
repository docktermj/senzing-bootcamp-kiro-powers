"""Property-based and unit tests for generate_docs_index.py using Hypothesis.

Feature: docs-file-placement (BUGFIX), Task 3.7 — Part B.

Validates the docs-index generator (Change 6): index completeness/currency
(Property 6), unit behavior for empty/single/nested trees and --check drift
detection, and CLI defaults/error paths.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_docs_index import (  # noqa: E402
    DEFAULT_DOCS_ROOT,
    DOCUMENT_EXTENSIONS,
    INDEX_FILENAME,
    IndexEntry,
    collect_entries,
    generate_index,
    is_document,
    main,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_basename():
    """Generate valid document basenames (no extension)."""
    return st.from_regex(r"[a-z][a-z0-9_]{1,12}", fullmatch=True)


def st_subdir():
    """Generate an optional single subdirectory under the docs root.

    The empty string denotes a document placed directly under the docs root.
    """
    return st.sampled_from(["", "mapping", "reference", "progress", "feedback"])


def st_doc_specs():
    """Generate a set of (subdir, basename) document specs with unique rel paths."""
    return st.lists(
        st.tuples(st_subdir(), st_basename()),
        min_size=1,
        max_size=8,
        unique_by=lambda spec: f"{spec[0]}/{spec[1]}",
    )


def _write_docs(docs_root: Path, specs: list[tuple[str, str]]) -> list[str]:
    """Materialize documents under a docs root and return their rel POSIX paths.

    Args:
        docs_root: Directory under which to create the documents.
        specs: (subdir, basename) pairs; an empty subdir places a doc at root.

    Returns:
        Sorted list of POSIX-relative document paths (e.g. "mapping/foo.md").
    """
    rels: list[str] = []
    for subdir, base in specs:
        target_dir = docs_root / subdir if subdir else docs_root
        target_dir.mkdir(parents=True, exist_ok=True)
        doc = target_dir / f"{base}.md"
        doc.write_text(f"# {base}\n\nbody for {base}\n", encoding="utf-8")
        rels.append(doc.relative_to(docs_root).as_posix())
    return sorted(rels)


# ---------------------------------------------------------------------------
# Property 6: Index completeness and currency
# ---------------------------------------------------------------------------


class TestProperty6IndexCompletenessAndCurrency:
    """Feature: docs-file-placement, Property 6: Index completeness/currency.

    For any generated set of docs documents, the written docs/README.md lists
    every document under docs/ (excluding README.md itself); adding or removing
    documents and regenerating keeps the index in sync.

    **Validates: Requirements 2.5**
    """

    @given(specs=st_doc_specs())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_index_lists_every_document(self, specs):
        """Every document under docs/ appears in the generated index."""
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            docs_root.mkdir()
            rels = _write_docs(docs_root, specs)

            index = generate_index(docs_root)

            for rel in rels:
                assert f"[{rel}]({rel})" in index, (
                    f"document {rel} missing from generated index"
                )
        finally:
            shutil.rmtree(tmp)

    @given(specs=st_doc_specs())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_index_excludes_itself(self, specs):
        """A pre-existing docs/README.md is never listed as an entry."""
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            docs_root.mkdir()
            _write_docs(docs_root, specs)
            (docs_root / INDEX_FILENAME).write_text("# stale index\n", encoding="utf-8")

            index = generate_index(docs_root)

            assert f"[{INDEX_FILENAME}]({INDEX_FILENAME})" not in index, (
                "the top-level README.md index listed itself"
            )
        finally:
            shutil.rmtree(tmp)

    @given(specs=st_doc_specs(), extra=st.tuples(st_subdir(), st_basename()))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_adding_then_removing_keeps_index_in_sync(self, specs, extra):
        """Adding a doc then removing it returns the index to its prior state."""
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            docs_root.mkdir()
            _write_docs(docs_root, specs)

            baseline = generate_index(docs_root)

            # Add a new document (skip if it collides with an existing rel path).
            subdir, base = extra
            target_dir = docs_root / subdir if subdir else docs_root
            target_dir.mkdir(parents=True, exist_ok=True)
            new_doc = target_dir / f"{base}.md"
            if new_doc.exists():
                return
            new_doc.write_text(f"# {base}\n", encoding="utf-8")

            with_added = generate_index(docs_root)
            rel = new_doc.relative_to(docs_root).as_posix()
            assert f"[{rel}]({rel})" in with_added, "added doc not reflected in index"

            # Remove it again; the index must match the original baseline.
            new_doc.unlink()
            after_removal = generate_index(docs_root)
            assert after_removal == baseline, (
                "index did not return to baseline after removing the added doc"
            )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Unit cases: empty tree, single doc, nested subdirs, --check drift
# ---------------------------------------------------------------------------


class TestIndexUnitCases:
    """Feature: docs-file-placement, unit cases for the index generator.

    Empty tree, single doc, nested subdirs, and --check drift detection.

    **Validates: Requirements 2.5**
    """

    def test_empty_tree_handled_gracefully(self, tmp_path):
        """An empty docs/ tree produces a valid index with no entries."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()

        index = generate_index(docs_root)

        assert collect_entries(docs_root) == []
        assert "_No documents found._" in index

    def test_single_doc_listed(self, tmp_path):
        """A single document is collected and listed in the index."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "intro.md").write_text("# Introduction\n", encoding="utf-8")

        entries = collect_entries(docs_root)
        index = generate_index(docs_root)

        assert entries == [IndexEntry(rel="intro.md", description="Introduction")]
        assert "[intro.md](intro.md) - Introduction" in index

    def test_nested_subdirs_grouped(self, tmp_path):
        """Documents in nested subdirs are listed under their subdir sections."""
        docs_root = tmp_path / "docs"
        (docs_root / "mapping").mkdir(parents=True)
        (docs_root / "reference").mkdir(parents=True)
        (docs_root / "mapping" / "playpalace_mapper.md").write_text(
            "# PlayPalace mapper\n", encoding="utf-8"
        )
        (docs_root / "reference" / "senzing_entity_specification.md").write_text(
            "# Entity Spec\n", encoding="utf-8"
        )
        (docs_root / "overview.md").write_text("# Overview\n", encoding="utf-8")

        index = generate_index(docs_root)

        assert "## Root" in index
        assert "## mapping" in index
        assert "## reference" in index
        assert "[mapping/playpalace_mapper.md](mapping/playpalace_mapper.md)" in index
        assert (
            "[reference/senzing_entity_specification.md]"
            "(reference/senzing_entity_specification.md)" in index
        )
        # Root section precedes subdir sections.
        assert index.index("## Root") < index.index("## mapping")

    def test_check_in_sync_returns_zero(self, tmp_path, capsys):
        """--check returns 0 when docs/README.md matches the generated index."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (docs_root / INDEX_FILENAME).write_text(
            generate_index(docs_root), encoding="utf-8"
        )

        exit_code = main(["--docs-root", str(docs_root), "--check"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "in sync" in captured.out.lower()

    def test_check_out_of_sync_returns_one(self, tmp_path, capsys):
        """--check returns 1 when docs/README.md is stale."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (docs_root / INDEX_FILENAME).write_text("# stale\n", encoding="utf-8")

        exit_code = main(["--docs-root", str(docs_root), "--check"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "out of sync" in captured.err.lower()

    def test_check_missing_index_returns_one(self, tmp_path, capsys):
        """--check returns 1 when docs/README.md does not yet exist."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "guide.md").write_text("# Guide\n", encoding="utf-8")

        exit_code = main(["--docs-root", str(docs_root), "--check"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "missing" in captured.err.lower()

    def test_is_document_recognizes_markdown_only(self, tmp_path):
        """is_document accepts Markdown extensions and rejects others/dirs."""
        md = tmp_path / "a.md"
        md.write_text("# a\n", encoding="utf-8")
        txt = tmp_path / "b.txt"
        txt.write_text("plain", encoding="utf-8")

        assert is_document(md) is True
        assert is_document(txt) is False
        assert is_document(tmp_path) is False
        # Sanity: the documented extensions all classify as documents.
        for ext in DOCUMENT_EXTENSIONS:
            doc = tmp_path / f"sample{ext}"
            doc.write_text("# s\n", encoding="utf-8")
            assert is_document(doc) is True


# ---------------------------------------------------------------------------
# CLI defaults and error paths
# ---------------------------------------------------------------------------


class TestCLIArgumentDefaults:
    """Feature: docs-file-placement, CLI defaults and error paths.

    Mirrors the organizer's TestCLIArgumentDefaults: default --docs-root, write
    mode exit 0, and the missing/invalid docs-root error path (exit 1).

    **Validates: Requirements 2.5**
    """

    def test_docs_root_defaults_to_docs(self, tmp_path, monkeypatch, capsys):
        """--docs-root defaults to ./docs relative to the cwd."""
        monkeypatch.chdir(tmp_path)
        docs_root = tmp_path / DEFAULT_DOCS_ROOT
        docs_root.mkdir()
        (docs_root / "intro.md").write_text("# Intro\n", encoding="utf-8")

        exit_code = main([])

        captured = capsys.readouterr()
        assert exit_code == 0
        index_path = docs_root / INDEX_FILENAME
        assert index_path.is_file()
        assert "[intro.md](intro.md)" in index_path.read_text(encoding="utf-8")
        assert "wrote docs index" in captured.out.lower()

    def test_write_mode_returns_zero_and_writes_index(self, tmp_path, capsys):
        """Write mode creates docs/README.md and returns 0."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "guide.md").write_text("# Guide\n", encoding="utf-8")

        exit_code = main(["--docs-root", str(docs_root)])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert (docs_root / INDEX_FILENAME).is_file()
        assert "wrote docs index" in captured.out.lower()

    def test_error_when_docs_root_does_not_exist(self, tmp_path, capsys):
        """A missing docs root yields an error message and exit code 1."""
        missing = tmp_path / "no_such_docs"

        exit_code = main(["--docs-root", str(missing)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "does not exist" in captured.err.lower() or "error" in captured.err.lower()

    def test_error_when_docs_root_is_file(self, tmp_path, capsys):
        """A docs root that is a file (not a directory) yields exit code 1."""
        not_a_dir = tmp_path / "docs.md"
        not_a_dir.write_text("# not a dir\n", encoding="utf-8")

        exit_code = main(["--docs-root", str(not_a_dir)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert (
            "not a directory" in captured.err.lower()
            or "does not exist" in captured.err.lower()
        )
