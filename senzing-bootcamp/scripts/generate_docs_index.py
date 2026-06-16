#!/usr/bin/env python3
"""Generate a deterministic docs/README.md index for a generated project.

Walks the generated project's ``docs/`` tree, collects every Markdown document
(excluding ``docs/README.md`` itself), derives a short description for each,
groups entries by subdirectory, and writes a stable ``docs/README.md`` index.
Output is deterministic (sorted traversal, stable rendering), so identical input
trees always produce byte-identical output. The generator only ever writes
``docs/README.md``; it never moves, modifies, or deletes any existing document.

Usage:
    python3 generate_docs_index.py                       # write/refresh index
    python3 generate_docs_index.py --docs-root <dir>     # custom docs root
    python3 generate_docs_index.py --check               # report drift only
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DOCS_ROOT = Path("docs")
INDEX_FILENAME = "README.md"

# Markdown extensions treated as documents for indexing purposes.
DOCUMENT_EXTENSIONS = (".md", ".markdown")


@dataclass(frozen=True)
class IndexEntry:
    """A single document entry in the generated docs index.

    Attributes:
        rel: POSIX-style path of the document relative to the docs root
            (e.g. ``mapping/playpalace_mapper.md``).
        description: Short one-line description derived from the document's
            first heading, first non-empty line, or its filename.
    """

    rel: str
    description: str


def is_document(path: Path) -> bool:
    """Return whether a path is an indexable Markdown document.

    Args:
        path: Filesystem path to test.

    Returns:
        True when ``path`` is a regular file with a Markdown extension.
    """
    return path.is_file() and path.suffix.lower() in DOCUMENT_EXTENSIONS


def describe(path: Path) -> str:
    """Derive a short description for a document.

    Uses the first Markdown heading (a line beginning with ``#``); failing that,
    the first non-empty line; falling back to the filename when the file is empty
    or cannot be read.

    Args:
        path: Path to the document to describe.

    Returns:
        A single-line description string with surrounding whitespace stripped.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return path.name

    first_non_empty: str | None = None
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if first_non_empty is None:
            first_non_empty = line
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                return heading

    if first_non_empty is not None:
        return first_non_empty
    return path.name


def collect_entries(docs_root: Path) -> list[IndexEntry]:
    """Collect index entries for every document under a docs root.

    Walks ``docs_root`` recursively in sorted order, excluding the top-level
    ``README.md`` index itself, and builds one IndexEntry per Markdown document.

    Args:
        docs_root: Path to the docs directory to scan.

    Returns:
        A list of IndexEntry records sorted by their POSIX-relative path.
    """
    entries: list[IndexEntry] = []
    for path in sorted(docs_root.rglob("*")):
        if not is_document(path):
            continue
        rel = path.relative_to(docs_root)
        rel_posix = rel.as_posix()
        # Exclude only the top-level index file, not nested READMEs.
        if rel_posix == INDEX_FILENAME:
            continue
        entries.append(IndexEntry(rel=rel_posix, description=describe(path)))
    entries.sort(key=lambda entry: entry.rel)
    return entries


def group_by_subdir(entries: list[IndexEntry]) -> dict[str, list[IndexEntry]]:
    """Group index entries by their immediate subdirectory under the docs root.

    Documents directly under the docs root are grouped under the empty-string
    key ``""``. All other documents are grouped by their first path component.

    Args:
        entries: Index entries to group.

    Returns:
        A dict mapping subdirectory name (``""`` for the docs root) to the list
        of entries in that group, each list sorted by relative path.
    """
    groups: dict[str, list[IndexEntry]] = {}
    for entry in entries:
        parts = entry.rel.split("/")
        subdir = "" if len(parts) == 1 else parts[0]
        groups.setdefault(subdir, []).append(entry)
    for group in groups.values():
        group.sort(key=lambda entry: entry.rel)
    return groups


def render_markdown(groups: dict[str, list[IndexEntry]]) -> str:
    """Render grouped index entries into deterministic Markdown.

    Sections are emitted in sorted subdirectory order, with the docs-root group
    (key ``""``) rendered first. Output is stable for identical inputs.

    Args:
        groups: Mapping of subdirectory name to its index entries.

    Returns:
        The rendered ``docs/README.md`` contents, terminated by a newline.
    """
    lines: list[str] = ["# Documentation Index", ""]

    if not groups:
        lines.append("_No documents found._")
        lines.append("")
        return "\n".join(lines)

    # Root group ("") first, then remaining subdirectories alphabetically.
    ordered_keys = sorted(groups, key=lambda key: (key != "", key))
    for key in ordered_keys:
        heading = "Root" if key == "" else key
        lines.append(f"## {heading}")
        lines.append("")
        for entry in groups[key]:
            lines.append(f"- [{entry.rel}]({entry.rel}) - {entry.description}")
        lines.append("")

    return "\n".join(lines)


def generate_index(docs_root: Path) -> str:
    """Generate the full docs index Markdown for a docs root.

    Args:
        docs_root: Path to the docs directory to index.

    Returns:
        The deterministic ``docs/README.md`` contents.
    """
    entries = collect_entries(docs_root)
    groups = group_by_subdir(entries)
    return render_markdown(groups)


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and generate or check the docs index.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        Exit code: 0 on success (or in-sync index for ``--check``), 1 on error
        or detected drift.
    """
    parser = argparse.ArgumentParser(
        description="Generate a deterministic docs/README.md index.",
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=DEFAULT_DOCS_ROOT,
        help=f"Path to the docs directory (default: {DEFAULT_DOCS_ROOT})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing (exit non-zero when out of sync)",
    )

    args = parser.parse_args(argv)

    docs_root = args.docs_root
    if not docs_root.exists() or not docs_root.is_dir():
        print(
            f"Error: docs root does not exist or is not a directory: {docs_root}",
            file=sys.stderr,
        )
        return 1

    expected = generate_index(docs_root)
    index_path = docs_root / INDEX_FILENAME

    if args.check:
        current = index_path.read_text(encoding="utf-8") if index_path.is_file() else None
        if current == expected:
            print(f"Docs index is in sync: {index_path}")
            return 0
        if current is None:
            print(f"Docs index is missing: {index_path}", file=sys.stderr)
        else:
            print(f"Docs index is out of sync: {index_path}", file=sys.stderr)
        return 1

    index_path.write_text(expected, encoding="utf-8")
    print(f"Wrote docs index: {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
