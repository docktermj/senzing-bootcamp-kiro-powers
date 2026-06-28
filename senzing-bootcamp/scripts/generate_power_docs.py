#!/usr/bin/env python3
"""Regenerate the volatile sections of POWER.md from machine-readable sources.

`POWER.md` ships four volatile sections whose contents derive from
machine-readable sources of truth: the MCP tool list, the hook list and count,
the steering file table, and the module overview table. This generator
regenerates each section in place between marker comments, preserves all
hand-written prose byte-for-byte, and exposes a ``--verify`` mode that CI runs
before the test step.

Modes
-----
--write   (default) Regenerate every in-scope Generated_Region in POWER.md on
          disk, leaving all hand-written prose unchanged. Atomic: POWER.md is
          either fully replaced or left byte-for-byte unchanged.
--verify  Compare what the generator would produce for each Generated_Region
          against the committed POWER.md, report any drift and the exact
          regeneration command, and exit 0 (clean) or 1 (drift). Never writes.

Usage
-----
    python3 senzing-bootcamp/scripts/generate_power_docs.py            # write (default)
    python3 senzing-bootcamp/scripts/generate_power_docs.py --write    # explicit write
    python3 senzing-bootcamp/scripts/generate_power_docs.py --verify   # verify, no writes

Only Python standard-library modules are imported at module top level; PyYAML is
imported only where YAML is parsed, consistent with ``validate_dependencies.py``.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# ---------------------------------------------------------------------------
# Repository-relative default paths
# ---------------------------------------------------------------------------
#
# This module lives at ``<repo_root>/senzing-bootcamp/scripts/generate_power_docs.py``.
# ``REPO_ROOT`` is therefore two parents above the ``scripts`` directory, i.e.
# ``<repo_root>``. All default source paths are resolved against it so the
# generator behaves identically regardless of the current working directory.

_SCRIPTS_DIR = Path(__file__).resolve().parent
_POWER_ROOT = _SCRIPTS_DIR.parent  # <repo_root>/senzing-bootcamp
REPO_ROOT = _POWER_ROOT.parent  # <repo_root>


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GeneratorError(Exception):
    """Source-level invariant violation (bad or missing source data).

    Raised when a source of truth is internally inconsistent — for example
    ``TOTAL_COUNT`` not matching ``len(ALL_TOOLS)``, a hook named in the
    categories file with no matching file, or a steering/module entry missing a
    required field. The caller maps this to a non-zero exit and leaves
    ``POWER.md`` byte-for-byte unchanged.
    """


class MarkerError(Exception):
    """Marker integrity violation in POWER.md.

    Raised when the begin/end Marker_Comments for a Generated_Region are
    missing, unpaired, misordered, or duplicated. The caller maps this to a
    non-zero exit and leaves ``POWER.md`` byte-for-byte unchanged.
    """


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourcePaths:
    """Filesystem locations of every input the generator reads.

    All fields default to the real repository paths (resolved relative to the
    repository root) but are overridable so tests can point the generator at a
    throwaway world under ``tmp_path``.

    Attributes:
        power_md: The POWER.md file to regenerate or verify.
        hooks_dir: Directory containing ``*.kiro.hook`` files.
        hook_categories: The ``hook-categories.yaml`` source.
        steering_index: The ``steering-index.yaml`` source.
        module_deps: The ``module-dependencies.yaml`` source.
        repo_root: Repository root, used to render repo-relative references.
    """

    power_md: Path
    hooks_dir: Path
    hook_categories: Path
    steering_index: Path
    module_deps: Path
    repo_root: Path


@dataclass(frozen=True)
class HookInfo:
    """A single discovered hook and whether it is categorized as critical.

    Attributes:
        hook_id: The hook identifier (the ``*.kiro.hook`` filename stem).
        is_critical: True when the hook is listed under ``critical:`` in
            ``hook-categories.yaml``.
    """

    hook_id: str
    is_critical: bool


@dataclass(frozen=True)
class SteeringFileInfo:
    """A steering file's recorded metadata from the steering index.

    Attributes:
        filename: The steering file name as recorded in the index.
        token_count: The recorded token count for the file.
        size_category: The recorded size category for the file.
    """

    filename: str
    token_count: int
    size_category: str


@dataclass(frozen=True)
class ModuleInfo:
    """A bootcamp module's number and name from the module source.

    Attributes:
        number: The module number.
        name: The module name exactly as recorded.
    """

    number: int
    name: str


@dataclass(frozen=True)
class Sources:
    """All loaded, validated source-of-truth data, ready for rendering.

    Attributes:
        tools: Tool names from ``ALL_TOOLS`` in source order.
        total_count: ``TOTAL_COUNT`` from the MCP tool inventory.
        hooks: Discovered and categorized hooks.
        steering: Steering file records.
        steering_budget_total: ``budget.total_tokens`` from the steering index.
        modules: Module records ordered ascending by number.
    """

    tools: tuple[str, ...]
    total_count: int
    hooks: tuple[HookInfo, ...]
    steering: tuple[SteeringFileInfo, ...]
    steering_budget_total: int
    modules: tuple[ModuleInfo, ...]


@dataclass(frozen=True)
class RegionSpan:
    """The location of one Generated_Region within a POWER.md document.

    Offsets are character offsets into the document string. ``body`` is the
    text strictly between the begin and end marker lines.

    Attributes:
        region_id: The region identifier carried by its markers.
        begin_marker_end: Offset just after the begin marker line.
        end_marker_start: Offset of the end marker line.
        body: Current text strictly between the markers.
    """

    region_id: str
    begin_marker_end: int
    end_marker_start: int
    body: str


@dataclass(frozen=True)
class VerifyResult:
    """The outcome of a Verify_Mode comparison.

    Attributes:
        drifted_region_ids: Ids of regions whose committed body differs from
            the freshly rendered body.
        missing_region_ids: Ids of regions the generator produces but that are
            absent from the committed POWER.md.
    """

    drifted_region_ids: tuple[str, ...]
    missing_region_ids: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True when no region drifted and none are missing."""
        return not self.drifted_region_ids and not self.missing_region_ids

    @property
    def drift_count(self) -> int:
        """Total number of drifted plus missing regions."""
        return len(self.drifted_region_ids) + len(self.missing_region_ids)


