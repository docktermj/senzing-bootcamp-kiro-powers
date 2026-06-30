"""Property-based and unit tests for generate_docs_index.py using Hypothesis.

Feature: graduation-docs-index.

Validates the reworked docs-index generator: depth-1 enumeration of all
top-level entries (Property 1), exclusion of the index file and dot-prefixed
entries (Property 2), deterministic case-insensitive ordering (Property 3),
full-replacement and idempotent regeneration (Property 4), round-trip as a
valid Markdown table of contents (Property 5), exactly-one well-formed
description per entry from the purpose map or generic fallback (Property 6),
and the subdirectory visual indicator that files never carry (Property 7).
"""

import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_docs_index  # noqa: E402
from generate_docs_index import (  # noqa: E402
    DEFAULT_DOCS_ROOT,
    INDEX_FILENAME,
    PURPOSE_MAP,
    SUBDIR_INDICATOR,
    _LIST_ITEM_RE,
    generate_index,
    main,
    scan_entries,
    validate_toc,
    write_index_atomically,
)

# ---------------------------------------------------------------------------
# graduation-docs-index: strategies and property tests
# ---------------------------------------------------------------------------

# Reuse curated purpose-map names so generated trees mix known and unknown
# entries. Files are keyed with an extension (contain "."); dirs are bare names.
_KNOWN_FILE_NAMES = [name for name in PURPOSE_MAP if "." in name]
_KNOWN_DIR_NAMES = [name for name in PURPOSE_MAP if "." not in name]


def st_top_level_file_name():
    """Generate a top-level docs file name (varied casing; never dotted/README)."""
    random_file = st.from_regex(
        r"[A-Za-z][A-Za-z0-9_]{0,14}\.(md|txt|json)", fullmatch=True
    )
    return st.one_of(st.sampled_from(_KNOWN_FILE_NAMES), random_file).filter(
        lambda name: name.lower() != INDEX_FILENAME.lower()
    )


def st_dir_name():
    """Generate a top-level subdirectory name (varied casing; no extension)."""
    random_dir = st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,14}", fullmatch=True)
    return st.one_of(st.sampled_from(_KNOWN_DIR_NAMES), random_dir)


def st_nested_file_name():
    """Generate a file name nested inside a subdirectory."""
    return st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,10}\.(md|txt)", fullmatch=True)


