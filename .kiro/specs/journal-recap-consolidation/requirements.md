# Requirements Document

## Introduction

The Senzing Bootcamp currently writes **two** near-duplicate per-module logs at every module
completion:

- `docs/bootcamp_recap.md` — a structured recap section (`## Module N: [Name] — [timestamp]` with
  `### Information Shared`, `### Questions & Responses`, `### Actions Taken`, `### Duration`
  subsections). This file is the enforced, machine-parseable source of truth: it is written by the
  `module-recap-append` `Stop` hook, verified and backfilled synchronously at module completion,
  reconciled again at track completion, and rendered into the recap PDF and (indirectly) the Q&A
  transcript.
- `docs/bootcamp_journal.md` — a lighter narrative entry (`## Module N: [Name] — Completed
  [timestamp]` with `**What we did:**`, `**What was produced:**`, `**Why it matters:**`,
  `**Bootcamper's takeaway:**` fields). This file is parsed by `record_export.py` to extract the
  Module 1 business problem and Module 8 performance evidence.

The two files restate largely the same per-module activity. This feature **consolidates them into a
single per-module log** and updates every dependent process so nothing breaks. This is a
cross-cutting contract change: the single-source-of-truth file contract must be made explicit, and
every dependent (steering slices, the recap-append hook, `completion_artifacts.py`,
`ensure_graduation_artifacts.py`, `record_export.py`, the recap PDF and transcript renderers, the
steering token budgets, and the CI gates) must be updated in lockstep.

**Chosen consolidation contract (decided in these requirements):** keep the single file at
`docs/bootcamp_recap.md` (the enforced, structured, tooling-anchored file that most dependents
already default to) as the **Consolidated_Log**, and fold the journal's narrative fields into each
per-module recap section as a new `### Journal` subsection. `docs/bootcamp_journal.md` is retired;
its content is migrated into the Consolidated_Log without loss. This choice minimizes downstream
churn (the recap PDF, transcript, `ensure_graduation_artifacts.py`, and `completion_artifacts.py`
already default to `docs/bootcamp_recap.md`), keeps the filename discoverable, and stays consistent
with the `docs/` file-placement conventions.

An alternative — introducing a brand-new neutral filename such as `docs/bootcamp_log.md` — was
considered and rejected because it would force a rename across every dependent default path and
every user-facing reference for no functional gain.

## Glossary

- **Consolidated_Log**: The single per-module log file at `docs/bootcamp_recap.md` that, after this
  feature, carries both the structured recap content and the narrative journal content for every
  completed module. It is the single source of truth for per-module completion history.
- **Recap_Section**: One `## Module N: [Name] — [timestamp]` block within the Consolidated_Log,
  containing the `### Information Shared`, `### Questions & Responses`, `### Actions Taken`,
  `### Duration`, and (new) `### Journal` subsections.
- **Journal_Subsection**: The new `### Journal` subsection within a Recap_Section, carrying the four
  narrative fields formerly written to `docs/bootcamp_journal.md`: `**What we did:**`,
  `**What was produced:**`, `**Why it matters:**`, and `**Bootcamper's takeaway:**`.
- **Legacy_Journal_File**: The retired `docs/bootcamp_journal.md` file that this feature consolidates
  into the Consolidated_Log.
- **Module_Completion_Workflow**: The fixed-order completion process defined in
  `steering/module-completion.md` and its slices (`module-completion-artifacts.md`,
  `module-completion-error-handling.md`, `module-completion-next-steps.md`,
  `module-completion-track.md`).
- **Boundary_Detection_Trigger**: The shared trigger that compares the current `modules_completed`
  array in `config/bootcamp_progress.json` against the prior state to detect a newly completed
  module.
- **Recap_Append_Hook**: The `Stop` hook defined in `hooks/module-recap-append.json` that appends a
  Recap_Section on boundary detection.
- **Completion_Planner**: The `scripts/completion_artifacts.py` CLI that plans, checks, and backfills
  per-module artifacts (`--plan`, `--check`, `--backfill`) and computes per-module and total
  Duration.
- **Graduation_Orchestrator**: The `scripts/ensure_graduation_artifacts.py` orchestrator that
  guarantees the transcript, recap Markdown, and rendered recap exist and are non-empty at every
  stopping point.
- **Record_Exporter**: The `scripts/record_export.py` CLI that reads per-module narrative content to
  extract the Module 1 business problem and Module 8 performance evidence into
  `docs/bootcamp_record.yaml`.
- **Recap_PDF_Generator**: The `scripts/generate_recap_pdf.py` CLI that renders the Consolidated_Log
  into `docs/bootcamp_recap.pdf`, degrading to Markdown/HTML when `fpdf2` is absent.
