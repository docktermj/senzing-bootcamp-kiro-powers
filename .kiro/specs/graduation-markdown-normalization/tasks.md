# Implementation Plan: Graduation Markdown Normalization

## Overview

This plan implements a single graduation-time Markdown normalization pass. It builds the new
`normalize_markdown.py` stdlib script (schema normalization for the recap + deterministic CommonMark
style fixes with atomic writes), re-scopes the `commonmark-validation` hook from `fileEdited` to
`userTriggered` with the full registry/steering cascade, wires the normalization step into the
graduation flow before recap-PDF generation, and adds pytest + Hypothesis coverage. Each task builds
on the previous one and ends with everything wired into the graduation flow. Implementation language
is Python 3.11+, stdlib-only, following the project script pattern.

## Tasks

- [x] 1. Scaffold `normalize_markdown.py` foundation
  - [x] 1.1 Create the script skeleton and data model
    - Create `senzing-bootcamp/scripts/normalize_markdown.py` with `#!/usr/bin/env python3`,
      `from __future__ import annotations`, stdlib-only imports
    - Define the `NormalizationResult` dataclass (`path`, `changed`, `schema_applied`, `warnings`, `error`)
    - Add a `main(argv=None)` skeleton returning exit code 0 on success and 1 on usage/argument errors,
      following the project script pattern
    - _Requirements: 6.1_

  - [x] 1.2 Implement CLI argument parsing and default target discovery
    - Implement `parse_args(argv)` with `--paths`/positional files, `--dir`, and `--check` flags
    - Implement default target discovery (only known artifacts that exist: `docs/bootcamp_recap.md`,
      `docs/bootcamp_journal.md`, mapper docs and other `docs/*.md`)
    - _Requirements: 6.1, 6.2_

- [x] 2. Implement deterministic CommonMark style fixes
  - [x] 2.1 Implement `apply_commonmark_fixes(content)`
    - Implement stdlib text transforms for MD022 (blank lines around headings), MD031 (blank lines
      around fenced code), MD032 (blank lines around lists), MD040 (default `text` language on fenced
      code), and bold-label colon spacing (`**Label:**`)
    - Preserve the CHANGELOG.md MD024 exception (allow duplicate headings) where applicable
    - Reuse the rule set defined by `validate_commonmark.py` rather than inventing new rules
    - _Requirements: 4.3, 6.3_

  - [x] 2.2 Write property test for CommonMark fix idempotence
    - **Property 2: Idempotence / stability**
    - Assert `apply_commonmark_fixes(apply_commonmark_fixes(x)) == apply_commonmark_fixes(x)` for any
      generated Markdown input
    - **Validates: Requirements 2.3, 2.4**

- [x] 3. Implement recap schema normalization
  - [x] 3.1 Implement `normalize_recap(content)` and the `SCHEMA_NORMALIZERS` registry
    - Define `SCHEMA_NORMALIZERS` mapping `docs/bootcamp_recap.md` → `normalize_recap`
    - Reuse `generate_recap_pdf.parse_recap_markdown` + `format_recap_document` for the recap
      schema round-trip
    - Retain content the parser cannot place (prose/extra headings) verbatim and collect it as a warning
      rather than dropping it
    - _Requirements: 2.3, 3.2, 3.4, 6.3, 6.4_

  - [x] 3.2 Write unit test for free-form recap conformance
    - Assert a free-form recap (e.g. `## Module 1: Business Problem`, prose, no timestamp) normalizes to
      schema-conforming Markdown that `parse_recap_markdown` parses into the expected sections
    - Assert unmappable content produces a warning and is retained in the output
    - _Requirements: 8.1, 3.2, 3.4_

  - [x] 3.3 Write property test for recap round-trip conformance
    - **Property 3: Recap round-trip conformance**
    - For any valid `RecapDocument`, format → perturb headings to free-form → `normalize_recap` yields
      Markdown that `parse_recap_markdown` parses back to an equivalent `RecapDocument` (section identity,
      list contents, Q&A pairing, durations preserved)
    - **Validates: Requirements 2.3, 5.2**

- [x] 4. Implement per-file normalization with atomic write
  - [x] 4.1 Implement `normalize_file(path)` and `normalize_paths(paths)`
    - Read → schema-normalize if registered → `apply_commonmark_fixes` → atomic write
    - Atomic write: write to a sibling temp file in the same directory, then `os.replace()` over the
      original so a mid-write failure cannot corrupt or truncate the original
    - Catch all per-file exceptions: return a `NormalizationResult` with `error` set; never raise to the
      caller (keep the pass non-blocking)
    - Skip non-existent targeted files silently (not an error)
    - _Requirements: 3.1, 3.5, 2.4, 2.5_

  - [x] 4.2 Write unit test for content preservation and atomic write
    - Assert a file with no registered Consumer_Schema is style-normalized only and keeps all content
    - Assert a simulated failure during write leaves the original file byte-identical
    - _Requirements: 8.1, 3.1, 3.5_

  - [x] 4.3 Write property test for content preservation
    - **Property 1: Content preservation (no silent loss)**
    - For any generated free-form Markdown (headings, prose, bullet lists, fenced code blocks in any
      order), the set of substantive content tokens in `normalize_file` output is a superset of the input's
    - **Validates: Requirements 3.1, 3.2**

