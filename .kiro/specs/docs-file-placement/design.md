# Docs File Placement Bugfix Design

## Overview

The senzing-bootcamp Power routes files in the **bootcamper's generated project** through
three cooperating mechanisms:

1. **`steering/project-structure.md`** — the convention bootcampers and the agent follow
   when deciding where a file belongs.
2. **`hooks/write-policy-gate.kiro.hook`** — a `preToolUse` write interceptor that blocks
   root placement of source/data/doc files and redirects them to conventional locations.
3. **`scripts/organize_mapping_files.py`** — a post-`mapping_workflow` organizer that sweeps
   generated mapping output into project subdirectories by file extension.

Five related defects all share one root cause family: these three mechanisms route
workflow-generated and helper files to **non-conventional locations** (or, for the docs
index, never create the conventional artifact). The organizer routes `.py` to a root
`scripts/` directory and `.md` to the `docs/` root; the hook offers an ambiguous
`src/` **or** `scripts/` destination for loose `.py`; the steering convention itself lists a
root `scripts/` directory and routes Markdown only as far as `docs/`; Module 5 writes
per-source mapper specs to `docs/{source}_mapper.md` (the `docs/` root) and fetches the
entity specification into both `docs/` and `docs/reference/`; and nothing ever produces a
`docs/README.md` index for the growing docs tree.

The fix is **targeted and minimal**: it changes the organizer's routing model, removes the
hook's `src/`-or-`scripts/` ambiguity (folding the utility fallback into `src/scripts/`),
realigns the two steering files to a single `src/`-rooted code convention with
`docs/`-subdirectory placement for mapping documentation, deduplicates the entity spec to
`docs/reference/`, and introduces a deterministic `docs/README.md` index generator. None of
the hook's security-relevant checks (Senzing SQL blocking, single-question enforcement,
feedback append-only guard, root whitelist) are weakened. All work stays within Python 3.11+
stdlib, kebab-case steering, and the hook's JSON schema.

## Glossary

- **Bug_Condition (C)**: A file write (workflow-generated, helper, or doc) lands somewhere
  other than its conventional project location, OR the expected `docs/README.md` index is
  absent while documents exist under `docs/`.
- **Property (P)**: The fixed power routes every such write to its conventional location and
  guarantees the docs index exists and is current.
- **Preservation**: Existing correct routing — bootcamper source-by-type, root-whitelist
  files, `data/`/`config/` writes, `.jsonl`/`.json` organizer routing, and every non-placement
  hook check — must remain byte-for-byte unchanged.
- **F / F'**: The current (buggy) power behavior / the fixed power behavior across the three
  mechanisms.
- **organize_mapping_files.py**: The organizer script in `senzing-bootcamp/scripts/` that
  moves `mapping_workflow` output from a flat source directory into project subdirectories
  using a routing table keyed by file extension.
- **write-policy-gate**: The `preToolUse` hook in `senzing-bootcamp/hooks/` that performs four
  checks; Check 4 (Root File Placement Enforcement) is the placement-relevant one.
- **project-structure.md**: The `inclusion: auto` steering file in `senzing-bootcamp/steering/`
  that defines the generated project's directory tree and root-placement rules.
- **module-05-phase2-data-mapping.md**: The `inclusion: manual` steering file that drives the
  mapping workflow and currently writes mapper specs to `docs/{source}_mapper.md`.
- **Mapper spec**: A per-source mapping specification Markdown file (e.g.,
  `playpalace_mapper.md`) — one per data source.
- **Entity spec**: `senzing_entity_specification.md`, the fetched Senzing entity specification
  reference.
- **Conventional location**: The single deterministic target a file type maps to under the
  corrected convention (see Fix Implementation routing table).

## Bug Details

### Bug Condition