@st.composite
def st_docs_tree(draw):
    """Generate a ``docs/`` tree spec: top-level files and subdirs with nesting.

    Returns a spec dict with ``files`` (top-level file names) and ``dirs`` (each
    a ``{"name", "nested"}`` mapping whose ``nested`` is a list of file names one
    level deep). Names mix curated purpose-map entries, random names, and varied
    casing. All top-level names are unique case-insensitively so the tree
    materializes identically on case-sensitive and case-insensitive filesystems.
    Subdirectories optionally contain nested files, which must never surface as
    top-level index entries. The spec is materialized with ``_materialize_docs_tree``.

    Args:
        draw: Hypothesis draw callable supplied by ``@st.composite``.

    Returns:
        A dict describing the docs tree to materialize.
    """
    files = draw(st.lists(st_top_level_file_name(), max_size=6))
    dirs = draw(
        st.lists(
            st.fixed_dictionaries(
                {
                    "name": st_dir_name(),
                    "nested": st.lists(st_nested_file_name(), max_size=4),
                }
            ),
            max_size=4,
        )
    )

    # Enforce unique top-level names (case-insensitive) across files and dirs so
    # the tree cannot collide when materialized on a case-insensitive filesystem.
    seen: set[str] = set()
    unique_files: list[str] = []
    for name in files:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_files.append(name)
    unique_dirs: list[dict] = []
    for spec in dirs:
        key = spec["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique_dirs.append(spec)

    return {"files": unique_files, "dirs": unique_dirs}


def _materialize_docs_tree(docs_root: Path, tree: dict) -> None:
    """Create the ``docs/`` tree described by an ``st_docs_tree()`` spec.

    Args:
        docs_root: Directory under which to materialize the tree (created if absent).
        tree: A spec dict as produced by ``st_docs_tree()``.
    """
    docs_root.mkdir(parents=True, exist_ok=True)
    for name in tree["files"]:
        (docs_root / name).write_text(f"# {name}\n", encoding="utf-8")
    for spec in tree["dirs"]:
        subdir = docs_root / spec["name"]
        subdir.mkdir(parents=True, exist_ok=True)
        for nested in spec["nested"]:
            (subdir / nested).write_text(f"# {nested}\n", encoding="utf-8")


class TestProperty1EnumerationMatchesEligibleEntries:
    """Feature: graduation-docs-index, Property 1: Enumeration matches the eligible top-level entries.

    For any ``docs/`` directory tree, the set of entry names produced by the
    generator equals exactly the eligible depth-1 entries: every top-level
    regular file and every immediate subdirectory (each counted exactly once,
    never recursing into a subdirectory's contents).

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    """

    @given(tree=st_docs_tree())
    def test_enumeration_matches_eligible_top_level_entries(self, tree):
        # Feature: graduation-docs-index, Property 1: Enumeration matches the
        # eligible top-level entries
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            eligible_files = set(tree["files"])
            eligible_dirs = {spec["name"] for spec in tree["dirs"]}
            eligible = eligible_files | eligible_dirs

            entries = scan_entries(docs_root)
            names = [entry.name for entry in entries]

            # Each eligible entry appears exactly once (no duplicates).
            assert len(names) == len(set(names)), "an entry was enumerated more than once"
            # The enumerated entry-name set equals the eligible depth-1 set.
            assert set(names) == eligible
            # Files and subdirectories are classified correctly.
            assert {e.name for e in entries if not e.is_dir} == eligible_files
            assert {e.name for e in entries if e.is_dir} == eligible_dirs
            # Each subdirectory appears exactly once.
            for spec in tree["dirs"]:
                count = sum(1 for e in entries if e.name == spec["name"])
                assert count == 1, f"subdirectory {spec['name']!r} appeared {count} times"
            # Nested files never surface as top-level index entries.
            nested_only = {
                nested for spec in tree["dirs"] for nested in spec["nested"]
            } - eligible
            assert nested_only.isdisjoint(set(names)), (
                "a nested file leaked into the top-level enumeration"
            )
        finally:
            shutil.rmtree(tmp)


def st_dot_name():
    """Generate a dot-prefixed entry name (file or directory) for exclusion tests.

    Returns:
        A Hypothesis strategy producing names that begin with ``.`` (e.g.
        ``.gitignore`` or ``.hidden``), which the generator must always exclude.
    """
    return st.from_regex(r"\.[A-Za-z][A-Za-z0-9_]{0,10}(\.(md|txt|json))?", fullmatch=True)


class TestProperty2IndexFileAndDotEntriesExcluded:
    """Feature: graduation-docs-index, Property 2: The index file and dot-prefixed entries are always excluded.

    For any ``docs/`` directory tree — including one that already contains a
    ``docs/README.md`` and arbitrary dot-prefixed files or directories — no entry
    whose name is ``README.md`` and no entry whose name begins with ``.`` ever
    appears in the generated index.

    **Validates: Requirements 2.6, 2.8**
    """

    @given(
        tree=st_docs_tree(),
        dot_files=st.lists(st_dot_name(), max_size=4),
        dot_dirs=st.lists(st_dot_name(), max_size=4),
        seed_readme=st.booleans(),
    )
    def test_index_file_and_dot_entries_excluded(
        self, tree, dot_files, dot_dirs, seed_readme
    ):
        # Feature: graduation-docs-index, Property 2: The index file and
        # dot-prefixed entries are always excluded
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            # Seed a pre-existing index file so we can confirm it is never
            # enumerated as one of its own entries.
            if seed_readme:
                (docs_root / INDEX_FILENAME).write_text(
                    "# stale index\n", encoding="utf-8"
                )

            # Materialize arbitrary dot-prefixed files and directories. Names are
            # deduplicated case-insensitively against everything already on disk
            # so materialization cannot collide on a case-insensitive filesystem.
            existing = {p.name.lower() for p in docs_root.iterdir()}
            dot_names: set[str] = set()
            for name in dot_files:
                key = name.lower()
                if key in existing or key in dot_names:
                    continue
                (docs_root / name).write_text("hidden\n", encoding="utf-8")
                dot_names.add(key)
            for name in dot_dirs:
                key = name.lower()
                if key in existing or key in dot_names:
                    continue
                (docs_root / name).mkdir()
                dot_names.add(key)

            entries = scan_entries(docs_root)
            names = [entry.name for entry in entries]

            # The index file itself is never enumerated.
            assert INDEX_FILENAME not in names, (
                "the index file README.md was enumerated as an entry"
            )
            # No dot-prefixed entry ever appears.
            assert not any(name.startswith(".") for name in names), (
                "a dot-prefixed entry leaked into the enumeration"
            )

            # The rendered index never references the index file or any dot entry.
            index = generate_index(docs_root)
            assert f"**{INDEX_FILENAME}**" not in index
            for line in index.splitlines():
                if line.startswith("- **"):
                    rendered = line[len("- **"):].split("**", 1)[0]
                    assert not rendered.startswith("."), (
                        f"rendered entry {rendered!r} starts with a dot"
                    )
        finally:
            shutil.rmtree(tmp)


class TestProperty3EntryOrderDeterministicAndCaseInsensitive:
    """Feature: graduation-docs-index, Property 3: Entry order is deterministic and case-insensitive.

    For any ``docs/`` directory tree, the entries are listed in case-insensitive
    alphabetical order by name, and regenerating the index from identical
    ``docs/`` contents (regardless of filesystem iteration or creation order)
    produces byte-identical output.

    **Validates: Requirements 2.7**
    """

    @given(tree=st_docs_tree())
    def test_entry_order_is_deterministic_and_case_insensitive(self, tree):
        # Feature: graduation-docs-index, Property 3: Entry order is
        # deterministic and case-insensitive
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            eligible = list(tree["files"]) + [spec["name"] for spec in tree["dirs"]]

            # Enumerated order equals case-insensitive alphabetical order by name.
            names = [entry.name for entry in scan_entries(docs_root)]
            assert names == sorted(eligible, key=str.lower)

            # Identical docs/ contents produce byte-identical output across runs.
            first = generate_index(docs_root)
            second = generate_index(docs_root)
            assert first == second
        finally:
            shutil.rmtree(tmp)


class TestProperty6EveryEntryWellFormedDescription:
    """Feature: graduation-docs-index, Property 6: Every entry has exactly one well-formed description.

    For any ``docs/`` directory tree, every listed entry shows its name together
    with exactly one purpose description rendered on a single line of 1 to 120
    characters — including entries whose names have no predefined purpose, which
    receive a non-empty generic description within the same bounds.

    **Validates: Requirements 3.1, 3.3**
    """

    @given(tree=st_docs_tree())
    def test_every_entry_has_exactly_one_well_formed_description(self, tree):
        # Feature: graduation-docs-index, Property 6: Every entry has exactly one
        # well-formed description
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            entries = scan_entries(docs_root)
            index = generate_index(docs_root)

            # Each scanned entry carries exactly one single-line description that
            # is non-empty and within the 1..120-char bound. This holds for both
            # known purpose-map names and unknown random names (the generic
            # fallback), so no entry is ever description-less (Requirement 3.3).
            for entry in entries:
                assert entry.description, f"entry {entry.name!r} has an empty description"
                assert "\n" not in entry.description, (
                    f"entry {entry.name!r} description spans multiple lines"
                )
                assert 1 <= len(entry.description) <= 120, (
                    f"entry {entry.name!r} description length "
                    f"{len(entry.description)} is outside 1..120"
                )

            # In the rendered index, each entry appears as exactly one list item
            # carrying exactly one description (Requirement 3.1).
            descriptions_by_entry: dict[str, list[str]] = {
                entry.name: [] for entry in entries
            }
            by_rendered_name = {
                entry.name + (SUBDIR_INDICATOR if entry.is_dir else ""): entry.name
                for entry in entries
            }
            for line in index.splitlines():
                if not line.startswith("- "):
                    continue
                match = _LIST_ITEM_RE.match(line)
                assert match is not None, f"malformed list item: {line!r}"
                rendered_name = match.group("name")
                description = match.group("description")
                assert rendered_name in by_rendered_name, (
                    f"unexpected entry {rendered_name!r} in rendered index"
                )
                # A rendered description is one single line of 1..120 chars.
                assert "\n" not in description
                assert 1 <= len(description) <= 120, (
                    f"rendered description for {rendered_name!r} length "
                    f"{len(description)} is outside 1..120"
                )
                descriptions_by_entry[by_rendered_name[rendered_name]].append(description)

            # Every entry shows exactly one description — no entry is missing and
            # none is duplicated.
            for name, descriptions in descriptions_by_entry.items():
                assert len(descriptions) == 1, (
                    f"entry {name!r} rendered with {len(descriptions)} descriptions, "
                    "expected exactly one"
                )
        finally:
            shutil.rmtree(tmp)


class TestProperty7SubdirectoriesCarryVisualIndicator:
    """Feature: graduation-docs-index, Property 7: Subdirectories carry a visual indicator that files never carry.

    For any ``docs/`` directory tree, every subdirectory entry renders with the
    consistent visual indicator (a trailing ``/`` — ``SUBDIR_INDICATOR``) and
    every file entry renders without it, so each entry is unambiguously
    identifiable as a file or a subdirectory.

    **Validates: Requirements 3.2**
    """

    @given(tree=st_docs_tree())
    def test_subdirectories_carry_indicator_files_never_do(self, tree):
        # Feature: graduation-docs-index, Property 7: Subdirectories carry a
        # visual indicator that files never carry
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            entries = scan_entries(docs_root)
            index = generate_index(docs_root)

            # Map each rendered list item's name to whether the source entry is
            # a directory, so each rendered line can be checked against the
            # indicator rule.
            is_dir_by_name = {entry.name: entry.is_dir for entry in entries}

            rendered_names: set[str] = set()
            for line in index.splitlines():
                if not line.startswith("- "):
                    continue
                match = _LIST_ITEM_RE.match(line)
                assert match is not None, f"malformed list item: {line!r}"
                rendered_name = match.group("name")

                if rendered_name.endswith(SUBDIR_INDICATOR):
                    # A trailing-indicator name must map to a subdirectory entry.
                    bare = rendered_name[: -len(SUBDIR_INDICATOR)]
                    assert bare in is_dir_by_name, (
                        f"rendered subdir {rendered_name!r} has no matching entry"
                    )
                    assert is_dir_by_name[bare], (
                        f"file entry {bare!r} carried the subdir indicator"
                    )
                    rendered_names.add(bare)
                else:
                    # A name without the indicator must map to a file entry, and
                    # a file name must never itself end with the indicator.
                    assert rendered_name in is_dir_by_name, (
                        f"rendered entry {rendered_name!r} has no matching entry"
                    )
                    assert not is_dir_by_name[rendered_name], (
                        f"subdirectory entry {rendered_name!r} rendered without "
                        "the indicator"
                    )
                    rendered_names.add(rendered_name)

            # Every entry was rendered, so the indicator rule was checked for all
            # of them (subdirs with the indicator, files without).
            assert rendered_names == set(is_dir_by_name), (
                "not every entry was represented in the rendered index"
            )

            # Directly assert the partition: every subdirectory carries the
            # indicator and no file does.
            for entry in entries:
                if entry.is_dir:
                    assert f"- **{entry.name}{SUBDIR_INDICATOR}** — " in index, (
                        f"subdirectory {entry.name!r} missing the visual indicator"
                    )
                else:
                    assert f"- **{entry.name}{SUBDIR_INDICATOR}** — " not in index, (
                        f"file {entry.name!r} carried the subdir indicator"
                    )
        finally:
            shutil.rmtree(tmp)


class TestProperty4RegenerationFullyReplacesAndIsIdempotent:
    """Feature: graduation-docs-index, Property 4: Regeneration fully replaces prior content and is idempotent.

    For any ``docs/`` directory tree and any pre-existing ``docs/README.md``
    content, after generation the on-disk index content equals a fresh
    ``generate_index(docs_root)`` (so no content unique to the prior file
    survives), and generating a second time produces byte-identical output.

    **Validates: Requirements 1.2**
    """

    @given(tree=st_docs_tree(), stale=st.text(max_size=400))
    def test_regeneration_fully_replaces_prior_content_and_is_idempotent(
        self, tree, stale
    ):
        # Feature: graduation-docs-index, Property 4: Regeneration fully replaces
        # prior content and is idempotent
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            # Seed arbitrary stale index content that must be entirely replaced.
            stale_index = docs_root / INDEX_FILENAME
            stale_index.write_text(stale, encoding="utf-8")

            # A fresh generation describes only the current docs/ contents and
            # never carries over anything from the prior README.md.
            fresh = generate_index(docs_root)

            # Regenerate and atomically replace the stale index on disk.
            write_index_atomically(docs_root, generate_index(docs_root))
            on_disk = stale_index.read_text(encoding="utf-8")

            # The written content equals a fresh generation: the prior file's
            # content was fully replaced (Requirement 1.2).
            assert on_disk == fresh, (
                "regenerated index did not fully replace the stale README.md content"
            )

            # A second regeneration over the just-written index is byte-identical:
            # generation is idempotent regardless of the now-current README.md.
            second = generate_index(docs_root)
            assert second == fresh, "second generation diverged from the first"
            write_index_atomically(docs_root, generate_index(docs_root))
            assert stale_index.read_text(encoding="utf-8") == on_disk, (
                "second atomic write produced a different on-disk index"
            )
        finally:
            shutil.rmtree(tmp)


class TestProperty5RenderedIndexRoundTripsAsValidToc:
    """Feature: graduation-docs-index, Property 5: Rendered index round-trips as a valid Markdown table of contents.

    For any ``docs/`` directory tree, the rendered Markdown parses as a table of
    contents whose listed entries are exactly the enumerated entries — parsing
    the rendered output back into a set of entry names returns the same set that
    was rendered (from ``scan_entries``) — and ``validate_toc`` accepts the
    rendered output.

    **Validates: Requirements 1.3, 1.4**
    """

    @given(tree=st_docs_tree())
    def test_rendered_index_round_trips_as_valid_toc(self, tree):
        # Feature: graduation-docs-index, Property 5: Rendered index round-trips
        # as a valid Markdown table of contents
        tmp = Path(tempfile.mkdtemp())
        try:
            docs_root = tmp / "docs"
            _materialize_docs_tree(docs_root, tree)

            entries = scan_entries(docs_root)
            index = generate_index(docs_root)

            # The set of names that were rendered (from scan_entries), with the
            # trailing SUBDIR_INDICATOR applied to subdirectories exactly as
            # render_markdown emits them.
            rendered_set = {
                entry.name + (SUBDIR_INDICATOR if entry.is_dir else "")
                for entry in entries
            }

            # Parse the rendered Markdown back into the set of entry names by
            # matching each list item with _LIST_ITEM_RE.
            parsed_set: set[str] = set()
            for line in index.splitlines():
                if not line.startswith("- "):
                    continue
                match = _LIST_ITEM_RE.match(line)
                assert match is not None, f"malformed list item: {line!r}"
                parsed_set.add(match.group("name"))

            # Round-trip: parsing the rendered output yields exactly the set of
            # entries that were rendered (Requirement 1.3).
            assert parsed_set == rendered_set, (
                "parsed entry names differ from the rendered entry set"
            )

            # The rendered Markdown is a valid, parseable table of contents
            # (Requirement 1.4): validate_toc accepts it.
            assert validate_toc(index, entries), (
                "validate_toc rejected the freshly rendered index"
            )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# graduation-docs-index: CLI output-contract unit tests
# ---------------------------------------------------------------------------


def _populate_docs(docs_root: Path) -> None:
    """Create a small populated ``docs/`` tree for CLI example tests.

    Args:
        docs_root: Directory to populate (created if absent).
    """
    docs_root.mkdir(parents=True, exist_ok=True)
    (docs_root / "bootcamp_recap.md").write_text("# recap\n", encoding="utf-8")
    (docs_root / "business_problem.md").write_text("# problem\n", encoding="utf-8")
    (docs_root / "mapping").mkdir()
    (docs_root / "mapping" / "nested.md").write_text("# nested\n", encoding="utf-8")


class TestCliOutputContract:
    """CLI output-contract example tests for ``main(argv=None)``.

    Feature: graduation-docs-index. These are example/unit tests (not Hypothesis
    property tests) covering the concrete CLI behavior: where the index is
    written, the clean skip when ``docs/`` is absent, the ordering of the success
    message before the one-line summary, the no-partial-file guarantee on
    failure, and ``--check`` drift detection.

    **Validates: Requirements 1.1, 1.4, 4.2, 4.4, 4.5**
    """

    def test_writes_index_at_docs_root(self, tmp_path, capsys):
        # Output location (Requirement 1.1): generating over a populated docs/
        # writes docs/README.md directly at the docs root.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        exit_code = main(["--docs-root", str(docs_root)])
        capsys.readouterr()

        index_path = docs_root / INDEX_FILENAME
        assert exit_code == 0
        assert index_path.is_file(), "docs/README.md was not written at the docs root"
        # It is written at the root of docs/, not nested inside a subdirectory.
        assert index_path.parent == docs_root

    def test_skip_when_docs_root_missing(self, tmp_path, capsys):
        # Skip (Requirement 4.2): a non-existent --docs-root exits 0 and prints a
        # one-line "not generated" summary; no index file is created.
        missing = tmp_path / "does-not-exist"

        exit_code = main(["--docs-root", str(missing)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "not generated" in captured.out
        assert not (missing / INDEX_FILENAME).exists()

    def test_success_message_precedes_summary(self, tmp_path, capsys):
        # Success ordering (Requirements 4.4, 4.5): stdout contains the success
        # message naming docs/README.md BEFORE the one-line summary.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        exit_code = main(["--docs-root", str(docs_root)])
        captured = capsys.readouterr()

        assert exit_code == 0

        index_path = docs_root / INDEX_FILENAME
        out = captured.out
        # The success message identifies the written location.
        wrote_idx = out.find("Wrote docs index:")
        summary_idx = out.find("Docs index generated at")
        assert wrote_idx != -1, "missing 'Wrote docs index:' success message"
        assert summary_idx != -1, "missing one-line summary"
        # Success message comes strictly before the one-line summary.
        assert wrote_idx < summary_idx
        # Both lines name the index location.
        assert str(index_path) in out

    def test_no_partial_file_on_validation_failure(self, tmp_path, capsys, monkeypatch):
        # No partial file on failure (Requirement 1.4): when validation rejects
        # the rendered Markdown, any pre-existing docs/README.md is unchanged,
        # no temp/malformed file remains, and main exits 1.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        index_path = docs_root / INDEX_FILENAME
        sentinel = "# pre-existing index - must remain untouched\n"
        index_path.write_text(sentinel, encoding="utf-8")

        # Force table-of-contents validation to reject, as if rendering produced
        # a malformed document. write_index_atomically looks up validate_toc as a
        # module global, so patching the module attribute takes effect.
        monkeypatch.setattr(generate_docs_index, "validate_toc", lambda *a, **k: False)

        exit_code = main(["--docs-root", str(docs_root)])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Failed to write docs index" in captured.err
        # The pre-existing index is byte-for-byte unchanged.
        assert index_path.read_text(encoding="utf-8") == sentinel
        # No temp/partial file is left behind in the docs directory.
        leftover = [
            p.name
            for p in docs_root.iterdir()
            if p.name.startswith(".docs-index-") or p.name.endswith(".tmp")
        ]
        assert leftover == [], f"temp/partial files left behind: {leftover}"

    def test_no_partial_file_on_write_failure(self, tmp_path, capsys, monkeypatch):
        # No partial file on failure (Requirement 1.4): a simulated write failure
        # (os.replace raising) leaves the pre-existing index untouched, removes
        # the temp file, and main exits 1.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        index_path = docs_root / INDEX_FILENAME
        sentinel = "# original - survives a write failure\n"
        index_path.write_text(sentinel, encoding="utf-8")

        def _boom(src, dst):
            raise OSError("simulated atomic replace failure")

        monkeypatch.setattr(generate_docs_index.os, "replace", _boom)

        exit_code = main(["--docs-root", str(docs_root)])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Failed to write docs index" in captured.err
        # The pre-existing index is unchanged because os.replace never ran.
        assert index_path.read_text(encoding="utf-8") == sentinel
        # The temp file was cleaned up.
        leftover = [
            p.name
            for p in docs_root.iterdir()
            if p.name.startswith(".docs-index-") or p.name.endswith(".tmp")
        ]
        assert leftover == [], f"temp/partial files left behind: {leftover}"

    def test_check_in_sync_exits_zero(self, tmp_path, capsys):
        # --check drift: an in-sync index (just written) exits 0.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        # Generate the index first so it is in sync with docs/ contents.
        assert main(["--docs-root", str(docs_root)]) == 0
        capsys.readouterr()

        exit_code = main(["--docs-root", str(docs_root), "--check"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "in sync" in captured.out

    def test_check_missing_index_exits_one(self, tmp_path, capsys):
        # --check drift: a missing index exits 1.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        exit_code = main(["--docs-root", str(docs_root), "--check"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "missing" in captured.err

    def test_check_stale_index_exits_one(self, tmp_path, capsys):
        # --check drift: a stale index (does not match a fresh generation) exits 1.
        docs_root = tmp_path / "docs"
        _populate_docs(docs_root)

        (docs_root / INDEX_FILENAME).write_text("# stale\n", encoding="utf-8")

        exit_code = main(["--docs-root", str(docs_root), "--check"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "stale" in captured.err