- **Transcript_Renderer**: The transcript generation and reconciliation chain
  (`scripts/generate_transcript.py`, `scripts/reconcile_transcript.py`) that produces
  `docs/bootcamp_transcript.md` from the session log reconciled against the Consolidated_Log's
  `### Questions & Responses` pairs.
- **Steering_Index**: The `steering/steering-index.yaml` file that records per-file token counts and
  budget thresholds.
- **CI_Gate**: The GitHub Actions pipeline (`validate_power.py`, `measure_steering.py --check`,
  `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest) that must remain green.
- **Dependent_Spec**: An existing spec whose behavior touches the recap or journal files —
  specifically `guaranteed-graduation-artifacts`, `export-results`, `bootcamp-record-export`,
  `bootcamp-qa-transcript`, `transcript-reconciliation`, and `recap-pdf-content-loss-fix`.

## Requirements

### Requirement 1: Single consolidated per-module log contract

**User Story:** As a bootcamper, I want a single per-module log instead of two overlapping files, so
that my completion history is captured in one discoverable place without redundancy.

#### Acceptance Criteria

1. THE Consolidated_Log SHALL be the single file at `docs/bootcamp_recap.md`.
2. THE Consolidated_Log SHALL contain exactly one Recap_Section per completed module.
3. THE Consolidated_Log SHALL preserve the existing Recap_Section heading form
   `## Module N: [Name] — [timestamp]` and the existing `### Information Shared`,
   `### Questions & Responses`, `### Actions Taken`, and `### Duration` subsections.
4. THE Consolidated_Log SHALL include a `### Journal` subsection within each Recap_Section carrying
   the four narrative fields `**What we did:**`, `**What was produced:**`, `**Why it matters:**`, and
   `**Bootcamper's takeaway:**`.
5. WHEN a module produces no value for the `**Bootcamper's takeaway:**` field, THE Recap_Section
   SHALL record `N/A` for that field.
6. THE Consolidated_Log SHALL retain its existing header block (`# Senzing Bootcamp Recap`,
   `**Bootcamper:**`, `**Started:**`, and the optional `**Total Duration:**` line).
7. THE feature SHALL retire the Legacy_Journal_File so that no new `docs/bootcamp_journal.md` is
   created after consolidation.
8. THE Consolidated_Log SHALL remain valid CommonMark so that `validate_commonmark.py` passes.

### Requirement 2: Migration and backward compatibility for in-progress projects

**User Story:** As a bootcamper who is partway through the bootcamp, I want my existing recap and
journal content merged into the single log without losing anything, so that consolidation does not
discard my history.

#### Acceptance Criteria

1. WHEN consolidation runs in a project that already has both `docs/bootcamp_recap.md` and
   `docs/bootcamp_journal.md`, THE system SHALL merge each Legacy_Journal_File narrative entry into
   the matching module's Recap_Section as its Journal_Subsection.
2. WHEN a Legacy_Journal_File entry exists for a module that has no Recap_Section, THE system SHALL
   create a Recap_Section for that module so the narrative content is preserved.
3. THE migration SHALL preserve all existing Consolidated_Log bytes for content that is already
   present, appending or filling only the missing Journal_Subsection content.
4. THE migration SHALL be idempotent so that running consolidation on an already-consolidated project
   makes no further changes.
5. IF only `docs/bootcamp_recap.md` exists and no Legacy_Journal_File is present, THEN the system
   SHALL treat the recap as already consolidated and add empty-but-valid Journal_Subsection scaffolding
   only when a module's narrative content is available.
6. WHEN migration completes for a module, THE Consolidated_Log SHALL contain every field that existed
   in that module's Legacy_Journal_File entry.
7. FOR ALL Consolidated_Log content, parsing the file then re-rendering it then parsing it again SHALL
   produce equivalent structured content (round-trip property) so that migration and downstream
   reformatting never silently drop a Recap_Section or Journal_Subsection.

### Requirement 3: Single consolidated completion step in the module-completion workflow

**User Story:** As a bootcamper, I want one completion step to produce the consolidated per-module
content, so that the workflow no longer runs two near-duplicate write steps.

#### Acceptance Criteria

1. THE Module_Completion_Workflow SHALL produce the consolidated per-module content (structured recap
   plus Journal_Subsection) in a single step that replaces the former separate `recap_append` and
   `journal_entry` steps.
2. THE Module_Completion_Workflow SHALL preserve the fixed step ordering for the remaining steps
   (progress update, consolidated log append, completion certificate, capture-hook safeguard,
   next-step options).
3. WHEN the Boundary_Detection_Trigger observes a newly completed module, THE Module_Completion_Workflow
   SHALL produce that module's consolidated content.
4. WHEN the newly completed module is the final module of the bootcamper's track, THE
   Module_Completion_Workflow SHALL still produce that module's consolidated content in addition to the
   track-completion celebration.
5. IF `config/.question_pending` exists at completion-check time, THEN the Module_Completion_Workflow
   SHALL produce no consolidated-log output and defer to `ask-bootcamper`.
6. IF the `modules_completed` array has gained no new entry since the previous state, THEN the
   Module_Completion_Workflow SHALL produce no consolidated-log output.
7. IF appending the consolidated content fails due to a file-system error or a timeout exceeding 30
   seconds, THEN the Module_Completion_Workflow SHALL log a warning and continue to the next step
   without halting.
8. WHEN the consolidated append genuinely fails or is intentionally skipped, THE
   Module_Completion_Workflow SHALL still execute the completion certificate and next-step options
   steps.
9. WHEN the consolidated append succeeds, THE Module_Completion_Workflow SHALL treat the append as
   complete and SHALL NOT mark it skipped.

### Requirement 4: Consolidated recap-append hook

**User Story:** As a maintainer, I want the recap-append hook to write the consolidated per-module
content, so that the single Stop-hook write covers both the structured recap and the narrative journal
fields.

#### Acceptance Criteria

1. THE Recap_Append_Hook SHALL append the consolidated Recap_Section, including the Journal_Subsection,
   to `docs/bootcamp_recap.md` on boundary detection.
2. IF `config/.question_pending` exists when the Recap_Append_Hook fires, THEN the Recap_Append_Hook
   SHALL produce no output and defer to `ask-bootcamper`.
3. WHEN the `modules_completed` array has not changed since the previous state, THE Recap_Append_Hook
   SHALL produce no output.
4. WHEN a Recap_Section for the completed module already exists in `docs/bootcamp_recap.md`, THE
   Recap_Append_Hook SHALL preserve the existing content without overwriting it.
5. IF `docs/bootcamp_recap.md` cannot be written due to a file-system error, THEN the Recap_Append_Hook
   SHALL log a warning and continue without halting the completion flow.
6. THE Recap_Append_Hook JSON SHALL remain schema-valid with the required `version` and `hooks` fields.
7. IF valid Recap_Append_Hook JSON cannot be produced, THEN the hook definition SHALL fail rather than
   ship partial or invalid JSON.
8. THE Recap_Append_Hook SHALL continue to source per-module Duration and cumulative Total Duration
   only from the Completion_Planner and SHALL omit a Duration field rather than writing a placeholder
   when the planner returns no value.
9. THE Recap_Append_Hook SHALL exclude secrets, credentials, environment variable values, and
   connection strings from the consolidated content.

### Requirement 5: Completion planner CLI operates on the consolidated file

**User Story:** As a maintainer, I want `completion_artifacts.py` to plan, check, and backfill against
the single consolidated file, so that the tooling no longer treats recap and journal as two separate
paths.

#### Acceptance Criteria

1. THE Completion_Planner SHALL operate on the Consolidated_Log as the single per-module content source
   rather than on separate `--recap` and `--journal` paths.
2. THE Completion_Planner SHALL define its updated CLI contract explicitly, including how the former
   `--journal` argument is handled (removed or repointed to the Consolidated_Log).
3. THE Completion_Planner SHALL retain the `--plan`, `--check`, and `--backfill` modes.
4. WHEN the Completion_Planner runs `--backfill` on a module missing a Recap_Section, THE
   Completion_Planner SHALL append a consolidated Recap_Section (including a Journal_Subsection
   scaffold) while preserving existing file bytes.
5. WHEN the Completion_Planner runs `--backfill` or `--plan` on an already-consistent Consolidated_Log,
   THE Completion_Planner SHALL make no changes (idempotent no-op).
6. THE Completion_Planner SHALL continue to compute per-module Duration and cumulative Total Duration
   from the ISO 8601 timestamps in `step_history` and the top-level `started_at`.
7. IF the Completion_Planner cannot read its input files, THEN the Completion_Planner SHALL exit with a
   non-zero code and a descriptive error message on standard error.
8. THE Completion_Planner SHALL remain Python 3.11+ standard-library only.

### Requirement 6: Graduation artifacts orchestrator operates on the consolidated file

**User Story:** As a maintainer, I want `ensure_graduation_artifacts.py` to guarantee artifacts from
the single consolidated file, so that the crown-jewel deliverables no longer reference a separate
journal path.

#### Acceptance Criteria

1. THE Graduation_Orchestrator SHALL reconstruct and verify the Consolidated_Log as the single recap
   source.
2. THE Graduation_Orchestrator SHALL define how its former separate `--journal` argument is handled
   (removed or repointed to the Consolidated_Log).
3. WHEN the Consolidated_Log is present, non-empty, and not stale, THE Graduation_Orchestrator SHALL
   leave it unchanged (idempotent no-op).
4. WHEN the Consolidated_Log is absent, empty, or stale, THE Graduation_Orchestrator SHALL reconstruct
   it from the available sources (`config/bootcamp_progress.json` and per-module artifacts under
   `docs/progress`) without depending on the Legacy_Journal_File.
5. WHEN the Consolidated_Log is absent, THE Graduation_Orchestrator SHALL treat it as requiring
   reconstruction regardless of any staleness check.
6. THE Graduation_Orchestrator SHALL continue to guarantee the Q&A transcript and a rendered recap
   (PDF, or HTML fallback when `fpdf2` is absent) exist and are non-empty.
7. THE Graduation_Orchestrator SHALL import `fpdf` lazily and never at module top level.
8. THE Graduation_Orchestrator SHALL remain Python 3.11+ standard-library only.

### Requirement 7: Record exporter reads Module 1 and Module 8 content from the consolidated file

**User Story:** As a bootcamper exporting my journey, I want the Module 1 business problem and Module 8
performance evidence extracted from the single consolidated file, so that the export still works after
the journal is retired.

#### Acceptance Criteria

1. THE Record_Exporter SHALL extract the Module 1 business problem (problem statement, identified data
   sources, and success criteria) from the Consolidated_Log.
2. THE Record_Exporter SHALL extract the Module 8 performance evidence from the Consolidated_Log.
3. WHEN Module 1 content is completely absent from the Consolidated_Log, THE Record_Exporter SHALL
   record a warning and continue without raising an error.
4. WHEN the Consolidated_Log has no Module 8 content, THE Record_Exporter SHALL omit the performance
   tuning section without raising an error.
5. THE Record_Exporter SHALL continue to redact secrets, credentials, connection strings, and detected
   PII from the exported manifest.
6. THE Record_Exporter SHALL remain Python 3.11+ standard-library only.

### Requirement 8: Downstream shareable deliverables sourced from the consolidated file

**User Story:** As a bootcamper, I want the recap PDF and Q&A transcript to still be produced from the
single consolidated file, so that my shareable deliverables remain complete after consolidation.

#### Acceptance Criteria

1. THE Recap_PDF_Generator SHALL render `docs/bootcamp_recap.pdf` from the Consolidated_Log.
2. THE Recap_PDF_Generator SHALL render the Journal_Subsection content in the rendered recap rather
   than dropping it.
3. WHEN `fpdf2` is absent, THE Recap_PDF_Generator SHALL retain the Markdown output and print the
   `pip install fpdf2` install hint rather than failing.
4. THE Transcript_Renderer SHALL derive the Q&A transcript from the Consolidated_Log's
   `### Questions & Responses` pairs reconciled against `config/session_log.jsonl`.
5. THE Transcript_Renderer SHALL NOT add or modify any write-tool hook and SHALL NOT introduce a
   per-write process spawn.
6. WHEN the Consolidated_Log has no `### Questions & Responses` content, THE Transcript_Renderer SHALL
   preserve its existing behavior of writing no misleading transcript.

### Requirement 9: Steering slices updated in lockstep

**User Story:** As a maintainer, I want every steering slice that describes the recap or journal
updated together, so that the agent-facing guidance is internally consistent after consolidation.

#### Acceptance Criteria

1. THE `steering/module-completion.md` router SHALL describe the single consolidated completion step
   and its position in the fixed step ordering.
2. THE `steering/module-completion-artifacts.md` slice SHALL describe the consolidated Recap_Section
   contract, including the Journal_Subsection, and SHALL remove the separate Bootcamp Journal step that
   wrote `docs/bootcamp_journal.md`.
3. THE `steering/module-completion-error-handling.md` slice SHALL describe non-blocking error handling
   for the single consolidated step consistently with Requirement 3.
4. THE `steering/module-completion-next-steps.md` slice SHALL reference the Consolidated_Log rather than
   the Legacy_Journal_File where it points the bootcamper to their completion history.
5. THE `steering/module-completion-track.md` slice SHALL reference the Consolidated_Log for the recap
   reconciliation, shareable deliverables, and any user-facing pointer to completion history, replacing
   references to `docs/bootcamp_journal.md`.
6. THE steering slices SHALL be internally consistent so that no slice references the Legacy_Journal_File
   as a live, separately written artifact after consolidation.
7. WHERE a steering slice logically needs to reference per-module completion history, THE slice SHALL
   reference the Consolidated_Log rather than referencing neither file.

### Requirement 10: Steering token budgets and CI gates remain green

**User Story:** As a maintainer, I want the steering token budgets accurate and the CI pipeline green
after consolidation, so that the power stays shippable.

#### Acceptance Criteria

1. WHEN any steering slice changes size, THE Steering_Index SHALL be updated so that its recorded token
   counts match the changed files.
2. THE `measure_steering.py --check` gate SHALL pass against the updated Steering_Index.
3. THE `validate_power.py` gate SHALL pass after consolidation.
4. THE `sync_hook_registry.py --verify` gate SHALL pass so that the hook registry stays consistent with
   the updated `hooks/module-recap-append.json`.
5. THE `validate_commonmark.py` gate SHALL pass against the updated steering and documentation files.
6. THE pytest suite SHALL pass after consolidation.

### Requirement 11: Test coverage for the consolidation

**User Story:** As a maintainer, I want tests covering the consolidated contract and every updated
dependent, so that the consolidation does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering the consolidated `completion_artifacts.py` planner,
   including `--plan`, `--check`, and `--backfill` idempotency on the Consolidated_Log.
2. THE feature SHALL update the module-completion integration tests
   (`tests/test_module_completion_artifacts_integration.py`,
   `tests/test_module_completion_process_integration.py`) to assert the single consolidated step and
   the consolidated Recap_Section format.
3. THE feature SHALL update the `record_export.py` tests to assert Module 1 and Module 8 extraction from
   the Consolidated_Log.
4. THE feature SHALL include a Hypothesis property test asserting the round-trip property from
   Requirement 2.7 (parse then render then parse yields equivalent structured content).
5. THE feature SHALL include a migration test asserting that existing recap and journal content is
   merged into the Consolidated_Log without content loss and that re-running migration is idempotent.
6. THE tests SHALL follow the project pattern (pytest plus Hypothesis, class-based, `sys.path` import)
   in `senzing-bootcamp/tests/`.

### Requirement 12: Existing dependent specs are not silently invalidated

**User Story:** As a maintainer, I want the consolidation to remain compatible with the specs that
already depend on the recap and journal files, so that prior guarantees are not broken.

#### Acceptance Criteria

1. THE feature SHALL preserve the guarantees of the `guaranteed-graduation-artifacts` spec that the
   recap Markdown, transcript, and rendered recap exist and are non-empty at every stopping point.
2. THE feature SHALL preserve the `recap-pdf-content-loss-fix` guarantee that content is never silently
   dropped from the rendered recap, including the raw-Markdown fallback.
3. THE feature SHALL preserve the `bootcamp-qa-transcript` and `transcript-reconciliation` guarantee
   that transcript reconciliation adds no per-write hook and reconciles from the recap source.
4. THE feature SHALL preserve the `export-results` and `bootcamp-record-export` behavior that the record
   export captures the Module 1 business problem and Module 8 performance evidence.
5. WHERE an existing Dependent_Spec references `docs/bootcamp_journal.md`, THE feature SHALL update that
   reference or provide equivalent behavior sourced from the Consolidated_Log so the dependent behavior
   continues to hold.
6. IF a reference to `docs/bootcamp_journal.md` in a dependent cannot be updated to the Consolidated_Log,
   THEN the consolidation SHALL fail rather than leave a stale reference in place.

### Requirement 13: Workspace and distribution constraints

**User Story:** As a maintainer, I want the consolidation to respect the workspace rules, so that the
change is safe to ship to users.

#### Acceptance Criteria

1. THE modified scripts (`completion_artifacts.py`, `record_export.py`, `ensure_graduation_artifacts.py`)
   SHALL use only the Python 3.11+ standard library, except for the existing lazily-imported optional
   `fpdf2` dependency used by the PDF renderers.
2. THE modified `hooks/module-recap-append.json` SHALL remain valid hook JSON.
3. THE modified files under `senzing-bootcamp/` SHALL contain no PII, credentials, or internal-only
   URLs, since everything under `senzing-bootcamp/` ships to users.
4. THE feature SHALL NOT add any new external endpoint during consolidation, keeping the Senzing MCP
   server URL (`mcp.senzing.com`) as the only external endpoint referenced.
5. THE feature SHALL preserve the Recap_Append_Hook's silent and deferral behavior so that no additional
   Stop-hook visual noise is introduced.