The bug manifests when the power routes a workflow-generated or helper file to a location
that violates the project-structure convention, or when the docs index that should describe
the generated project's `docs/` tree is never created. The three mechanisms are responsible:
the organizer's extension table sends `.py` to a root `scripts/` directory and `.md` to the
`docs/` root; the hook's Check 4 fallback offers `src/` **or** `scripts/`; the steering files
encode a root `scripts/` directory and stop Markdown routing at `docs/`; Module 5 writes
mapper specs and the entity spec to the `docs/` root; and no mechanism emits `docs/README.md`.

**Formal Specification:**

```
FUNCTION isBugCondition(write)
  INPUT: write of type FileWrite  // {path, kind, content, origin}
  OUTPUT: boolean

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

### Examples

- `mapping_workflow` emits `sz_json_analyzer.py`; the organizer routes it to `scripts/sz_json_analyzer.py`
  (root) — **expected** `src/mapping/sz_json_analyzer.py` (under `src/`).
- Module 5 writes the PlayPalace mapper spec to `docs/playpalace_mapper.md` (docs root) —
  **expected** `docs/mapping/playpalace_mapper.md`.
- The entity-spec fetch writes `docs/senzing_entity_specification.md` while
  `docs/reference/senzing_entity_specification.md` already exists — **expected** a single copy
  at `docs/reference/senzing_entity_specification.md`, root duplicate removed.
- A generator script is written to `scripts/make_results_dashboard.py` (root, beside `src/`) —
  **expected** `src/scripts/make_results_dashboard.py`.
- After several modules `docs/` holds many documents across `docs/progress/`, `docs/mapping/`,
  `docs/reference/`, `docs/feedback/`, but there is no `docs/README.md` — **expected** a current
  index listing each document with a short description.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Bootcamper-authored source files routed by type continue to land in `src/transform/`,
  `src/load/`, and `src/query/` (Check 4 transform/load/query branches).
- Root-whitelist files (`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`,
  `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`) remain permitted in the project root.
- Writes to `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/`, `config/`, and
  `database/G2C.db` route and store exactly as today.
- The organizer's `.jsonl → data/` and `.json → config/` routing is unchanged.
- The hook's non-placement checks — Senzing SQL blocking (Check 1), single-question
  enforcement for `.question_pending` (Check 2), and the append-only guard for
  `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` (Check 3) — apply unchanged.
- Documents already in a correct `docs/` subdirectory (`docs/reference/`, `docs/mapping/`,
  `docs/feedback/`, `docs/progress/`) are left in place and never moved.

**Scope:**

All writes that do NOT satisfy `isBugCondition` must be completely unaffected by this fix.
This includes:

- Bootcamper source-by-type writes and root-whitelist writes.
- Data and config writes (`.jsonl`, `.csv`, `.json` to their existing destinations).
- Non-placement hook checks (SQL, single-question, feedback append-only).
- Already-correctly-placed documents.

**Note:** The expected correct placement for buggy writes is defined in the Correctness
Properties section (Property 1 and its sub-properties). This section enumerates only what must
NOT change.

## Hypothesized Root Cause

Each defect clause traces to a specific mechanism:

1. **Organizer routing table is too coarse and points at the wrong roots (1.1, 1.2, 1.3)**.
   `ROUTING_RULES` in `organize_mapping_files.py` maps `.py → "scripts"` (a *root* `scripts/`
   directory) and `.md → "docs"` (the `docs/` *root*). Because routing is purely
   extension-based, every Markdown file — mapper specs, the entity spec, reference docs —
   lands flat in `docs/`, and every Python helper lands in root `scripts/`. There is no
   filename-aware rule to send `*_mapper.md` to `docs/mapping/` or
   `senzing_entity_specification.md` to `docs/reference/`.

2. **Hook Check 4 encodes the `src/`-or-`scripts/` ambiguity (1.4)**. The `.py` corrective
   routing in `write-policy-gate.kiro.hook` ends with "Otherwise (utility scripts, CLI tools)
   → `scripts/{filename}`", placing utilities in a root `scripts/` directory beside `src/` and
   splitting executable code across two top-level locations.

3. **Steering convention itself lists a root `scripts/` (1.4)**. `project-structure.md` shows
   `scripts/` as a top-level sibling of `src/` in the directory tree, lists it in the
   create-structure snippets, and routes loose `.py` to "`src/transform/`, `src/load/`,
   `src/query/`, or `scripts/`". The convention the agent is told to follow is itself
   inconsistent.

4. **Module 5 targets the `docs/` root for per-source artifacts and re-fetches the entity
   spec (1.2, 1.3)**. `module-05-phase2-data-mapping.md` instructs the agent to save mapper
   specs to `docs/{source_name}_mapper.md` and mapping docs to `docs/mapping_[name].md`, and
   the entity-spec reference is fetched/written without a single canonical `docs/reference/`
   target, allowing a `docs/` root duplicate.

5. **No mechanism produces a docs index (1.5)**. Neither steering nor any script creates or
   maintains `docs/README.md`, so the growing `docs/` tree has no index.

## Correctness Properties

Property 1: Bug Condition — Conventional Placement Of Routed And Generated Files

_For any_ file write where the bug condition holds (`isBugCondition` returns true), the fixed
power SHALL route the file to its conventional location: Python mapping-support scripts into a
`src/` subdirectory (`src/mapping/`), helper/utility scripts into `src/scripts/`,
`identifier_crosswalk.json` into `config/` (a permitted `src/`-or-`config/` location),
reference Markdown into the appropriate `docs/` subdirectory, per-source mapper specs into
`docs/mapping/`, the entity specification into `docs/reference/` as a single copy, and SHALL
ensure `docs/README.md` exists and lists every document under `docs/`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation — Non-Buggy Writes Are Unchanged

_For any_ file write where the bug condition does NOT hold (`isBugCondition` returns false),
the fixed power SHALL produce exactly the same result as the original power, preserving
bootcamper source-by-type routing, root-whitelist allowance, `data/`/`config/` writes, the
organizer's `.jsonl`/`.json` routing, the hook's SQL/single-question/feedback-append-only
checks, and the in-place position of already-correctly-placed documents.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

Property 3: Routing Determinism — Single Destination Per File

_For any_ filename, the organizer's `route(filename)` function SHALL return exactly one target
subdirectory (or a single "unrouted" outcome), with no input mapping to two candidate
locations — eliminating the `src/`-or-`scripts/` ambiguity.

**Validates: Requirements 2.4**

Property 4: Mapper-Spec And Entity-Spec Routing

_For any_ filename matching the mapper-spec pattern (`*_mapper.md`), `route` SHALL return
`docs/mapping`; _for any_ filename equal to `senzing_entity_specification.md`, `route` SHALL
return `docs/reference`.

**Validates: Requirements 2.2, 2.3**

Property 5: Entity-Spec Deduplication

_For any_ source `senzing_entity_specification.md` whose routed destination
(`docs/reference/senzing_entity_specification.md`) already exists, the organizer SHALL remove
the misplaced source copy rather than leaving a duplicate, yielding exactly one copy under
`docs/reference/`.

**Validates: Requirements 2.3**

Property 6: Docs Index Completeness And Currency

_For any_ `docs/` tree containing one or more documents, the index generator SHALL produce a
`docs/README.md` that contains an entry for every document under `docs/` and its
subdirectories (excluding `README.md` itself), and regenerating after documents are added or
removed SHALL keep the index in sync.

**Validates: Requirements 2.5**

Property 7: Idempotence And Preservation Of Correct Placement

_For any_ set of files, running the organizer twice SHALL produce no additional moves on the
second run, and files already in their correct destination SHALL never be moved or modified.

**Validates: Requirements 3.5, 3.6**

## Fix Implementation

### Summary Of The Corrected Convention

The corrected routing model is the single source of placement truth. All three mechanisms
align to it:

| File (origin) | Old destination (F) | New destination (F') | Defect |
|---|---|---|---|
| `sz_*.py`, mapping helper/analyzer `.py` (organizer) | `scripts/` (root) | `src/mapping/` | 1.1 |
| Loose utility/CLI `.py` (hook fallback) | `src/` **or** `scripts/` | `src/scripts/` | 1.4 |
| Bootcamper transform/load/query `.py` (hook) | `src/transform|load|query/` | `src/transform|load|query/` (unchanged) | preserve 3.1 |
| `identifier_crosswalk.json` (organizer) | `config/` | `config/` (unchanged, permitted) | 1.1 / preserve |
| `*_mapper.md` (organizer + Module 5) | `docs/` (root) | `docs/mapping/` | 1.2 |
| `senzing_entity_specification.md` (organizer + Module 5) | `docs/` (root) + `docs/reference/` (dup) | `docs/reference/` (single) | 1.3 |
| other mapping reference `.md` (organizer) | `docs/` (root) | `docs/mapping/` | 1.1 |
| `.jsonl` (organizer) | `data/` | `data/` (unchanged) | preserve 3.5 |
| `.json` (organizer) | `config/` | `config/` (unchanged) | preserve 3.5 |
| docs index | (none) | `docs/README.md` (generated) | 1.5 |

### Change 1 — Organizer routing model (`scripts/organize_mapping_files.py`)

Defects: 1.1, 1.2, 1.3 (and supports 2.1, 2.2, 2.3).

Replace the flat, extension-only `ROUTING_RULES` dict with an **ordered rule list** evaluated
first-match-wins, where each rule is a `(matcher, target_subdir)` pair. Matchers test the
filename first (exact name and suffix patterns), then fall back to extension. Expose a pure
`route(filename: str) -> str | None` function so it is directly unit- and property-testable.

```
# Ordered, first-match-wins. target is a POSIX-style relative subdir.
ROUTING_RULES: list[RoutingRule] = [
    RoutingRule(match_name("senzing_entity_specification.md"), "docs/reference"),
    RoutingRule(match_suffix("_mapper.md"),                    "docs/mapping"),
    RoutingRule(match_ext(".md"),                              "docs/mapping"),
    RoutingRule(match_ext(".py"),                              "src/mapping"),
    RoutingRule(match_ext(".jsonl"),                           "data"),
    RoutingRule(match_ext(".json"),                            "config"),
]

