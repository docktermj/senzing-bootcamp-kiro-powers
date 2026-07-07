# Requirements Document

## Introduction

The Senzing Bootcamp Power's most valuable deliverables — the Q&A transcript
(`docs/bootcamp_transcript.md`), the recap (`docs/bootcamp_recap.md`), and an accompanying
recap PDF (`docs/bootcamp_recap.pdf`) — are currently produced on a best-effort,
"non-blocking" basis. Their generation depends on bundled scripts (`generate_transcript.py`,
`generate_recap_pdf.py`, `generate_completion_summary.py`) and on the optional `fpdf2`
dependency. When those scripts are not materialized in a bootcamper's workspace, or when
`fpdf2` is absent, the crown-jewel artifacts are silently skipped, leaving the bootcamper
with no durable, shareable record of the bootcamp.

This feature makes these artifacts an **enforced completion invariant**. It guarantees that
the transcript, the recap Markdown, and a rendered recap document are always produced and
non-empty at every track-completion and graduation stopping point, reconstructing them from
always-present source data rather than depending on bundled scripts. It guarantees a rendered
recap document even when `fpdf2` is unavailable, by falling back to an HTML rendering. Finally,
it requires a mandatory closing announcement after graduation that tells the bootcamper the
recap exists, where it is, and what it contains.

## Glossary

- **Bootcamp_Power**: The distributed Senzing Bootcamp Kiro Power, comprising its scripts,
  hooks, and steering files under `senzing-bootcamp/`.
- **Artifact_Enforcement_Hook**: An `agentStop` / track-completion Kiro hook (proposed id
  `enforce-critical-artifacts`) that regenerates the guaranteed artifacts and blocks
  completion until each exists and is non-empty.
- **Transcript_Generator**: The self-contained generation logic that produces
  `docs/bootcamp_transcript.md`.
- **Recap_Generator**: The self-contained generation logic that produces
  `docs/bootcamp_recap.md`.
- **Recap_Renderer**: The self-contained generation logic that produces a rendered recap
  document (`docs/bootcamp_recap.pdf`, or an HTML fallback) from the recap Markdown.
- **Graduation_Announcer**: The mandatory closing step that reports the recap's existence,
  path, and contents to the bootcamper after graduation completes.
- **Guaranteed_Artifact**: Any of `docs/bootcamp_transcript.md`, `docs/bootcamp_recap.md`,
  and the rendered recap document (`docs/bootcamp_recap.pdf` or its HTML fallback).
- **Transcript**: `docs/bootcamp_transcript.md` — an ordered, per-module record pairing every
  substantive question asked with the bootcamper's response.
- **Recap**: `docs/bootcamp_recap.md` — a per-module record in the canonical format with
  `## Module N: [Name] — [timestamp]` sections, each containing `### Information Shared`,
  `### Questions & Responses`, and `### Actions Taken`.
- **Rendered_Recap**: A shareable, rendered form of the Recap — a PDF (`docs/bootcamp_recap.pdf`)
  when `fpdf2` is available, or an HTML document (`docs/bootcamp_recap.html`) when it is not.
- **Always_Present_Source**: Source data that exists in the workspace independent of the
  bundled generation scripts — `config/session_log.jsonl`, `config/bootcamp_progress.json`,
  the Recap's `### Questions & Responses` pairs, and per-module artifacts.
- **Non_Empty**: A file that exists and contains at least one non-whitespace character beyond
  any required header or title.
- **fpdf2**: The optional, lazily-imported Python PDF library (`import fpdf`) used only by
  PDF-generation scripts.
- **Stopping_Point**: Any track-completion or graduation moment at which the agent would
  otherwise report "done".

## Requirements

### Requirement 1: Guarantee the Q&A transcript

**User Story:** As a bootcamper, I want the Q&A transcript to always be produced at track
completion and graduation, so that I retain an ordered, per-module record of every question
and my response for replay and audit.

#### Acceptance Criteria

1. WHEN a Stopping_Point is reached, THE Transcript_Generator SHALL ensure that, before the Stopping_Point completes, `docs/bootcamp_transcript.md` exists and is Non_Empty.
2. WHERE the bundled `generate_transcript.py` script is absent, THE Transcript_Generator SHALL reconstruct `docs/bootcamp_transcript.md` from an Always_Present_Source without depending on any bundled script.
3. WHEN reconstructing the Transcript, THE Transcript_Generator SHALL read Q&A pairs from `config/session_log.jsonl` when that source exists and contains at least one Q&A pair.
4. IF `config/session_log.jsonl` is absent or contains no Q&A pairs, THEN THE Transcript_Generator SHALL reconstruct the Transcript from the Recap's `### Questions & Responses` pairs.
5. WHEN producing the Transcript, THE Transcript_Generator SHALL order module sections by ascending module number and SHALL order the question-and-response pairs within each module in ascending ask order.
6. WHEN writing a question-and-response pair, THE Transcript_Generator SHALL record the question text, the response text, and the single module to which the pair is attributed.
7. WHERE reconstruction source data exists, THE Transcript_Generator SHALL regenerate the Transcript rather than omit it.
8. IF no Always_Present_Source contains any Q&A pairs, THEN THE Transcript_Generator SHALL create a Non_Empty `docs/bootcamp_transcript.md` containing a record that states no Q&A history was available.
9. IF writing or reconstructing the Transcript fails, THEN THE Transcript_Generator SHALL leave any existing `docs/bootcamp_transcript.md` unchanged and return an error indicating the failure.

