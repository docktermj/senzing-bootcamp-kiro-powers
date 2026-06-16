# Bugfix Requirements Document

## Introduction

The senzing-bootcamp Kiro Power guides bootcampers through building a working Senzing
entity-resolution project. As the bootcamp progresses, the power's steering files, the
`write-policy-gate` hook, and the `organize_mapping_files.py` helper are responsible for
routing files into a conventional project structure (source code under `src/`,
documentation under `docs/`, data under `data/`, and so on).

This bug groups five related defects, all about the **generated project's** file
organization being inconsistent with the project-structure conventions the bootcamp
otherwise enforces. The defects manifest in the bootcamper's working project, not in the
power repository itself — but the fix lives entirely in the power's guidance and
automation (steering files, the hook, and the organizer script).

The five misplacement symptoms are:

1. Workflow-provided mapping support files (Python helper/analyzer scripts, an identifier
   crosswalk JSON, and reference Markdown) land in the project root and the mapping
   working directory instead of `src/` and `docs/`.
2. Per-source mapper specification Markdown files land in the `docs/` root instead of
   `docs/mapping/`, even though a `docs/mapping/` directory already exists.
3. `senzing_entity_specification.md` is duplicated — one copy in the `docs/` root and one
   in `docs/reference/`.
4. A root-level `scripts/` directory sits beside `src/`, splitting executable code across
   two top-level locations; the write-policy gate even routes loose root `.py` files to
   `src/` **or** `scripts/`, which is itself inconsistent.
5. The generated project's `docs/` directory accumulates many documents and subdirectories
   with no README index describing them.

The unifying theme: files in the generated project are routed to non-conventional
locations (or, for item 5, the conventional index artifact is never created), making the
project structure inconsistent and harder to navigate.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the Module 5 mapping workflow produces support files (e.g., `sz_json_analyzer.py`, `sz_schema_generator.py`, `sz_verbatim_check.py`, `sz_routing_report.py`, `identifier_crosswalk.json`, `senzing_entity_specification.md`, `profile_report.md`, `senzing_mapping_examples.md`) THEN the system writes them to the project root or the mapping working directory (`data/temp/mapping_*`) instead of a conventional `src/` or `docs/` location, bypassing the type-based organization the write-policy gate applies to the bootcamper's own files.

1.2 WHEN the mapping workflow writes a per-source mapper specification (e.g., `playpalace_mapper.md`, `kidzkart_mapper.md`, `toyworld_mapper.md`) THEN the system writes it to the `docs/` root rather than `docs/mapping/`, even though `docs/mapping/` already exists and holds related mapping artifacts such as `profile_report.md`.

1.3 WHEN the entity specification reference is fetched/written during the mapping workflow THEN the system produces `senzing_entity_specification.md` in both `docs/` (root) and `docs/reference/`, creating a duplicate with no single authoritative copy.

1.4 WHEN helper/utility scripts are generated (e.g., `make_results_dashboard.py`, the toy-customer data generator) THEN the system places them in a root-level `scripts/` directory beside `src/`, and the write-policy gate routes loose root `.py` files to either `src/` subdirectories OR `scripts/`, splitting executable code across two top-level locations.

1.5 WHEN documents accumulate in the generated project's `docs/` directory and its subdirectories (`docs/progress/`, `docs/mapping/`, `docs/reference/`, `docs/feedback/`) across modules THEN the system provides no `docs/README.md` index describing the documents, leaving no single place that lists what each document is or why it matters.

### Expected Behavior (Correct)

2.1 WHEN the Module 5 mapping workflow produces support files THEN the system SHALL route them to conventional locations: Python helper/analyzer scripts into an appropriate `src/` subdirectory (e.g., `src/mapping/` or `src/tools/`), `identifier_crosswalk.json` under `src/` (or a `config/`/data location), and reference `.md` files under the appropriate `docs/` location — applying the same type-based organization used for the bootcamper's own files.

2.2 WHEN the mapping workflow writes a per-source mapper specification THEN the system SHALL write it into `docs/mapping/` (e.g., `docs/mapping/playpalace_mapper.md`), and any existing mapper specs in the `docs/` root SHALL be relocated to `docs/mapping/`.

2.3 WHEN the entity specification reference is fetched/written THEN the system SHALL keep a single copy in `docs/reference/senzing_entity_specification.md`, remove the duplicate from the `docs/` root, and target `docs/reference/` so the duplicate is not re-created.

2.4 WHEN helper/utility scripts are generated THEN the system SHALL place them under `src/scripts/`, drop the root-level `scripts/` location from the project-structure convention so all code lives under `src/`, route loose root `.py` files to a single deterministic `src/` location (no `src/` OR `scripts/` ambiguity), and relocate any existing files from a root `scripts/` directory into `src/scripts/`.

