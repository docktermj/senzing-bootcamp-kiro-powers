# Implementation Plan: Session Handoff

## Overview

This plan implements the Session_Handoff capability as Kiro Power content. The single load-bearing
program artifact is the stdlib-only structural validator (`validate_handoff_summary.py`), which is the
testable surface for the five structural Correctness Properties. The primary deliverable is the
manual-inclusion steering file (`session-handoff.md`) that instructs the Agent how to synthesize a
fixed 8-section Handoff_Summary from the Current_Session and the bootcamp's persisted state files.

The build order is test-first where practical: build the validator, then its property + example tests,
then author the steering content, edit the coordination file, register the file in the steering index,
and finally run the existing CI pipeline (`measure_steering.py --check`, `validate_commonmark.py`,
`validate_power.py`, pytest) to confirm conformance. No `.kiro.hook` is added in v1 (per the design's
"Optional trigger hook — analysis").

The design document uses a specific programming language (Python 3.11+, stdlib-only) for the validator
and pytest + Hypothesis for tests, so no implementation-language question is required.

## Tasks

- [x] 1. Implement the structural validator `validate_handoff_summary.py`
  - [x] 1.1 Scaffold the validator module and data models
    - Create `senzing-bootcamp/scripts/validate_handoff_summary.py` with `#!/usr/bin/env python3`,
      `from __future__ import annotations`, and stdlib-only imports (no third-party deps)
    - Define `@dataclass HandoffFinding` with `code: str` and `detail: str` fields, where `code` is one
      of `MISSING_SECTION`, `SECTION_OUT_OF_ORDER`, `RELATIVE_PATH`, `FORBIDDEN_PHRASE`, `EMOJI`,
      `EMPTY_SECTION_NOT_NONE`, `UNQUOTED_CONTINUATION`
    - Define `@dataclass HandoffValidation` with `ok: bool` and `findings: list[HandoffFinding]`
    - Define the canonical section constants: the ordered 8 headings (Title, "Where it started",
      "Decisions locked + what shipped", "Key files for next session", "Running state",
      "Verification — how to confirm things still work", "Deferred + open questions", "Pick up here"),
      the 8 forbidden temporal phrases, and the `validate_handoff_summary(text: str) -> HandoffValidation`
      signature returning `ok=True` on empty findings
    - Guarantee never-raise posture: the function returns findings for malformed/arbitrary text rather
      than throwing
    - _Requirements: 11.5_

  - [x] 1.2 Implement section presence, order, and empty-section checks
    - Parse the summary into its Title line and `##` sections; emit `MISSING_SECTION` for any of the 8
      canonical headings absent, `SECTION_OUT_OF_ORDER` when headings appear out of canonical order, and
      require a single-line non-empty Title
    - Emit `EMPTY_SECTION_NOT_NONE` when a section has no content and does not read exactly "none"
    - _Requirements: 4.1, 4.2, 4.3, 9.4, 1.4_

  - [x] 1.3 Implement absolute-path, forbidden-phrase, emoji, and quoted-continuation checks
    - Emit `RELATIVE_PATH` for any path-like token in file/running-state sections (including the SQLite
      database entry and completion-artifact references) that does not start with `/`
    - Emit `FORBIDDEN_PHRASE` when the "Pick up here" section contains any of the eight forbidden temporal
      phrases; emit `EMOJI` when any emoji code point appears anywhere in the summary
    - Emit `UNQUOTED_CONTINUATION` when the resume phrase in "Pick up here" is not enclosed in quotation
      marks
    - _Requirements: 5.1, 5.4, 8.3, 7.4, 9.2, 7.2_

  - [x] 1.4 Implement the argparse CLI entry point
    - Add `main(argv=None)` with argparse accepting a single `<path-to-summary.md>` argument; read the
      file, run `validate_handoff_summary`, print findings, and exit 0 when `ok` else 1
    - Add the standard `if __name__ == "__main__": sys.exit(main())` guard
    - _Requirements: 11.5_

