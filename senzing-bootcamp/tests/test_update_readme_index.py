"""Property-based and unit tests for update_readme_index.py using Hypothesis.

Feature: graduation-enrichment.

Validates the top-level README managed-section updater that points to the
per-directory indexes (``docs/README.md``, ``src/README.md``,
``data/README.md``). The managed section lists an entry for exactly the indexes
confirmed to exist at probe time and omits the ones that do not (Property 8).
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

import update_readme_index as uri  # noqa: E402

# ---------------------------------------------------------------------------
# graduation-enrichment: shared strategies and index-existence materializer
# ---------------------------------------------------------------------------

# The separator ``render_managed_section`` places between the bolded index link
# and its one-line synopsis: ``- **[path](path)** — <synopsis>``. Parsing on it
# lets a test recover the rendered synopsis for length checks.
_SYNOPSIS_SEP = "** — "


def st_index_existence():
    """Generate a boolean triple controlling which per-directory indexes exist.

    The triple is ``(docs_exists, src_exists, data_exists)`` — one boolean per
    entry in :data:`update_readme_index.INDEX_REFS`, in the same order
    (``docs/README.md``, ``src/README.md``, ``data/README.md``). Each boolean
    decides whether ``_materialize_indexes`` writes that index file under the
    temporary project root.

    Returns:
        A Hypothesis strategy producing a 3-tuple of booleans.
    """
    return st.tuples(st.booleans(), st.booleans(), st.booleans())


def _materialize_indexes(project_root: Path, existence: tuple[bool, bool, bool]) -> None:
    """Materialize the per-directory index files selected by ``existence``.

    Pairs each boolean in ``existence`` with the matching path in
    :data:`update_readme_index.INDEX_REFS` (order preserved) and writes a
    ``README.md`` under ``project_root`` for every index flagged ``True``,
    creating parent directories as needed. Indexes flagged ``False`` are left
    absent so ``probe_indexes`` reports them as non-existent.

    Args:
        project_root: Root directory under which to materialize the indexes.
        existence: The ``(docs, src, data)`` boolean triple.
    """
    project_root.mkdir(parents=True, exist_ok=True)
    for (path, _description), should_exist in zip(uri.INDEX_REFS, existence):
        if not should_exist:
            continue
        target = project_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# index\n", encoding="utf-8")


class TestManagedSectionProperties:
    """Feature: graduation-enrichment — managed-section content properties for
    ``update_readme_index.probe_indexes`` and ``render_managed_section``.

    Validates that the managed section rendered for the top-level README lists a
    list-item entry for exactly the per-directory indexes confirmed to exist at
    probe time and omits the entries for indexes that do not exist, with each
    included entry accompanied by a single-line synopsis of 1 to 120 characters,
    and that the section is bounded by the begin and end markers.

    **Validates: Requirements 5.1, 5.2, 5.8**
    """

    @given(st_index_existence())
    def test_managed_section_lists_exactly_existing_indexes(self, existence):
        # Feature: graduation-enrichment, Property 8:
        # Managed section lists exactly the existing per-directory indexes
        tmp = Path(tempfile.mkdtemp())
        try:
            project_root = tmp / "project"
            _materialize_indexes(project_root, existence)

            refs = uri.probe_indexes(project_root)
            section = uri.render_managed_section(refs)

            # The section is bounded by both stable markers (Requirement 5.2).
            assert uri.BEGIN_MARKER in section
            assert uri.END_MARKER in section

            lines = section.splitlines()
            included_count = 0
            for (path, description), should_exist in zip(uri.INDEX_REFS, existence):
                # A list item links the path iff its index file exists on disk.
                matching = [
                    line
                    for line in lines
                    if line.startswith(f"- **[{path}]({path})**")
                ]
                if should_exist:
                    assert len(matching) == 1, (
                        f"expected exactly one entry for existing index {path!r}, "
                        f"found {len(matching)}"
                    )
                    included_count += 1
                    # The rendered entry carries a single-line synopsis of
                    # 1..120 chars (Requirement 5.1, 3-style synopsis bound).
                    line = matching[0]
                    assert _SYNOPSIS_SEP in line, (
                        f"entry for {path!r} is missing its synopsis separator"
                    )
                    synopsis = line.split(_SYNOPSIS_SEP, 1)[1]
                    assert synopsis == description
                    assert 1 <= len(synopsis) <= 120, (
                        f"synopsis for {path!r} must be 1..120 chars, "
                        f"got {len(synopsis)}"
                    )
                else:
                    # A non-existent index is omitted from the section entirely.
                    assert not matching, (
                        f"index {path!r} does not exist but appeared in the section"
                    )
                    assert f"[{path}]({path})" not in section, (
                        f"omitted index {path!r} was still linked in the section"
                    )

            # The section lists an entry for exactly the existing indexes — no
            # more, no fewer.
            rendered_items = [line for line in lines if line.startswith("- **[")]
            assert len(rendered_items) == included_count
            assert included_count == sum(existence)
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# graduation-enrichment: README-content strategy for scoped-write properties
# ---------------------------------------------------------------------------


def st_readme_content():
    """Generate arbitrary top-level README content, with and without markers.

    Two flavors are produced so the scoped-write behavior is exercised on both
    of its branches:

    - **marker-free**: arbitrary Markdown text that contains neither the begin
      nor the end managed-section marker, so ``update_readme`` treats it as a
      README with no managed section and appends one.
    - **with a managed section**: a ``BEGIN_MARKER ... END_MARKER`` block
      surrounded by marker-free prefix and suffix text, so ``update_readme``
      replaces only the marker span and leaves the surrounding bytes untouched.

    The surrounding/inner text is drawn from :func:`hypothesis.strategies.text`
    and filtered so it never accidentally contains either marker string; this
    keeps the generated markers the only ones present and their positions
    unambiguous.

    Returns:
        A Hypothesis strategy producing README content strings.
    """
    marker_free = st.text().filter(
        lambda s: uri.BEGIN_MARKER not in s and uri.END_MARKER not in s
    )
    with_markers = st.builds(
        lambda prefix, inner, suffix: (
            f"{prefix}{uri.BEGIN_MARKER}\n{inner}\n{uri.END_MARKER}{suffix}"
        ),
        marker_free,
        marker_free,
        marker_free,
    )
    return st.one_of(marker_free, with_markers)


class TestScopedWriteProperties:
    """Feature: graduation-enrichment — scoped-write preservation for
    ``update_readme_index.update_readme``.

    Validates that updating the top-level README is a scoped, non-destructive
    edit: every byte outside the managed-section markers is preserved. When the
    README already contains a managed section only the marker span is rewritten
    and the content before the begin marker and after the end marker is
    byte-identical; when it contains no managed section the pre-existing content
    is preserved verbatim as a prefix with the managed section appended. In both
    cases the result carries exactly one begin marker preceding exactly one end
    marker.

    **Validates: Requirements 5.3, 5.4, 5.5**
    """

    @given(st_readme_content(), st_index_existence())
    def test_content_outside_markers_is_preserved(self, readme_content, existence):
        # Feature: graduation-enrichment, Property 9:
        # Content outside markers is preserved (scoped-write)
        tmp = Path(tempfile.mkdtemp())
        try:
            project_root = tmp / "project"
            _materialize_indexes(project_root, existence)

            readme_path = project_root / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")

            # The content ``update_readme`` actually operates on is the file as
            # read back with ``read_text`` (identical to the reader inside
            # ``update_readme``), so use it as the byte-identity baseline. This
            # keeps the assertions exact regardless of any newline normalization
            # applied when the arbitrary text was written to disk.
            original = readme_path.read_text(encoding="utf-8")

            managed_section = uri.render_managed_section(uri.probe_indexes(project_root))
            result = uri.update_readme(readme_path, managed_section)

            begin = uri.BEGIN_MARKER
            end = uri.END_MARKER
            orig_begin = original.find(begin)
            orig_end = original.find(end)
            had_markers = (
                orig_begin != -1 and orig_end != -1 and orig_begin < orig_end
            )

            if had_markers:
                # Only the BEGIN..END span is rewritten: the bytes before the
                # begin marker and after the end marker are unchanged (Req 5.3,
                # 5.4).
                orig_after_end = orig_end + len(end)
                res_begin = result.find(begin)
                res_after_end = result.find(end) + len(end)
                assert result[:res_begin] == original[:orig_begin], (
                    "content before the begin marker was modified"
                )
                assert result[res_after_end:] == original[orig_after_end:], (
                    "content after the end marker was modified"
                )
            else:
                # No pre-existing managed section: the original content is
                # preserved verbatim as a prefix and the section is appended
                # (Req 5.5). All original content is "outside the markers", so
                # preserving it as a prefix preserves every outside byte.
                assert result.startswith(original), (
                    "pre-existing content was not preserved as a prefix"
                )

            # In both branches the result carries exactly one well-formed
            # managed section (Req 5.4 marker invariant).
            assert result.count(begin) == 1
            assert result.count(end) == 1
            assert result.find(begin) < result.find(end)
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# graduation-enrichment: idempotency property for the scoped README update
# ---------------------------------------------------------------------------


class TestIdempotencyProperties:
    """Feature: graduation-enrichment — idempotency of the README update for
    ``update_readme_index.update_readme``.

    Validates that, once the top-level README carries the managed section, a
    subsequent run whose per-directory index state and rendered managed section
    are unchanged produces a byte-identical README. The first run either appends
    or replaces the managed section; writing that result back and running again
    over the same index state must reproduce the exact same bytes, so graduation
    can re-run the step without drift.

    **Validates: Requirement 5.7**
    """

    @given(st_readme_content(), st_index_existence())
    def test_readme_update_is_idempotent(self, readme_content, existence):
        # Feature: graduation-enrichment, Property 10: README update is idempotent
        tmp = Path(tempfile.mkdtemp())
        try:
            project_root = tmp / "project"
            _materialize_indexes(project_root, existence)

            readme_path = project_root / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")

            # The managed section reflects the unchanged on-disk index state and
            # is held fixed across both runs, matching the idempotency premise
            # (indexes and managed section unchanged between consecutive runs).
            managed_section = uri.render_managed_section(uri.probe_indexes(project_root))

            # First run: compute the updated content, then write it back so the
            # second run observes the file exactly as the atomic write would have
            # left it (Req 5.7).
            first = uri.update_readme(readme_path, managed_section)
            readme_path.write_text(first, encoding="utf-8")

            # Second run over the identical, unchanged state.
            second = uri.update_readme(readme_path, managed_section)
            assert second == first, (
                "second run over unchanged index state and managed section "
                "produced different bytes"
            )

            # A third run stays fixed as well, confirming the update reached a
            # stable fixed point rather than merely alternating.
            readme_path.write_text(second, encoding="utf-8")
            third = uri.update_readme(readme_path, managed_section)
            assert third == second, (
                "third run over unchanged state was not byte-identical"
            )
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# graduation-enrichment: CLI output-contract example tests for main()
# ---------------------------------------------------------------------------


class TestUpdateReadmeIndexCLI:
    """Feature: graduation-enrichment — CLI output-contract tests for
    ``update_readme_index.main``.

    Concrete, example-based (non-property) coverage of the stdout/stderr/exit
    contract implemented in task 7.2: creating a missing README, appending a
    managed section to a marker-free README, replacing only the marker span of
    a README that already has one, leaving the original untouched on a write
    failure, ``--check`` drift detection that never writes, and omitting the
    entries for per-directory indexes that do not exist.

    **Validates: Requirements 5.4, 5.5, 5.6, 5.8, 5.9, 10.3**
    """

    def test_create_when_missing(self, tmp_path, capsys):
        # Req 5.6: no existing README -> the file is created with the managed section.
        project_root = tmp_path / "project"
        _materialize_indexes(project_root, (True, True, True))
        readme_path = project_root / "README.md"
        assert not readme_path.exists()

        exit_code = uri.main(
            ["--readme", str(readme_path), "--project-root", str(project_root)]
        )

        assert exit_code == 0
        assert readme_path.is_file()
        content = readme_path.read_text(encoding="utf-8")
        assert uri.BEGIN_MARKER in content
        assert uri.END_MARKER in content

        captured = capsys.readouterr()
        assert "Created README index:" in captured.out

    def test_append_when_no_markers(self, tmp_path, capsys):
        # Req 5.5: an existing marker-free README keeps its content as a prefix.
        project_root = tmp_path / "project"
        _materialize_indexes(project_root, (True, True, True))
        readme_path = project_root / "README.md"

        original = "# Existing Project\n\nHand-written intro that must survive.\n"
        readme_path.write_text(original, encoding="utf-8")

        exit_code = uri.main(
            ["--readme", str(readme_path), "--project-root", str(project_root)]
        )

        assert exit_code == 0
        result = readme_path.read_text(encoding="utf-8")
        # The pre-existing content is preserved verbatim as a prefix and the
        # managed section is appended after it.
        assert result.startswith(original)
        assert uri.BEGIN_MARKER in result
        assert uri.END_MARKER in result
        assert "## Project Index" in result

        captured = capsys.readouterr()
        assert "Updated README index:" in captured.out

    def test_replace_between_markers(self, tmp_path, capsys):
        # Req 5.4: only the content between the markers is refreshed; the
        # surrounding content is left byte-for-byte unchanged.
        project_root = tmp_path / "project"
        _materialize_indexes(project_root, (True, True, True))
        readme_path = project_root / "README.md"

        prefix = "# Title\n\nIntro paragraph that precedes the managed block.\n\n"
        stale_body = "\n## Project Index\n\n- **[stale](stale)** — outdated entry\n\n"
        suffix = "\nTrailing footer content that follows the managed block.\n"
        readme_path.write_text(
            prefix + uri.BEGIN_MARKER + stale_body + uri.END_MARKER + suffix,
            encoding="utf-8",
        )

        exit_code = uri.main(
            ["--readme", str(readme_path), "--project-root", str(project_root)]
        )

        assert exit_code == 0
        result = readme_path.read_text(encoding="utf-8")

        # The bytes before the begin marker and after the end marker are
        # identical to what was seeded; only the marker span changed.
        assert result[: result.find(uri.BEGIN_MARKER)] == prefix
        assert result[result.find(uri.END_MARKER) + len(uri.END_MARKER) :] == suffix
        # The stale inner content was replaced by the freshly rendered section.
        assert "outdated entry" not in result
        assert "[docs/README.md](docs/README.md)" in result
        # Still exactly one well-formed managed section.
        assert result.count(uri.BEGIN_MARKER) == 1
        assert result.count(uri.END_MARKER) == 1

    def test_no_partial_file_on_write_failure(self, tmp_path, monkeypatch):
        # Req 5.9: a write failure exits 1 and leaves the original untouched.
        project_root = tmp_path / "project"
        _materialize_indexes(project_root, (True, True, True))
        readme_path = project_root / "README.md"

        original = "# Project\n\nExisting content that must not be corrupted.\n"
        readme_path.write_text(original, encoding="utf-8")
        original_bytes = readme_path.read_bytes()

        # Force the atomic move to fail after the temp file is written; the
        # scoped-write cleanup must remove the temp file and never touch the
        # original README.md.
        def _boom(*_args, **_kwargs):
            raise OSError("simulated os.replace failure")

        monkeypatch.setattr(uri.os, "replace", _boom)

        exit_code = uri.main(
            ["--readme", str(readme_path), "--project-root", str(project_root)]
        )

        assert exit_code == 1
        assert readme_path.read_bytes() == original_bytes

    def test_check_detects_drift_without_writing(self, tmp_path):
        # Req 10.3: --check exits 0 in sync, 1 when drift appears, and never
        # writes to the README in either case.
        project_root = tmp_path / "project"
        _materialize_indexes(project_root, (True, False, False))
        readme_path = project_root / "README.md"

        # Bring the README in sync with the current index state.
        assert (
            uri.main(["--readme", str(readme_path), "--project-root", str(project_root)])
            == 0
        )
        # In sync -> exit 0.
        assert (
            uri.main(
                ["--readme", str(readme_path), "--project-root", str(project_root), "--check"]
            )
            == 0
        )

        # Introduce drift: a newly materialized index means the freshly rendered
        # managed section now differs from what is on disk.
        _materialize_indexes(project_root, (True, True, False))
        before_bytes = readme_path.read_bytes()

        assert (
            uri.main(
                ["--readme", str(readme_path), "--project-root", str(project_root), "--check"]
            )
            == 1
        )
        # --check must not modify the README even when it reports drift.
        assert readme_path.read_bytes() == before_bytes

    def test_omit_missing_indexes(self, tmp_path):
        # Req 5.8: only the per-directory indexes that exist are linked.
        project_root = tmp_path / "project"
        # docs and data exist; src is absent.
        _materialize_indexes(project_root, (True, False, True))
        readme_path = project_root / "README.md"

        exit_code = uri.main(
            ["--readme", str(readme_path), "--project-root", str(project_root)]
        )

        assert exit_code == 0
        content = readme_path.read_text(encoding="utf-8")
        assert "[docs/README.md](docs/README.md)" in content
        assert "[data/README.md](data/README.md)" in content
        assert "[src/README.md](src/README.md)" not in content