2.5 WHEN documents accumulate in the generated project's `docs/` directory and its subdirectories THEN the system SHALL provide a `docs/README.md` index that lists every document under `docs/` and its subdirectories with a short description and a note on why/when to read it, and SHALL keep this index current as documents are created across modules.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper writes their own new source files by type (transformation, loading, or query code) THEN the write-policy gate SHALL CONTINUE TO route them to their conventional `src/transform/`, `src/load/`, and `src/query/` locations.

3.2 WHEN a file on the root whitelist is written to the project root (e.g., `.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`) THEN the write-policy gate SHALL CONTINUE TO allow it at the project root.

3.3 WHEN a write targets a non-source location such as `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/`, `config/`, or `database/G2C.db` THEN the system SHALL CONTINUE TO route and store those files as it does today.

3.4 WHEN the write-policy gate's non-placement checks run (Senzing SQL blocking, single-question enforcement for `.question_pending`, and the append-only guard for `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`) THEN the system SHALL CONTINUE TO apply them unchanged.

3.5 WHEN the mapping workflow produces files whose extensions are already routed correctly by the organizer (e.g., `.jsonl` data into `data/`) THEN the system SHALL CONTINUE TO route those files to their conventional, unchanged locations.

3.6 WHEN documents already reside in their correct `docs/` subdirectory (e.g., `docs/reference/`, `docs/mapping/`, `docs/feedback/`, `docs/progress/`) THEN the system SHALL CONTINUE TO leave them in place and SHALL NOT move correctly-placed files.

## Deriving the Bug Condition

**F** is the current power behavior (steering guidance + `write-policy-gate` hook +
`organize_mapping_files.py`). **F'** is the corrected behavior after the fix.

### Bug Condition

```pascal
FUNCTION isBugCondition(write)
  INPUT: write of type FileWrite  // {path, kind, content, origin}
  OUTPUT: boolean

  // A write triggers the bug when a workflow-provided or generated file
  // lands somewhere other than its conventional location, OR when the
  // docs index that should exist for the generated project is missing.

  RETURN
    // 1.1 — mapping support files at root or mapping working dir
    (write.origin = "mapping_workflow_support"
        AND isPythonHelper(write) AND NOT under(write.path, "src/"))
    OR (write.origin = "mapping_workflow_support"
        AND isCrosswalkJson(write) AND NOT under(write.path, "src/")
        AND NOT under(write.path, "config/"))
    OR (write.origin = "mapping_workflow_support"
        AND isReferenceMarkdown(write) AND NOT under(write.path, "docs/"))
    // 1.2 — per-source mapper spec in docs/ root
    OR (isMapperSpec(write) AND parentDir(write.path) = "docs/")
    // 1.3 — entity spec written to docs/ root (duplicate of docs/reference/)
    OR (isEntitySpec(write) AND parentDir(write.path) = "docs/")
    // 1.4 — helper/utility script outside src/ (root scripts/ or root .py)
    OR (isUtilityScript(write) AND NOT under(write.path, "src/"))
    // 1.5 — docs index never created
    OR (docsHasDocuments() AND NOT exists("docs/README.md"))
END FUNCTION
```

### Property — Fix Checking

```pascal
// For every buggy write, the fixed power routes it to the conventional location
// (and ensures the docs index exists and is current).
FOR ALL write WHERE isBugCondition(write) DO
  result ← F'(write)
  ASSERT conventionalLocation(result)
    // Python helper/analyzer scripts  -> src/ subdir (e.g. src/mapping/, src/tools/)
    // identifier_crosswalk.json       -> src/ (or config/ / data location)
    // reference .md                   -> docs/ (appropriate subdir)
    // per-source mapper spec .md      -> docs/mapping/
    // entity specification .md        -> docs/reference/ (single copy only)
    // helper/utility scripts          -> src/scripts/ (no root scripts/)
    // docs index                      -> docs/README.md exists and lists every doc
END FOR
```

### Property — Preservation Checking

```pascal
// For every non-buggy write, the fixed power behaves identically to today:
// correctly-placed files, root-whitelist files, data/config writes, and the
// hook's SQL / single-question / feedback-append-only checks are unchanged.
FOR ALL write WHERE NOT isBugCondition(write) DO
  ASSERT F(write) = F'(write)
END FOR
```

### Counterexamples (concrete demonstrations of the bug)

- `mapping_workflow` writes `sz_json_analyzer.py` to the project root -> expected `src/mapping/sz_json_analyzer.py`.
- `mapping_workflow` writes `playpalace_mapper.md` to `docs/playpalace_mapper.md` -> expected `docs/mapping/playpalace_mapper.md`.
- Entity-spec fetch writes `docs/senzing_entity_specification.md` while `docs/reference/senzing_entity_specification.md` already exists -> expected single copy in `docs/reference/`.
- Generator script written to `scripts/make_results_dashboard.py` (root) -> expected `src/scripts/make_results_dashboard.py`.
- After several modules, `docs/` holds many documents but no `docs/README.md` -> expected a current index listing each document with a description.
