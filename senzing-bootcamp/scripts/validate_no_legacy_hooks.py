#!/usr/bin/env python3
"""Fail CI if any shipped artifact still references the legacy hook schema.

This is the stale-legacy-reference gate for the Kiro 1.0 hook migration
(Requirement 14.5). After the migration, every shipped hook is a ``v1`` JSON
wrapper (``{"version": "v1", "hooks": [{name, trigger, matcher, action}]}``) and
the pre-1.0 ``*.kiro.hook`` model — a ``when`` block (``type``/``patterns``/
``toolTypes``) plus a ``then`` block (``askAgent``/``runCommand``) — no longer
exists. This gate scans the *shipped, user-facing* surface and fails (exit 1),
naming each stale reference by file and line, if a legacy artifact reappears.

Scope and scoping rationale
---------------------------
The migration is complete, so a naive substring scan for names like
``agentStop`` or ``.kiro.hook`` would be useless: the migration is *documented*
throughout the shipped tree in legitimate prose (CHANGELOG rename entries,
POWER.md compatibility notes, ``hook-architecture.md`` describing the renamed
``Stop`` trigger, ``hooks/README.md`` explaining the removed manual trigger,
the slash-command files that replace the former manual hooks, and so on). Those
mentions are correct and MUST NOT be flagged. The gate therefore detects
*actual legacy schema usage*, not any occurrence of a legacy word:

* **Legacy hook files** — any ``*.kiro.hook`` file under ``senzing-bootcamp/``
  (excluding the ``scripts/`` and ``tests/`` trees, which legitimately carry
  legacy names as *data*: the rename tables in ``hook_renames.py``, the
  translators in ``hook_matcher.py``/``migrate_hooks.py``, and the validators
  and tests that reference the legacy schema in order to *reject* it). A
  ``*.kiro.hook`` file is matched by *file existence*, never by the substring
  appearing in prose.

* **Hook ``.json`` files** (``hooks/*.json``) — parsed as JSON and inspected
  structurally: a ``when`` or ``then`` key anywhere, a ``trigger`` whose value
  is a legacy trigger name, or an action ``type`` of ``askAgent``/``runCommand``
  all indicate a hook that was not migrated (or was reintroduced) in the legacy
  shape.

* **Hook config ``.yaml`` files** (``hooks/*.yaml`` — ``hook-categories.yaml``,
  ``hooks.lock.yaml``) — scanned line by line, case-sensitively, for a legacy
  trigger/action name used as a mapping *value* (e.g. ``event_type:
  fileEdited``) or a ``.kiro.hook`` path reference. The case-sensitive match is
  essential: the legacy ``preToolUse``/``postToolUse`` triggers differ from the
  1.0 ``PreToolUse``/``PostToolUse`` triggers only by case, and ``event_type:
  PreToolUse`` is the *correct* 1.0 value.

* **Steering and docs ``.md`` files** (``steering/**/*.md``, ``docs/**/*.md``)
  — scanned for two kinds of stale reference. First, an embedded legacy hook
  *definition* (a reintroduced JSON snippet) is flagged unconditionally via its
  JSON key shape (``"when":``, ``"then":``, ``"type": "askAgent"``). Second, a
  *distinctive* legacy identifier — a legacy trigger/action name
  (``fileEdited``, ``agentStop``, ``askAgent`` ...) or a ``.kiro.hook`` path —
  is flagged when it appears on a line that is NOT migration prose. A line is
  treated as legitimate migration prose (and skipped) when it carries a removal
  / historical / routing marker (``legacy``, ``former``, ``renamed``,
  ``removed``, ``dropped``, ``no longer``, ``replaces``, ``slash``, a
  ``/slash-command`` name, ...). This targeted, marker-gated scan is why the
  documentation that *records* the migration passes — ``hook-architecture.md``'s
  "the legacy ``agentStop`` event renamed", ``HOOKS_INSTALLATION_GUIDE.md``'s
  "Kiro 1.0 removes the manual (``userTriggered``) trigger", and the "former
  ``commonmark-validation`` hook ... now the ``/commonmark-validation`` slash
  command" notes all sit on marker-bearing lines — while a doc that still
  *describes the legacy schema as current* (``.kiro.hook`` files with
  ``when``/``then`` blocks and ``fileEdited``/``agentStop`` triggers) is flagged
  by file and line. Generic English words (``when``, ``then``) are never scanned
  in prose; only the JSON key shape counts for those.

Together the gate FAILS if someone reintroduces a legacy ``*.kiro.hook`` file, a
``when``/``then``-shaped hook JSON, or a legacy trigger/action in a shipped hook
or config, and PASSES cleanly against the fully-migrated tree.

The canonical legacy trigger and action names come from ``hook_renames.py`` (the
single source of truth for the migration), extended with the removed manual
``userTriggered`` trigger, so this gate cannot drift from the rename tables.

Usage:
    python senzing-bootcamp/scripts/validate_no_legacy_hooks.py
    python senzing-bootcamp/scripts/validate_no_legacy_hooks.py \\
        --repo-root path/to/checkout

Exit codes:
    0 — No stale legacy hook-schema reference found in the shipped surface.
    1 — At least one stale reference was found (each is printed to stderr with
        its file and line), or an internal error occurred.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

# Allow importing sibling scripts (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hook_renames as renames  # noqa: E402

# ---------------------------------------------------------------------------
# Legacy vocabulary (single-sourced from the rename tables)
# ---------------------------------------------------------------------------

#: The removed manual trigger. Kiro 1.0 has no manual trigger, so it is absent
#: from ``hook_renames.TRIGGER_RENAMES``; a shipped v1 hook must never use it.
_MANUAL_TRIGGER = "userTriggered"

#: Every legacy trigger name that must not appear as hook/config schema: the
#: eight automatic legacy triggers plus the removed manual trigger.
LEGACY_TRIGGERS: frozenset[str] = renames.LEGACY_TRIGGERS | {_MANUAL_TRIGGER}

#: Legacy action ``type`` values (``askAgent``, ``runCommand``).
LEGACY_ACTION_TYPES: frozenset[str] = renames.LEGACY_ACTION_TYPES

#: Legacy trigger + action names, for value-position scans of config/markdown.
_LEGACY_NAMES: frozenset[str] = LEGACY_TRIGGERS | LEGACY_ACTION_TYPES

# Repo-relative anchors.
_POWER_REL = "senzing-bootcamp"
# Subtrees excluded from the *.kiro.hook file walk: the migration tooling and
# its tests legitimately carry legacy names as data / rejection fixtures.
_EXCLUDED_DIRS = frozenset({"scripts", "tests", "__pycache__", ".hypothesis"})

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------


def _alternation(names: frozenset[str]) -> str:
    """Return a regex alternation of the escaped names, longest first.

    Ordering longest-first prevents a shorter name from pre-empting a longer one
    that shares its prefix.

    Args:
        names: The literal names to alternate.

    Returns:
        A regex fragment ``name1|name2|...`` with each name escaped.
    """
    return "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))


# A legacy trigger/action used as a YAML mapping value (``key: fileEdited``) or a
# block-sequence item (``- agentStop``). Case-sensitive on purpose so the 1.0
# ``PreToolUse``/``PostToolUse`` values are never mistaken for legacy ones.
_YAML_VALUE_LEGACY_RE = re.compile(
    r"""(?::|-)\s*                 # a ':' mapping value or '-' sequence item
        ["']?                       # optional opening quote
        (""" + _alternation(_LEGACY_NAMES) + r""")   # a legacy name
        ["']?                       # optional closing quote
        \s*(?:\#.*)?$               # optional trailing comment, then EOL
    """,
    re.VERBOSE,
)

# A literal reference to a legacy hook file (a stale path, not prose).
_KIRO_HOOK_RE = re.compile(r"\.kiro\.hook\b")

# Legacy schema expressed as an embedded JSON hook definition (flagged
# unconditionally: a reintroduced legacy hook block is always stale).
_MD_WHEN_KEY_RE = re.compile(r'"when"\s*:')
_MD_THEN_KEY_RE = re.compile(r'"then"\s*:')
_MD_ACTION_TYPE_RE = re.compile(
    r'"type"\s*:\s*"(' + _alternation(LEGACY_ACTION_TYPES) + r')"'
)

# A distinctive legacy trigger/action identifier as a whole word (case-sensitive
# so 1.0 ``PreToolUse``/``PostToolUse`` are never confused with the legacy
# ``preToolUse``/``postToolUse`` spellings). Used for the marker-gated prose scan
# and for the ``createHook`` belt-and-suspenders check.
_LEGACY_WORD_RE = re.compile(r"\b(" + _alternation(_LEGACY_NAMES) + r")\b")

# Removal / historical / routing markers (lower-cased substrings) that make a
# line legitimate migration prose. A line naming a legacy identifier is flagged
# ONLY when it carries none of these — that is what separates "the legacy
# agentStop event was renamed" (documentation) from "fires on agentStop"
# (a stale description of the current schema). Deliberately tight: broad words
# like "was"/"were" are excluded so ordinary descriptive prose still gets
# flagged when it presents the legacy schema as current.
_MIGRATION_MARKERS: tuple[str, ...] = (
    "legacy",
    "former",
    "formerly",
    "renamed",
    "rename",
    "replaces",
    "replaced",
    "replacement",
    "removed",
    "removes",
    "removal",
    "dropped",
    "drops",
    "no longer",
    "migrat",  # migrated / migration
    "slash",
    "/backup-project",
    "/git-commit",
    "/commonmark-validation",
    "previously",
    "used to",
    "pre-1.0",
    "prior to",
)

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One stale legacy-schema reference located in the shipped surface.

    Attributes:
        path: Repo-root-relative path to the offending file (POSIX separators).
        line: 1-based line number of the reference, or 0 when it applies to the
            whole file (a legacy ``*.kiro.hook`` file's mere existence).
        detail: Human-readable description of what makes the reference stale.
    """

    path: str
    line: int
    detail: str


def _locate(lines: list[str], *tokens: str, start: int = 0) -> int:
    """Return the 1-based line number of the first line containing any token.

    Args:
        lines: The file's lines (without trailing newlines).
        tokens: One or more substrings to search for.
        start: 0-based index to begin the search from.

    Returns:
        The 1-based line number of the first matching line, or 0 if no line
        contains any of the tokens.
    """
    for offset, text in enumerate(lines[start:], start=start):
        if any(token in text for token in tokens):
            return offset + 1
    return 0


# ---------------------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------------------


def find_legacy_hook_files(power_dir: Path, repo_root: Path) -> list[Finding]:
    """Find any residual ``*.kiro.hook`` files in the shipped tree.

    Walks ``power_dir`` and reports every ``*.kiro.hook`` file, skipping the
    ``scripts/`` and ``tests/`` subtrees (and caches) whose legacy names are
    legitimate migration data. Matching is by file name, so a ``.kiro.hook``
    substring appearing only in prose is never reported here.

    Args:
        power_dir: The ``senzing-bootcamp`` directory to walk.
        repo_root: Repository root used to make reported paths relative.

    Returns:
        A list of findings, one per residual legacy hook file (line 0).
    """
    findings: list[Finding] = []
    if not power_dir.is_dir():
        return findings
    for path in sorted(power_dir.rglob("*.kiro.hook")):
        parts = set(path.relative_to(power_dir).parts[:-1])
        if parts & _EXCLUDED_DIRS:
            continue
        findings.append(
            Finding(
                path=_rel(path, repo_root),
                line=0,
                detail=(
                    "legacy *.kiro.hook file must not ship — migrate it to a v1 "
                    "JSON hook (or delete it)"
                ),
            )
        )
    return findings


def _walk_json_for_legacy(node: object) -> list[str]:
    """Collect legacy-schema descriptions from a parsed hook JSON structure.

    Recursively inspects every mapping in the decoded JSON. A mapping is stale
    when it carries a legacy ``when``/``then`` block, a ``trigger`` whose value
    is a legacy trigger name, or a ``type`` whose value is a legacy action type.

    Args:
        node: A decoded JSON value (dict, list, or scalar).

    Returns:
        A list of ``(detail, token)``-style detail strings; empty when clean.
        Each detail embeds the offending literal so the caller can locate the
        source line.
    """
    details: list[str] = []
    if isinstance(node, dict):
        if "when" in node:
            details.append('legacy "when" block :: "when"')
        if "then" in node:
            details.append('legacy "then" block :: "then"')
        trigger = node.get("trigger")
        if isinstance(trigger, str) and trigger in LEGACY_TRIGGERS:
            details.append(f'legacy trigger "{trigger}" :: "{trigger}"')
        type_value = node.get("type")
        if isinstance(type_value, str) and type_value in LEGACY_ACTION_TYPES:
            details.append(f'legacy action type "{type_value}" :: "{type_value}"')
        for value in node.values():
            details.extend(_walk_json_for_legacy(value))
    elif isinstance(node, list):
        for item in node:
            details.extend(_walk_json_for_legacy(item))
    return details


def scan_hook_json_files(power_dir: Path, repo_root: Path) -> list[Finding]:
    """Scan ``hooks/*.json`` for legacy hook-schema shapes.

    Each file is parsed as JSON and inspected structurally. If a file is not
    valid JSON, it falls back to a line scan for the raw legacy tokens so a
    malformed-but-legacy file is still reported rather than silently skipped.

    Args:
        power_dir: The ``senzing-bootcamp`` directory.
        repo_root: Repository root used to make reported paths relative.

    Returns:
        A list of findings for every legacy shape discovered, de-duplicated per
        file by ``(line, detail)``.
    """
    findings: list[Finding] = []
    hooks_dir = power_dir / "hooks"
    if not hooks_dir.is_dir():
        return findings

    for path in sorted(hooks_dir.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        rel = _rel(path, repo_root)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            findings.extend(_scan_json_text_fallback(lines, rel))
            continue

        seen: set[tuple[int, str]] = set()
        for raw_detail in _walk_json_for_legacy(data):
            detail, _, token = raw_detail.partition(" :: ")
            line = _locate(lines, token)
            key = (line, detail)
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding(path=rel, line=line, detail=detail))
    return findings


def _scan_json_text_fallback(lines: list[str], rel: str) -> list[Finding]:
    """Line-scan a non-parseable hook JSON for raw legacy tokens.

    Args:
        lines: The file's lines.
        rel: The repo-root-relative path (for the finding).

    Returns:
        Findings for any line bearing a legacy ``"when"``/``"then"`` key, a
        legacy action type, or a legacy trigger value.
    """
    findings: list[Finding] = []
    for offset, text in enumerate(lines, start=1):
        if _MD_WHEN_KEY_RE.search(text) or _MD_THEN_KEY_RE.search(text):
            findings.append(
                Finding(rel, offset, "legacy when/then block in (invalid) hook JSON")
            )
        name = _LEGACY_WORD_RE.search(text)
        if name:
            findings.append(
                Finding(
                    rel,
                    offset,
                    f'legacy hook trigger/action "{name.group(1)}" in '
                    "(invalid) hook JSON",
                )
            )
    return findings


def scan_hook_config_files(power_dir: Path, repo_root: Path) -> list[Finding]:
    """Scan ``hooks/*.yaml`` configs for legacy trigger values or hook paths.

    Line scan (case-sensitive) reports a legacy trigger/action name used as a
    mapping value or sequence item, and any ``.kiro.hook`` path reference. The
    case-sensitive match keeps the 1.0 ``PreToolUse``/``PostToolUse`` values,
    which differ from the legacy names only by case, from being flagged.

    Args:
        power_dir: The ``senzing-bootcamp`` directory.
        repo_root: Repository root used to make reported paths relative.

    Returns:
        A list of findings for every stale reference in the config files.
    """
    findings: list[Finding] = []
    hooks_dir = power_dir / "hooks"
    if not hooks_dir.is_dir():
        return findings

    for path in sorted(hooks_dir.glob("*.yaml")):
        rel = _rel(path, repo_root)
        for offset, text in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            value_match = _YAML_VALUE_LEGACY_RE.search(text)
            if value_match:
                findings.append(
                    Finding(
                        rel,
                        offset,
                        f'legacy hook name "{value_match.group(1)}" used as a '
                        "config value",
                    )
                )
            if _KIRO_HOOK_RE.search(text):
                findings.append(
                    Finding(rel, offset, "reference to a legacy *.kiro.hook file")
                )
    return findings


def _line_has_marker(text: str) -> bool:
    """Return whether a line reads as legitimate migration/removal prose.

    Args:
        text: The raw line.

    Returns:
        True if the line carries any removal / historical / routing marker
        (case-insensitive), meaning a legacy identifier on it documents the
        migration rather than presenting the legacy schema as current.
    """
    lowered = text.lower()
    return any(marker in lowered for marker in _MIGRATION_MARKERS)


def scan_markdown_files(power_dir: Path, repo_root: Path) -> list[Finding]:
    """Scan steering/docs markdown for stale legacy hook-schema references.

    Two kinds of reference are reported (see the module docstring): an embedded
    legacy hook *definition* (JSON key shape), flagged unconditionally; and a
    distinctive legacy identifier or ``.kiro.hook`` path in *prose*, flagged
    only on lines that are not migration/removal/routing prose.

    Args:
        power_dir: The ``senzing-bootcamp`` directory.
        repo_root: Repository root used to make reported paths relative.

    Returns:
        A list of findings for every stale reference found.
    """
    findings: list[Finding] = []
    for subdir in ("steering", "docs"):
        base = power_dir / subdir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = _rel(path, repo_root)
            for offset, text in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                findings.extend(_scan_markdown_line(text, offset, rel))
    return findings


def _scan_markdown_line(text: str, offset: int, rel: str) -> list[Finding]:
    """Return findings for one markdown line's stale legacy-schema references.

    Args:
        text: The raw line.
        offset: The 1-based line number.
        rel: The repo-root-relative path (for the findings).

    Returns:
        Zero or more findings. Details are de-duplicated so a single line yields
        each distinct reason at most once.
    """
    details: list[str] = []

    def _add(detail: str) -> None:
        if detail not in details:
            details.append(detail)

    # Embedded legacy hook definition — always stale, regardless of context.
    if _MD_WHEN_KEY_RE.search(text) or _MD_THEN_KEY_RE.search(text):
        _add("legacy when/then hook definition in markdown")
    action = _MD_ACTION_TYPE_RE.search(text)
    if action:
        _add(f'legacy action type "{action.group(1)}" in a hook definition')

    # Distinctive legacy identifiers / .kiro.hook in prose — stale unless the
    # line is migration/removal/routing prose (carries a marker).
    if not _line_has_marker(text):
        if _KIRO_HOOK_RE.search(text):
            _add("reference to the legacy *.kiro.hook hook schema")
        identifiers = sorted(set(_LEGACY_WORD_RE.findall(text)))
        if identifiers:
            _add(
                "legacy hook trigger/action name(s) presented as current schema: "
                + ", ".join(identifiers)
            )

    # Belt-and-suspenders: a createHook example carrying a legacy trigger, even
    # on an otherwise marker-bearing line.
    if "createHook" in text:
        legacy_word = _LEGACY_WORD_RE.search(text)
        if legacy_word:
            _add(f'createHook uses legacy trigger "{legacy_word.group(1)}"')

    return [Finding(rel, offset, detail) for detail in details]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _rel(path: Path, repo_root: Path) -> str:
    """Return ``path`` relative to ``repo_root`` using POSIX separators.

    Args:
        path: The absolute path to relativize.
        repo_root: The repository root.

    Returns:
        The relative path as a POSIX string, or the path's string form when it
        is not under ``repo_root``.
    """
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scan_power(repo_root: Path) -> list[Finding]:
    """Run every scanner against the shipped surface under ``repo_root``.

    Args:
        repo_root: Repository root. The shipped surface is ``<repo_root>/
            senzing-bootcamp/{hooks,steering,docs}``.

    Returns:
        All findings, sorted by ``(path, line, detail)`` for stable output.
    """
    power_dir = repo_root / _POWER_REL
    findings: list[Finding] = []
    findings.extend(find_legacy_hook_files(power_dir, repo_root))
    findings.extend(scan_hook_json_files(power_dir, repo_root))
    findings.extend(scan_hook_config_files(power_dir, repo_root))
    findings.extend(scan_markdown_files(power_dir, repo_root))
    return sorted(findings, key=lambda f: (f.path, f.line, f.detail))


def _format_finding(finding: Finding) -> str:
    """Render one finding as ``path:line: detail`` (``path: detail`` when line 0).

    Args:
        finding: The finding to render.

    Returns:
        A single-line, human-readable description of the stale reference.
    """
    location = f"{finding.path}:{finding.line}" if finding.line else finding.path
    return f"{location}: {finding.detail}"


def report(
    findings: list[Finding],
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> None:
    """Print findings to stderr and a summary line to stdout.

    Args:
        findings: The findings produced by :func:`scan_power`.
        stdout: Stream for the pass/fail summary (defaults to ``sys.stdout``).
        stderr: Stream for each finding (defaults to ``sys.stderr``).
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    for finding in findings:
        print(_format_finding(finding), file=err)

    if findings:
        print(
            f"Stale legacy hook-reference gate: FAIL "
            f"({len(findings)} stale reference(s))",
            file=out,
        )
    else:
        print("Stale legacy hook-reference gate: PASS", file=out)


def main(argv: list[str] | None = None) -> int:
    """Scan the shipped surface for stale legacy hook-schema references.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        0 when no stale reference is found, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Fail if any shipped hook, config, steering file, or doc still "
            "references the legacy *.kiro.hook / when-then hook schema."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root containing senzing-bootcamp/ "
            "(default: inferred from this script's location)."
        ),
    )
    args = parser.parse_args(argv)

    # <repo_root>/senzing-bootcamp/scripts/validate_no_legacy_hooks.py
    repo_root = (
        Path(args.repo_root)
        if args.repo_root
        else Path(__file__).resolve().parent.parent.parent
    )

    findings = scan_power(repo_root)
    report(findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
