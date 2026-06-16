# Implementation Plan

## Overview

This plan follows the exploratory bugfix workflow: first surface counterexamples that
demonstrate each defect on the **unfixed** code, then apply the six targeted changes from the
design, and finally validate with fix-checking and preservation-checking property-based tests.

All work stays within Python 3.11+ stdlib, pytest + Hypothesis (`@settings(max_examples=20)`,
`st_`-prefixed strategies, class-based organization, `sys.path` import shim), kebab-case
steering, and the hook's JSON schema. The `write-policy-gate` security checks (Senzing SQL
blocking, single-question enforcement, feedback append-only guard, root whitelist) MUST NOT be
weakened.

Affected files:
- `senzing-bootcamp/scripts/organize_mapping_files.py` (Changes 1, 2)
- `senzing-bootcamp/scripts/generate_docs_index.py` (Change 6, new)
- `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` (Change 3)
- `senzing-bootcamp/steering/project-structure.md` (Change 4)
- `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` (Change 5)
- `senzing-bootcamp/tests/test_organize_mapping_files.py` (updated)
- `senzing-bootcamp/tests/test_generate_docs_index.py` (new)

## Tasks

- [x] 1. Write bug condition exploration tests (BEFORE implementing any fix)
  - **Property 1: Bug Condition** - Conventional Placement Of Routed And Generated Files
  - **CRITICAL**: These tests MUST FAIL on unfixed code — failure confirms the defects exist
  - **DO NOT attempt to fix the test or the code when it fails** at this stage
  - **NOTE**: These tests encode the expected (fixed) behavior — they will validate the fix once they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate each of the five misplacement defects
  - **Scoped PBT Approach**: Each routing defect is deterministic, so scope the property to the concrete failing filename(s) for reproducibility, then generalize with a basename strategy where noted
  - Add these exploratory cases to `senzing-bootcamp/tests/test_organize_mapping_files.py` (and a new `senzing-bootcamp/tests/test_generate_docs_index.py` for the index case):
    - **Case 1 — Python helper routing (defect 1.1)**: assert `route("sz_json_analyzer.py")` returns `"src/mapping"`. On unfixed code the organizer routes `.py` to root `scripts` → FAILS. Generalize: for any `st_basename()`, `route(f"{base}.py")` → `"src/mapping"`.
    - **Case 2 — Mapper spec routing (defect 1.2)**: assert `route("playpalace_mapper.md")` returns `"docs/mapping"`. On unfixed code `.md` routes to `docs` root → FAILS. Generalize: for any `st_basename()`, `route(f"{base}_mapper.md")` → `"docs/mapping"`.
    - **Case 3 — Entity-spec routing (defect 1.3)**: assert `route("senzing_entity_specification.md")` returns `"docs/reference"`. On unfixed code routes to `docs` root → FAILS.
    - **Case 4 — Utility-script fallback in hook (defect 1.4)**: parse `write-policy-gate.kiro.hook` and assert the Check 4 `.py` fallback prompt routes non-typed `.py` to `src/scripts/` and contains NO root `scripts/` fallback option. On unfixed code the prompt offers `scripts/{filename}` → FAILS.
    - **Case 5 — Docs index presence (defect 1.5)**: given a `docs/` tree containing documents, assert `generate_docs_index` produces `docs/README.md`. On unfixed code the script does not exist (import fails) → FAILS.
  - Run the suite on UNFIXED code
  - **EXPECTED OUTCOME**: All five exploratory cases FAIL (this is correct — it proves the defects exist)
  - Document the observed counterexamples (e.g., `route("sz_json_analyzer.py") == "scripts"` instead of `"src/mapping"`; `route("playpalace_mapper.md") == "docs"`; entity spec → `"docs"`; hook prompt still contains `scripts/{filename}`; no `docs/README.md` generator)
  - Mark this task complete when the tests are written, run, and the failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write preservation property tests (BEFORE implementing any fix)
  - **Property 2: Preservation** - Non-Buggy Writes Are Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED code, then encode it
  - **GOAL**: Capture the behaviors that MUST remain byte-for-byte unchanged so the fix cannot regress them
  - Add/confirm these property-based tests in `senzing-bootcamp/tests/test_organize_mapping_files.py`:
    - **Observe & preserve `.jsonl -> data` (3.5)**: for any `st_basename()`, `route(f"{base}.jsonl")` → `"data"` (unchanged from today).
    - **Observe & preserve `.json -> config` (3.5)**: for any `st_basename()`, `route(f"{base}.json")` → `"config"`; confirm `identifier_crosswalk.json` → `"config"` is a permitted, unchanged destination (3.3).
    - **Conflict-skip preserved (3.6)**: a same-named NON-canonical file already at the destination is `skipped` (not overwritten), exactly as today.
    - **Idempotence preserved (3.5, 3.6)**: running the organizer twice produces zero moves on the second run.
    - **Correct placement untouched (3.6)**: files already under `docs/mapping/`, `docs/reference/`, `docs/progress/`, `docs/feedback/` are never moved or modified.
    - **Dry-run preserved**: dry-run plans moves without touching the filesystem (unchanged).
    - **Hook non-placement checks intact (3.4)**: parse `write-policy-gate.kiro.hook` and assert the Check 1 (Senzing SQL blocking), Check 2 (single-question `.question_pending`), and Check 3 (feedback append-only `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`) prompt sections are present verbatim; assert the root whitelist entries are unchanged.
    - **Hook transform/load/query branches preserved (3.1)**: assert the Check 4 `.py` routing still sends transform/load/query code to `src/transform/`, `src/load/`, `src/query/`.
    - **Root whitelist preserved (3.2)**: assert `.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json` remain permitted at the project root.
  - Run these tests on UNFIXED code
  - **EXPECTED OUTCOME**: All preservation tests PASS (this confirms the baseline behavior to preserve)
  - Mark this task complete when the tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for inconsistent file placement across the generated project's structure

  - [x] 3.1 Rework the organizer routing into an ordered, filename-aware `route()` function (Change 1)
    - In `senzing-bootcamp/scripts/organize_mapping_files.py`, replace the flat extension-only `ROUTING_RULES` dict with an ordered, first-match-wins rule list of `(matcher, target_subdir)` pairs using `match_name`, `match_suffix`, and `match_ext` helpers
    - Expose a pure `route(filename: str) -> str | None` function evaluated first-match-wins; return `None` for unrouted files (warned, left in place — unchanged)
    - Order: `senzing_entity_specification.md` → `docs/reference`; `*_mapper.md` → `docs/mapping`; `.md` → `docs/mapping`; `.py` → `src/mapping`; `.jsonl` → `data`; `.json` → `config`
    - Confirm `plan_moves` resolves `project_root / target_subdir / name` and `execute_moves` calls `mkdir(parents=True, exist_ok=True)` so nested targets (e.g., `src/mapping`, `docs/reference`) work without further plumbing
    - Keep `.jsonl -> data` and `.json -> config` verbatim to preserve today's behavior
    - _Bug_Condition: isBugCondition(write) for clauses 1.1, 1.2, 1.3 — Python helper / mapper spec / entity spec / reference md outside conventional location_
    - _Expected_Behavior: route() returns exactly one conventional subdir per filename (Property 1, Property 3, Property 4)_
    - _Preservation: `.jsonl -> data`, `.json -> config` unchanged (Property 2, Property 7)_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Add the "deduplicate" MoveResult outcome for the entity spec (Change 2)
    - Add a `"deduplicate"` status to `MoveResult`
    - In `plan_moves`, when a source file's routed destination already exists AND the file is the known canonical-single artifact (`senzing_entity_specification.md` routing to `docs/reference/`), mark it `deduplicate` instead of `skipped`
    - In `execute_moves`, remove the misplaced source copy for `deduplicate` entries only after confirming the destination exists, leaving exactly one copy under `docs/reference/`
    - Keep the existing `skipped` (conflict, no overwrite) behavior for all other files unchanged
    - Report deduplicated files on stderr in `print_summary`
    - Scope the deletion narrowly to the single named canonical artifact so it cannot remove bootcamper data or correctly-placed files
    - _Bug_Condition: isBugCondition(write) for clause 1.3 — entity spec duplicated in docs/ root and docs/reference/_
    - _Expected_Behavior: exactly one copy at docs/reference/senzing_entity_specification.md; misplaced source removed (Property 5)_
    - _Preservation: non-canonical conflicts still `skipped`, not deleted (Property 7)_
    - _Requirements: 2.3_

  - [x] 3.3 Realign the hook Check 4 `.py` fallback to `src/scripts/` (Change 3)
    - In `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`, change the Check 4 `.py` final branch from `Otherwise (utility scripts, CLI tools) -> scripts/{filename}` to `-> src/scripts/{filename}`
    - Leave the transform/load/query branches unchanged (preserve 3.1)
    - Do NOT touch Check 1 (SQL), Check 2 (single-question), Check 3 (feedback append-only), or the root whitelist (preserve 3.2, 3.4)
    - Keep the hook JSON schema valid: `name`, `version`, `when`, `then` present; `when.type` is `preToolUse` with `toolTypes: ["write"]`; the only edit is prompt text inside `then.prompt`
    - _Bug_Condition: isBugCondition(write) for clause 1.4 — utility script routed to root scripts/ via src/-or-scripts/ ambiguity_
    - _Expected_Behavior: non-typed .py routes to a single deterministic src/scripts/ destination (Property 3)_
    - _Preservation: Checks 1-3, root whitelist, and transform/load/query branches unchanged (Property 2)_
    - _Requirements: 2.4_

  - [x] 3.4 Realign `project-structure.md` to a single `src/`-rooted convention (Change 4)
    - In `senzing-bootcamp/steering/project-structure.md`, remove the top-level `scripts/` entry from the directory tree; add `src/{...,scripts}` and the docs subdirectories used (`docs/{mapping,reference,progress,feedback}`)
    - Change the Root File Placement Enforcement list from "Source code (`.py`) -> ... or `scripts/`" to "... or `src/scripts/`"
    - Change "The `scripts/` directory is reserved for executable code only" to "The `src/scripts/` directory ..."
    - Update the Create-Structure snippets (Python `os.makedirs`, Linux/macOS `mkdir -p`, Windows PowerShell): replace standalone `scripts` with `src/scripts` and add `docs/mapping`, `docs/reference`, `docs/progress`
    - Add a one-line rule: all executable code lives under `src/` (no top-level `scripts/`)
    - Preserve `inclusion: auto` frontmatter, kebab-case filename, and the no-external-URL steering rule
    - _Bug_Condition: isBugCondition(write) for clause 1.4 — convention itself lists a root scripts/ split_
    - _Expected_Behavior: single src/-rooted code convention with docs subdirs (Requirement 2.4)_
    - _Preservation: data/config and root-whitelist guidance unchanged (Property 2)_
    - _Requirements: 2.4_

  - [x] 3.5 Realign `module-05-phase2-data-mapping.md` doc targets and add a docs-index step (Change 5)
    - In `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`, change all per-source mapper-spec targets from `docs/{source_name}_mapper.md` to `docs/mapping/{source_name}_mapper.md` (inline instruction, mandatory-gate text, and per-source completion checkpoint)
    - Change `docs/mapping_[name].md`, the quality HTML, and the transformation-lineage doc to the `docs/mapping/` subdirectory
    - Instruct that the entity specification reference is written only to `docs/reference/senzing_entity_specification.md` (single canonical copy), and any existing `docs/` root copy is removed (or left to the organizer's dedup pass)
    - Add a step after the organizer invocation: run the docs-index generator (`generate_docs_index.py`) to create/refresh `docs/README.md`, noting the index is regenerated whenever documents are added across modules
    - Preserve frontmatter, kebab-case filename, and no-external-URL rule
    - _Bug_Condition: isBugCondition(write) for clauses 1.2, 1.3, 1.5 — mapper/entity spec to docs/ root, no index step_
    - _Expected_Behavior: mapper specs -> docs/mapping/, entity spec -> docs/reference/ only, index regenerated (Requirements 2.2, 2.3, 2.5)_
    - _Preservation: already-correct docs left in place (Property 7)_
    - _Requirements: 2.2, 2.3, 2.5_

  - [x] 3.6 Create the new docs-index generator `scripts/generate_docs_index.py` (Change 6)
    - Add `senzing-bootcamp/scripts/generate_docs_index.py` following the established script pattern: `#!/usr/bin/env python3`, module docstring with usage, `from __future__ import annotations`, stdlib only, `@dataclass`, `argparse`, `main(argv=None)`, `if __name__ == "__main__"`, exit code 0/1
    - Walk the generated project's `docs/` tree (sorted traversal), collect every document excluding `docs/README.md` itself, derive a short description (first Markdown heading or first non-empty line, falling back to the filename), group entries by subdirectory, and write a deterministic `docs/README.md`
    - Add a `--check` mode (consistent with `measure_steering.py --check`) that reports drift without writing and exits non-zero when out of sync
    - Ensure deterministic output (sorted traversal, stable rendering) so it is property-testable
    - Type hints use `X | None` / `list[str]`; line length <= 100; Google-style docstrings
    - _Bug_Condition: isBugCondition(write) for clause 1.5 — docs/ has documents but no docs/README.md_
    - _Expected_Behavior: docs/README.md exists and lists every document with a description (Property 6)_
    - _Preservation: generator only writes docs/README.md; existing docs untouched (Property 7)_
    - _Requirements: 2.5_

  - [x] 3.7 Add fix-checking and new property tests for the organizer and index generator
    - In `senzing-bootcamp/tests/test_organize_mapping_files.py`, add/extend property tests:
      - **Routing determinism (Property 3)**: for any generated filename, `route` returns exactly one target or `None`, and calling twice is stable
      - **Mapper/entity routing (Property 4)**: for any basename, `{base}_mapper.md -> docs/mapping` and `senzing_entity_specification.md -> docs/reference`
      - **Conventional placement (Property 1)**: recognized files land under their conventional subdir after `execute_moves` and never at the project root or `docs/` root
      - **Dedup (Property 5)**: with a pre-existing `docs/reference/` entity spec and a misplaced root copy, exactly one copy exists under `docs/reference/` after the run, and stderr reports the dedup
      - **Unit `route()` table**: helpers, mapper specs, entity spec, reference `.md`, `.jsonl`, `.json`, and an unrouted `.txt` (-> `None`)
      - **Hook schema validity**: `name`/`version`/`when`/`then` present, `when.type == preToolUse`, `toolTypes == ["write"]`
    - Create `senzing-bootcamp/tests/test_generate_docs_index.py` with the `sys.path` shim and class-based organization:
      - **Index completeness/currency (Property 6)**: for any generated set of `docs/` documents, `docs/README.md` lists every document; adding/removing documents and regenerating keeps the index in sync
      - **Unit cases**: empty tree, single doc, nested subdirs, `--check` drift detection
      - **CLI defaults/errors**: mirror existing `TestCLIArgumentDefaults`
    - Use `@settings(max_examples=20)`, `st_`-prefixed strategies
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.8 Verify bug condition exploration tests now pass
    - **Property 1: Expected Behavior** - Conventional Placement Of Routed And Generated Files
    - **IMPORTANT**: Re-run the SAME exploratory tests from task 1 — do NOT write new tests
    - The tests from task 1 encode the expected behavior; when they pass, the fix is confirmed
    - Run the five exploratory cases from task 1 against the FIXED code
    - **EXPECTED OUTCOME**: All five tests PASS (confirms each defect 1.1-1.5 is resolved)
    - _Requirements: Expected Behavior Properties 2.1, 2.2, 2.3, 2.4, 2.5 (Property 1)_

  - [x] 3.9 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy Writes Are Unchanged
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 — do NOT write new tests
    - Run the preservation property tests from task 2 against the FIXED code
    - **EXPECTED OUTCOME**: All preservation tests PASS (confirms no regressions to 3.1-3.6)
    - Confirm `.jsonl`/`.json` routing, conflict-skip, idempotence, dry-run, already-correct placement, hook Checks 1-3, transform/load/query branches, and the root whitelist are all unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Integration tests and checkpoint — ensure all tests pass
  - Add an integration test: a mixed source directory (helper `.py`, `*_mapper.md`, entity spec, `profile_report.md`, `.jsonl`, `.json`) organizes into `src/mapping/`, `docs/mapping/`, `docs/reference/`, `data/`, `config/` in one run, then the index generator produces a complete `docs/README.md`
  - Re-run the sweep to confirm idempotence and a stable index (no spurious moves or diffs)
  - CI alignment: confirm `validate_power.py`, `validate_commonmark.py`, and the full pytest suite pass with the updated steering and new script
  - Confirm the hook JSON remains schema-valid and the `write-policy-gate` security checks are unweakened
  - Ensure all tests pass; ask the user if questions arise
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1"],
      "description": "Bug condition exploration tests — must FAIL on unfixed code"
    },
    {
      "wave": 2,
      "tasks": ["2"],
      "description": "Preservation property tests — must PASS on unfixed code"
    },
    {
      "wave": 3,
      "tasks": ["3.1", "3.3", "3.4", "3.6"],
      "description": "Independent fixes: organizer route() rework, hook Check 4 fallback, project-structure realignment, new docs-index generator"
    },
    {
      "wave": 4,
      "tasks": ["3.2", "3.5"],
      "description": "Dependent fixes: entity-spec dedup (needs 3.1 route), module-05 realignment + index step (needs 3.6 generator)"
    },
    {
      "wave": 5,
      "tasks": ["3.7"],
      "description": "Fix-checking and new property tests (needs 3.1, 3.2, 3.6)"
    },
    {
      "wave": 6,
      "tasks": ["3.8", "3.9"],
      "description": "Re-run exploration tests (now PASS) and preservation tests (still PASS)"
    },
    {
      "wave": 7,
      "tasks": ["4"],
      "description": "Integration tests + checkpoint — full suite and CI checks pass"
    }
  ]
}
```

```text
1. Bug condition exploration tests (FAIL on unfixed code)
        |
        v