### Requirement 2: Enforce guaranteed artifacts as a completion invariant

**User Story:** As a bootcamper, I want the transcript and recap PDF enforced rather than
best-effort, so that the most valuable deliverables cannot be silently skipped when they
matter most.

#### Acceptance Criteria

1. WHEN a Stopping_Point is reached, THE Artifact_Enforcement_Hook SHALL verify that each Guaranteed_Artifact exists and is Non_Empty, where Non_Empty means the file contains at least one non-whitespace character.
2. IF a Guaranteed_Artifact is absent, empty, or stale at a Stopping_Point, THEN THE Artifact_Enforcement_Hook SHALL regenerate that Guaranteed_Artifact before completion is reported, where stale means the artifact's last-modified time is earlier than the latest last-modified time among its Always_Present_Source inputs.
3. WHEN regenerating a Guaranteed_Artifact, THE Artifact_Enforcement_Hook SHALL attempt regeneration at most once per artifact per Stopping_Point.
4. IF any Guaranteed_Artifact is absent or empty after regeneration is attempted, THEN THE Artifact_Enforcement_Hook SHALL block the "done" state, retain every already-valid Guaranteed_Artifact, and report each missing or empty Guaranteed_Artifact by its identity.
5. WHEN generating any Guaranteed_Artifact, THE Bootcamp_Power SHALL reconstruct the artifact from an Always_Present_Source (`config/session_log.jsonl`, `config/bootcamp_progress.json`, the Recap's `### Questions & Responses` pairs, or per-module artifacts) without depending on any bundled generation script.
6. WHEN a Stopping_Point is reached more than once, THE Artifact_Enforcement_Hook SHALL perform idempotent regeneration such that a Guaranteed_Artifact that is already Non_Empty and not stale is left byte-for-byte unchanged.
7. IF `fpdf2` is unavailable when the rendered recap is verified, THEN THE Artifact_Enforcement_Hook SHALL treat a Non_Empty HTML Rendered_Recap as satisfying the rendered recap Guaranteed_Artifact.
8. THE Artifact_Enforcement_Hook SHALL be defined as a `.kiro.hook` JSON file containing the `name`, `version`, `when`, and `then` fields.
9. THE Artifact_Enforcement_Hook SHALL declare its `when` trigger as type `agentStop`.

### Requirement 3: Guarantee the recap Markdown in canonical format

**User Story:** As a bootcamper, I want `docs/bootcamp_recap.md` always produced in the
canonical per-module format, so that I finish with a complete, structured record of the
bootcamp.

#### Acceptance Criteria

1. WHEN a Stopping_Point (track-completion or graduation) is reached, THE Recap_Generator SHALL ensure `docs/bootcamp_recap.md` exists and is Non_Empty, where Non_Empty means the file contains non-whitespace content and at least one `## Module N` section.
2. WHERE the bundled recap script is absent, THE Recap_Generator SHALL reconstruct `docs/bootcamp_recap.md` from `config/bootcamp_progress.json` and per-module artifacts.
3. IF `config/bootcamp_progress.json` and all per-module artifacts are absent or unreadable when reconstruction is required, THEN THE Recap_Generator SHALL leave any existing `docs/bootcamp_recap.md` unchanged and return an error indicating that recap source data is unavailable.
4. WHEN producing the Recap, THE Recap_Generator SHALL write exactly one `## Module N: [Name] — [timestamp]` section for each completed module.
5. WHEN writing a module section, THE Recap_Generator SHALL include an `### Information Shared` subsection, a `### Questions & Responses` subsection, and an `### Actions Taken` subsection.
6. WHEN a module's Information Shared, Questions & Responses, or Actions Taken source data contains no entries, THE Recap_Generator SHALL still write the corresponding subsection with an explicit indicator that no entries exist.
7. WHEN writing module sections, THE Recap_Generator SHALL order the sections by ascending module completion timestamp, and SHALL break ties by ascending module number N.
8. WHERE reconstruction source data exists, THE Recap_Generator SHALL regenerate the Recap rather than omit it.

### Requirement 4: Guarantee a rendered recap document with a graceful PDF path

**User Story:** As a bootcamper, I want a rendered, shareable recap document always produced,
so that I have a durable takeaway even when the PDF library is unavailable.

#### Acceptance Criteria

1. WHEN a Stopping_Point is reached and `docs/bootcamp_recap.md` is Non_Empty, THE Recap_Renderer SHALL ensure exactly one Rendered_Recap exists and is Non_Empty (a file present on disk containing at least one non-whitespace character).
2. WHERE `fpdf2` is available, WHEN a Stopping_Point is reached, THE Recap_Renderer SHALL produce a Non_Empty `docs/bootcamp_recap.pdf` derived from `docs/bootcamp_recap.md`.
3. IF `fpdf2` is unavailable, THEN THE Recap_Renderer SHALL produce a Non_Empty HTML Rendered_Recap at `docs/bootcamp_recap.html` derived from `docs/bootcamp_recap.md`.
4. IF `fpdf2` is unavailable, THEN THE Recap_Renderer SHALL emit to standard output a message stating the exact command required to install `fpdf2` to enable PDF rendering.
5. THE Recap_Renderer SHALL import `fpdf` lazily inside the rendering function and SHALL NOT import `fpdf` at module top level.
6. WHEN producing the Rendered_Recap, THE Recap_Renderer SHALL derive its content from the current `docs/bootcamp_recap.md` so that the Rendered_Recap reflects every per-module section present in that source file.
7. IF `docs/bootcamp_recap.md` is absent or not Non_Empty when a Stopping_Point is reached, THEN THE Recap_Renderer SHALL NOT produce a Rendered_Recap and SHALL emit to standard output an error message indicating that the recap source is unavailable.
8. IF `fpdf2` is available but PDF generation fails, THEN THE Recap_Renderer SHALL produce the HTML Rendered_Recap at `docs/bootcamp_recap.html` instead and SHALL emit to standard output an error message indicating that PDF rendering failed and HTML was produced.

### Requirement 5: Mandatory post-graduation announcement

**User Story:** As a bootcamper, I want to be explicitly told about the recap after graduation,
so that the most valuable artifact does not go unnoticed.

#### Acceptance Criteria

1. WHEN graduation completes, THE Graduation_Announcer SHALL, as a mandatory closing step executed exactly once before graduation is reported as finished, emit a single announcement message informing the bootcamper that the Recap exists.
2. WHEN announcing the Recap, THE Graduation_Announcer SHALL state the path `docs/bootcamp_recap.md` and the path of the Rendered_Recap (`docs/bootcamp_recap.pdf` when `fpdf2` is available, otherwise `docs/bootcamp_recap.html`).
3. WHEN announcing the Recap, THE Graduation_Announcer SHALL state, for every completed module, that the Recap contains the three labeled sections Information Shared, Questions & Responses, and Actions Taken.
4. IF one or more Guaranteed_Artifacts are missing at the time of announcement, THEN THE Graduation_Announcer SHALL trigger regeneration of every missing Guaranteed_Artifact and SHALL withhold the announcement until regeneration completes.
5. IF regeneration of a Guaranteed_Artifact fails, THEN THE Graduation_Announcer SHALL identify each failed Guaranteed_Artifact, mark the announcement as incomplete, and preserve every successfully generated Guaranteed_Artifact.
6. WHEN announcing the Recap, THE Graduation_Announcer SHALL report only those Guaranteed_Artifacts confirmed to exist at their stated paths at announcement time.

### Requirement 6: Self-contained, dependency-free generation

**User Story:** As a power maintainer, I want artifact generation to be self-contained and
stdlib-only, so that guaranteed artifacts are produced regardless of which bundled scripts or
optional dependencies are present.

#### Acceptance Criteria

1. THE Bootcamp_Power SHALL generate every Guaranteed_Artifact using only the Python 3.11+ standard library, except for the optional `fpdf2` library, which SHALL be imported lazily and never at module top level and used solely for PDF rendering.
2. IF a bundled generation script is absent, THEN THE Bootcamp_Power SHALL generate the corresponding Guaranteed_Artifact from an Always_Present_Source (`config/session_log.jsonl`, `config/bootcamp_progress.json`, the Recap's `### Questions & Responses` pairs, or per-module artifacts).
3. IF a required Always_Present_Source is missing or unreadable when generation is required, THEN THE Bootcamp_Power SHALL stop generating the affected Guaranteed_Artifact, return an error identifying the unavailable source, and preserve every previously generated Guaranteed_Artifact.
4. IF `fpdf2` is absent, THEN THE Bootcamp_Power SHALL still generate the Markdown Guaranteed_Artifacts and SHALL skip only PDF rendering without raising an unhandled exception.
5. WHERE new scripts are added, THE Bootcamp_Power SHALL place them under `senzing-bootcamp/scripts/` using `snake_case.py` naming with a `main()` entry point and an argparse command-line interface.
6. WHERE the Artifact_Enforcement_Hook is added, THE Bootcamp_Power SHALL place it under `senzing-bootcamp/hooks/` as a `hook-id.kiro.hook` file whose id matches the hook registry.
7. WHEN generating any Guaranteed_Artifact, THE Bootcamp_Power SHALL exclude secrets, credentials, environment variable values, connection strings, and PII from the artifact content.
