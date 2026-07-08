#!/usr/bin/env python3
"""Validate references to power-owned documentation files.

Scans shipped Power files (``.py``, ``.md``, ``.json``) for references to the
Power's own documentation/asset directories and fails if any referenced file
does not exist. This catches the class of drift where a script or steering file
points at a doc that was renamed or removed (e.g. a script telling the user to
"see docs/guides/<some-removed-guide>.md").

Only *unambiguously Power-owned* directories are checked, so bootcamper runtime
paths (created in the user's own project) are never treated as broken:

    docs/guides/      docs/modules/     docs/policies/
    docs/diagrams/    templates/        steering/

Deliberately NOT checked (ambiguous or runtime-generated, would false-positive):

    docs/ (bare)   docs/feedback/   config/   data/   src/   database/

References may appear power-root-relative (``docs/guides/FAQ.md``), with a
``senzing-bootcamp/`` prefix, or as ``../`` markdown links — all are normalized
to the Power root before the existence check. Glob/placeholder tokens (``*`` and
module-number placeholders like ``NN``) are skipped.

The ``tests/`` tree and the changelogs are excluded: test files legitimately
name removed/synthetic paths, and the changelog is a historical record that
cites files which have since been removed.

Usage:
    python senzing-bootcamp/scripts/validate_doc_references.py
    python senzing-bootcamp/scripts/validate_doc_references.py --list
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

POWER_DIR = Path(__file__).resolve().parent.parent

# Power-owned documentation/asset directories that a reference may target.
# A reference beginning with one of these prefixes must resolve to a real file.
ANCHOR_DIRS: tuple[str, ...] = (
    "docs/guides",
    "docs/modules",
    "docs/policies",
    "docs/diagrams",
    "templates",
    "steering",
)

# File suffixes to scan. The ``tests/`` subtree is excluded separately.
SCANNED_SUFFIXES: frozenset[str] = frozenset({".py", ".md", ".json"})

# Files/dirs excluded from scanning (historical records, dev-only content, and
# generated caches). CHANGELOGs cite removed files by design; the tests tree
# names removed/synthetic paths in preservation and negative tests.
EXCLUDED_NAMES: frozenset[str] = frozenset({"CHANGELOG.md", "CHANGELOG-ARCHIVE.md"})
EXCLUDED_DIR_PARTS: frozenset[str] = frozenset(
    {"tests", "__pycache__", ".hypothesis", ".pytest_cache"}
)

# Intentional references to files that do not (and should not) exist. Mirrors
# the ``validate_links.py`` ``SKIP_PATTERNS`` convention; each entry is
# documented so exemptions stay auditable.
ALLOWED_MISSING: frozenset[str] = frozenset(
    {
        # Metasyntactic placeholder in a lint_steering.py code comment explaining
        # that path-bearing prose refs are repo-relative, not steering names.
        "docs/modules/FOO.md",
        # Retired monolithic registry output. sync_hook_registry.py references
        # this as a deprecated-path sentinel: ``--write`` removes it and
        # ``--verify`` flags it as an orphan. It is superseded by the per-module
        # hook-registry-module-*.md slices.
        "steering/hook-registry-modules.md",
    }
)

# A reference token. The optional ``../`` / ``senzing-bootcamp/`` prefix is
# matched but not captured; ``path`` is always Power-root-relative. A lazy body
# stops at the first extension so ``team.yaml.example`` is captured whole while
# glob forms like ``module-*.md`` never match (``*`` is not a path char).
_ANCHOR_ALT = "|".join(re.escape(a) for a in ANCHOR_DIRS)
_REF_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:\.{1,2}/|senzing-bootcamp/)*"
    r"(?P<path>(?:" + _ANCHOR_ALT + r")/[A-Za-z0-9_./-]+?\.(?:md|ya?ml)(?:\.example)?)"
    r"(?![A-Za-z0-9_.-])"
)

# Module-number placeholder token (e.g. ``hook-registry-module-NN.md``,
# ``MODULE_N_*.md``): an uppercase ``N``/``NN`` run not embedded in a word.
_PLACEHOLDER_RE = re.compile(r"(?<![A-Za-z])N{1,2}(?![A-Za-z])")


@dataclass(frozen=True)
class Reference:
    """A single documentation reference found in a scanned file.

    Attributes:
        source: Power-root-relative path of the file containing the reference.
        line: 1-based line number of the reference.
        target: Power-root-relative path the reference points at.
    """

    source: str
    line: int
    target: str


def color(code: str, text: str) -> str:
    """Wrap ``text`` in an ANSI color when stdout is a TTY."""
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(t: str) -> str:
    """Return ``t`` colored green on a TTY."""
    return color("0;32", t)


def red(t: str) -> str:
    """Return ``t`` colored red on a TTY."""
    return color("0;31", t)


def is_placeholder(target: str) -> bool:
    """Return True if ``target`` contains a module-number placeholder token."""
    return _PLACEHOLDER_RE.search(target) is not None


def find_scanned_files(power_dir: Path) -> list[Path]:
    """Return the shipped Power files to scan, sorted and de-duplicated.

    Excludes the ``tests/`` tree, cache dirs, and the changelogs (see module
    docstring for rationale).
    """
    files: list[Path] = []
    for path in power_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        rel_parts = set(path.relative_to(power_dir).parts)
        if rel_parts & EXCLUDED_DIR_PARTS:
            continue
        files.append(path)
    return sorted(files)


def extract_references(path: Path, power_dir: Path) -> list[Reference]:
    """Extract Power-owned doc references (skipping placeholders) from a file."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    source = str(path.relative_to(power_dir))
    refs: list[Reference] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in _REF_RE.finditer(line):
            target = match.group("path")
            if is_placeholder(target):
                continue
            refs.append(Reference(source=source, line=line_num, target=target))
    return refs


def find_broken_references(power_dir: Path = POWER_DIR) -> list[Reference]:
    """Return references whose target file does not exist under ``power_dir``.

    Args:
        power_dir: The Power root to scan and resolve references against.

    Returns:
        Broken references, sorted by (source, line, target).
    """
    broken: list[Reference] = []
    for path in find_scanned_files(power_dir):
        for ref in extract_references(path, power_dir):
            if ref.target in ALLOWED_MISSING:
                continue
            if not (power_dir / ref.target).is_file():
                broken.append(ref)
    return sorted(broken, key=lambda r: (r.source, r.line, r.target))


def main(argv: list[str] | None = None) -> int:
    """Validate power-owned doc references and return a process exit code."""
    parser = argparse.ArgumentParser(
        description="Validate references to power-owned documentation files."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List every checked reference instead of only failures.",
    )
    args = parser.parse_args(argv)

    scanned = find_scanned_files(POWER_DIR)
    print(f"Scanning {len(scanned)} files in {POWER_DIR} for doc references...")

    if args.list:
        all_refs = [
            ref for path in scanned for ref in extract_references(path, POWER_DIR)
        ]
        for ref in sorted(all_refs, key=lambda r: (r.source, r.line)):
            exists = (POWER_DIR / ref.target).is_file()
            mark = green("✓") if exists else red("✗")
            print(f"  {mark} {ref.source}:{ref.line} -> {ref.target}")
        print(f"\nFound {len(all_refs)} doc reference(s).")

    broken = find_broken_references(POWER_DIR)

    print(f"\n{'=' * 50}")
    if broken:
        print(red(f"FAILED: {len(broken)} reference(s) to missing doc file(s)"))
        for ref in broken:
            print(f"  {red('✗')} {ref.source}:{ref.line} -> {ref.target} (not found)")
        return 1
    print(green("PASSED: All power-owned doc references resolve"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
