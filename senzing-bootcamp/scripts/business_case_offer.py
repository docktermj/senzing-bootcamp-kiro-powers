#!/usr/bin/env python3
"""Senzing Bootcamp - Business Case Offer validation/recording helper.

Models a Generated_Scenario produced when a bootcamper accepts the Module 1
Business Case Offer, validates its invariants (multi-source, mapping
complexity, recognized category, completeness), renders the
``docs/business_problem.md`` body, and records Scenario_Data sources into the
``config/data_sources.yaml`` registry by reusing ``data_sources.py``.

This module is pure logic: it does not call the Senzing MCP server or the
Agent. It operates only on data the Agent has already gathered, keeping it a
fast, deterministic, property-testable unit. All Senzing/CORD facts come from
the MCP server at runtime — no CORD dataset names or record counts appear here.

Usage:
    # Validate a recorded generated scenario (business_problem.md + data_sources.yaml)
    python business_case_offer.py validate \\
        --business-problem docs/business_problem.md \\
        --data-sources config/data_sources.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── Sibling-module import (scripts aren't packages) ─────────────────────────

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import (  # noqa: E402  (path manipulated above)
    CURRENT_SCHEMA_VERSION,
    Registry,
    RegistryEntry,
    _registry_to_dict,
    parse_registry_yaml,
    serialize_registry_yaml,
)

# ── Constants ───────────────────────────────────────────────────────────────

# The 10 use-case categories recognized by Module 1. A Generated_Scenario's
# use_case_category must be exactly one of these (Requirements 2.2).
RECOGNIZED_CATEGORIES: frozenset[str] = frozenset({
    "Customer 360",
    "Fraud Detection",
    "Data Migration",
    "Compliance",
    "Marketing",
    "Healthcare",
    "Supply Chain",
    "KYC",
    "Insurance",
    "Vendor MDM",
})

# Observable marker text written into business_problem.md to identify a case as
# bootcamp-generated rather than bootcamper-supplied (Requirements 4.3).
GENERATED_MARKER: str = "> 🤖 Bootcamp-generated business case"


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass
class ScenarioDataSource:
    """A single distinct data source contributing to a Generated_Scenario."""

    name: str
    fields: list[str] = field(default_factory=list)
    records: list[dict] = field(default_factory=list)


@dataclass
class GeneratedScenario:
    """A complete business case generated on the bootcamper's behalf."""

    problem_description: str
    use_case_category: str
    success_definition: str
    data_sources: list[ScenarioDataSource] = field(default_factory=list)
    provenance: str = "generated"
    selected_pattern_category: str | None = None


# ── Validation ───────────────────────────────────────────────────────────────


def validate_scenario(s: GeneratedScenario) -> list[str]:
    """Return a list of invariant violations; an empty list means valid.

    Checks the structural invariants of a Generated_Scenario without raising:
    a non-empty problem description and definition of success, a recognized
    use-case category, at least two distinctly named data sources each
    contributing at least one record, a known provenance, and — when a gallery
    pattern was selected — a category that matches that pattern.

    Args:
        s: The Generated_Scenario to validate.

    Returns:
        A list of human-readable violation strings (empty when valid).
    """
    violations: list[str] = []

    # Completeness: problem description must be non-empty after trimming (2.1).
    if not (s.problem_description or "").strip():
        violations.append("problem_description must be non-empty.")

    # Completeness: definition of success must be non-empty after trimming (2.1).
    if not (s.success_definition or "").strip():
        violations.append("success_definition must be non-empty.")

    # Category: must be exactly one value in the recognized set (2.1, 2.2).
    if s.use_case_category not in RECOGNIZED_CATEGORIES:
        violations.append(
            f"use_case_category must be one of the recognized categories; "
            f"got {s.use_case_category!r}."
        )

    # Multi-source: at least two distinctly named sources, each with >= 1
    # record (3.1).
    names = [src.name for src in s.data_sources]
    distinct_names = {name for name in names if (name or "").strip()}
    if len(distinct_names) < 2:
        violations.append(
            "data_sources must include at least 2 distinctly named sources; "
            f"found {len(distinct_names)}."
        )
    for src in s.data_sources:
        label = src.name if (src.name or "").strip() else "<unnamed>"
        if len(src.records) < 1:
            violations.append(
                f"data source {label!r} must contribute at least 1 record."
            )

    # Provenance: must be one of the known values (3.3).
    if s.provenance not in {"cord", "generated"}:
        violations.append(
            f"provenance must be 'cord' or 'generated'; got {s.provenance!r}."
        )

    # Selected pattern: when set, category must match the selected pattern (2.3).
    if (
        s.selected_pattern_category is not None
        and s.selected_pattern_category != s.use_case_category
    ):
        violations.append(
            "use_case_category must match selected_pattern_category "
            f"({s.use_case_category!r} != {s.selected_pattern_category!r})."
        )

    return violations


