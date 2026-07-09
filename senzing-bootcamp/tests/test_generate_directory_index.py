"""Property-based and unit tests for generate_directory_index.py using Hypothesis.

Feature: graduation-enrichment.

Validates the shared directory-index generator that produces ``src/README.md``
and ``data/README.md``: depth-1 enumeration of every top-level regular file and
immediate subdirectory, with the ``README.md`` index file and dot-prefixed
entries excluded and nested files never surfacing (Property 1).
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

import generate_directory_index as gdi  # noqa: E402

# ---------------------------------------------------------------------------
# graduation-enrichment: shared strategies and target-tree materializer
# ---------------------------------------------------------------------------

_INDEX_FILENAME = gdi.INDEX_FILENAME

# Reuse curated purpose-map names (from both the src and data maps) so generated
# trees mix known and unknown entries. Files are keyed with an extension
# (contain "."); dirs are bare names.
_KNOWN_FILE_NAMES = sorted(
    name for name in {**gdi.SRC_PURPOSE_MAP, **gdi.DATA_PURPOSE_MAP} if "." in name
)
_KNOWN_DIR_NAMES = sorted(
    name for name in {**gdi.SRC_PURPOSE_MAP, **gdi.DATA_PURPOSE_MAP} if "." not in name
)


def st_top_level_file_name():
    """Generate an eligible top-level file name (varied casing; never dotted/README)."""
    random_file = st.from_regex(
        r"[A-Za-z][A-Za-z0-9_]{0,14}\.(md|txt|json|py|csv)", fullmatch=True
    )
    return st.one_of(st.sampled_from(_KNOWN_FILE_NAMES), random_file).filter(
        lambda name: name.lower() != _INDEX_FILENAME.lower()
    )


def st_dir_name():
    """Generate a top-level subdirectory name (varied casing; no extension)."""
    random_dir = st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,14}", fullmatch=True)
    return st.one_of(st.sampled_from(_KNOWN_DIR_NAMES), random_dir)


def st_nested_file_name():
    """Generate a file name nested inside a subdirectory."""
    return st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,10}\.(md|txt|py)", fullmatch=True)


def st_dot_name():
    """Generate a dot-prefixed entry name (file or directory) for exclusion coverage.

    Returns:
        A Hypothesis strategy producing names that begin with ``.`` (e.g.
        ``.gitignore`` or ``.hidden``), which the generator must always exclude.
    """
    return st.from_regex(
        r"\.[A-Za-z][A-Za-z0-9_]{0,10}(\.(md|txt|json))?", fullmatch=True
    )


@st.composite
def st_target_tree(draw):
    """Generate a target-directory tree spec: top-level entries plus nesting.

    Returns a spec dict describing what to materialize under a target root:

    - ``files``: eligible top-level file names (never dotted, never ``README.md``).
    - ``dirs``: eligible top-level subdirectories, each a ``{"name", "nested"}``
      mapping whose ``nested`` is a list of file names one level deep.
    - ``dot_files`` / ``dot_dirs``: dot-prefixed files and directories that the
      generator must always exclude.
    - ``seed_readme``: whether to seed a pre-existing ``README.md`` index file
      (which must be excluded from the enumeration).

    Names mix curated purpose-map entries, random names, and varied casing. All
    top-level names are deduplicated case-insensitively across every category so
    the tree materializes identically on case-sensitive and case-insensitive
    filesystems. The spec is data only (no filesystem effects); a test
    materializes it with ``_materialize_target_tree``.

    Args:
        draw: Hypothesis draw callable supplied by ``@st.composite``.

    Returns:
        A dict describing the target-directory tree to materialize.
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
    dot_files = draw(st.lists(st_dot_name(), max_size=3))
    dot_dirs = draw(st.lists(st_dot_name(), max_size=3))
    seed_readme = draw(st.booleans())

    # Deduplicate every top-level name case-insensitively across all categories
    # so materialization cannot collide on a case-insensitive filesystem. When a
    # README.md is seeded, its key is reserved first so no eligible file shadows it.
    seen: set[str] = set()
    if seed_readme:
        seen.add(_INDEX_FILENAME.lower())

    def _dedupe(names):
        unique = []
        for name in names:
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(name)
        return unique

    unique_files = _dedupe(files)
    unique_dirs = []
    for spec in dirs:
        key = spec["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique_dirs.append(spec)
    unique_dot_files = _dedupe(dot_files)
    unique_dot_dirs = _dedupe(dot_dirs)

    return {
        "files": unique_files,
        "dirs": unique_dirs,
        "dot_files": unique_dot_files,
        "dot_dirs": unique_dot_dirs,
        "seed_readme": seed_readme,
    }


def _materialize_target_tree(target_root: Path, tree: dict) -> None:
    """Create the target-directory tree described by an ``st_target_tree()`` spec.

    Args:
        target_root: Directory under which to materialize the tree (created if absent).
        tree: A spec dict as produced by ``st_target_tree()``.
    """
    target_root.mkdir(parents=True, exist_ok=True)
    for name in tree["files"]:
        (target_root / name).write_text(f"# {name}\n", encoding="utf-8")
    for spec in tree["dirs"]:
        subdir = target_root / spec["name"]
        subdir.mkdir(parents=True, exist_ok=True)
        for nested in spec["nested"]:
            (subdir / nested).write_text(f"# {nested}\n", encoding="utf-8")
    for name in tree["dot_files"]:
        (target_root / name).write_text("hidden\n", encoding="utf-8")
    for name in tree["dot_dirs"]:
        (target_root / name).mkdir(parents=True, exist_ok=True)
    if tree["seed_readme"]:
        (target_root / _INDEX_FILENAME).write_text("# stale index\n", encoding="utf-8")


class TestEnumerationProperties:
    """Feature: graduation-enrichment — depth-1 enumeration properties for
    ``generate_directory_index.scan_entries``.

    Validates that enumeration matches exactly the eligible top-level entries:
    every regular file and immediate subdirectory located at depth 1 of the
    target directory, excluding the ``README.md`` index file and dot-prefixed
    names, with each subdirectory counted exactly once and nested files never
    surfacing as separate entries.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    """

    @given(tree=st_target_tree())
    def test_enumeration_matches_eligible_top_level_entries(self, tree):
        # Feature: graduation-enrichment, Property 1: Enumeration matches the eligible top-level entries
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            eligible_files = set(tree["files"])
            eligible_dirs = {spec["name"] for spec in tree["dirs"]}
            eligible = eligible_files | eligible_dirs

            entries = gdi.scan_entries(target_root)
            names = [entry.name for entry in entries]

            # Each eligible entry appears exactly once (no duplicates).
            assert len(names) == len(set(names)), "an entry was enumerated more than once"
            # The enumerated entry-name set equals the eligible depth-1 set —
            # every depth-1 regular file and immediate subdirectory, with the
            # README.md index file and dot-prefixed names excluded.
            assert set(names) == eligible
            # Files and subdirectories are classified correctly.
            assert {e.name for e in entries if not e.is_dir} == eligible_files
            assert {e.name for e in entries if e.is_dir} == eligible_dirs
            # Each subdirectory appears exactly once (contents not recursed into).
            for spec in tree["dirs"]:
                count = sum(1 for e in entries if e.name == spec["name"])
                assert count == 1, f"subdirectory {spec['name']!r} appeared {count} times"
            # Nested files (inside subdirectories) never surface as entries.
            nested_only = {
                nested for spec in tree["dirs"] for nested in spec["nested"]
            } - eligible
            assert nested_only.isdisjoint(set(names)), (
                "a nested file leaked into the top-level enumeration"
            )
        finally:
            shutil.rmtree(tmp)


class TestExclusionProperties:
    """Feature: graduation-enrichment — exclusion properties for
    ``generate_directory_index.scan_entries``.

    Validates that the ``README.md`` index file and every dot-prefixed entry are
    always excluded from the enumeration, even when they are present on disk: a
    seeded stale ``README.md`` and arbitrary dot-prefixed files and directories
    never surface as enumerated entries.

    **Validates: Requirements 2.6, 2.8**
    """

    @given(tree=st_target_tree())
    def test_index_file_and_dot_entries_are_excluded(self, tree):
        # Feature: graduation-enrichment, Property 2: The index file and dot-prefixed entries are always excluded
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            names = [entry.name for entry in gdi.scan_entries(target_root)]

            # The README.md index file never appears, even when a stale
            # README.md was seeded on disk (Requirement 2.6).
            assert _INDEX_FILENAME not in names, (
                "the README.md index file leaked into the enumeration"
            )
            # No entry name begins with '.', even when dot-prefixed files and
            # directories were materialized on disk (Requirement 2.8).
            dotted = [name for name in names if name.startswith(".")]
            assert not dotted, f"dot-prefixed entries leaked into the enumeration: {dotted}"
        finally:
            shutil.rmtree(tmp)


class TestOrderingProperties:
    """Feature: graduation-enrichment — ordering and determinism properties for
    ``generate_directory_index``.

    Validates that enumerated entries are listed in case-insensitive alphabetical
    order by name (ties broken by name to match the implementation's
    ``(name.lower(), name)`` sort key), and that generating the full index from
    identical target-directory contents produces byte-identical output —
    regardless of filesystem creation or iteration order.

    **Validates: Requirements 2.7, 1.5**
    """

    @given(st_target_tree())
    def test_entry_order_is_deterministic_and_case_insensitive(self, tree):
        # Feature: graduation-enrichment, Property 3: Entry order is deterministic and case-insensitive
        tmp = Path(tempfile.mkdtemp())
        tmp2 = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            entries = gdi.scan_entries(target_root)
            names = [entry.name for entry in entries]

            # The enumerated names are in case-insensitive alphabetical order.
            assert names == sorted(names, key=str.lower)

            # The order equals the eligible entry names sorted with the same key
            # the implementation uses: case-insensitive, ties broken by name.
            eligible = list(tree["files"]) + [spec["name"] for spec in tree["dirs"]]
            expected = sorted(eligible, key=lambda name: (name.lower(), name))
            assert names == expected

            # (a) Generating twice from the same directory is byte-identical.
            purpose_map = gdi.select_purpose_map(target_root)
            first = gdi.generate_index(target_root, purpose_map)
            second = gdi.generate_index(target_root, purpose_map)
            assert first == second

            # (b) Materializing the SAME spec into a different temp directory
            # yields identical output, proving order is independent of the
            # filesystem's creation/iteration order.
            other_root = tmp2 / "src"
            _materialize_target_tree(other_root, tree)
            other = gdi.generate_index(other_root, gdi.select_purpose_map(other_root))
            assert first == other
        finally:
            shutil.rmtree(tmp)
            shutil.rmtree(tmp2)


class TestRegenerationProperties:
    """Feature: graduation-enrichment — regeneration and idempotency properties
    for ``generate_directory_index``.

    Validates that regenerating a directory index fully replaces whatever content
    a prior ``README.md`` held — retaining nothing unique to the stale file — so
    the on-disk result equals a fresh ``generate_index(target_root)`` (Requirement
    1.3), and that generating a second time from identical target-directory
    contents produces byte-identical on-disk output (Requirement 1.5).

    **Validates: Requirements 1.3, 1.5**
    """

    @given(st_target_tree(), st.text())
    def test_regeneration_replaces_prior_content_and_is_idempotent(self, tree, stale):
        # Feature: graduation-enrichment, Property 4: Regeneration fully replaces prior content and is idempotent
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            # Seed an arbitrary stale README.md on disk *before* generating. Since
            # scan_entries excludes the README.md index file, this stale content
            # never influences enumeration — it only proves that regeneration
            # fully replaces prior contents rather than merging with them.
            index_path = target_root / _INDEX_FILENAME
            index_path.write_text(stale, encoding="utf-8")

            purpose_map = gdi.select_purpose_map(target_root)

            # Generate and atomically write the index over the stale file.
            gdi.write_index_atomically(
                target_root, gdi.generate_index(target_root, purpose_map), purpose_map
            )

            # (Requirement 1.3) The on-disk index equals a fresh generation, so no
            # content unique to the prior stale README.md survives.
            fresh = gdi.generate_index(target_root, purpose_map)
            after_first = index_path.read_text(encoding="utf-8")
            assert after_first == fresh, "regeneration did not fully replace prior content"

            # (Requirement 1.5) Regenerating from identical target contents produces
            # byte-identical on-disk output.
            gdi.write_index_atomically(
                target_root, gdi.generate_index(target_root, purpose_map), purpose_map
            )
            after_second = index_path.read_text(encoding="utf-8")
            assert after_second == after_first, "second regeneration was not byte-identical"
        finally:
            shutil.rmtree(tmp)


class TestRoundTripProperties:
    """Feature: graduation-enrichment — round-trip properties for
    ``generate_directory_index``.

    Validates that the rendered Markdown index round-trips as a valid table of
    contents: parsing the rendered output back into a set of list-item names
    returns exactly the set of rendered entry names, and ``validate_toc`` accepts
    the rendered output as a well-formed table of contents for the described
    entries.

    **Validates: Requirements 1.4, 1.6**
    """

    @given(st_target_tree())
    def test_rendered_index_round_trips_as_valid_toc(self, tree):
        # Feature: graduation-enrichment, Property 5: Rendered index round-trips as a valid Markdown table of contents
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            purpose_map = gdi.select_purpose_map(target_root)
            markdown = gdi.generate_index(target_root, purpose_map)

            # Parse the rendered output back into the set of list-item names by
            # matching each line with the implementation's list-item regex and
            # collecting the captured name group (which includes the trailing
            # SUBDIR_INDICATOR for subdirectories, exactly as rendered).
            parsed_names = set()
            for line in markdown.split("\n"):
                match = gdi._LIST_ITEM_RE.match(line)
                if match is not None:
                    parsed_names.add(match.group("name"))

            # Reconstruct the expected rendered names directly from the enumerated
            # entries: a subdirectory's rendered name carries the trailing
            # indicator; a file's does not.
            scanned = gdi.scan_entries(target_root)
            expected_names = {
                entry.name + gdi.SUBDIR_INDICATOR if entry.is_dir else entry.name
                for entry in scanned
            }

            # Round-trip: parsing the rendered output yields exactly the set of
            # rendered entry names — nothing added, nothing lost.
            assert parsed_names == expected_names

            # validate_toc accepts the rendered output for the described entries,
            # rebuilt the same way generate_index describes them (scan then
            # apply describe_entry per entry using the target's purpose map).
            described = [
                gdi.DirEntry(
                    name=entry.name,
                    is_dir=entry.is_dir,
                    description=gdi.describe_entry(entry.name, entry.is_dir, purpose_map),
                )
                for entry in scanned
            ]
            assert gdi.validate_toc(markdown, described) is True
        finally:
            shutil.rmtree(tmp)


class TestDescriptionProperties:
    """Feature: graduation-enrichment — description properties for
    ``generate_directory_index``.

    Validates that every listed entry shows its name together with exactly one
    synopsis rendered on a single line of 1 to 120 characters. Because
    ``st_target_tree()`` mixes curated purpose-map names with random unknown
    names, this covers both mapped synopses (known names) and the non-empty
    generic fallback synopsis (unknown names) — every entry is described within
    the same bounds, and none is omitted.

    **Validates: Requirements 3.1, 3.3**
    """

    @given(st_target_tree())
    def test_every_entry_has_exactly_one_well_formed_description(self, tree):
        # Feature: graduation-enrichment, Property 6: Every entry has exactly one well-formed description
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            purpose_map = gdi.select_purpose_map(target_root)
            markdown = gdi.generate_index(target_root, purpose_map)

            # Parse every list item into its (name, description) pair using the
            # implementation's list-item regex. The captured name carries the
            # trailing SUBDIR_INDICATOR for subdirectories, exactly as rendered.
            parsed: list[tuple[str, str]] = []
            for line in markdown.split("\n"):
                match = gdi._LIST_ITEM_RE.match(line)
                if match is not None:
                    parsed.append((match.group("name"), match.group("description")))

            # The rendered-name form for each enumerated entry: a subdirectory
            # carries the trailing indicator; a file does not.
            expected_names = [
                entry.name + gdi.SUBDIR_INDICATOR if entry.is_dir else entry.name
                for entry in gdi.scan_entries(target_root)
            ]

            # (Requirement 3.1) Every enumerated entry appears in EXACTLY ONE
            # list item — its name shown together with exactly one synopsis.
            parsed_names = [name for name, _ in parsed]
            for expected in expected_names:
                count = parsed_names.count(expected)
                assert count == 1, (
                    f"entry {expected!r} appeared in {count} list items, expected exactly one"
                )

            # (Requirements 3.1, 3.3) Each synopsis — for both known-name entries
            # (mapped) and unknown-name entries (generic fallback) — is a single
            # line of 1 to 120 characters, never omitted.
            for name, description in parsed:
                assert "\n" not in description, (
                    f"description for {name!r} spans multiple lines"
                )
                assert "\r" not in description, (
                    f"description for {name!r} contains a carriage return"
                )
                assert 1 <= len(description) <= gdi.MAX_DESCRIPTION_LEN, (
                    f"description for {name!r} has length {len(description)}, "
                    f"expected 1..{gdi.MAX_DESCRIPTION_LEN}"
                )
        finally:
            shutil.rmtree(tmp)


class TestIndicatorProperties:
    """Feature: graduation-enrichment — subdirectory-indicator properties for
    ``generate_directory_index``.

    Validates that the rendered index applies a consistent visual indicator (a
    trailing ``/``) to every subdirectory entry that is applied to no file entry,
    so each entry is unambiguously identifiable as either a file or a
    subdirectory. Because ``st_target_tree()`` file names always contain a ``.``
    and never end with the indicator, and directory names never contain the
    indicator, each parsed rendered name maps back to its scanned entry
    unambiguously by stripping a trailing indicator to recover the bare name.

    **Validates: Requirement 3.2**
    """

    @given(st_target_tree())
    def test_subdirectories_carry_indicator_files_never_do(self, tree):
        # Feature: graduation-enrichment, Property 7: Subdirectories carry a visual indicator that files never carry
        tmp = Path(tempfile.mkdtemp())
        try:
            target_root = tmp / "src"
            _materialize_target_tree(target_root, tree)

            purpose_map = gdi.select_purpose_map(target_root)
            markdown = gdi.generate_index(target_root, purpose_map)

            # Parse each list item into its rendered name group. The captured
            # name carries the trailing SUBDIR_INDICATOR for subdirectories,
            # exactly as render_markdown emits it.
            parsed_names = []
            for line in markdown.split("\n"):
                match = gdi._LIST_ITEM_RE.match(line)
                if match is not None:
                    parsed_names.append(match.group("name"))

            # The bare directory and file names actually enumerated on disk.
            scanned = gdi.scan_entries(target_root)
            dir_names = {entry.name for entry in scanned if entry.is_dir}
            file_names = {entry.name for entry in scanned if not entry.is_dir}

            indicator = gdi.SUBDIR_INDICATOR

            # Partition the parsed rendered names by whether they carry the
            # trailing indicator.
            with_indicator = {name for name in parsed_names if name.endswith(indicator)}
            without_indicator = {
                name for name in parsed_names if not name.endswith(indicator)
            }

            # Every subdirectory entry renders as ``<dir_name>/`` — the set of
            # names carrying the indicator equals exactly the directory names
            # with the indicator appended, and each ends with the indicator.
            expected_dir_rendered = {name + indicator for name in dir_names}
            assert with_indicator == expected_dir_rendered

            # No file entry carries the indicator — the set of names without the
            # indicator equals exactly the bare file names.
            assert without_indicator == file_names

            # Per-item round-trip: strip a trailing indicator to recover the bare
            # name and confirm it maps back to a directory; a name without the
            # indicator maps back to a file. The mapping is unambiguous because
            # file names contain a "." and directory names never contain "/".
            for name in parsed_names:
                if name.endswith(indicator):
                    bare = name[: -len(indicator)]
                    assert bare in dir_names, (
                        f"{name!r} carries the indicator but is not a subdirectory"
                    )
                    assert bare not in file_names
                else:
                    assert name in file_names, (
                        f"{name!r} lacks the indicator but is not a file"
                    )
                    assert name not in dir_names
        finally:
            shutil.rmtree(tmp)


class TestGenerateDirectoryIndexCLI:
    """Feature: graduation-enrichment — CLI output-contract example tests for
    ``generate_directory_index.main``.

    Concrete (non-property) pytest scenarios covering the stdout/stderr/exit
    contract implemented in task 7.1: where the ``README.md`` index is written
    (over ``src/`` and ``data/``), the clean skip when the target directory is
    absent, success-output ordering, the no-partial-file guarantee on both
    validation and write failures, ``--check`` drift detection (in-sync, stale,
    missing), and purpose-map selection by the target-root's final path
    component.

    Validates: Requirements 1.1, 1.2, 1.6, 4.2, 4.4, 4.5, 10.3, 10.4
    """

    @staticmethod
    def _populate(target_root: Path, names: list[str]) -> None:
        """Materialize a populated target directory with the given entry names.

        A name containing ``.`` becomes a regular file; a bare name becomes a
        subdirectory. The target directory itself is created if absent.

        Args:
            target_root: Directory to populate (created if it does not exist).
            names: Entry names to create as files (dotted) or subdirectories.
        """
        target_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            if "." in name:
                (target_root / name).write_text(f"# {name}\n", encoding="utf-8")
            else:
                (target_root / name).mkdir(parents=True, exist_ok=True)

    def test_writes_index_at_src_and_data_target_roots(self, tmp_path, capsys):
        # Output location (Req 1.1, 1.2): a populated src/ and data/ each get a
        # README.md written at the target root, and main exits 0.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py", "utils"])
        data_dir = tmp_path / "data"
        self._populate(data_dir, ["raw", "samples"])

        assert gdi.main(["--target-root", str(src_dir)]) == 0
        assert (src_dir / gdi.INDEX_FILENAME).is_file()

        assert gdi.main(["--target-root", str(data_dir)]) == 0
        assert (data_dir / gdi.INDEX_FILENAME).is_file()

        # Both runs report success on stdout and write nothing to stderr.
        captured = capsys.readouterr()
        assert captured.err == ""
        assert "Wrote directory index:" in captured.out

    def test_absent_target_skips_cleanly(self, tmp_path, capsys):
        # Skip when target absent (Req 4.2): a non-existent --target-root exits 0
        # with a "not generated" summary and creates no README.
        missing = tmp_path / "src"  # deliberately never created

        assert gdi.main(["--target-root", str(missing)]) == 0

        captured = capsys.readouterr()
        assert "not generated" in captured.out
        assert not (missing / gdi.INDEX_FILENAME).exists()

    def test_success_output_orders_message_before_summary(self, tmp_path, capsys):
        # Success output ordering (Req 4.4, 4.5): the "Wrote directory index:"
        # success message appears BEFORE the one-line summary on stdout.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py"])

        assert gdi.main(["--target-root", str(src_dir)]) == 0

        out = capsys.readouterr().out
        message_pos = out.index("Wrote directory index:")
        summary_pos = out.index("Directory index generated at")
        assert message_pos < summary_pos, (
            "the success message must precede the one-line summary"
        )

    def test_validation_failure_leaves_no_partial_file(
        self, tmp_path, capsys, monkeypatch
    ):
        # No partial file on validation failure (Req 1.6): when validation
        # rejects the rendered index, main exits 1, the existing README is
        # byte-identical to what was seeded, and no temp files are left behind.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py"])
        index_path = src_dir / gdi.INDEX_FILENAME
        seeded = "# pre-existing index\nkeep me untouched\n"
        index_path.write_text(seeded, encoding="utf-8")

        monkeypatch.setattr(gdi, "validate_toc", lambda markdown, entries: False)

        assert gdi.main(["--target-root", str(src_dir)]) == 1

        # The seeded README is untouched (never overwritten).
        assert index_path.read_text(encoding="utf-8") == seeded
        # No leftover temp files from the aborted atomic write.
        leftover = [
            p.name for p in src_dir.iterdir() if p.name.startswith(".dir-index-")
        ]
        assert leftover == [], f"leftover temp files remained: {leftover}"
        # The failure reason is reported to stderr.
        assert "Failed to write directory index" in capsys.readouterr().err

    def test_write_failure_leaves_original_untouched(
        self, tmp_path, capsys, monkeypatch
    ):
        # No partial file on write failure (Req 10.4): when the atomic replace
        # raises, main exits 1 and the existing README is untouched.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py"])
        index_path = src_dir / gdi.INDEX_FILENAME
        seeded = "# pre-existing index\nkeep me untouched\n"
        index_path.write_text(seeded, encoding="utf-8")

        def _raise_oserror(*args, **kwargs):
            raise OSError("simulated os.replace failure")

        monkeypatch.setattr(gdi.os, "replace", _raise_oserror)

        assert gdi.main(["--target-root", str(src_dir)]) == 1

        # The seeded README is untouched because os.replace never succeeded.
        assert index_path.read_text(encoding="utf-8") == seeded
        # The temp file created before the failed replace was cleaned up.
        leftover = [
            p.name for p in src_dir.iterdir() if p.name.startswith(".dir-index-")
        ]
        assert leftover == [], f"leftover temp files remained: {leftover}"
        # The failure reason is reported to stderr.
        assert "Failed to write directory index" in capsys.readouterr().err

    def test_check_detects_in_sync_stale_and_missing(self, tmp_path, capsys):
        # --check drift detection (Req 10.3): an in-sync index exits 0, while a
        # stale index and a missing index each exit 1.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py", "utils"])
        index_path = src_dir / gdi.INDEX_FILENAME

        # Generate a correct index first.
        assert gdi.main(["--target-root", str(src_dir)]) == 0
        capsys.readouterr()  # drain the generation output

        # In sync → exit 0.
        assert gdi.main(["--target-root", str(src_dir), "--check"]) == 0

        # Stale on disk → exit 1.
        index_path.write_text("# tampered index\n", encoding="utf-8")
        assert gdi.main(["--target-root", str(src_dir), "--check"]) == 1

        # Missing on disk → exit 1.
        index_path.unlink()
        assert gdi.main(["--target-root", str(src_dir), "--check"]) == 1

    def test_purpose_map_selection_by_target_root_name(self, tmp_path, capsys):
        # Purpose map selection (Req 10.1): a src/ target uses SRC_PURPOSE_MAP and
        # a data/ target uses DATA_PURPOSE_MAP, so the known synopses appear.
        src_dir = tmp_path / "src"
        self._populate(src_dir, ["main.py"])
        assert gdi.main(["--target-root", str(src_dir)]) == 0
        src_index = (src_dir / gdi.INDEX_FILENAME).read_text(encoding="utf-8")
        assert gdi.SRC_PURPOSE_MAP["main.py"] in src_index
        assert "Application entry point." in src_index

        data_dir = tmp_path / "data"
        self._populate(data_dir, ["raw"])
        assert gdi.main(["--target-root", str(data_dir)]) == 0
        data_index = (data_dir / gdi.INDEX_FILENAME).read_text(encoding="utf-8")
        assert gdi.DATA_PURPOSE_MAP["raw"] in data_index
        assert "Original unprocessed source files." in data_index
