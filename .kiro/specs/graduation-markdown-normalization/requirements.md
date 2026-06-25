# Requirements Document

## Introduction

Throughout the Senzing Bootcamp the agent produces many Markdown artifacts (the recap, mapper docs,
progress notes, journals). Some downstream tools — notably `generate_recap_pdf.py` — require a strict,
specific schema (an exact heading format and a fixed set of `### ` subsections). When the in-flight
Markdown does not match that shape, content is silently dropped (the recap-PDF empty-output defect
tracked by the `recap-pdf-content-loss-fix` spec). Two friction points follow from this coupling:

1. Authoring to a rigid schema *during* the run is easy to get wrong mid-session and slows the
   learning flow. The formatting requirement really only matters for the final shareable artifacts.
2. The `commonmark-validation` hook is a `fileEdited` hook on `**/*.md` that validates and auto-fixes
   CommonMark *style* on every Markdown save via `askAgent`. That adds an agent round-trip on every
   `.md` write and enforces style mid-session — the exact friction the free-form-during-bootcamp idea
   aims to remove. (Note: `commonmark-validation` covers style only; it does not enforce the recap
   PDF's structural schema, so it would not have prevented the empty-PDF bug.)

This feature decouples in-flight Markdown authoring from downstream parser expectations. During the
modules, Markdown is written naturally (capture content first, structure second). At graduation, a
single normalization pass rewrites each created Markdown file into the schema its consumer expects,
and only then are derived artifacts (recap PDF, reports) generated from the normalized files. The
per-edit `commonmark-validation` hook is re-scoped from a per-save trigger to that single
graduation-time pass rather than being deleted. The normalization is paired with the tolerant
parser + fallback work in `recap-pdf-content-loss-fix` so that a schema or style mismatch never
silently drops content.

## Glossary

- **Markdown_Artifact**: Any `.md` document produced during the bootcamp (e.g. `docs/bootcamp_recap.md`,
  mapper docs, journal, progress notes).
- **Free_Form_Authoring**: Writing Markdown_Artifacts in whatever natural structure suits the moment
  during modules, without enforcing a downstream parser's schema at write time.
- **Normalization_Pass**: A single graduation-time step that rewrites each Markdown_Artifact into the
  schema its consumer expects, before derived artifacts are generated.
- **Markdown_Normalizer**: The stdlib-only Python script in `senzing-bootcamp/scripts/` that performs
  the Normalization_Pass.
- **Consumer_Schema**: The exact heading format and recognized subsection names a downstream tool
  requires (for example the recap PDF schema documented by `recap-pdf-content-loss-fix`).
- **Commonmark_Hook**: The existing hook `senzing-bootcamp/hooks/commonmark-validation.kiro.hook`,
  currently a `fileEdited` `askAgent` hook on `**/*.md`.
- **Commonmark_Validator**: The existing script `senzing-bootcamp/scripts/validate_commonmark.py`.
- **Graduation_Flow**: The workflow in `senzing-bootcamp/steering/graduation.md` that runs at track
  completion; its Step 0 generates the recap PDF.
- **Derived_Artifact**: A non-Markdown output generated from a Markdown_Artifact (for example
  `docs/bootcamp_recap.pdf`).

## Requirements

### Requirement 1: Free-Form Markdown During Modules

**User Story:** As a bootcamper, I want to write documentation naturally during the modules, so that I
can capture content without fighting a rigid formatting schema mid-session.

#### Acceptance Criteria

1. WHILE the bootcamper is working through modules (before graduation), THE bootcamp SHALL allow
   Markdown_Artifacts to be written in free-form structure without enforcing any Consumer_Schema at
   write time.
2. THE bootcamp SHALL NOT block or gate a module step on a Markdown_Artifact matching a downstream
   Consumer_Schema.
3. THE in-flight authoring guidance SHALL direct the agent to capture content first and defer
   structural formatting to the Normalization_Pass.
4. THE change SHALL NOT remove any content-capture behavior that modules currently rely on (recap
   sections, journal entries, and mapper docs SHALL still be written during the run).

### Requirement 2: Graduation-Time Normalization Pass

**User Story:** As a bootcamper, I want my Markdown formatted correctly at graduation, so that the
shareable artifacts render properly without me hand-formatting during the run.

#### Acceptance Criteria

1. THE Graduation_Flow SHALL include a Normalization_Pass that runs before any Derived_Artifact is
   generated from a Markdown_Artifact.
2. THE Normalization_Pass SHALL run before the recap PDF generation step (current Step 0) so the PDF is
   generated from normalized input.
3. FOR EACH Markdown_Artifact that has a known Consumer_Schema, THE Normalization_Pass SHALL rewrite
   that file to conform to its Consumer_Schema.
4. WHEN a Markdown_Artifact has no known Consumer_Schema, THE Normalization_Pass SHALL leave its
   content intact (style-normalize only, never drop content).
5. THE Normalization_Pass SHALL be non-blocking in the same spirit as the existing recap-PDF step:
   IF normalization of a file fails, THEN the flow SHALL log a warning, preserve the original file,
   and continue graduation.

### Requirement 3: Content Preservation (No Silent Loss)

**User Story:** As a bootcamper, I want normalization to never lose my content, so that reformatting is
safe even when a document does not match the expected shape.

#### Acceptance Criteria

1. THE Normalization_Pass SHALL preserve all substantive content (headings, prose paragraphs, list
   items, code blocks) of each Markdown_Artifact it rewrites.
2. WHEN the Markdown_Normalizer cannot confidently map content into a Consumer_Schema, THE
   Markdown_Normalizer SHALL retain the unmapped content in the output rather than discarding it.
3. THE Normalization_Pass SHALL be paired with the tolerant parser and raw-Markdown fallback from the
   `recap-pdf-content-loss-fix` spec so that a downstream mismatch never silently drops content.
4. THE Markdown_Normalizer SHALL emit a warning when a file's content could not be fully mapped to its
   Consumer_Schema, making the mismatch visible at graduation time.
5. THE Markdown_Normalizer SHALL NOT modify a file in place until it has produced a complete normalized
   output, so a failure mid-write cannot corrupt or truncate the original.

### Requirement 4: Re-Scope the CommonMark Validation Hook

**User Story:** As a power maintainer, I want CommonMark validation to run once at graduation instead of
on every Markdown save, so that per-edit agent round-trips no longer slow the session.

#### Acceptance Criteria

1. THE Commonmark_Hook SHALL be re-scoped from its per-edit `fileEdited` trigger on `**/*.md` to run as
   part of the graduation-time Normalization_Pass (for example a `userTriggered` hook or an explicit
   graduation step) rather than per save.
2. THE Commonmark_Hook SHALL NOT be deleted — its CommonMark style checks SHALL be preserved and run at
   graduation time.
3. THE re-scoped validation SHALL retain the existing CommonMark checks (MD022, MD031, MD032, MD040,
   bold-label colon spacing) and the existing CHANGELOG.md MD024 exception.
4. WHEN the re-scoped validation runs, THE flow SHALL apply CommonMark fixes across all
   Markdown_Artifacts in a single pass rather than one file at a time.
5. THE re-scoped hook file SHALL remain a valid Kiro hook (containing `name`, `version`, `when`, `then`)
   and SHALL stay consistent with the hook registry per the project's hook conventions.
6. AFTER the change, no `fileEdited` hook SHALL trigger an `askAgent` CommonMark validation on routine
   in-module `.md` saves.

### Requirement 5: Generate Derived Artifacts From Normalized Files

**User Story:** As a bootcamper, I want the recap PDF and other derived artifacts built from normalized
Markdown, so that they render completely instead of dropping content.

#### Acceptance Criteria

1. THE Graduation_Flow SHALL generate Derived_Artifacts (e.g. the recap PDF) only after the
   Normalization_Pass has completed.
2. WHEN the Normalization_Pass has run, THE recap PDF generation SHALL consume the normalized
   `docs/bootcamp_recap.md`.
3. IF the Normalization_Pass was skipped or failed for a given file, THEN the corresponding
   Derived_Artifact generation SHALL still run against the original file and rely on the tolerant
   parser/fallback rather than failing.
4. THE ordering change SHALL preserve the existing non-blocking behavior of the recap-PDF step and the
   always-generated graduation report.

### Requirement 6: Normalizer Script and Conventions

**User Story:** As a maintainer, I want the normalizer implemented as a conventional stdlib script, so
that it fits the existing tooling and CI.

#### Acceptance Criteria

1. THE Markdown_Normalizer SHALL be a Python 3.11+ stdlib-only script in `senzing-bootcamp/scripts/`
   following the project script pattern (`main(argv=None)`, argparse, exit code 0 on success and 1 on
   error).
2. THE Markdown_Normalizer SHALL accept the set of files (or a directory) to normalize via CLI
   arguments, with sensible defaults targeting the known Markdown_Artifacts.
3. THE Markdown_Normalizer SHALL reuse the existing `validate_commonmark.py` style logic rather than
   duplicating CommonMark rules.
4. THE Markdown_Normalizer SHALL document each Consumer_Schema it targets (heading format and
   recognized subsection names), consistent with the schema documentation added by
   `recap-pdf-content-loss-fix`.

### Requirement 7: Steering and Documentation Updates

**User Story:** As a power maintainer, I want the workflow change reflected in steering, so that the
agent behaves consistently and the new step is discoverable.

#### Acceptance Criteria

1. THE `senzing-bootcamp/steering/graduation.md` file SHALL describe the Normalization_Pass as an
   explicit step that runs before recap-PDF and other Derived_Artifact generation.
2. THE in-module authoring guidance SHALL be updated to state that Markdown is free-form during the
   bootcamp and normalized at graduation.
3. WHEN steering files are added or their size changes, THE steering token budgets in
   `steering/steering-index.yaml` SHALL be updated accordingly.
4. THE documentation SHALL note the relationship to `recap-pdf-content-loss-fix` (tolerant parser +
   fallback) so the two changes are understood as paired.

### Requirement 8: Test Coverage

**User Story:** As a maintainer, I want tests for the normalizer and the re-scoped hook, so that the
behavior does not regress.

#### Acceptance Criteria

1. THE feature SHALL include pytest tests for the Markdown_Normalizer covering: conforming a free-form
   recap to the recap Consumer_Schema, preserving content with no known schema, and warning on
   unmappable content.
2. THE feature SHALL include a Hypothesis property test asserting that normalization preserves all
   substantive content (no headings, list items, prose, or code blocks are dropped) for any generated
   free-form Markdown input.
3. THE feature SHALL include a test asserting the re-scoped Commonmark_Hook is a valid hook, is no
   longer a per-edit `fileEdited` `**/*.md` trigger, and stays consistent with the hook registry.
4. THE feature SHALL include a test asserting that a normalized recap renders a non-empty recap PDF
   body (consistent with the `recap-pdf-content-loss-fix` expectations).
