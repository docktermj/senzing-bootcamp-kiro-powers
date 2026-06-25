#!/usr/bin/env python3
"""Generate a deterministic index of the spec catalog under .kiro/specs/.

Scans the specs root for spec directories, derives each spec's lifecycle status
from existing signals (task-checkbox state, document presence) plus a curated
metadata file (status overrides, supersession and related-spec relationships),
and writes a human-readable CommonMark index (the Spec_Index) plus an optional
machine-readable JSON summary (the Catalog_Summary). Output is deterministic, so
identical inputs always produce byte-identical output. The generator is strictly
read-only over the spec catalog; it only ever writes its own index and summary
outputs and never modifies, moves, or deletes any spec directory or document.

Usage:
    python3 generate_spec_catalog.py                          # write/refresh index
    python3 generate_spec_catalog.py --specs-root <dir>       # custom specs root
    python3 generate_spec_catalog.py --output <path>          # custom index path
    python3 generate_spec_catalog.py --metadata <path>        # custom metadata file
    python3 generate_spec_catalog.py --summary <path>         # also write JSON summary
    python3 generate_spec_catalog.py --check                  # report drift only
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SPECS_ROOT = Path(".kiro/specs")
DEFAULT_INDEX_PATH = Path(".kiro/SPEC_CATALOG.md")
DEFAULT_METADATA_PATH = Path(".kiro/spec-catalog.yaml")
CONFIG_FILENAME = ".config.kiro"
SPEC_DOCUMENTS = ("requirements.md", "design.md", "tasks.md")
STATUS_ORDER = ("in-progress", "implemented", "superseded", "abandoned", "unknown")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CatalogError(Exception):
    """Raised for any detected, recoverable processing error.

    Carries a human-readable message that ``main()`` prints to ``sys.stderr``
    before returning exit code 1.
    """


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecConfig:
    """Parsed ``.config.kiro`` contents (only the fields the catalog uses).

    Attributes:
        workflow_type: The ``workflowType`` value, or None when absent.
        spec_type: The ``specType`` value, or None when absent.
    """

    workflow_type: str | None
    spec_type: str | None


@dataclass(frozen=True)
class SpecRecord:
    """A discovered spec directory and its derived signals.

    Attributes:
        identifier: Directory name, used as the spec identifier.
        has_requirements: Whether ``requirements.md`` is present.
        has_design: Whether ``design.md`` is present.
        has_tasks: Whether ``tasks.md`` is present.
        config: Parsed ``.config.kiro``, or None when the file is absent.
        task_total: Total number of Task_Checkbox lines in ``tasks.md``.
        task_complete: Number of completed Task_Checkbox lines in ``tasks.md``.
    """

    identifier: str
    has_requirements: bool
    has_design: bool
    has_tasks: bool
    config: SpecConfig | None
    task_total: int
    task_complete: int


@dataclass(frozen=True)
class SpecRelationships:
    """Reciprocal, sorted relationship lists for one spec.

    Attributes:
        supersedes: Identifiers this spec supersedes.
        superseded_by: Identifiers that supersede this spec.
        related: Identifiers associated with this spec without supersession.
    """

    supersedes: tuple[str, ...] = ()
    superseded_by: tuple[str, ...] = ()
    related: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogMetadata:
    """Curated editorial facts from the Catalog_Metadata_File.

    Attributes:
        status_overrides: Mapping of identifier to an explicit Status_Value.
        supersessions: Directional ``(superseding, superseded)`` pairs.
        related: Normalized unordered ``(a, b)`` related pairs.
    """

    status_overrides: dict[str, str] = field(default_factory=dict)
    supersessions: tuple[tuple[str, str], ...] = ()
    related: tuple[tuple[str, str], ...] = ()

    @classmethod
    def empty(cls) -> CatalogMetadata:
        """Return an empty CatalogMetadata with no overrides or relationships.

        Returns:
            A CatalogMetadata carrying no editorial facts, used when the
            Catalog_Metadata_File is absent (Requirement 3.6).
        """
        return cls(status_overrides={}, supersessions=(), related=())


@dataclass(frozen=True)
class SpecEntry:
    """A fully-resolved catalog entry ready for rendering/serialization.

    Attributes:
        record: The discovered SpecRecord.
        status: The derived Status_Value (one of ``STATUS_ORDER``).
        relationships: The resolved reciprocal relationships for this spec.
    """

    record: SpecRecord
    status: str
    relationships: SpecRelationships


@dataclass(frozen=True)
class Catalog:
    """The ordered, resolved catalog model.

    Attributes:
        entries: SpecEntry items in case-insensitive ascending identifier order.
        status_counts: Per-status counts keyed over ``STATUS_ORDER``.
    """

    entries: tuple[SpecEntry, ...]
    status_counts: dict[str, int]


# ---------------------------------------------------------------------------
# Discovery and config parsing
# ---------------------------------------------------------------------------


def read_config(config_path: Path) -> SpecConfig | None:
    """Parse a ``.config.kiro`` file into a SpecConfig.

    Reads the JSON-formatted Config_File and extracts the ``workflowType`` and
    ``specType`` values used by the catalog. Each value is None when its key is
    absent from the object. When the Config_File itself does not exist, None is
    returned so callers can treat a missing config as "no config".

    Args:
        config_path: Path to the ``.config.kiro`` file inside a Spec_Directory.

    Returns:
        A SpecConfig with the parsed ``workflow_type``/``spec_type`` values, or
        None when the Config_File is absent.

    Raises:
        CatalogError: When the Config_File content is not valid JSON. The error
            message names the offending Spec_Directory (Requirement 8.7).
    """
    if not config_path.exists():
        return None
    text = config_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        spec_dir = config_path.parent.name
        raise CatalogError(
            f"invalid JSON in {CONFIG_FILENAME} for spec directory "
            f"'{spec_dir}': {exc}"
        ) from exc
    if not isinstance(data, dict):
        spec_dir = config_path.parent.name
        raise CatalogError(
            f"invalid JSON in {CONFIG_FILENAME} for spec directory "
            f"'{spec_dir}': expected a JSON object"
        )
    workflow_type = data.get("workflowType")
    spec_type = data.get("specType")
    return SpecConfig(
        workflow_type=workflow_type if isinstance(workflow_type, str) else None,
        spec_type=spec_type if isinstance(spec_type, str) else None,
    )


def count_task_checkboxes(tasks_md: Path) -> tuple[int, int]:
    """Count Task_Checkbox lines in a ``tasks.md`` file.

    Scans the file line by line and recognizes a Task_Checkbox as a line whose
    stripped form starts with ``- [ ]`` (incomplete), ``- [x]`` or ``- [X]``
    (complete). Any other content — including prose that merely contains
    brackets — is ignored. When the file is absent, ``(0, 0)`` is returned.

    Args:
        tasks_md: Path to the ``tasks.md`` file inside a Spec_Directory.

    Returns:
        A ``(total, complete)`` tuple where ``total`` is the number of
        Task_Checkbox lines and ``complete`` is the number marked done.
    """
    if not tasks_md.exists():
        return (0, 0)
    total = 0
    complete = 0
    for line in tasks_md.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            total += 1
        elif stripped.startswith("- [x]") or stripped.startswith("- [X]"):
            total += 1
            complete += 1
    return (total, complete)


def discover_specs(specs_root: Path) -> list[SpecRecord]:
    """Enumerate immediate subdirectories of ``specs_root`` as SpecRecords.

    Each immediate subdirectory of the Specs_Root is treated as one
    Spec_Directory and captured as a SpecRecord recording its identifier (the
    directory name), the presence of each Spec_Document in ``SPEC_DOCUMENTS``,
    its parsed ``.config.kiro`` (None when absent), and its Task_Checkbox
    counts. Directories with no documents and no config are still included so
    their status can later resolve to ``unknown`` (Requirement 1.5). The
    returned records are sorted by a case-insensitive key
    (``identifier.casefold()``) with the raw identifier as a deterministic
    tiebreaker (Requirement 1.6).

    Args:
        specs_root: The Specs_Root directory to scan for Spec_Directories.

    Returns:
        A list of SpecRecords, one per immediate subdirectory, in
        case-insensitive ascending order of identifier.

    Raises:
        CatalogError: When a Spec_Directory's ``.config.kiro`` is not valid
            JSON (propagated from ``read_config``, Requirement 8.7).
    """
    records: list[SpecRecord] = []
    for child in specs_root.iterdir():
        if not child.is_dir():
            continue
        identifier = child.name
        has_requirements = (child / "requirements.md").is_file()
        has_design = (child / "design.md").is_file()
        has_tasks = (child / "tasks.md").is_file()
        config = read_config(child / CONFIG_FILENAME)
        task_total, task_complete = count_task_checkboxes(child / "tasks.md")
        records.append(
            SpecRecord(
                identifier=identifier,
                has_requirements=has_requirements,
                has_design=has_design,
                has_tasks=has_tasks,
                config=config,
                task_total=task_total,
                task_complete=task_complete,
            )
        )
    records.sort(key=lambda record: (record.identifier.casefold(), record.identifier))
    return records


# ---------------------------------------------------------------------------
# Metadata Resolution
# ---------------------------------------------------------------------------


def _strip_inline_comment(value: str) -> str:
    """Strip a trailing ``# comment`` from an unquoted scalar value.

    Comments are only stripped from bare (unquoted) values so that a ``#``
    inside a quoted string is preserved.

    Args:
        value: The raw scalar text following a ``key:`` separator.

    Returns:
        The value with any trailing inline comment removed and surrounding
        whitespace stripped.
    """
    if value.startswith('"') or value.startswith("'"):
        return value
    idx = value.find(" #")
    if idx != -1:
        return value[:idx].strip()
    return value


def _parse_yaml_scalar(value: str) -> str | None:
    """Parse a single YAML scalar into a Python value.

    Quoted strings have their surrounding quotes removed; the YAML null tokens
    (``null``, ``~``) and the empty string map to None. All other values are
    returned as plain strings, which covers every scalar in the
    Catalog_Metadata_File schema (identifiers and Status_Values).

    Args:
        value: The raw scalar text.

    Returns:
        The parsed string, or None for null/empty scalars.
    """
    value = value.strip()
    if len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    if value in ("", "null", "~"):
        return None
    return value


def _is_mapping_entry(text: str) -> bool:
    """Return True when ``text`` is a ``key: value`` mapping entry.

    A mapping entry has a colon that is either at the end of the text or
    followed by whitespace. Bare scalars such as identifiers (which contain no
    colon) are not mapping entries.

    Args:
        text: The candidate entry text (already stripped of list markers).

    Returns:
        True when the text is a mapping entry, False when it is a bare scalar.
    """
    colon = text.find(":")
    if colon == -1:
        return False
    after = text[colon + 1:]
    return after == "" or after.startswith(" ")


def _parse_simple_yaml(text: str) -> dict:
    """Parse the minimal YAML subset used by the Catalog_Metadata_File.

    Supports only the constructs the metadata schema needs, with no PyYAML
    dependency (Requirement 8.9): top-level keys, nested mappings, ``- `` list
    items (scalar items, ``key: value`` mapping items, and nested lists), and
    scalar ``key: value`` pairs. Blank lines and ``#`` comment lines are
    ignored.

    Args:
        text: The raw YAML text of the Catalog_Metadata_File.

    Returns:
        A nested dict mirroring the document's top-level mapping.

    Raises:
        ValueError: When the text is not a well-formed instance of the
            supported YAML subset (for example a non-mapping top level or an
            entry that is neither a list item nor a ``key: value`` pair).
    """
    entries: list[tuple[int, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        entries.append((indent, stripped))
    if not entries:
        return {}
    top_indent = entries[0][0]
    if top_indent != 0:
        raise ValueError("top-level content must not be indented")
    if entries[0][1].startswith("- "):
        raise ValueError("top-level content must be a mapping, not a list")
    result, index = _parse_yaml_mapping(entries, 0, 0)
    if index != len(entries):
        raise ValueError("unexpected trailing content")
    return result


def _parse_yaml_block(entries: list[tuple[int, str]], i: int, indent: int) -> tuple[object, int]:
    """Dispatch to a list or mapping parser based on the first entry.

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first entry of the block.
        indent: The indentation level of the block.

    Returns:
        A ``(value, next_index)`` tuple where ``value`` is the parsed list or
        dict and ``next_index`` is the entry index following the block.
    """
    if entries[i][1].startswith("- "):
        return _parse_yaml_list(entries, i, indent)
    return _parse_yaml_mapping(entries, i, indent)


def _parse_yaml_mapping(
    entries: list[tuple[int, str]], i: int, indent: int
) -> tuple[dict, int]:
    """Parse a YAML mapping at a fixed indentation level.

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first entry of the mapping.
        indent: The indentation level shared by the mapping's keys.

    Returns:
        A ``(mapping, next_index)`` tuple.

    Raises:
        ValueError: When an entry at this level is neither a ``key: value`` pair
            nor a recognized nested block.
    """
    result: dict = {}
    while i < len(entries):
        cur_indent, text = entries[i]
        if cur_indent < indent:
            break
        if text.startswith("- "):
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indentation: {text!r}")
        colon = text.find(":")
        if colon == -1:
            raise ValueError(f"expected 'key: value', got: {text!r}")
        key = text[:colon].strip().strip("\"'")
        rest = _strip_inline_comment(text[colon + 1:].strip())
        if rest:
            result[key] = _parse_yaml_scalar(rest)
            i += 1
            continue
        i += 1
        if i < len(entries):
            next_indent, next_text = entries[i]
            if next_text.startswith("- ") and next_indent >= indent:
                child, i = _parse_yaml_list(entries, i, next_indent)
                result[key] = child
            elif next_indent > indent:
                child, i = _parse_yaml_block(entries, i, next_indent)
                result[key] = child
            else:
                result[key] = None
        else:
            result[key] = None
    return result, i


def _parse_yaml_list(
    entries: list[tuple[int, str]], i: int, indent: int
) -> tuple[list, int]:
    """Parse a YAML list at a fixed indentation level.

    Handles scalar items (``- value``), inline mapping items (``- key: value``
    followed by aligned ``key: value`` continuation lines), and nested lists
    (``- - value``), which together let ``related`` be either a single flat
    group or a list of groups.

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first list item.
        indent: The indentation level of the list markers.

    Returns:
        A ``(items, next_index)`` tuple.
    """
    result: list = []
    while i < len(entries):
        cur_indent, text = entries[i]
        if cur_indent < indent or not text.startswith("- "):
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indentation in list: {text!r}")
        content = text[2:].strip()
        content_col = cur_indent + 2
        if content.startswith("- "):
            entries[i] = (content_col, content)
            nested, i = _parse_yaml_list(entries, i, content_col)
            result.append(nested)
        elif _is_mapping_entry(content):
            item_map: dict = {}
            colon = content.find(":")
            key = content[:colon].strip().strip("\"'")
            rest = _strip_inline_comment(content[colon + 1:].strip())
            item_map[key] = _parse_yaml_scalar(rest) if rest else None
            i += 1
            while (
                i < len(entries)
                and entries[i][0] >= content_col
                and not entries[i][1].startswith("- ")
            ):
                ctext = entries[i][1]
                ccolon = ctext.find(":")
                if ccolon == -1:
                    raise ValueError(f"expected 'key: value', got: {ctext!r}")
                ckey = ctext[:ccolon].strip().strip("\"'")
                crest = _strip_inline_comment(ctext[ccolon + 1:].strip())
                item_map[ckey] = _parse_yaml_scalar(crest) if crest else None
                i += 1
            result.append(item_map)
        else:
            result.append(_parse_yaml_scalar(content))
            i += 1
    return result, i


def _normalize_related_groups(raw_related: list) -> list[list[str]]:
    """Normalize the ``related`` value into a list of identifier groups.

    A flat list of scalars is treated as one mutually-related group (matching
    the documented schema); a list of lists is treated as multiple groups.

    Args:
        raw_related: The parsed value of the ``related`` key.

    Returns:
        A list of groups, each a list of identifier strings.

    Raises:
        ValueError: When an element is neither a string nor a list of strings.
    """
    if all(isinstance(element, str) for element in raw_related):
        return [list(raw_related)]
    groups: list[list[str]] = []
    for element in raw_related:
        if isinstance(element, list):
            if not all(isinstance(member, str) for member in element):
                raise ValueError("related group members must be strings")
            groups.append(list(element))
        elif isinstance(element, str):
            groups.append([element])
        else:
            raise ValueError("related entries must be identifiers or groups")
    return groups


def load_metadata(metadata_path: Path) -> CatalogMetadata:
    """Load and parse the curated Catalog_Metadata_File.

    Reads the YAML Catalog_Metadata_File and extracts the curated editorial
    facts the generator cannot derive: ``status_overrides`` (identifier to
    Status_Value), ``supersessions`` (directional ``{supersedes, superseded}``
    mappings recorded as ``(superseding, superseded)`` pairs), and ``related``
    groups (lists of mutually-related identifiers expanded into normalized,
    deduplicated, sorted unordered pairs). When the file is absent, an empty
    CatalogMetadata is returned and generation proceeds from derived signals
    only (Requirement 3.6).

    Args:
        metadata_path: Path to the Catalog_Metadata_File (YAML).

    Returns:
        A CatalogMetadata carrying the parsed overrides, supersessions, and
        related pairs.

    Raises:
        CatalogError: When the file is present but cannot be parsed or does not
            conform to the documented schema (Requirement 8.8).
    """
    if not metadata_path.exists():
        return CatalogMetadata.empty()
    text = metadata_path.read_text(encoding="utf-8")
    try:
        data = _parse_simple_yaml(text)
    except ValueError as exc:
        raise CatalogError(
            f"failed to parse metadata file '{metadata_path}': {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise CatalogError(
            f"failed to parse metadata file '{metadata_path}': "
            "expected a top-level mapping"
        )

    status_overrides: dict[str, str] = {}
    raw_overrides = data.get("status_overrides")
    if raw_overrides:
        if not isinstance(raw_overrides, dict):
            raise CatalogError(
                f"invalid metadata file '{metadata_path}': "
                "'status_overrides' must be a mapping"
            )
        for identifier, value in raw_overrides.items():
            if value is None:
                raise CatalogError(
                    f"invalid metadata file '{metadata_path}': status override "
                    f"for '{identifier}' must name a status value"
                )
            status_overrides[str(identifier)] = str(value)

    supersessions: list[tuple[str, str]] = []
    raw_supersessions = data.get("supersessions")
    if raw_supersessions:
        if not isinstance(raw_supersessions, list):
            raise CatalogError(
                f"invalid metadata file '{metadata_path}': "
                "'supersessions' must be a list"
            )
        for item in raw_supersessions:
            if (
                not isinstance(item, dict)
                or item.get("supersedes") is None
                or item.get("superseded") is None
            ):
                raise CatalogError(
                    f"invalid metadata file '{metadata_path}': each supersession "
                    "must provide 'supersedes' and 'superseded' identifiers"
                )
            supersessions.append((str(item["supersedes"]), str(item["superseded"])))

    related_pairs: set[tuple[str, str]] = set()
    raw_related = data.get("related")
    if raw_related:
        if not isinstance(raw_related, list):
            raise CatalogError(
                f"invalid metadata file '{metadata_path}': "
                "'related' must be a list"
            )
        try:
            groups = _normalize_related_groups(raw_related)
        except ValueError as exc:
            raise CatalogError(
                f"invalid metadata file '{metadata_path}': {exc}"
            ) from exc
        for group in groups:
            members = sorted(set(group))
            for outer in range(len(members)):
                for inner in range(outer + 1, len(members)):
                    related_pairs.add((members[outer], members[inner]))

    return CatalogMetadata(
        status_overrides=status_overrides,
        supersessions=tuple(supersessions),
        related=tuple(sorted(related_pairs)),
    )


def validate_metadata_refs(metadata: CatalogMetadata, known_ids: set[str]) -> list[str]:
    """Find metadata-referenced identifiers that match no discovered spec.

    Collects every spec identifier referenced anywhere in the
    Catalog_Metadata_File — the ``status_overrides`` keys, both members of each
    supersession pair (superseding and superseded), and both members of each
    related pair — and returns those that do not name a discovered
    Spec_Directory. A non-empty result drives the exit-code-1 contract: the
    caller reports each unresolved identifier to standard error and exits with
    status code 1 (Requirement 3.5).

    Args:
        metadata: The curated CatalogMetadata to validate.
        known_ids: The set of identifiers of discovered Spec_Directories.

    Returns:
        The sorted list of distinct referenced identifiers that are not present
        in ``known_ids``. Empty when every reference resolves.
    """
    referenced: set[str] = set()
    referenced.update(metadata.status_overrides.keys())
    for superseding, superseded in metadata.supersessions:
        referenced.add(superseding)
        referenced.add(superseded)
    for first, second in metadata.related:
        referenced.add(first)
        referenced.add(second)
    return sorted(referenced - known_ids)


# ---------------------------------------------------------------------------
# Status derivation
# ---------------------------------------------------------------------------


def derive_status(record: SpecRecord, metadata: CatalogMetadata) -> str:
    """Assign exactly one Status_Value to a spec using a fixed precedence.

    Status resolution applies the following signals in strict precedence order,
    returning the first that applies (Requirement 2.8). The result is always
    exactly one value drawn from ``STATUS_ORDER`` (Requirements 2.1, 2.8):

    1. An explicit status override in the Catalog_Metadata_File takes priority
       over every derived signal (Requirement 2.2).
    2. A recorded supersession — the spec appears as the superseded target (the
       second element) of any supersession pair — yields ``superseded``
       (Requirement 2.3).
    3. The ``tasks.md`` checkbox state, when ``tasks.md`` is present: all
       Task_Checkboxes complete yields ``implemented`` (Requirement 2.4); any
       incomplete yields ``in-progress`` (Requirement 2.5); present with no
       Task_Checkbox yields ``unknown`` (Requirement 2.6).
    4. Document presence, when ``tasks.md`` is absent: ``requirements.md`` or
       ``design.md`` present yields ``in-progress`` (Requirement 2.7).
    5. Otherwise ``unknown``.

    Args:
        record: The discovered SpecRecord whose status is being derived.
        metadata: The curated CatalogMetadata supplying overrides and
            supersessions.

    Returns:
        Exactly one Status_Value from ``STATUS_ORDER``.
    """
    # 1. Explicit override wins over all derived signals (Req 2.2).
    override = metadata.status_overrides.get(record.identifier)
    if override is not None:
        return override

    # 2. Recorded supersession: spec is the superseded target of a pair (Req 2.3).
    for _superseding, superseded in metadata.supersessions:
        if superseded == record.identifier:
            return "superseded"

    # 3. tasks.md checkbox state (Req 2.4, 2.5, 2.6).
    if record.has_tasks:
        if record.task_total == 0:
            return "unknown"
        if record.task_complete >= record.task_total:
            return "implemented"
        return "in-progress"

    # 4. Document presence when tasks.md is absent (Req 2.7).
    if record.has_requirements or record.has_design:
        return "in-progress"

    # 5. Otherwise unknown.
    return "unknown"


# ---------------------------------------------------------------------------
# Relationship assembly
# ---------------------------------------------------------------------------


def resolve_relationships(metadata: CatalogMetadata) -> dict[str, SpecRelationships]:
    """Build per-identifier reciprocal, deterministic relationship lists.

    Expands the curated supersession and related links into reciprocal
    relationships keyed by spec identifier. For each directional supersession
    pair ``(A, B)`` (A supersedes the superseded B), ``B`` is added to ``A``'s
    ``supersedes`` and ``A`` is added to ``B``'s ``superseded_by``
    (Requirements 3.1, 3.2, 3.3). Each related pair ``(a, b)`` is recorded
    symmetrically, adding ``b`` to ``a``'s ``related`` list and ``a`` to ``b``'s
    (Requirement 3.4). Every list is sorted and deduplicated so the resulting
    relationships are deterministic regardless of metadata ordering, and each is
    stored as a tuple in the frozen ``SpecRelationships`` dataclass.

    Args:
        metadata: The curated CatalogMetadata supplying supersession and related
            pairs.

    Returns:
        A dict mapping each participating spec identifier to its resolved
        SpecRelationships. Identifiers that appear in no relationship are absent
        from the mapping.
    """
    supersedes: dict[str, set[str]] = {}
    superseded_by: dict[str, set[str]] = {}
    related: dict[str, set[str]] = {}

    for superseding, superseded in metadata.supersessions:
        supersedes.setdefault(superseding, set()).add(superseded)
        superseded_by.setdefault(superseded, set()).add(superseding)

    for first, second in metadata.related:
        related.setdefault(first, set()).add(second)
        related.setdefault(second, set()).add(first)

    identifiers = set(supersedes) | set(superseded_by) | set(related)
    result: dict[str, SpecRelationships] = {}
    for identifier in identifiers:
        result[identifier] = SpecRelationships(
            supersedes=tuple(sorted(supersedes.get(identifier, set()))),
            superseded_by=tuple(sorted(superseded_by.get(identifier, set()))),
            related=tuple(sorted(related.get(identifier, set()))),
        )
    return result


# ---------------------------------------------------------------------------
# Catalog composition
# ---------------------------------------------------------------------------


def build_catalog(records: list[SpecRecord], metadata: CatalogMetadata) -> Catalog:
    """Compose the fully-resolved, ordered in-memory Catalog model.

    Resolves each discovered SpecRecord into a SpecEntry by deriving its
    Status_Value via ``derive_status`` and attaching its reciprocal
    relationships from ``resolve_relationships`` (an empty SpecRelationships
    when the spec participates in none). Entries are ordered case-insensitively
    by identifier with the raw identifier as a deterministic tiebreaker — the
    same ordering ``discover_specs`` produces (Requirements 1.6, 5.4). The
    ``status_counts`` mapping is keyed over every Status_Value in
    ``STATUS_ORDER`` so statuses with no specs report 0, and the counts sum to
    the number of records (Requirement 4.4).

    Args:
        records: The discovered SpecRecords to compose into the catalog.
        metadata: The curated CatalogMetadata supplying status overrides,
            supersessions, and related pairs.

    Returns:
        A Catalog with entries in case-insensitive ascending identifier order
        and per-status counts keyed over ``STATUS_ORDER``.
    """
    relationships = resolve_relationships(metadata)
    ordered_records = sorted(
        records, key=lambda record: (record.identifier.casefold(), record.identifier)
    )
    status_counts: dict[str, int] = {status: 0 for status in STATUS_ORDER}
    entries: list[SpecEntry] = []
    for record in ordered_records:
        status = derive_status(record, metadata)
        status_counts[status] = status_counts.get(status, 0) + 1
        entries.append(
            SpecEntry(
                record=record,
                status=status,
                relationships=relationships.get(record.identifier, SpecRelationships()),
            )
        )
    return Catalog(entries=tuple(entries), status_counts=status_counts)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_PROVENANCE_COMMENT = (
    "<!-- Generated by generate_spec_catalog.py. "
    "Do not edit by hand; regenerate. -->"
)
_MISSING_FIELD = "unknown"


def render_index(catalog: Catalog) -> str:
    """Render the CommonMark Spec_Index for a resolved Catalog.

    Produces the deterministic, CommonMark-compliant Spec_Index described in the
    design: a provenance banner at the very top (an HTML comment plus the
    ``# Spec Catalog Index`` heading and a regeneration blockquote, Requirements
    4.6, 9.3), a ``## Status Summary`` section listing every Status_Value in
    ``STATUS_ORDER`` with its count (Requirement 4.4), and a ``## Specs`` section
    with one ``### <identifier>`` subsection per spec showing its status, type
    (``specType``), workflow (``workflowType``), a CommonMark link to its
    Spec_Directory, and any supersession/related identifiers (Requirements 4.2,
    4.3, 4.5). A missing ``specType``/``workflowType`` renders as ``unknown``.
    Entries follow the catalog's case-insensitive ascending order, and the
    output terminates with a single trailing newline (Requirement 9.3).

    Args:
        catalog: The fully-resolved, ordered Catalog model to render.

    Returns:
        The rendered Spec_Index as a CommonMark string ending in a single
        newline.
    """
    lines: list[str] = [
        _PROVENANCE_COMMENT,
        "",
        "# Spec Catalog Index",
        "",
        "> This file is generated by `generate_spec_catalog.py`. Do not edit it "
        "by hand —",
        "> regenerate it instead.",
        "",
        "## Status Summary",
        "",
    ]
    for status in STATUS_ORDER:
        lines.append(f"- {status}: {catalog.status_counts.get(status, 0)}")
    lines.extend(["", "## Specs"])

    for entry in catalog.entries:
        record = entry.record
        identifier = record.identifier
        spec_type = record.config.spec_type if record.config else None
        workflow_type = record.config.workflow_type if record.config else None
        directory = f".kiro/specs/{identifier}/"
        lines.extend(
            [
                "",
                f"### {identifier}",
                "",
                f"- Status: {entry.status}",
                f"- Type: {spec_type if spec_type else _MISSING_FIELD}",
                f"- Workflow: {workflow_type if workflow_type else _MISSING_FIELD}",
                f"- Directory: [{directory}]({directory})",
            ]
        )
        relationships = entry.relationships
        if relationships.supersedes:
            lines.append(f"- Supersedes: {', '.join(relationships.supersedes)}")
        if relationships.superseded_by:
            lines.append(
                f"- Superseded by: {', '.join(relationships.superseded_by)}"
            )
        if relationships.related:
            lines.append(f"- Related: {', '.join(relationships.related)}")

    return "\n".join(lines) + "\n"


def render_summary(catalog: Catalog) -> str:
    """Render the machine-readable Catalog_Summary as JSON.

    Serializes the resolved Catalog into a JSON Catalog_Summary containing, for
    each spec, its identifier, derived Status_Value, ``specType``,
    ``workflowType``, the document-presence flags for each Spec_Document, and
    its recorded supersession/related relationships (Requirement 5.2). Spec
    entries appear in the catalog's case-insensitive ascending identifier order
    (Requirement 5.4); the JSON is emitted with ``indent=2, sort_keys=True`` and
    a single trailing newline so output is deterministic and byte-identical for
    unchanged inputs (Requirement 5.1). ``specType``/``workflowType`` serialize
    as JSON ``null`` when the Config_File omits them, which is a recorded
    absence rather than an uncollectable field.

    Args:
        catalog: The fully-resolved, ordered Catalog model to serialize.

    Returns:
        The Catalog_Summary as a JSON string ending in a single newline.

    Raises:
        CatalogError: When a required field for a spec cannot be collected — a
            missing identifier or a status outside ``STATUS_ORDER``. The caller
            skips writing the summary and exits with status code 1
            (Requirement 5.5).
    """
    specs: list[dict] = []
    for entry in catalog.entries:
        record = entry.record
        identifier = record.identifier
        if not identifier:
            raise CatalogError(
                "cannot collect required summary field: a spec is missing its "
                "identifier"
            )
        if entry.status not in STATUS_ORDER:
            raise CatalogError(
                f"cannot collect required summary field for spec '{identifier}': "
                f"status '{entry.status}' is not a recognized Status_Value"
            )
        config = record.config
        relationships = entry.relationships
        specs.append(
            {
                "identifier": identifier,
                "status": entry.status,
                "specType": config.spec_type if config else None,
                "workflowType": config.workflow_type if config else None,
                "documents": {
                    "requirements": record.has_requirements,
                    "design": record.has_design,
                    "tasks": record.has_tasks,
                },
                "relationships": {
                    "supersedes": list(relationships.supersedes),
                    "superseded_by": list(relationships.superseded_by),
                    "related": list(relationships.related),
                },
            }
        )
    summary = {
        "status_counts": dict(catalog.status_counts),
        "specs": specs,
    }
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# CLI / I/O shell
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, run the pipeline, and write outputs or check drift.

    Wires the command-line interface to the catalog pipeline. After validating
    that the Specs_Root exists and is a directory (Requirement 8.6), it runs
    discovery, metadata loading, reference validation (Requirement 3.5), catalog
    composition, and index rendering. In Drift_Check_Mode (``--check``) it
    writes nothing: it reports a missing index as drift (Requirement 6.4) and
    otherwise compares the committed index against a freshly rendered one,
    returning 0 when they match and reporting drift on any difference
    (Requirements 6.2, 6.3). In write mode it writes the rendered index in a
    single all-or-nothing write and, when ``--summary`` is given, the JSON
    Catalog_Summary (Requirements 4.1, 5.1, 5.3). Any CatalogError raised in the
    pipeline is reported to standard error and converted to exit code 1
    (Requirements 8.5, 8.7, 8.8). All error messages are routed to
    ``sys.stderr``.

    Args:
        argv: Optional argument list (excluding the program name). When None,
            arguments are read from ``sys.argv``.

    Returns:
        ``0`` on success or when the committed index is in sync; ``1`` on any
        detected error, unresolved metadata reference, missing index, or drift
        (Requirements 8.4, 8.5).
    """
    parser = argparse.ArgumentParser(
        description="Generate a deterministic index of the spec catalog.",
    )
    parser.add_argument(
        "--specs-root",
        type=Path,
        default=DEFAULT_SPECS_ROOT,
        help="Specs root directory to scan (default: .kiro/specs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Index output path (default: .kiro/SPEC_CATALOG.md).",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help="Curated metadata file (default: .kiro/spec-catalog.yaml).",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Also write the JSON Catalog_Summary to this path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Drift_Check_Mode: compare without writing.",
    )
    args = parser.parse_args(argv)

    specs_root: Path = args.specs_root
    output: Path = args.output
    metadata_path: Path = args.metadata
    summary_path: Path | None = args.summary

    # Pre-check the Specs_Root (Req 8.6).
    if not specs_root.exists() or not specs_root.is_dir():
        print(
            f"error: specs root '{specs_root}' does not exist or is not a directory",
            file=sys.stderr,
        )
        return 1

    try:
        records = discover_specs(specs_root)
        metadata = load_metadata(metadata_path)
        known_ids = {record.identifier for record in records}
        unresolved = validate_metadata_refs(metadata, known_ids)
        if unresolved:
            for identifier in unresolved:
                print(
                    f"error: metadata references unknown spec '{identifier}'",
                    file=sys.stderr,
                )
            return 1
        catalog = build_catalog(records, metadata)
        rendered_index = render_index(catalog)

        # Drift_Check_Mode: write nothing (Req 6.2, 6.3, 6.4).
        if args.check:
            if not output.exists():
                print(
                    f"error: index file '{output}' is missing; run without --check "
                    "to generate it",
                    file=sys.stderr,
                )
                return 1
            committed = output.read_text(encoding="utf-8")
            if committed == rendered_index:
                return 0
            print(
                f"error: index file '{output}' is out of date; regenerate it",
                file=sys.stderr,
            )
            return 1

        # Write mode: all-or-nothing index write (Req 4.1).
        if summary_path is not None:
            rendered_summary = render_summary(catalog)
            output.write_text(rendered_index, encoding="utf-8")
            summary_path.write_text(rendered_summary, encoding="utf-8")
        else:
            output.write_text(rendered_index, encoding="utf-8")
        return 0
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