# ── Mapping-complexity detection ───────────────────────────────────────────────

# Maps normalized field-name tokens to a canonical "concept" so that fields
# expressing the same logical attribute under different names line up across
# sources. Keys are the result of ``_normalize`` (lowercase, alphanumerics
# only). These are generic entity attributes — not Senzing/CORD specifics.
_CONCEPT_SYNONYMS: dict[str, str] = {
    # Full name (composite)
    "name": "name",
    "fullname": "name",
    "customername": "name",
    "personname": "name",
    "completename": "name",
    # Name components
    "firstname": "first_name",
    "fname": "first_name",
    "givenname": "first_name",
    "forename": "first_name",
    "lastname": "last_name",
    "lname": "last_name",
    "surname": "last_name",
    "familyname": "last_name",
    "middlename": "middle_name",
    "mname": "middle_name",
    "middleinitial": "middle_name",
    # Phone
    "phone": "phone",
    "phonenumber": "phone",
    "telephone": "phone",
    "tel": "phone",
    "mobile": "phone",
    "mobilenumber": "phone",
    "cell": "phone",
    "cellphone": "phone",
    "contactnumber": "phone",
    # Email
    "email": "email",
    "emailaddress": "email",
    "emailaddr": "email",
    "mail": "email",
    # Address (composite)
    "address": "address",
    "addr": "address",
    "fulladdress": "address",
    "streetaddress": "address",
    "mailingaddress": "address",
    # Address components
    "street": "street",
    "street1": "street",
    "addressline1": "street",
    "addr1": "street",
    "city": "city",
    "town": "city",
    "locality": "city",
    "state": "state",
    "province": "state",
    "region": "state",
    "zip": "postal",
    "zipcode": "postal",
    "postal": "postal",
    "postalcode": "postal",
    "postcode": "postal",
    # Date of birth
    "dob": "dob",
    "dateofbirth": "dob",
    "birthdate": "dob",
    "birthday": "dob",
    # Government identifiers
    "ssn": "ssn",
    "socialsecuritynumber": "ssn",
    "taxid": "tax_id",
    "taxidnumber": "tax_id",
}

# Composite concepts and the component concepts they decompose into. Used to
# detect that one source carries a combined field while another carries the
# separated parts (or vice versa) — i.e. a combine/split transformation.
_COMPOSITE_COMPONENTS: dict[str, frozenset[str]] = {
    "name": frozenset({"first_name", "last_name", "middle_name"}),
    "address": frozenset({"street", "city", "state", "postal"}),
}


def _normalize(name: str) -> str:
    """Reduce a field name to lowercase alphanumerics for comparison.

    Args:
        name: A raw field name.

    Returns:
        The name lowercased with all non-alphanumeric characters removed.
    """
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _concept_key(name: str) -> str:
    """Map a raw field name to its canonical concept.

    Recognized synonyms collapse to a shared concept (e.g. ``telephone`` and
    ``phone`` both map to ``"phone"``); unrecognized names map to their own
    normalized form.

    Args:
        name: A raw field name.

    Returns:
        The canonical concept key for the field.
    """
    normalized = _normalize(name)
    return _CONCEPT_SYNONYMS.get(normalized, normalized)