2. Preservation property tests (PASS on unfixed code)
        |
        v
3. Fix implementation
   |- 3.1 Organizer route() rework ............ (foundation)
   |- 3.2 Entity-spec deduplicate outcome ..... (depends on 3.1)
   |- 3.3 Hook Check 4 fallback -> src/scripts/  (independent)
   |- 3.4 project-structure.md realignment .... (independent)
   |- 3.6 generate_docs_index.py (new) ........ (independent)
   |- 3.5 module-05 doc targets + index step .. (depends on 3.6)
   |- 3.7 Fix-checking + new property tests ... (depends on 3.1, 3.2, 3.6)
   |- 3.8 Verify exploration tests PASS ....... (depends on 3.1-3.6)
   \- 3.9 Verify preservation tests PASS ...... (depends on 3.1-3.6)
        |
        v
4. Integration tests + checkpoint (depends on all of 3)
```

## Notes

- Tasks 1 and 2 MUST come before any fix (exploratory tests fail; preservation tests pass on unfixed code).
- 3.1 (route rework) is the foundation; 3.2 (dedup) builds on the new routing.
- 3.3 (hook), 3.4 (project-structure), 3.6 (new generator) are independent and can proceed in parallel.
- 3.5 (module-05 steering) references the generator added in 3.6.
- 3.8/3.9 re-run the unchanged tests from tasks 1/2 to confirm the fix and guard against regressions.
- Task 4 is the final gate ensuring the whole suite and CI checks pass.
- Property 1 (Bug Condition) and Property 2 (Preservation) drive the PBT hover status; Properties 3-7 from the design are validated within tasks 3.7 and 4.
- Hook edits are confined to `then.prompt` text; the JSON schema (`name`, `version`, `when`, `then`) and `when.type: preToolUse` with `toolTypes: ["write"]` are preserved.
