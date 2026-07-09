#!/usr/bin/env python3
"""Update the top-level README.md with a managed project-index section.

Inserts or replaces a managed section bounded by HTML-comment markers that links
to the per-directory indexes (``docs/README.md``, ``src/README.md``,
``data/README.md``). Only indexes confirmed to exist at their paths at probe
time are included. All content outside the markers is preserved byte-for-byte,
so the step is a scoped, non-destructive edit rather than a full-file rewrite.
The result is validated (exactly one begin marker preceding exactly one end
marker) and written atomically, so a malformed or partial ``README.md`` is never
left behind.

Usage:
    python3 update_readme_index.py                              # update ./README.md
    python3 update_readme_index.py --readme README.md --project-root .
    python3 update_readme_index.py --check                      # report drift only
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Stable HTML-comment markers that bound the managed section. They are invisible
# in rendered Markdown and let the section be located and replaced on subsequent
# runs, mirroring the project's existing ``<!-- BEGIN GENERATED: ... -->``
# convention (e.g. the example-coverage report).
BEGIN_MARKER = "<!-- BEGIN GENERATED: bootcamp-index -->"
END_MARKER = "<!-- END GENERATED: bootcamp-index -->"


@dataclass(frozen=True)
class IndexRef:
    """A reference to a per-directory index in the managed section.

    Attributes:
        path: Relative path to the index file (e.g. ``docs/README.md``).
        description: One-line synopsis, 1..120 chars, never empty.
        exists: Whether the index file was confirmed to exist at probe time.
    """

    path: str
    description: str
    exists: bool


# Fixed per-directory index references with their one-line synopses, in the order
# they should appear in the managed section. ``probe_indexes`` pairs each of
# these ``(path, description)`` tuples with its on-disk existence to build the
# IndexRef list; only entries confirmed to exist are rendered.
INDEX_REFS: list[tuple[str, str]] = [
    ("docs/README.md", "Documentation index — bootcamp artifacts, guides, and references."),
    ("src/README.md", "Source code index — modules, utilities, and application entry points."),
    ("data/README.md", "Data index — raw sources, transformations, and output files."),
]


def probe_indexes(project_root: Path) -> list[IndexRef]:
    """Detect which per-directory index files exist under a project root.

    Checks the existence of each path in :data:`INDEX_REFS` relative to
    ``project_root`` and returns a matching IndexRef with ``exists`` reflecting
    the actual on-disk state.

    Args:
        project_root: Root directory used to resolve per-directory index paths.

    Returns:
        A list of IndexRef records, one per entry in :data:`INDEX_REFS`, with
        ``exists`` set from disk.
    """
    return [
        IndexRef(
            path=path,
            description=description,
            exists=(project_root / path).is_file(),
        )
        for path, description in INDEX_REFS
    ]


def render_managed_section(refs: list[IndexRef]) -> str:
    """Render the managed-section Markdown for the existing indexes.

    Emits only the refs whose ``exists`` is True as list items, wrapped by
    :data:`BEGIN_MARKER` and :data:`END_MARKER` and introduced by a
    ``## Project Index`` heading.

    Args:
        refs: The candidate index references to render.

    Returns:
        The rendered managed-section Markdown, markers included.
    """
    items = [
        f"- **[{ref.path}]({ref.path})** — {ref.description}"
        for ref in refs
        if ref.exists
    ]

    # A blank line follows the begin marker and the heading so the block is
    # valid CommonMark (a list must be preceded by a blank line). When no
    # indexes exist the section is just the markers plus the heading with an
    # empty list; the list items and their trailing blank line are omitted.
    lines = [BEGIN_MARKER, "", "## Project Index", ""]
    if items:
        lines.extend(items)
        lines.append("")
    lines.append(END_MARKER)

    return "\n".join(lines) + "\n"


def update_readme(readme_path: Path, managed_section: str) -> str:
    """Compute the updated README content with the managed section applied.

    Behaves as a scoped, non-destructive edit:

    - If a well-formed managed section is present (both markers, with the begin
      marker preceding the end marker), the whole ``BEGIN..END`` span — markers
      included — is replaced with ``managed_section`` while every byte outside
      that span is preserved.
    - If the markers are absent or malformed (a begin without an end, or an end
      before a begin), the managed section is appended after the existing
      content, separated by a blank line so it never merges into prior content.
    - If the file does not exist (or is empty), ``managed_section`` alone becomes
      the full content.

    Trailing newlines are handled so that a first run that appends the section
    and a subsequent run that replaces it produce byte-identical output
    (idempotency).

    Args:
        readme_path: Path to the top-level README to update.
        managed_section: The rendered managed section (markers included) to
            insert or replace. Expected to end with a single trailing newline.

    Returns:
        The full updated README content.

    Raises:
        ValueError: When the computed result does not contain exactly one begin
            marker preceding exactly one end marker.
    """
    try:
        content = readme_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        content = ""

    begin_pos = content.find(BEGIN_MARKER)
    end_pos = content.find(END_MARKER)

    if begin_pos != -1 and end_pos != -1 and begin_pos < end_pos:
        # Well-formed markers: replace the whole BEGIN..END span (inclusive).
        # Drop the section's trailing newline so any bytes that followed the old
        # end marker (including a lone "\n" written by a prior append) survive
        # untouched, which is what keeps re-runs byte-identical.
        span_end = end_pos + len(END_MARKER)
        updated = content[:begin_pos] + managed_section.rstrip("\n") + content[span_end:]
    elif content == "":
        # Missing or empty file: the managed section becomes the whole content.
        updated = managed_section
    else:
        # Markers absent or malformed: append after the existing content with a
        # single blank line separating it from what came before.
        separator = "\n" if content.endswith("\n") else "\n\n"
        updated = content + separator + managed_section

    if (
        updated.count(BEGIN_MARKER) != 1
        or updated.count(END_MARKER) != 1
        or updated.find(BEGIN_MARKER) > updated.find(END_MARKER)
    ):
        raise ValueError(
            "managed section must contain exactly one begin marker preceding "
            "exactly one end marker"
        )

    return updated


def write_readme_atomically(readme_path: Path, content: str) -> None:
    """Validate then atomically write the README (temp file + os.replace).

    Confirms the content contains exactly one begin marker preceding exactly one
    end marker before writing to a temp file in the same directory and moving it
    into place. On any failure the temp file is removed and the original file is
    left untouched.

    Args:
        readme_path: Path to the top-level README to write.
        content: The full README content to validate and write.

    Raises:
        ValueError: When the content fails managed-section marker validation.
        OSError: When the atomic write fails; the original file is left intact.
    """
    # Validate the managed-section markers *before* touching any existing file
    # so a malformed or partial README.md is never left behind (Requirement 5.9).
    if (
        content.count(BEGIN_MARKER) != 1
        or content.count(END_MARKER) != 1
        or content.find(BEGIN_MARKER) > content.find(END_MARKER)
    ):
        raise ValueError(
            "README content must contain exactly one begin marker preceding "
            "exactly one end marker"
        )

    # Write to a temp file in the same directory as the target so os.replace is
    # atomic on the same filesystem. On any failure, remove the temp file and
    # leave the original README.md untouched.
    directory = readme_path.parent
    fd, tmp_name = tempfile.mkstemp(dir=str(directory), prefix=".readme-index-", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, readme_path)
    except OSError:
        # Clean up the temp file; the original README.md (if any) is untouched
        # because os.replace either fully succeeds or never ran.
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and update or check the top-level README index.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        Exit code: 0 on success, 1 on error or detected drift.
    """
    parser = argparse.ArgumentParser(
        description="Update or check the top-level README managed project-index section.",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="Path to the top-level README to update (default: README.md).",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Root directory for probing per-directory indexes (default: .).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing; exit non-zero when the on-disk "
        "README differs from a freshly generated one.",
    )
    args = parser.parse_args(argv)

    readme_path = Path(args.readme)
    project_root = Path(args.project_root)

    # Capture whether the README already existed *before* any write so the
    # success message can distinguish an update from a creation (Req 5.4-5.6).
    existed_before = readme_path.exists()

    # Build the managed section from the indexes that currently exist and
    # compute the full updated README content. The pipeline only reads the
    # probed paths and the existing README; it writes nothing.
    try:
        refs = probe_indexes(project_root)
        managed_section = render_managed_section(refs)
        new_content = update_readme(readme_path, managed_section)
    except (ValueError, OSError) as error:
        print(f"Failed to update README index: {error}", file=sys.stderr)
        return 1

    # --check mode: compare the freshly computed content against the on-disk
    # README (an absent file counts as empty) and report drift without writing.
    if args.check:
        try:
            current = readme_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            current = ""
        except OSError as error:
            print(f"Failed to read README index: {error}", file=sys.stderr)
            return 1

        if current == new_content:
            print(f"README index in sync: {readme_path}.")
            return 0
        print(f"README index out of sync: {readme_path}.", file=sys.stderr)
        return 1

    # Default mode: atomically write the updated README. On validation or write
    # failure the original file is left untouched (Req 5.9).
    try:
        write_readme_atomically(readme_path, new_content)
    except (ValueError, OSError) as error:
        print(f"Failed to write README index: {error}", file=sys.stderr)
        return 1

    # Distinguish create vs. update in the success message (Req 5.4, 5.5, 5.6),
    # then follow with a one-line summary mirroring the sibling generator.
    included = sum(1 for ref in refs if ref.exists)
    noun = "index" if included == 1 else "indexes"
    if existed_before:
        print(f"Updated README index: {readme_path}")
    else:
        print(f"Created README index: {readme_path}")
    print(f"README project index links {included} per-directory {noun}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