def _format_signature(value: object) -> str:
    """Derive a structural format signature for a value.

    Collapses runs of letters to ``A`` and runs of digits to ``9`` while
    preserving punctuation and spacing, so that differences in grouping or
    delimiters surface while incidental length differences do not. For
    example ``"555-1234"`` and ``"5551234"`` yield ``"9-9"`` and ``"9"``, and
    ``"2020-01-01"`` and ``"01/01/2020"`` yield ``"9-9-9"`` and ``"9/9/9"``.

    Args:
        value: The value to summarize (coerced to ``str``).

    Returns:
        A signature string capturing the value's structural format.
    """
    text = str(value)
    text = re.sub(r"[A-Za-z]+", "A", text)
    text = re.sub(r"\d+", "9", text)
    return text


def detect_mapping_complexity(sources: list[ScenarioDataSource]) -> set[str]:
    """Return the transformation types present across the given sources.

    Inspects field names and record values across the supplied
    ``Scenario_Data`` sources and reports which Senzing-mapping transformations
    the data would require (Requirements 3.2, 3.5):

    - ``differing_field_names`` — two sources use different field names for the
      same concept (e.g. ``phone`` in one source, ``telephone`` in another).
    - ``combine_or_split`` — a field in one source maps to multiple Senzing
      fields, or several fields map to one (e.g. ``full_name`` in one source
      versus ``first_name``/``last_name`` in another).
    - ``inconsistent_formatting`` — the same logical attribute is formatted
      differently across sources (e.g. ``555-1234`` versus ``5551234``).

    Raises no exceptions for malformed input; unrecognized or non-string field
    names and non-dict records are skipped.

    Args:
        sources: The Scenario_Data sources to inspect.

    Returns:
        A subset of ``{"differing_field_names", "combine_or_split",
        "inconsistent_formatting"}`` describing the transformations present.
    """
    result: set[str] = set()
    if not sources:
        return result

    # Per source, map each canonical concept to the raw field names that
    # express it within that source.
    source_concepts: list[dict[str, set[str]]] = []
    for src in sources:
        concept_to_raw: dict[str, set[str]] = {}
        for raw in getattr(src, "fields", None) or []:
            if not isinstance(raw, str) or not raw.strip():
                continue
            concept_to_raw.setdefault(_concept_key(raw), set()).add(raw)
        source_concepts.append(concept_to_raw)

    # Concept -> set of source indices that carry it, and the set of
    # normalized raw names used for it across all sources.
    concept_sources: dict[str, set[int]] = {}
    concept_raw_names: dict[str, set[str]] = {}
    for idx, concept_to_raw in enumerate(source_concepts):
        for concept, raws in concept_to_raw.items():
            concept_sources.setdefault(concept, set()).add(idx)
            for raw in raws:
                concept_raw_names.setdefault(concept, set()).add(_normalize(raw))

    # differing_field_names: a concept shared by >= 2 sources whose raw field
    # names are not all identical.
    for concept, srcs in concept_sources.items():
        if len(srcs) >= 2 and len(concept_raw_names.get(concept, set())) >= 2:
            result.add("differing_field_names")
            break

    # combine_or_split: a composite concept present in some source while its
    # components appear in a different source (or vice versa).
    for composite, components in _COMPOSITE_COMPONENTS.items():
        srcs_with_composite = concept_sources.get(composite, set())
        srcs_with_components: set[int] = set()
        for comp in components:
            srcs_with_components |= concept_sources.get(comp, set())
        if not (srcs_with_composite and srcs_with_components):
            continue
        # Detected when the composite and the components are not confined to
        # the exact same set of sources — i.e. a combine/split is required.
        if srcs_with_composite - srcs_with_components or srcs_with_components - srcs_with_composite:
            result.add("combine_or_split")
            break

    # inconsistent_formatting: a concept shared by >= 2 sources whose value
    # format signatures differ between sources.
    concept_signatures: dict[str, dict[int, set[str]]] = {}
    for idx, src in enumerate(sources):
        records = getattr(src, "records", None) or []
        for concept, raws in source_concepts[idx].items():
            signatures: set[str] = set()
            for record in records:
                if not isinstance(record, dict):
                    continue
                for raw in raws:
                    if raw not in record or record[raw] is None:
                        continue
                    value = record[raw]
                    if isinstance(value, str) and not value.strip():
                        continue
                    signatures.add(_format_signature(value))
            if signatures:
                concept_signatures.setdefault(concept, {})[idx] = signatures

    for by_source in concept_signatures.values():
        if len(by_source) < 2:
            continue
        signature_sets = list(by_source.values())
        baseline = signature_sets[0]
        if any(sig_set != baseline for sig_set in signature_sets[1:]):
            result.add("inconsistent_formatting")
            break

    return result