FUNCTION route(filename) -> str | None
  FOR rule IN ROUTING_RULES DO
    IF rule.matcher(filename) THEN RETURN rule.target
  RETURN None   // unrouted (warned, left in place — unchanged behavior)
```

Notes:
- `.json → config` and `.jsonl → data` are carried over verbatim, preserving today's behavior
  (Property 2, Property 7) and the existing CLI-default tests.
- `target_subdir` becomes a nested path (e.g., `src/mapping`, `docs/reference`). `plan_moves`
  already resolves `project_root / target_subdir / name` and `execute_moves` already calls
  `mkdir(parents=True, exist_ok=True)`, so nested targets need no further plumbing.
- The function is filename-based and deterministic — one filename yields exactly one target
  (Property 3, Property 4).

### Change 2 — Entity-spec deduplication in the organizer

Defect: 1.3 (supports 2.3).

Add a `"deduplicate"` outcome to `MoveResult.status`. In `plan_moves`, when a source file's
routed destination already exists AND the file is a known canonical-single artifact
(currently `senzing_entity_specification.md` routing to `docs/reference/`), mark it
`deduplicate` instead of `skipped`. `execute_moves` removes the misplaced source copy for
`deduplicate` entries (after confirming the destination exists), leaving exactly one copy
under `docs/reference/`. For all other extensions, the existing `skipped` (conflict, no
overwrite) behavior is retained unchanged (Property 7). `print_summary` reports deduplicated
files on stderr.

This dedup removal is the only file deletion the organizer performs and is narrowly scoped to
the single named canonical artifact, so it cannot remove bootcamper data or correctly-placed
files.

### Change 3 — Hook Check 4 `.py` fallback (`hooks/write-policy-gate.kiro.hook`)

Defect: 1.4 (supports 2.4).

In Check 4's `.py` corrective routing, change the final branch from:

```
- Otherwise (utility scripts, CLI tools) -> scripts/{filename}
```

to:

```
- Otherwise (utility scripts, CLI tools) -> src/scripts/{filename}
```

The transform/load/query branches are unchanged (preserve 3.1). This removes the only
`src/`-or-`scripts/` ambiguity in the gate and routes all non-typed `.py` to a single
deterministic `src/scripts/` destination. No other check (1, 2, 3) or the root whitelist is
touched. The hook JSON `name`/`version`/`when`/`then` schema is preserved; the only edit is
prompt text inside `then.prompt`.

### Change 4 — `project-structure.md` steering realignment

Defect: 1.4 (supports 2.4).

- Directory tree: remove the top-level `scripts/` entry; add `src/{...,scripts}` and the docs
  subdirectories actually used (`docs/{mapping,reference,progress,feedback}`).
- Root File Placement Enforcement list: change "Source code (`.py`) -> Route to
  `src/transform/`, `src/load/`, `src/query/`, or `scripts/`" to "... or `src/scripts/`"
  (drop the root `scripts/` option).
- "The `scripts/` directory is reserved for executable code only" -> "The `src/scripts/`
  directory ...".
- Create-Structure snippets (Python `os.makedirs`, Linux/macOS `mkdir -p`, Windows
  PowerShell): replace the standalone `scripts` entry with `src/scripts` and add
  `docs/mapping`, `docs/reference`, `docs/progress` so the conventional tree exists up front.
- Add a one-line rule: all executable code lives under `src/` (no top-level `scripts/`).

Frontmatter (`inclusion: auto`), kebab-case filename, and the no-external-URL steering rule
are preserved.

### Change 5 — `module-05-phase2-data-mapping.md` steering realignment

Defects: 1.2, 1.3, 1.5 (supports 2.2, 2.3, 2.5).

- Change all per-source mapper-spec targets from `docs/{source_name}_mapper.md` to
  `docs/mapping/{source_name}_mapper.md` (the inline instruction, the mandatory-gate text, and
  the per-source completion checkpoint).
- Change `docs/mapping_[name].md` and the quality HTML to the `docs/mapping/` subdirectory for
  consistency; the transformation-lineage doc likewise targets `docs/mapping/`.
- Entity spec: instruct that the entity specification reference is written only to
  `docs/reference/senzing_entity_specification.md` (single canonical copy), and that any
  existing `docs/` root copy is removed (or left to the organizer's dedup pass).
- Add a step after the organizer invocation: run the docs-index generator (Change 6) to
  create/refresh `docs/README.md`, and note that the index is regenerated whenever documents
  are added across modules.

### Change 6 — New docs-index generator (`scripts/generate_docs_index.py`)

Defect: 1.5 (supports 2.5).

Add a new stdlib-only script following the established script pattern (shebang,
`from __future__ import annotations`, module docstring with usage, `@dataclass`, `argparse`,
`main(argv=None)`, exit 0/1). It walks the generated project's `docs/` tree, collects every
document (excluding `docs/README.md` itself), derives a short description (first Markdown
heading or first non-empty line, falling back to the filename), groups entries by
subdirectory, and writes a deterministic `docs/README.md` index. A `--check` mode (consistent
with `measure_steering.py --check` in CI) reports drift without writing.

```
FUNCTION generate_index(docs_root) -> str
  entries := []
  FOR path IN sorted(walk(docs_root)) WHERE isDocument(path) AND name != "README.md" DO
    entries.append(IndexEntry(rel=relative_to(docs_root, path),
                              desc=describe(path)))
  RETURN render_markdown(group_by_subdir(entries))