- [x] 2. Write property-based and example tests for the validator
  - [x] 2.1 Build Hypothesis strategies and test scaffolding
    - Create `senzing-bootcamp/tests/test_handoff_summary.py`, class-based
      (`class TestHandoffSummaryProperties:`), importing `validate_handoff_summary`,
      `HandoffFinding`, `HandoffValidation`
    - Add `st_`-prefixed strategies: `st_handoff_summary()` (conformant summary from random section
      contents), `st_relative_path()`, `st_forbidden_phrase()`, plus emoji and quoted/unquoted
      continuation strategies
    - Do not hand-set `@settings(max_examples=...)`; rely on the active Hypothesis profile baseline
    - _Requirements: 11.5_

  - [x] 2.2 Write property test for structure stability
    - `# Feature: session-handoff, Property 1: Structure stability`
    - Conformant summaries return `ok`; metamorphic mutations (drop a section, swap two sections, blank a
      section without "none") yield the matching finding (`MISSING_SECTION` / `SECTION_OUT_OF_ORDER` /
      `EMPTY_SECTION_NOT_NONE`)
    - **Validates: Requirements 1.4, 4.1, 4.2, 4.3, 9.4**

  - [x] 2.3 Write property test for the absolute-path invariant
    - `# Feature: session-handoff, Property 2: Absolute-path invariant`
    - Entries mixing absolute and random relative paths return `ok` iff all absolute; a relative entry
      (including the SQLite database path) yields `RELATIVE_PATH`
    - **Validates: Requirements 5.1, 5.4, 8.3**

  - [x] 2.4 Write property test for forbidden temporal-phrase exclusion
    - `# Feature: session-handoff, Property 3: Forbidden temporal-phrase exclusion`
    - From a conformant summary, injecting any one of the eight forbidden phrases yields
      `FORBIDDEN_PHRASE`; without injection there is no such finding
    - **Validates: Requirements 7.4**

  - [x] 2.5 Write property test for no-emoji discipline
    - `# Feature: session-handoff, Property 4: No-emoji discipline`
    - Injecting a random emoji code point yields `EMOJI`; an emoji-free summary produces no such finding
    - **Validates: Requirements 9.2**

  - [x] 2.6 Write property test for the quoted continuation phrase
    - `# Feature: session-handoff, Property 5: Quoted continuation phrase`
    - Quoted resume phrases return `ok` for this check; unquoted resume phrases yield
      `UNQUOTED_CONTINUATION`
    - **Validates: Requirements 7.2**

  - [x] 2.7 Write example/smoke tests for the fixed verification block and never-raise robustness
    - Assert the design's representative Handoff_Summary Verification section contains the
      `get_capabilities` re-establish line, the exact
      `python3 senzing-bootcamp/scripts/baseline_status.py` command, and the current-module
      artifact-existence check, each paired with an expected outcome
    - Assert `validate_handoff_summary` returns `ok=False` (never raises) on arbitrary/malformed input,
      and the CLI exits 0 when `ok` else 1
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 3. Checkpoint - Ensure validator and its tests pass
  - Run `python3 -m pytest senzing-bootcamp/tests/test_handoff_summary.py`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Author the primary steering file `session-handoff.md`
  - [x] 4.1 Create the steering file with frontmatter and invocation/synthesis sections
    - Create `senzing-bootcamp/steering/session-handoff.md` with YAML frontmatter `inclusion: manual`
      and a `description` key (kebab-case filename)
    - Write the **Invocation & Offers** section: enumerate Trigger_Phrases and near-equivalents; define
      the two offer paths (clear-context intent, Context_Reset_Message) as one-line offers that respect
      the single-question protocol; handle the empty-session case by still emitting all 8 sections with
      "none"
    - Write the **Session-Scoped Synthesis** section: derive content only from the Current_Session
      conversation and touched artifacts; prohibit git-history queries and repo-wide file searches; use
      the whole conversation, not just recent turns
    - Write the **State Gathering & Reconciliation** section: list every state item to collect and
      instruct reconciliation (read-only) against `config/bootcamp_progress.json`,
      `config/bootcamp_preferences.yaml`, `config/mapping_state_*.json`, `config/session_log.jsonl`,
      `config/.question_pending`, `docs/bootcamp_recap.md`
    - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 8.1_

  - [x] 4.2 Add the fixed output template, precision, verification, and continuation sections
    - Write the **Output Template**: the fixed, ordered 8-section skeleton with "none" for empty sections
      and a single next action in "Pick up here"; include the concrete bootcamp-flavored example from the
      design verbatim as the reference
    - Write the **Precision Rules** section: absolute paths everywhere; Driving_Artifact first in "Key
      files"; per-process port + stop command; database as absolute SQLite path or PostgreSQL connection
      description; MCP status in "Running state"
    - Write the **Verification Block** section with the three baked-in checks: re-establish MCP via
      `get_capabilities` (expect reachable server + capabilities list), run
      `python3 senzing-bootcamp/scripts/baseline_status.py` (expect data-source coverage report), and
      confirm Current_Module artifacts exist (expect all present)
    - Write the **Pick Up Here & Continuation** section: emit the quoted Continuation_Phrase naming the
      Current_Module read from `current_module`; reuse the `agent-context-management.md` convention;
      exclude the eight forbidden temporal phrases
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4_

  - [x] 4.3 Add coordination, tone/discipline, and output-destination sections
    - Write the **Coordination Boundaries** section: explicit "never rewrite" list (Progress_File,
      Preferences_File, Recap_File) and reference-completion-artifacts-by-absolute-path rule
    - Write the **Tone & Discipline** section: terse engineering tone; no emojis/celebration/retrospective;
      only the single "Pick up here" recommendation; "none" over inference
    - Write the **Output Destination** section: chat-only by default; write a file only on explicit user
      request to a user-specified absolute path, then report that path
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3_

  - [x] 4.4 Write packaging and security conformance tests for the steering file
    - Assert `session-handoff.md` exists with a kebab-case name and frontmatter `inclusion: manual` plus a
      `description`
    - Scan the file for PII/credentials/internal URLs and confirm no external endpoint other than the
      Senzing MCP host is referenced (the host string lives only in `mcp.json`; the steering file refers
      to it by name/tool, not URL)
    - _Requirements: 11.1, 11.3, 11.4_