# ── Rendering ─────────────────────────────────────────────────────────────────


def _distinct_sources(s: GeneratedScenario) -> list[ScenarioDataSource]:
    """Return the scenario's data sources de-duplicated by name, in order.

    The first occurrence of each distinctly named source is kept; sources with
    an empty or whitespace-only name are skipped.

    Args:
        s: The Generated_Scenario whose data sources to de-duplicate.

    Returns:
        The distinct data sources in their original order.
    """
    seen: set[str] = set()
    distinct: list[ScenarioDataSource] = []
    for src in s.data_sources or []:
        name = (getattr(src, "name", "") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        distinct.append(src)
    return distinct


def _matching_criteria(sources: list[ScenarioDataSource]) -> list[str]:
    """Derive distinct field names across sources for Key Matching Criteria.

    Collects the field names contributed by the supplied sources, preserving
    first-seen order and skipping blanks. Non-string field names are ignored.

    Args:
        sources: The distinct data sources to inspect.

    Returns:
        The distinct field names across all sources, in first-seen order.
    """
    seen: set[str] = set()
    criteria: list[str] = []
    for src in sources:
        for raw in getattr(src, "fields", None) or []:
            if not isinstance(raw, str):
                continue
            name = raw.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            criteria.append(name)
    return criteria


def render_business_problem(s: GeneratedScenario) -> str:
    """Render the ``business_problem.md`` body for a Generated_Scenario.

    Produces the standard Module 1 problem-statement structure (the Step 12
    template sections: Problem Description, Use Case Category, Data Sources,
    Key Matching Criteria, Success Criteria) and embeds the observable
    bootcamp-generated marker (``GENERATED_MARKER``) so the document is
    recognizable as generated (Requirements 4.1, 4.3, 4.4).

    The output contains the problem description, the use-case category, every
    distinct data source, and the definition of success. Raises no exceptions
    for malformed input: empty fields render as empty sections and unnamed or
    duplicate sources are omitted.

    Args:
        s: The Generated_Scenario to render.

    Returns:
        The Markdown body using the standard Module 1 template plus the
        generated marker.
    """
    problem = (s.problem_description or "").strip()
    category = (s.use_case_category or "").strip()
    success = (s.success_definition or "").strip()
    distinct = _distinct_sources(s)

    lines: list[str] = []
    lines.append("# Business Problem Statement")
    lines.append("")
    # Observable marker identifying the case as bootcamp-generated (4.3).
    lines.append(GENERATED_MARKER)
    lines.append("")

    pattern = (s.selected_pattern_category or "").strip()
    lines.append(f"**Design Pattern**: {pattern if pattern else 'Custom'}")
    lines.append("")

    lines.append("## Problem Description")
    lines.append("")
    lines.append(problem)
    lines.append("")

    lines.append("## Use Case Category")
    lines.append("")
    lines.append(category)
    lines.append("")

    lines.append("## Data Sources")
    lines.append("")
    for index, src in enumerate(distinct, start=1):
        name = (src.name or "").strip()
        lines.append(f"{index}. **{name}**")
        source_fields = [
            f.strip()
            for f in (getattr(src, "fields", None) or [])
            if isinstance(f, str) and f.strip()
        ]
        if source_fields:
            lines.append(f"   - Fields: {', '.join(source_fields)}")
        lines.append(f"   - Records: {len(getattr(src, 'records', None) or [])}")
    lines.append("")

    lines.append("## Key Matching Criteria")
    lines.append("")
    criteria = _matching_criteria(distinct)
    for name in criteria:
        lines.append(f"- **{name}**")
    if not criteria:
        lines.append("- [None identified]")
    lines.append("")

    lines.append("## Success Criteria")
    lines.append("")
    lines.append(success)
    lines.append("")

    return "\n".join(lines)


# ── Registry recording ─────────────────────────────────────────────────────────


def _data_source_key(name: str, taken: set[str]) -> str:
    """Derive a unique registry DATA_SOURCE key from a source name.

    Registry keys must match ``^[A-Z][A-Z0-9_]*$``. The name is upper-cased,
    non-alphanumeric runs collapse to underscores, and a leading ``SOURCE_`` is
    added when the result would not begin with a letter. A numeric suffix is
    appended when needed so the key is unique among ``taken``.

    Args:
        name: The source name to convert.
        taken: Keys already assigned within this recording (mutated callers).

    Returns:
        A registry-valid key unique with respect to ``taken``.
    """
    base = re.sub(r"[^A-Z0-9]+", "_", (name or "").upper()).strip("_")
    if not base or not base[0].isalpha():
        base = f"SOURCE_{base}" if base else "SOURCE"

    key = base
    suffix = 2
    while key in taken:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def record_data_sources(s: GeneratedScenario) -> str:
    """Serialize one registry entry per distinct Scenario_Data source.

    Builds a registry containing exactly one ``RegistryEntry`` for each
    distinctly named ``ScenarioDataSource`` (de-duplicated by trimmed name,
    first occurrence kept) and serializes it to ``data_sources.yaml`` text by
    reusing the registry types and serializer from ``data_sources.py``. The
    number of recorded entries equals the number of distinct sources
    (Requirements 4.2, 5.1, 5.2).

    Each source's original name is preserved in the entry's ``name`` field so a
    downstream module reading the registry recovers every recorded source. The
    Senzing-mappable ``DATA_SOURCE`` key is derived from that name. Raises no
    exceptions for malformed input: unnamed or duplicate sources are skipped.

    Args:
        s: The Generated_Scenario whose data sources to record.

    Returns:
        The ``data_sources.yaml`` text produced by ``serialize_registry_yaml``.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entries: list[RegistryEntry] = []
    taken: set[str] = set()
    for src in _distinct_sources(s):
        name = (src.name or "").strip()
        key = _data_source_key(name, taken)
        taken.add(key)
        entries.append(RegistryEntry(
            data_source=key,
            name=name,
            file_path="",
            format="other",
            record_count=len(getattr(src, "records", None) or []),
            file_size_bytes=None,
            quality_score=None,
            mapping_status="pending",
            load_status="not_loaded",
            added_at=now,
            updated_at=now,
        ))

    registry = Registry(version=CURRENT_SCHEMA_VERSION, sources=entries)
    return serialize_registry_yaml(_registry_to_dict(registry))


# ── CLI Entry Point ─────────────────────────────────────────────────────────────

# Section headings the rendered Business_Problem_Document must contain. Each
# tuple is (human-readable label, regex matched case-insensitively against the
# document) so a recorded generated scenario is recognizably complete (4.4).
_REQUIRED_SECTIONS: list[tuple[str, str]] = [
    ("problem description", r"(?im)^\s*#+\s*problem description\b"),
    ("use case category", r"(?im)^\s*#+\s*use case category\b"),
    ("data sources", r"(?im)^\s*#+\s*data sources\b"),
    ("success criteria", r"(?im)^\s*#+\s*success criteria\b"),
]


def _read_text(path: str) -> tuple[str | None, str | None]:
    """Read a UTF-8 text file without raising.

    Args:
        path: The filesystem path to read.

    Returns:
        A ``(content, error)`` pair: ``content`` is the file text and ``error``
        is ``None`` on success; on failure ``content`` is ``None`` and
        ``error`` is a human-readable description of the condition.
    """
    try:
        return Path(path).read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except IsADirectoryError:
        return None, f"path is a directory, not a file: {path}"
    except UnicodeDecodeError as exc:
        return None, f"file is not valid UTF-8 text: {path} ({exc})"
    except OSError as exc:
        return None, f"cannot read {path}: {exc}"


def _validate_business_problem(path: str) -> list[str]:
    """Check a rendered ``business_problem.md`` for generated-scenario content.

    Confirms the document is readable, carries the observable bootcamp-generated
    marker, and contains the required Module 1 sections (problem description,
    use case category, data sources, success criteria). Raises no exceptions —
    a missing or unreadable file is reported as a violation (4.5, 5.4).

    Args:
        path: Path to the ``business_problem.md`` artifact.

    Returns:
        A list of human-readable violation strings (empty when valid).
    """
    violations: list[str] = []
    content, error = _read_text(path)
    if error is not None:
        violations.append(f"business_problem.md: {error}")
        return violations

    assert content is not None  # for type-checkers; guaranteed by error is None
    if GENERATED_MARKER not in content:
        violations.append(
            "business_problem.md: missing the bootcamp-generated marker "
            f"({GENERATED_MARKER!r})."
        )

    for label, pattern in _REQUIRED_SECTIONS:
        if not re.search(pattern, content):
            violations.append(
                f"business_problem.md: missing required section '{label}'."
            )

    return violations


def _validate_data_sources(path: str) -> list[str]:
    """Check a ``data_sources.yaml`` registry for the multi-source invariant.

    Confirms the registry is readable and parses, and that it records at least
    two distinct sources (mirroring the multi-source invariant enforced by
    ``validate_scenario``). Raises no exceptions — a missing, unreadable, or
    unparseable file is reported as a violation (4.5, 5.4); the underlying
    parser is itself tolerant.

    Args:
        path: Path to the ``data_sources.yaml`` artifact.

    Returns:
        A list of human-readable violation strings (empty when valid).
    """
    violations: list[str] = []
    content, error = _read_text(path)
    if error is not None:
        violations.append(f"data_sources.yaml: {error}")
        return violations

    assert content is not None  # guaranteed by error is None
    try:
        raw = parse_registry_yaml(content)
    except Exception as exc:  # tolerant: report rather than crash
        violations.append(f"data_sources.yaml: failed to parse ({exc}).")
        return violations

    sources = raw.get("sources")
    if not isinstance(sources, dict):
        violations.append("data_sources.yaml: no 'sources' mapping found.")
        return violations

    distinct = {str(key).strip() for key in sources if str(key).strip()}
    if len(distinct) < 2:
        violations.append(
            "data_sources.yaml: must record at least 2 distinct sources; "
            f"found {len(distinct)}."
        )

    return violations


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    The ``validate`` subcommand loads an existing ``business_problem.md`` +
    ``data_sources.yaml`` pair and checks the generated-scenario invariants:
    the document carries the bootcamp-generated marker and the required Module 1
    sections, and the registry records at least two distinct data sources. It
    degrades gracefully when an artifact is missing or unreadable — the
    condition is reported and a non-zero exit code returned, never an
    unhandled exception (Requirements 4.5, 5.4).

    Args:
        argv: Optional argument vector (defaults to ``sys.argv``).

    Returns:
        0 when the pair is valid, 1 on any violation or usage error.
    """
    parser = argparse.ArgumentParser(
        prog="business_case_offer.py",
        description=(
            "Validate a recorded Module 1 generated scenario "
            "(business_problem.md + data_sources.yaml)."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Check an existing business_problem.md + data_sources.yaml pair.",
    )
    validate_parser.add_argument(
        "--business-problem",
        default="docs/business_problem.md",
        metavar="PATH",
        help="Path to business_problem.md (default: docs/business_problem.md).",
    )
    validate_parser.add_argument(
        "--data-sources",
        default="config/data_sources.yaml",
        metavar="PATH",
        help="Path to data_sources.yaml (default: config/data_sources.yaml).",
    )

    args = parser.parse_args(argv)

    if args.command == "validate":
        violations: list[str] = []
        violations.extend(_validate_business_problem(args.business_problem))
        violations.extend(_validate_data_sources(args.data_sources))

        if violations:
            print("Generated-scenario validation FAILED:", file=sys.stderr)
            for violation in violations:
                print(f"  - {violation}", file=sys.stderr)
            return 1

        print("Generated-scenario validation passed: artifacts are valid.")
        return 0

    # argparse with required=True guarantees a known command; defensive only.
    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