# ---------------------------------------------------------------------------
# Default source paths
# ---------------------------------------------------------------------------


def default_source_paths() -> SourcePaths:
    """Return the real repository :class:`SourcePaths`.

    Paths are resolved relative to the repository root so the generator works
    regardless of the current working directory. Tests construct their own
    :class:`SourcePaths` pointing at a throwaway world instead.
    """
    return SourcePaths(
        power_md=_POWER_ROOT / "POWER.md",
        hooks_dir=_POWER_ROOT / "hooks",
        hook_categories=_POWER_ROOT / "hooks" / "hook-categories.yaml",
        steering_index=_POWER_ROOT / "steering" / "steering-index.yaml",
        module_deps=_POWER_ROOT / "config" / "module-dependencies.yaml",
        repo_root=REPO_ROOT,
    )


# ---------------------------------------------------------------------------
# Shared text and filesystem helpers
# ---------------------------------------------------------------------------


def normalize_newlines(text: str) -> str:
    """Normalize line endings to a single trailing Unix newline.

    Converts Windows (``\\r\\n``) and classic-Mac (bare ``\\r``) line endings to
    Unix line-feeds and ensures the result terminates with exactly one trailing
    ``\\n``. An empty string is returned unchanged (no trailing newline is added
    to empty content).

    Args:
        text: The text whose line endings should be normalized.

    Returns:
        The text with all carriage returns removed and, when non-empty,
        terminated by exactly one trailing newline.
    """
    unix = text.replace("\r\n", "\n").replace("\r", "\n")
    if unix == "":
        return unix
    return f"{unix.rstrip(chr(10))}\n"