```

Determinism (sorted traversal, stable rendering) makes the output property-testable
(Property 6).

### Files Changed

- `senzing-bootcamp/scripts/organize_mapping_files.py` — routing model + dedup (Changes 1, 2).
- `senzing-bootcamp/scripts/generate_docs_index.py` — new generator (Change 6).
- `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` — Check 4 `.py` fallback (Change 3).
- `senzing-bootcamp/steering/project-structure.md` — convention realignment (Change 4).
- `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` — doc targets + index step (Change 5).
- `senzing-bootcamp/tests/test_organize_mapping_files.py` — updated expectations + new properties.
- `senzing-bootcamp/tests/test_generate_docs_index.py` — new test module.

### Out Of Scope / Considered Alternatives

- **Routing organizer `.py` to `src/scripts/` instead of `src/mapping/`**: rejected because
  the organizer exclusively processes `mapping_workflow` output, so `src/mapping/` is the
  semantically correct grouping; `src/scripts/` remains the destination for general
  utility/CLI scripts via the hook fallback. Both live under `src/`, so neither reintroduces
  the prohibited top-level split.
- **Making the organizer move arbitrary already-misplaced files across the whole project**:
  rejected as too broad; it risks moving correctly-placed files (violating 3.6). Relocation is
  handled by re-applying the deterministic `route()` to files the organizer already scans,
  plus the narrowly-scoped entity-spec dedup.

## Testing Strategy

### Validation Approach

Two phases. First, surface counterexamples that demonstrate each defect on the **unfixed**
code (confirming the root-cause analysis). Then verify the fix routes buggy inputs correctly
and preserves all non-buggy behavior. Tests use the existing pytest + Hypothesis suite and the
established `sys.path` import shim, class-based organization, `st_`-prefixed strategies, and
`@settings(max_examples=20)`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix.
Confirm or refute the root-cause analysis; if refuted, re-hypothesize.

**Test Plan**: Drive the current `plan_moves`/`route` and inspect the hook/steering text. Run
against the UNFIXED code to observe the misplacements.

**Test Cases**:
1. **Python helper routing**: route `sz_json_analyzer.py` -> asserts `src/mapping`; on unfixed
   code returns `scripts` (root). (will fail on unfixed code)
2. **Mapper spec routing**: route `playpalace_mapper.md` -> asserts `docs/mapping`; on unfixed
   code returns `docs`. (will fail on unfixed code)
3. **Entity-spec routing/dedup**: route `senzing_entity_specification.md` -> asserts
   `docs/reference`; on unfixed code returns `docs` (root duplicate). (will fail on unfixed code)
4. **Utility-script fallback (hook)**: assert the hook prompt routes non-typed `.py` to
   `src/scripts/` with no `scripts/` (root) option; on unfixed code the prompt still offers
   root `scripts/`. (will fail on unfixed code)
5. **Docs index presence**: given a `docs/` tree with documents, assert `generate_docs_index`
   produces `docs/README.md`; on unfixed code the generator does not exist. (will fail on unfixed code)

**Expected Counterexamples**:
- `.py` routed to root `scripts/`, `.md` (including mapper/entity spec) routed to `docs/` root.
- Hook prompt still contains the `src/` OR `scripts/` fallback.
- No `docs/README.md` produced.

### Fix Checking

**Goal**: For all inputs where the bug condition holds, the fixed power produces conventional
placement.

**Pseudocode:**
```
FOR ALL write WHERE isBugCondition(write) DO
  result := F'(write)
  ASSERT conventionalLocation(result)
    // mapping helper/analyzer .py    -> src/mapping/
    // utility/CLI .py (hook)         -> src/scripts/
    // identifier_crosswalk.json      -> config/
    // *_mapper.md                    -> docs/mapping/
    // senzing_entity_specification.md -> docs/reference/ (single copy)
    // other reference .md            -> docs/mapping/
    // docs index                     -> docs/README.md exists and lists every doc