- [x] 5. Wire reporting and non-blocking behavior into `main`
  - [x] 5.1 Complete `main(argv)` orchestration and warning output
    - Call `normalize_paths` over resolved targets, print a one-line summary of files normalized
    - Print per-file warnings and errors to stderr without aborting the run
    - Return 0 even when individual files warn or error; return 1 only for argument/usage errors
    - Honor `--check` (report-only; exit 1 if any file would change — for CI use)
    - _Requirements: 2.5, 3.4, 6.1_

  - [x] 5.2 Write property test for non-blocking pass
    - **Property 4: Non-blocking pass**
    - For any target file set (including files that raise during normalization), `main` returns 0 and
      every original file is either fully replaced with normalized output or left byte-identical
    - **Validates: Requirements 2.5, 3.5**

- [x] 6. Checkpoint - Ensure all normalizer tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Re-scope the CommonMark validation hook
  - [x] 7.1 Update `commonmark-validation.kiro.hook` trigger and version
    - Change `when.type` from `fileEdited` (patterns `**/*.md`) to `userTriggered`
    - Preserve the `then.askAgent` prompt (MD022/MD031/MD032/MD040 + bold-label colon checks, CHANGELOG
      MD024 exception), re-framed to validate all Markdown in one pass
    - Keep `name` starting with `"to "` (governance regex `"name":\s*"to\s"`); bump `version` to `2.0.0`
    - Keep the file a valid Kiro hook (`name`, `version`, `when`, `then` present)
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6_

  - [x] 7.2 Regenerate the hook registry and lock file
    - Run `python scripts/sync_hook_registry.py --write` to regenerate `hooks/hooks.lock.yaml`
      (event_type/version)
    - Verify `hooks/hook-categories.yaml` keeps `commonmark-validation` in `critical`
    - _Requirements: 4.5_

  - [x] 7.3 Write test for the re-scoped hook
    - Assert `when.type == "userTriggered"`, NOT `fileEdited` on `**/*.md`, `name` matches `^to `,
      hook is valid (`name`/`version`/`when`/`then`), and present in `hooks.lock.yaml` with matching
      event_type
    - _Requirements: 8.3, 4.1, 4.5, 4.6_

- [x] 8. Update hook-cascade steering and docs
  - [x] 8.1 Update hook-registry and onboarding steering descriptors
    - Update `steering/hook-registry.md` and `steering/hook-registry-critical.md` descriptor from
      `fileEdited → askAgent` to `userTriggered → askAgent`
    - Update `steering/onboarding-flow.md` disabled-hook description wording
    - _Requirements: 4.5, 7.3_

  - [x] 8.2 Update remaining trigger-description references
    - Update `scripts/install_hooks.py` description string if it encodes the trigger
    - Regenerate the `POWER.md` generated hooks block via `python scripts/generate_power_docs.py` if it
      records the trigger
    - Update `docs/guides/ARCHITECTURE.md` and `hooks/README.md` trigger descriptions
    - _Requirements: 4.5, 7.3_

  - [x] 8.3 Verify governance and registry consistency
    - Run `python scripts/sync_hook_registry.py --verify` and `python scripts/validate_governance_rules.py`
      and resolve any failures
    - _Requirements: 4.5_

- [x] 9. Wire normalization into the graduation flow
  - [x] 9.1 Insert Step 0 Normalization Pass into `steering/graduation.md`
    - Add an explicit **Step 0: Markdown Normalization Pass** that runs
      `python scripts/normalize_markdown.py` over the known Markdown_Artifacts before the recap-PDF step
    - Renumber the existing recap-PDF step to Step 0b and state it consumes the normalized
      `docs/bootcamp_recap.md`
    - Describe the step as non-blocking (one-line summary, warn-and-continue), consistent with the
      existing recap-PDF / `GRADUATION_REPORT.md` spirit; note fallback to the original file via the
      tolerant parser when skipped/failed
    - _Requirements: 2.1, 2.2, 5.1, 5.2, 5.3, 5.4, 7.1, 7.4_

  - [x] 9.2 Update in-module authoring guidance and steering index
    - Update the in-module authoring guidance steering to state Markdown is free-form during the
      bootcamp and normalized at graduation, capturing content first
    - Note the relationship to `recap-pdf-content-loss-fix` (tolerant parser + fallback) as paired changes
    - Update steering token budgets in `steering/steering-index.yaml` for changed/added steering files
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.2, 7.3, 7.4_

- [x] 10. Integration: derived artifacts from normalized files
  - [x] 10.1 Write integration test for normalized recap → non-empty PDF body
    - Assert a normalized recap renders a non-empty recap PDF body (ties to
      `recap-pdf-content-loss-fix` expectations)
    - _Requirements: 8.4, 5.2, 5.3_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirement sub-clauses for traceability.
- Checkpoints (tasks 6 and 11) ensure incremental validation.
- Property tests validate the four universal correctness properties from the design; unit and
  integration tests validate specific examples and edge cases.
- This feature depends on `recap-pdf-content-loss-fix` for the tolerant recap parser and raw-Markdown
  fallback; tasks assume that fix is in place.
- All script paths are relative to `senzing-bootcamp/`; tests live in `senzing-bootcamp/tests/` except
  hook-file validation, which goes in repo-root `tests/`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "7.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1", "7.2", "8.1", "8.2"] },
    { "id": 2, "tasks": ["2.2", "3.2", "3.3", "4.1", "7.3", "8.3"] },
    { "id": 3, "tasks": ["4.2", "4.3", "5.1", "9.1", "9.2"] },
    { "id": 4, "tasks": ["5.2", "10.1"] }
  ]
}
```