- [x] 5. Wire the handoff offer into the context-reset flow
  - [x] 5.1 Edit `agent-context-management.md` to add the handoff-offer hook-in
    - In the "Context Reset Communication" section, after the four required Context_Reset_Message
      elements, add a directive that the Agent offer a Session_Handoff before the user opens the fresh
      chat, reusing the same Continuation_Phrase/module convention already defined there
    - Leave the four required elements and the forbidden-phrase list unchanged
    - _Requirements: 1.3, 7.3, 8.4_

  - [x] 5.2 Write coordination regression tests
    - Assert `agent-context-management.md` still contains its four required Context_Reset_Message elements
      and forbidden-phrase list after the edit
    - Assert the handoff path adds no writer of `config/bootcamp_progress.json`,
      `config/bootcamp_preferences.yaml`, or `docs/bootcamp_recap.md`
    - _Requirements: 8.2, 8.4, 10.2_

- [x] 6. Register the steering file in the steering index
  - [x] 6.1 Add `session-handoff.md` to `file_metadata` in `steering-index.yaml`
    - Add a `session-handoff.md` entry under `file_metadata` with a `token_count` and `size_category`
    - Confirm the file stays under the `split_threshold_tokens` budget (5000 tokens); if not, add a
      justified `split_allowlist` entry or trim the content to remain a single cohesive file
    - _Requirements: 11.2_

  - [x] 6.2 Write a registration test
    - Assert `session-handoff.md` is registered in `steering-index.yaml` `file_metadata` with a
      `token_count`
    - _Requirements: 11.2_

- [x] 7. Final checkpoint - Run the CI pipeline and confirm conformance
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` (token budget / split threshold)
  - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` (Markdown conformance of the new files)
  - Run `python3 senzing-bootcamp/scripts/validate_power.py` (power packaging conformance)
  - Run `python3 -m pytest senzing-bootcamp/tests/test_handoff_summary.py` and the coordination/registration tests
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific granular requirements (and Correctness Properties) for traceability.
- The validator (`validate_handoff_summary.py`) is the only property-testable surface; the rest of the
  feature is Agent behavior enforced by `session-handoff.md` instructions and verified by example/smoke
  tests.
- No `.kiro.hook` is created in v1 per the design's "Optional trigger hook — analysis"; therefore
  `sync_hook_registry.py --verify` is unaffected and no hook-registry task is included.
- Checkpoints (tasks 3 and 7) ensure incremental validation before and after the steering content lands.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["2.1", "4.1", "5.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "4.2", "5.2"] },
    { "id": 4, "tasks": ["4.3"] },
    { "id": 5, "tasks": ["4.4", "6.1"] },
    { "id": 6, "tasks": ["6.2"] }
  ]
}
```