END FOR
```

### Preservation Checking

**Goal**: For all inputs where the bug condition does NOT hold, the fixed power produces the
same result as the original.

**Pseudocode:**
```
FOR ALL write WHERE NOT isBugCondition(write) DO
  ASSERT F(write) = F'(write)
END FOR
```

**Testing Approach**: Property-based testing is preferred for preservation because it
generates many inputs across the routing domain, catches edge cases manual tests miss, and
gives strong assurance that `.jsonl`/`.json` routing, conflict-skip behavior, idempotence, and
already-correct placements are unchanged.

**Test Plan**: Capture current `.jsonl -> data`, `.json -> config`, conflict-skip, dry-run, and
idempotence behavior (these already pass on unfixed code) and assert they still hold after the
fix. Confirm the hook's Checks 1-3 prompt text is byte-identical.

**Test Cases**:
1. **Data/config routing preserved**: `.jsonl -> data/`, `.json -> config/` unchanged across
   generated filenames.
2. **Conflict-skip preserved**: same-named non-canonical files at destination are skipped, not
   overwritten.
3. **Idempotence preserved**: a second organizer run produces zero moves.
4. **Correct placement untouched**: files already under `docs/mapping/`, `docs/reference/`,
   etc. are not moved.
5. **Hook non-placement checks intact**: assert the hook prompt still contains the SQL,
   single-question, and feedback append-only sections verbatim.

### Unit Tests

- `route()` returns the expected subdir for each representative filename (helpers, mapper
  specs, entity spec, reference `.md`, `.jsonl`, `.json`, unrouted `.txt`).
- Entity-spec dedup: when `docs/reference/senzing_entity_specification.md` exists, the root
  copy is removed and exactly one copy remains; stderr reports the dedup.
- `generate_docs_index`: empty tree, single doc, nested subdirs, and `--check` drift detection.
- CLI defaults/errors for both scripts (mirror existing `TestCLIArgumentDefaults`).
- Hook JSON remains schema-valid (`name`, `version`, `when`, `then`) and `when.type` is
  `preToolUse` with `toolTypes: ["write"]`.

### Property-Based Tests

- **Routing determinism (Property 3)**: for any generated filename, `route` returns exactly
  one target or `None`; calling twice is stable.
- **Mapper/entity routing (Property 4)**: for any basename, `{base}_mapper.md -> docs/mapping`
  and `senzing_entity_specification.md -> docs/reference`.
- **Conventional placement (Property 1)**: generated recognized files land under their
  conventional subdir after `execute_moves`, and never at the project root or `docs/` root.
- **Dedup (Property 5)**: with a pre-existing `docs/reference/` entity spec and a misplaced
  root copy, after the run exactly one copy exists under `docs/reference/`.
- **Index completeness/currency (Property 6)**: for any generated set of `docs/` documents,
  `docs/README.md` lists every document; adding/removing documents and regenerating keeps the
  index in sync.
- **Preservation (Property 2, Property 7)**: `.jsonl`/`.json` routing, conflict-skip,
  idempotence, and dry-run hold across generated file sets exactly as on unfixed code.

### Integration Tests

- Full mapping-output sweep: a mixed source directory (helper `.py`, `*_mapper.md`, entity
  spec, `profile_report.md`, `.jsonl`, `.json`) organizes into `src/mapping/`, `docs/mapping/`,
  `docs/reference/`, `data/`, `config/` in one run, then the index generator produces a
  complete `docs/README.md`.
- Re-run the sweep to confirm idempotence and a stable index (no spurious moves or diffs).
- CI alignment: `validate_power.py`, `validate_commonmark.py`, and the pytest suite pass with
  the updated steering and new script.