def write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically.

    The content is written to a temporary file in the same directory as the
    target and then moved over the target with :func:`os.replace`, an atomic
    rename on the same filesystem. No reader ever observes a partially written
    file: either the previous content or the complete new content is present.

    Args:
        path: The destination file to write.
        content: The full text to write to the destination.

    Raises:
        OSError: If the temporary file cannot be created, written, or renamed.
    """
    directory = path.parent
    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as tmp_file:
            tmp_file.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        # On any failure, remove the temp file so no partial artifact is left.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# CommonMark validation
# ---------------------------------------------------------------------------
#
# Before Write_Mode atomically replaces POWER.md, the fully assembled,
# newline-normalized candidate document is validated for CommonMark compliance
# so a malformed render can never be committed (Requirements 5.1 and 5.7). The
# ``markdownlint`` CLI (the same tool ``validate_commonmark.py`` runs in CI) has
# no in-memory single-string API, so the candidate is written to a temporary
# ``.md`` file in a throwaway directory and linted there; the temp directory is
# always removed via ``try/finally``.

# Candidate config locations, repo root first then the power directory, mirroring
# where ``validate_commonmark.py`` looks for ``.markdownlint.json``.
_MARKDOWNLINT_CONFIGS: tuple[Path, ...] = (
    REPO_ROOT / ".markdownlint.json",
    _POWER_ROOT / ".markdownlint.json",
)


def _resolve_markdownlint() -> str | None:
    """Return the runnable ``markdownlint`` command, or ``None`` when absent.

    Resolution mirrors ``validate_commonmark.py``: on Windows the ``.cmd`` shim
    is preferred when present. Returns ``None`` when no ``markdownlint`` binary
    is on ``PATH`` so callers can degrade gracefully.

    Returns:
        The command name to pass to :func:`subprocess.run`, or ``None`` if the
        ``markdownlint`` CLI is not installed.
    """
    ml_cmd = "markdownlint"
    if sys.platform == "win32" and shutil.which("markdownlint.cmd"):
        ml_cmd = "markdownlint.cmd"
    if shutil.which(ml_cmd) is None:
        return None
    return ml_cmd


def validate_commonmark_text(content: str) -> None:
    """Validate that a candidate document string is CommonMark-compliant.

    The candidate ``content`` is written to a temporary ``.md`` file and linted
    with the ``markdownlint`` CLI (the same gate ``validate_commonmark.py`` runs
    in CI), using the repo's ``.markdownlint.json`` config when one is present
    (checked at the repository root and then under ``senzing-bootcamp/``). The
    temporary directory is always cleaned up.

    Graceful degradation: when the ``markdownlint`` CLI is not installed, the
    generator must remain usable in environments without npm (for example a
    local stdlib-only checkout). In that case validation is skipped — a warning
    is printed to stderr and the function returns ``None`` (treated as a pass).
    CI installs ``markdownlint-cli`` separately and runs the real
    ``validate_commonmark.py`` gate, so skipping here does not weaken CI.

    Args:
        content: The fully assembled, newline-normalized candidate document.

    Returns:
        ``None`` on success (valid content, or validation skipped).

    Raises:
        GeneratorError: If the candidate content is not CommonMark-valid. The
            error message includes the ``markdownlint`` output naming the
            violations so the failure is reported.
    """
    ml_cmd = _resolve_markdownlint()
    if ml_cmd is None:
        print(
            "⚠️  CommonMark validation skipped: markdownlint-cli is not installed "
            "(install with: npm install -g markdownlint-cli)",
            file=sys.stderr,
        )
        return None

    tmp_dir = tempfile.mkdtemp(prefix="generate_power_docs_commonmark_")
    try:
        candidate = Path(tmp_dir) / "POWER.md"
        candidate.write_text(content, encoding="utf-8")

        command = [ml_cmd, str(candidate)]
        config = next((cfg for cfg in _MARKDOWNLINT_CONFIGS if cfg.is_file()), None)
        if config is not None:
            command.extend(["--config", str(config)])

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            detail = "\n".join(part for part in (result.stdout, result.stderr) if part)
            raise GeneratorError(
                "CommonMark validation failed for the assembled POWER.md:\n"
                f"{detail.strip()}"
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return None


# ---------------------------------------------------------------------------
# Marker scheme and region location
# ---------------------------------------------------------------------------
#
# Each Generated_Region is delimited by a pair of CommonMark HTML comments
# carrying a stable, unique region identifier, for example::
#
#     <!-- BEGIN GENERATED: mcp-tools -->
#     ... generated body ...
#     <!-- END GENERATED: mcp-tools -->
#
# HTML comments render to nothing, so the markers are invisible in the rendered
# POWER.md. The markers are matched with an anchored, whitespace-tolerant regex
# (``re.MULTILINE``) so leading/trailing spaces around the comment are tolerated
# while every marker must still occupy its own line. Markers are treated as
# prose: they are never rewritten, only the body strictly between them is.

_BEGIN_MARKER_RE = re.compile(
    r"^<!--\s*BEGIN GENERATED:\s*(?P<id>[a-z0-9-]+)\s*-->\s*$",
    re.MULTILINE,
)
_END_MARKER_RE = re.compile(
    r"^<!--\s*END GENERATED:\s*(?P<id>[a-z0-9-]+)\s*-->\s*$",
    re.MULTILINE,
)


def _make_region_span(
    doc: str,
    region_id: str,
    begin_match: re.Match[str],
    end_match: re.Match[str],
) -> RegionSpan:
    """Build a :class:`RegionSpan` from a matched begin/end marker pair.

    The body of the region is the text strictly between the begin marker line
    and the end marker line. ``begin_marker_end`` is the offset of the first
    character after the begin marker's terminating newline; ``end_marker_start``
    is the offset at which the end marker line begins.

    Args:
        doc: The full document text.
        region_id: The region identifier shared by the marker pair.
        begin_match: The match for the begin marker.
        end_match: The match for the end marker.

    Returns:
        A :class:`RegionSpan` describing the located region.
    """
    newline_index = doc.find("\n", begin_match.start())
    begin_marker_end = len(doc) if newline_index == -1 else newline_index + 1
    end_marker_start = end_match.start()
    body = doc[begin_marker_end:end_marker_start]
    return RegionSpan(
        region_id=region_id,
        begin_marker_end=begin_marker_end,
        end_marker_start=end_marker_start,
        body=body,
    )


def locate_regions(doc: str, expected_ids: set[str]) -> dict[str, RegionSpan]:
    """Locate every expected Generated_Region in a POWER.md document.

    Scans all begin and end Marker_Comments in positional order and validates
    their pairing, ordering, and uniqueness, returning a :class:`RegionSpan`
    for each identifier in ``expected_ids``.

    Args:
        doc: The full POWER.md document text.
        expected_ids: The region identifiers that must be present and paired.

    Returns:
        A mapping from region identifier to its :class:`RegionSpan`, containing
        exactly one entry for every identifier in ``expected_ids``.

    Raises:
        MarkerError: If a begin identifier is duplicated, an end marker appears
            before its matching begin marker, a begin marker has no matching
            end marker, or an expected region's markers are missing entirely.
    """
    events: list[tuple[int, str, str, re.Match[str]]] = []
    for match in _BEGIN_MARKER_RE.finditer(doc):
        events.append((match.start(), "begin", match.group("id"), match))
    for match in _END_MARKER_RE.finditer(doc):
        events.append((match.start(), "end", match.group("id"), match))
    events.sort(key=lambda event: event[0])

    open_begins: dict[str, re.Match[str]] = {}
    spans: dict[str, RegionSpan] = {}
    for _offset, kind, region_id, match in events:
        if kind == "begin":
            if region_id in open_begins or region_id in spans:
                raise MarkerError(region_id, "duplicate begin marker")
            open_begins[region_id] = match
        else:  # end marker
            begin_match = open_begins.pop(region_id, None)
            if begin_match is None:
                raise MarkerError(
                    region_id, "end marker appears before its begin marker"
                )
            spans[region_id] = _make_region_span(doc, region_id, begin_match, match)

    if open_begins:
        unmatched_id = next(iter(open_begins))
        raise MarkerError(unmatched_id, "begin marker has no matching end marker")

    missing = sorted(rid for rid in expected_ids if rid not in spans)
    if missing:
        raise MarkerError(missing[0], "missing begin or end marker")

    return {rid: spans[rid] for rid in expected_ids}


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------
#
# ``load_sources`` reads every source of truth and returns a fully populated
# :class:`Sources`. It loads data only; source-level invariant checks (counts,
# missing fields, cross-references) belong to the per-region renderers and the
# render-time validation in later tasks. Any read failure (``OSError``) or parse
# failure (``yaml.YAMLError`` / import failure) is surfaced as a
# :class:`GeneratorError` that names the offending file path and the cause, and
# nothing is ever written.

_HOOK_SUFFIX = ".kiro.hook"


def _load_mcp_inventory() -> tuple[tuple[str, ...], int]:
    """Import the canonical MCP tool inventory and return its tools and count.

    ``mcp_tool_inventory`` lives in the same ``scripts/`` directory as this
    module, so the directory is added to ``sys.path`` (the established
    test/script convention) before importing it. ``ALL_TOOLS`` and
    ``TOTAL_COUNT`` are read directly rather than re-parsed.

    Returns:
        A pair of ``(ALL_TOOLS, TOTAL_COUNT)``.

    Raises:
        GeneratorError: If the inventory module cannot be imported.
    """
    scripts_dir = str(_SCRIPTS_DIR)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        import mcp_tool_inventory as inventory
    except ImportError as exc:
        raise GeneratorError(
            f"{_SCRIPTS_DIR / 'mcp_tool_inventory.py'}: cannot import MCP tool "
            f"inventory — {exc}"
        ) from exc
    return tuple(inventory.ALL_TOOLS), int(inventory.TOTAL_COUNT)


def _load_yaml(path: Path) -> dict:
    """Read and parse a YAML mapping, naming the file on any failure.

    PyYAML is imported here rather than at module top level, consistent with
    ``validate_dependencies.py`` and Requirement 6.2.

    Args:
        path: The YAML file to read and parse.

    Returns:
        The parsed top-level mapping.

    Raises:
        GeneratorError: If the file cannot be read, cannot be parsed as YAML, or
            does not contain a top-level mapping.
    """
    import yaml

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GeneratorError(f"{path}: cannot read source file — {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise GeneratorError(f"{path}: cannot parse YAML — {exc}") from exc
    if not isinstance(data, dict):
        raise GeneratorError(f"{path}: expected a top-level YAML mapping")
    return data


def _category_hook_ids(categories: dict) -> set[str]:
    """Collect every hook id referenced anywhere in ``hook-categories.yaml``.

    The union spans the top-level ``critical:`` list and every list under
    ``modules:`` (each module-number bucket plus the ``any:`` group), so it
    represents the full set of hook ids the categories file claims to cover.

    Args:
        categories: The parsed ``hook-categories.yaml`` mapping.

    Returns:
        The set of all hook ids named anywhere in the categories file.
    """
    ids: set[str] = set(categories.get("critical") or [])
    modules = categories.get("modules") or {}
    if isinstance(modules, dict):
        for bucket in modules.values():
            ids.update(bucket or [])
    return ids


def _load_hooks(hooks_dir: Path, hook_categories: Path) -> tuple[HookInfo, ...]:
    """Discover hook files, mark which are critical, and cross-check categories.

    Hooks are discovered via ``sorted(hooks_dir.glob("*.kiro.hook"))`` so the
    returned order is deterministic. The ``hook_id`` is the filename with the
    ``.kiro.hook`` suffix stripped. A hook is critical when its id appears in
    the top-level ``critical:`` list of ``hook-categories.yaml``.

    Two consistency cross-checks are enforced against the full set of hook ids
    named anywhere in ``hook-categories.yaml`` (the ``critical:`` list and every
    list under ``modules:``, including the ``any:`` group):

    * Every hook id named in the categories file must have a matching
      ``*.kiro.hook`` file (Requirement 10.4).
    * Every discovered ``*.kiro.hook`` file must appear in at least one category
      list (Requirement 10.5).

    Either inconsistency names the first offending hook id (sorted, for
    determinism) and aborts; nothing is written.

    Args:
        hooks_dir: Directory containing ``*.kiro.hook`` files.
        hook_categories: The ``hook-categories.yaml`` source.

    Returns:
        Discovered hooks in glob (sorted) order.

    Raises:
        GeneratorError: If the hooks directory cannot be listed, the categories
            file cannot be read or parsed, a categorized hook has no file, or a
            discovered file appears in no category list.
    """
    try:
        hook_files = sorted(hooks_dir.glob(f"*{_HOOK_SUFFIX}"))
    except OSError as exc:
        raise GeneratorError(f"{hooks_dir}: cannot list hook files — {exc}") from exc

    categories = _load_yaml(hook_categories)
    critical_ids = set(categories.get("critical") or [])
    category_ids = _category_hook_ids(categories)

    discovered_ids = {path.name[: -len(_HOOK_SUFFIX)] for path in hook_files}

    # Req 10.4: every hook id named in the categories file must have a file.
    orphan_categories = sorted(category_ids - discovered_ids)
    if orphan_categories:
        raise GeneratorError(
            f"{hook_categories}: hook '{orphan_categories[0]}' is listed in "
            "hook-categories.yaml but has no matching *.kiro.hook file"
        )

    # Req 10.5: every discovered file must appear in at least one category list.
    uncategorized_files = sorted(discovered_ids - category_ids)
    if uncategorized_files:
        raise GeneratorError(
            f"{hook_categories}: hook file '{uncategorized_files[0]}.kiro.hook' "
            "is not listed in any category list in hook-categories.yaml"
        )

    hooks: list[HookInfo] = []
    for path in hook_files:
        hook_id = path.name[: -len(_HOOK_SUFFIX)]
        hooks.append(HookInfo(hook_id=hook_id, is_critical=hook_id in critical_ids))
    return tuple(hooks)


def _load_steering(steering_index: Path) -> tuple[tuple[SteeringFileInfo, ...], int]:
    """Load steering file metadata and the budget total from the steering index.

    One :class:`SteeringFileInfo` is built per ``file_metadata`` entry, storing
    the recorded ``token_count`` and ``size_category`` as-is. Missing-field
    validation is performed at render time (Requirement 11.5), not here.

    Args:
        steering_index: The ``steering-index.yaml`` source.

    Returns:
        A pair of ``(steering_file_infos, budget_total_tokens)``.

    Raises:
        GeneratorError: If the steering index cannot be read or parsed.
    """
    data = _load_yaml(steering_index)

    file_metadata = data.get("file_metadata") or {}
    steering: list[SteeringFileInfo] = []
    for filename, meta in file_metadata.items():
        meta = meta or {}
        steering.append(
            SteeringFileInfo(
                filename=str(filename),
                token_count=meta.get("token_count"),
                size_category=meta.get("size_category"),
            )
        )

    budget = data.get("budget") or {}
    budget_total = budget.get("total_tokens")
    return tuple(steering), budget_total


def _load_modules(module_deps: Path) -> tuple[ModuleInfo, ...]:
    """Load module records from the module dependency source.

    One :class:`ModuleInfo` is built per entry in the ``modules`` map, using the
    integer map key as the module number and the recorded ``name``. Missing-field
    validation and numeric ordering are applied at render time (Requirement 12).

    Args:
        module_deps: The ``module-dependencies.yaml`` source.

    Returns:
        Module records in source order.

    Raises:
        GeneratorError: If the module source cannot be read or parsed.
    """
    data = _load_yaml(module_deps)
    modules_map = data.get("modules") or {}
    modules: list[ModuleInfo] = []
    for key, value in modules_map.items():
        value = value or {}
        modules.append(ModuleInfo(number=int(key), name=value.get("name")))
    return tuple(modules)


def load_sources(paths: SourcePaths) -> Sources:
    """Read and parse every source of truth into a :class:`Sources`.

    Loads the MCP tool inventory, discovers and categorizes hooks, reads the
    steering index (file metadata and budget total), and reads the module map.
    This function loads data only — source-level invariant checks belong to the
    per-region renderers. On any read or parse failure it raises a
    :class:`GeneratorError` naming the affected file and the cause and never
    writes to disk.

    Args:
        paths: The filesystem locations of every input to read.

    Returns:
        The fully populated source data, ready for rendering.

    Raises:
        GeneratorError: If any source cannot be read, imported, or parsed.
    """
    tools, total_count = _load_mcp_inventory()
    hooks = _load_hooks(paths.hooks_dir, paths.hook_categories)
    steering, steering_budget_total = _load_steering(paths.steering_index)
    modules = _load_modules(paths.module_deps)
    return Sources(
        tools=tools,
        total_count=total_count,
        hooks=hooks,
        steering=steering,
        steering_budget_total=steering_budget_total,
        modules=modules,
    )


# ---------------------------------------------------------------------------
# Region renderer interface
# ---------------------------------------------------------------------------


class Region(Protocol):
    """A single Generated_Region renderer.

    Each region exposes a stable identity and a pure render function whose
    output depends only on ``sources`` — never on the current time, locale, or
    filesystem enumeration order. Concrete regions are implemented in later
    tasks.
    """

    region_id: str

    def render(self, sources: Sources) -> str:
        """Return the deterministic Markdown body for this region.

        Args:
            sources: The loaded source-of-truth data.

        Returns:
            The Markdown body to splice between this region's markers.
        """
        ...


def kiro_include(repo_root: Path, path: Path) -> str:
    """Return a Kiro file-include directive for ``path`` relative to the repo.

    Emits ``#[[file:<repo-relative-path>]]`` using forward slashes. An absolute
    ``path`` is made relative to ``repo_root``; a relative ``path`` is used as
    given.

    Args:
        repo_root: The repository root the include path is relative to.
        path: The referenced file, absolute or repo-relative.

    Returns:
        A ``#[[file:...]]`` include directive with a repo-relative POSIX path.
    """
    candidate = Path(path)
    if candidate.is_absolute():
        rel = candidate.resolve().relative_to(Path(repo_root).resolve())
    else:
        rel = candidate
    return f"#[[file:{rel.as_posix()}]]"


# ---------------------------------------------------------------------------
# MCP tools region
# ---------------------------------------------------------------------------
#
# The MCP tools Generated_Region lists every tool the power exposes, one bullet
# per tool. Tool *names and order* come from ``ALL_TOOLS`` (the single source of
# truth in ``mcp_tool_inventory``); only the human-readable *presentation text*
# lives here, in ``TOOL_DESCRIPTIONS``. Keeping the description map keyed by the
# exact tool ids — with no missing and no extra keys — means adding or removing
# a tool in the inventory forces a matching edit here (a hard error otherwise),
# so the rendered bullets can never silently drift from the inventory.

# Em dash (U+2014) used as the name/description separator in each bullet.
_TOOL_BULLET_SEP = "\u2014"

# Static presentation text for each tool id in ``ALL_TOOLS``. Keys MUST match
# ``set(ALL_TOOLS)`` exactly — every tool needs a description and no extra
# descriptions are allowed.
TOOL_DESCRIPTIONS: dict[str, str] = {
    "get_capabilities": "Discover all tools and workflows",
    "mapping_workflow": "Interactive 8-step data mapping to Senzing JSON",
    "analyze_record": "Analyze and validate mapped data against the Senzing Entity Specification",
    "download_resource": "Download workflow resources (entity spec, analyzer script)",
    "explain_error_code": "Diagnose Senzing errors (456 error codes)",
    "search_docs": "Search indexed Senzing documentation",
    "find_examples": "Working code from 37 Senzing GitHub repositories",
    "generate_scaffold": "Generate SDK code (Python, Java, C#, Rust, TypeScript)",
    "get_sample_data": "Download sample datasets (Las Vegas, London, Moscow)",
    "get_sdk_reference": "SDK method signatures and flags",
    "sdk_guide": "Platform-specific SDK installation and setup",
    "reporting_guide": "Reporting, visualization, and dashboard guidance",
    "submit_feedback": "Report issues or suggestions",
}


class McpToolsRegion:
    """Renderer for the ``mcp-tools`` Generated_Region.

    Emits one Markdown bullet per tool in ``sources.tools`` (``ALL_TOOLS``)
    order, using the static :data:`TOOL_DESCRIPTIONS` presentation text. Each
    bullet has the exact shape ``- `tool_name` — description`` so that
    ``validate_power.py``'s ``_power_md_tool_bullets`` regex (``^- `([a-z_]+)```)
    extracts exactly the tool names. The ``## Available MCP Tools`` header is
    hand-written prose outside the region and is intentionally not rendered here.
    """

    region_id: str = "mcp-tools"

    def render(self, sources: Sources) -> str:
        """Return the Markdown bullet list for the MCP tools region.

        Args:
            sources: The loaded source-of-truth data; ``tools`` and
                ``total_count`` come from the MCP tool inventory.

        Returns:
            One bullet per tool in ``sources.tools`` order, joined by newlines.
            The body is wrapped with a leading and a trailing blank line so the
            bullet list is surrounded by blank lines inside its marker lines
            (CommonMark MD032).

        Raises:
            GeneratorError: If ``sources.total_count`` disagrees with
                ``len(sources.tools)``, or if the tool ids do not match the keys
                of :data:`TOOL_DESCRIPTIONS` exactly (a tool with no description
                or an extra description key). The offending tool(s) are named.
        """
        if sources.total_count != len(sources.tools):
            raise GeneratorError(
                "MCP tool inventory count mismatch: TOTAL_COUNT="
                f"{sources.total_count} but len(ALL_TOOLS)={len(sources.tools)}"
            )

        tool_ids = set(sources.tools)
        description_ids = set(TOOL_DESCRIPTIONS)
        missing = sorted(tool_ids - description_ids)
        if missing:
            raise GeneratorError(
                "MCP tool(s) missing a description in TOOL_DESCRIPTIONS: "
                f"{', '.join(missing)}"
            )
        extra = sorted(description_ids - tool_ids)
        if extra:
            raise GeneratorError(
                "TOOL_DESCRIPTIONS has description(s) for unknown tool(s) not in "
                f"ALL_TOOLS: {', '.join(extra)}"
            )

        lines = [
            f"- `{tool}` {_TOOL_BULLET_SEP} {TOOL_DESCRIPTIONS[tool]}"
            for tool in sources.tools
        ]
        content = "\n".join(lines) + "\n"
        return f"\n{content}\n"


# ---------------------------------------------------------------------------
# Hooks region
# ---------------------------------------------------------------------------
#
# The hooks Generated_Region states how many ``*.kiro.hook`` files ship with the
# power and lists every hook id. Critical hooks (those named under ``critical:``
# in ``hook-categories.yaml``) are marked with a star and listed first. Both the
# count and the list derive solely from the discovered hook files and their
# categorization, so the region can never silently drift from the actual hooks.
# The category cross-checks (a categorized hook with no file, or a file in no
# category) run during source loading (``_load_hooks``), so by the time
# rendering happens ``sources.hooks`` is already known consistent.

# Star (U+2B50) marking a critical hook in the rendered list.
_CRITICAL_MARK = "\u2b50"


class HooksRegion:
    """Renderer for the ``hooks`` Generated_Region.

    Emits a single line stating the hook count followed by every hook id
    wrapped in backticks. Critical hooks are marked with a star and ordered
    first (alphabetical by hook id), then the remaining hooks (alphabetical) —
    a total order derived entirely from the source with the hook id as the
    deterministic tie-breaker. The count equals the number of discovered
    ``*.kiro.hook`` files.
    """

    region_id: str = "hooks"

    def render(self, sources: Sources) -> str:
        """Return the Markdown body for the hooks region.

        Args:
            sources: The loaded source-of-truth data; ``hooks`` carries the
                discovered hooks and their critical flag.

        Returns:
            A single ``Available (N hooks): ...`` line listing every hook id in
            backticks (critical hooks first, marked with a star). The line is
            wrapped with a leading and a trailing blank line so the body is
            surrounded by blank lines inside its marker lines.
        """
        critical = sorted(
            hook.hook_id for hook in sources.hooks if hook.is_critical
        )
        regular = sorted(
            hook.hook_id for hook in sources.hooks if not hook.is_critical
        )

        entries = [f"`{hook_id}` {_CRITICAL_MARK}" for hook_id in critical]
        entries += [f"`{hook_id}`" for hook_id in regular]

        count = len(sources.hooks)
        content = f"Available ({count} hooks): {', '.join(entries)}.\n"
        return f"\n{content}\n"


# ---------------------------------------------------------------------------
# Steering files region
# ---------------------------------------------------------------------------
#
# The steering Generated_Region renders one table row per ``file_metadata``
# entry in ``steering-index.yaml`` — the authoritative per-file record — sorted
# alphabetically by filename, emitting each file's ``token_count`` and
# ``size_category`` exactly as recorded. A footer line emits the budget total
# (``budget.total_tokens``) verbatim. Two source-level invariants are enforced
# at render time: every entry must carry both a ``token_count`` and a
# ``size_category`` (Req 11.5), and every listed steering file must actually
# exist under the steering directory (Req 5.4). Either violation names the
# offender and aborts; nothing is written.


class SteeringRegion:
    """Renderer for the ``steering-files`` Generated_Region.

    Emits a Markdown table with one row per ``file_metadata`` entry from
    ``steering-index.yaml``, sorted alphabetically by filename, followed by a
    footer line stating the total token budget verbatim. The steering directory
    is captured at construction so the existence check (Req 5.4) can be pointed
    at a throwaway world in tests while still defaulting to the real steering
    directory for ordinary use.
    """

    region_id: str = "steering-files"

    def __init__(self, steering_dir: Path | None = None) -> None:
        """Capture the steering directory used for the existence check.

        Args:
            steering_dir: Directory the listed steering files must exist under.
                Defaults to the real steering directory (the parent of the
                ``steering-index.yaml`` source) so a no-argument construction
                works against the real repository.
        """
        if steering_dir is None:
            steering_dir = default_source_paths().steering_index.parent
        self._steering_dir = Path(steering_dir)

    def render(self, sources: Sources) -> str:
        """Return the Markdown table body for the steering files region.

        Args:
            sources: The loaded source-of-truth data; ``steering`` carries the
                per-file records and ``steering_budget_total`` the budget total.

        Returns:
            A Markdown table with one row per steering file (sorted by
            filename) followed by a blank line and a budget footer line. The
            body is wrapped with a leading and a trailing blank line so the
            table and footer are surrounded by blank lines inside the marker
            lines (CommonMark MD058).

        Raises:
            GeneratorError: If a steering entry is missing its ``token_count``
                or ``size_category`` (the file and missing field are named), or
                if a listed steering file does not exist under the steering
                directory (the missing path is named).
        """
        entries = sorted(sources.steering, key=lambda info: info.filename)

        lines = ["| Steering File | Tokens | Size |", "|---|---|---|"]
        for info in entries:
            if info.token_count is None:
                raise GeneratorError(
                    f"steering file '{info.filename}' is missing required "
                    "field 'token_count' in steering-index.yaml"
                )
            if info.size_category is None:
                raise GeneratorError(
                    f"steering file '{info.filename}' is missing required "
                    "field 'size_category' in steering-index.yaml"
                )
            steering_path = self._steering_dir / info.filename
            if not steering_path.exists():
                raise GeneratorError(
                    f"steering file referenced in steering-index.yaml does not "
                    f"exist: {steering_path}"
                )
            lines.append(
                f"| `{info.filename}` | {info.token_count} | {info.size_category} |"
            )

        lines.append("")
        lines.append(f"**Total budget:** {sources.steering_budget_total} tokens")
        content = "\n".join(lines) + "\n"
        return f"\n{content}\n"


# ---------------------------------------------------------------------------
# Modules region
# ---------------------------------------------------------------------------
#
# The modules Generated_Region renders one table row per entry in the
# ``modules`` map of ``module-dependencies.yaml`` — the authoritative module
# source of truth — ordered by module number ascending (numeric sort, Req
# 12.3), emitting each module's number and ``name`` exactly as recorded (Req
# 12.2). A count line states the number of rows, which equals the number of
# recorded modules (Req 12.4). One source-level invariant is enforced at render
# time: every module must carry both a ``number`` and a ``name`` (Req 12.5).
# A violation names the offending module and the missing field and aborts;
# nothing is written. The descriptive "What It Does / Why It Matters" narrative
# table in ``POWER.md`` is hand-written prose and stays outside this region.


class ModulesRegion:
    """Renderer for the ``modules`` Generated_Region.

    Emits a Markdown table with one row per entry in the ``modules`` map of
    ``module-dependencies.yaml``, ordered by module number ascending (numeric
    sort), each row carrying the module number and name exactly as recorded.
    A count line follows, stating the number of rows, which equals the number
    of recorded modules.
    """

    region_id: str = "modules"

    def render(self, sources: Sources) -> str:
        """Return the Markdown table body for the modules region.

        Args:
            sources: The loaded source-of-truth data; ``modules`` carries the
                per-module records.

        Returns:
            A Markdown table with one row per module (ascending by number)
            followed by a blank line and a count line. The body is wrapped with
            a leading and a trailing blank line so the table and count line are
            surrounded by blank lines inside the marker lines (CommonMark
            MD058).

        Raises:
            GeneratorError: If a module is missing its ``number`` or ``name``
                (the offending module and missing field are named).
        """
        for info in sources.modules:
            if info.number is None:
                raise GeneratorError(
                    f"module '{info.name}' is missing required field 'number' "
                    "in module-dependencies.yaml"
                )
            if info.name is None:
                raise GeneratorError(
                    f"module {info.number} is missing required field 'name' "
                    "in module-dependencies.yaml"
                )

        entries = sorted(sources.modules, key=lambda info: info.number)

        lines = ["| # | Module |", "|---|---|"]
        for info in entries:
            lines.append(f"| {info.number} | {info.name} |")

        lines.append("")
        lines.append(f"Total: {len(entries)} modules.")
        content = "\n".join(lines) + "\n"
        return f"\n{content}\n"


# ---------------------------------------------------------------------------
# Orchestration: render and assemble
# ---------------------------------------------------------------------------
#
# ``render_all`` turns the fixed, ordered list of region renderers into a
# mapping of ``region_id -> rendered body``. ``assemble`` splices those bodies
# back into POWER.md using the located :class:`RegionSpan` offsets, replacing
# only the bytes strictly between each region's begin and end markers and
# leaving the markers themselves and every out-of-region byte untouched.


def render_all(sources: Sources, regions: list[Region]) -> dict[str, str]:
    """Render every region body from the loaded sources.

    Iterates the supplied region list in order and renders each region from
    ``sources``. The fixed, ordered region list itself is built by the CLI; this
    function renders whatever list it is given, so the result is deterministic
    whenever the input list and ``sources`` are.

    Args:
        sources: The loaded source-of-truth data shared by every renderer.
        regions: The ordered list of region renderers to render.

    Returns:
        A mapping from each region's ``region_id`` to its rendered Markdown body.

    Raises:
        GeneratorError: If any region's ``render`` reports a source-level
            invariant violation.
    """
    return {region.region_id: region.render(sources) for region in regions}


def assemble(doc: str, spans: dict[str, RegionSpan], bodies: dict[str, str]) -> str:
    """Splice freshly rendered bodies into ``doc`` between region markers.

    For every region present in both ``spans`` and ``bodies``, the text strictly
    between its begin and end markers is replaced by the rendered body. The
    marker comment lines and every byte outside the regions are preserved
    byte-for-byte. Regions are replaced in document order so the resulting string
    is rebuilt in a single forward pass.

    Args:
        doc: The original POWER.md document text.
        spans: The located region spans, keyed by ``region_id``.
        bodies: The freshly rendered region bodies, keyed by ``region_id``.

    Returns:
        A new document with each region's body replaced and all other bytes
        (markers and out-of-region prose) byte-for-byte unchanged.
    """
    replacements = [
        (spans[region_id].begin_marker_end, spans[region_id].end_marker_start, body)
        for region_id, body in bodies.items()
        if region_id in spans
    ]
    replacements.sort(key=lambda item: item[0])

    parts: list[str] = []
    cursor = 0
    for begin_marker_end, end_marker_start, body in replacements:
        parts.append(doc[cursor:begin_marker_end])
        parts.append(body)
        cursor = end_marker_start
    parts.append(doc[cursor:])
    return "".join(parts)


def verify(doc: str, spans: dict[str, RegionSpan], bodies: dict[str, str]) -> VerifyResult:
    """Compare committed region bodies against freshly rendered ones, read-only.

    Performs a per-region byte-for-byte comparison of the committed body (the
    text strictly between markers, carried by each :class:`RegionSpan`) against
    the freshly rendered body. A region the generator produces but that is
    absent from POWER.md (no located span) is reported as missing; a region
    whose committed body differs from its rendered body is reported as drifted.
    This function is pure: it operates only over the in-memory strings and never
    opens any file for reading or writing.

    Args:
        doc: The committed POWER.md document text (unused except as context for
            the located spans; retained for signature symmetry with
            :func:`assemble`).
        spans: The located region spans, keyed by ``region_id``.
        bodies: The freshly rendered region bodies, keyed by ``region_id``.

    Returns:
        A :class:`VerifyResult` whose ``drifted_region_ids`` and
        ``missing_region_ids`` are sorted for deterministic reporting.
    """
    drifted: list[str] = []
    missing: list[str] = []
    for region_id, rendered_body in bodies.items():
        span = spans.get(region_id)
        if span is None:
            missing.append(region_id)
        elif span.body != rendered_body:
            drifted.append(region_id)
    return VerifyResult(
        drifted_region_ids=tuple(sorted(drifted)),
        missing_region_ids=tuple(sorted(missing)),
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


# The exact, runnable command a Developer (or CI) pastes to regenerate the
# volatile sections after Verify_Mode reports drift (Requirement 3.5). It is a
# fixed string anchored at the repository root so the guidance is identical in
# every environment.
REGEN_COMMAND = "python3 senzing-bootcamp/scripts/generate_power_docs.py --write"


def build_regions(paths: SourcePaths) -> list[Region]:
    """Build the fixed, ordered list of Generated_Region renderers.

    The order is stable and total: MCP tools, hooks, steering files, then
    modules. ``SteeringRegion`` is pointed at the steering directory derived
    from ``paths`` (the parent of ``steering-index.yaml``) so its file-existence
    check (Requirement 5.4) targets the same world the sources were loaded from,
    including throwaway worlds under ``tmp_path`` in tests.

    Args:
        paths: The resolved source locations the generator reads.

    Returns:
        The ordered region renderers whose ``region_id`` values are exactly
        ``{"mcp-tools", "hooks", "steering-files", "modules"}``.
    """
    return [
        McpToolsRegion(),
        HooksRegion(),
        SteeringRegion(steering_dir=paths.steering_index.parent),
        ModulesRegion(),
    ]


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the generator CLI.

    The parser exposes a mutually exclusive ``--write`` / ``--verify`` mode
    group (defaulting to Write_Mode when neither is given, per Requirement 8.3)
    plus ``--power-md`` and the individual source-path overrides so tests can
    point the generator at a throwaway world. Unknown arguments cause argparse
    to exit non-zero with a usage message on stderr (Requirements 6.7, 8.6).

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    defaults = default_source_paths()
    parser = argparse.ArgumentParser(
        prog="generate_power_docs.py",
        description=(
            "Regenerate or verify the volatile sections of POWER.md from "
            "machine-readable sources of truth."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Regenerate every Generated_Region in POWER.md (default mode).",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Report drift without modifying any file; exit 1 on drift.",
    )
    parser.add_argument(
        "--power-md", type=Path, default=defaults.power_md,
        help="Path to the POWER.md file to regenerate or verify.",
    )
    parser.add_argument(
        "--hooks-dir", type=Path, default=defaults.hooks_dir,
        help="Directory containing *.kiro.hook files.",
    )
    parser.add_argument(
        "--hook-categories", type=Path, default=defaults.hook_categories,
        help="Path to hook-categories.yaml.",
    )
    parser.add_argument(
        "--steering-index", type=Path, default=defaults.steering_index,
        help="Path to steering-index.yaml.",
    )
    parser.add_argument(
        "--module-deps", type=Path, default=defaults.module_deps,
        help="Path to module-dependencies.yaml.",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=defaults.repo_root,
        help="Repository root used to render repo-relative references.",
    )
    return parser


def _paths_from_args(args: argparse.Namespace) -> SourcePaths:
    """Assemble a :class:`SourcePaths` from parsed CLI arguments.

    Args:
        args: The namespace produced by the argument parser.

    Returns:
        A :class:`SourcePaths` carrying the (possibly overridden) locations.
    """
    return SourcePaths(
        power_md=args.power_md,
        hooks_dir=args.hooks_dir,
        hook_categories=args.hook_categories,
        steering_index=args.steering_index,
        module_deps=args.module_deps,
        repo_root=args.repo_root,
    )


def _run_write(paths: SourcePaths) -> int:
    """Execute Write_Mode: regenerate every region and write POWER.md atomically.

    Loads the sources, renders every region, locates the regions in the existing
    POWER.md, splices the fresh bodies in, normalizes line endings, validates the
    candidate for CommonMark compliance, then writes it atomically. On any source
    or marker problem the existing POWER.md is left byte-for-byte unchanged.

    Args:
        paths: The resolved source locations.

    Returns:
        ``0`` on success.

    Raises:
        GeneratorError: On a source-level invariant violation or invalid output.
        MarkerError: On a marker integrity violation in POWER.md.
        OSError: If POWER.md cannot be read or written.
    """
    sources = load_sources(paths)
    regions = build_regions(paths)
    bodies = render_all(sources, regions)
    expected_ids = {region.region_id for region in regions}

    doc = paths.power_md.read_text(encoding="utf-8")
    spans = locate_regions(doc, expected_ids)
    assembled = assemble(doc, spans, bodies)
    normalized = normalize_newlines(assembled)
    validate_commonmark_text(normalized)
    write_atomic(paths.power_md, normalized)
    print(f"✅ Regenerated {len(expected_ids)} region(s) in {paths.power_md}")
    return 0


def _run_verify(paths: SourcePaths) -> int:
    """Execute Verify_Mode: report drift without modifying any file.

    Loads the sources, renders every region, reads the committed POWER.md,
    locates the regions, and compares each committed body against its freshly
    rendered body. On clean it prints a success line and returns 0; on drift it
    prints every drifted and missing region id, the drift count, and the exact
    runnable regeneration command, then returns 1. A missing or unreadable
    POWER.md is reported and surfaced as an ``OSError`` to the caller. No file
    is ever created, modified, or deleted.

    Args:
        paths: The resolved source locations.

    Returns:
        ``0`` when every region matches; ``1`` on drift.

    Raises:
        GeneratorError: On a source-level invariant violation.
        MarkerError: On a marker integrity violation in POWER.md.
        OSError: If POWER.md is missing or unreadable.
    """
    sources = load_sources(paths)
    regions = build_regions(paths)
    bodies = render_all(sources, regions)
    expected_ids = {region.region_id for region in regions}

    doc = paths.power_md.read_text(encoding="utf-8")
    spans = locate_regions(doc, expected_ids)
    result = verify(doc, spans, bodies)
    if result.ok:
        print(f"✅ POWER.md is up to date ({len(expected_ids)} region(s) verified).")
        return 0

    for region_id in result.drifted_region_ids:
        print(f"❌ drifted region: {region_id}")
    for region_id in result.missing_region_ids:
        print(f"❌ missing region: {region_id}")
    print(f"Drift detected in {result.drift_count} region(s).")
    print(f"Run the following to regenerate: {REGEN_COMMAND}")
    return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the POWER.md documentation generator.

    Parses arguments (defaulting to Write_Mode when no mode flag is given),
    builds the source paths, and dispatches to Write_Mode or Verify_Mode. All
    expected failure modes — source invariant violations, marker integrity
    problems, and filesystem errors — are caught here and reported to stderr as
    a single cause line with a non-zero return; tracebacks never leak. Invalid
    command-line arguments cause argparse to exit non-zero, whose code is
    returned as an int so callers always receive an exit status.

    Args:
        argv: The argument vector (defaults to ``sys.argv[1:]`` via argparse).

    Returns:
        ``0`` on success, ``1`` on a handled failure or detected drift, or the
        argparse exit code (``2``) on invalid arguments.
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse prints usage to stderr and raises SystemExit on bad args;
        # return its code as an int so main() always yields an exit status.
        return int(exc.code) if isinstance(exc.code, int) else 2

    paths = _paths_from_args(args)
    try:
        if args.verify:
            return _run_verify(paths)
        return _run_write(paths)
    except (GeneratorError, MarkerError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
