# Bugfix Requirements Document

## Introduction

The bootcamp recap is a primary completion deliverable: `docs/bootcamp_recap.md`
and the PDF rendered from it (`docs/bootcamp_recap.pdf`). Two related High-priority
failures let the recap deliverable be reported as successfully produced while it
silently omits content — the most dangerous failure mode, because exit-code and
file-exists checks pass and the loss is only visible when a human opens the file.

There are two content-loss paths:

1. **Missing per-module recap sections.** At track completion,
   `docs/bootcamp_recap.md` contained sections only for Modules 1–5; the Module 6
   and Module 7 sections were absent. Two distinct causes combined: (a) Module 6's
   recap section was appended in an earlier session and the tool reported success,
   but the write did not persist across the session boundary; (b) Module 7's recap
   is produced by the `module-recap-append` agentStop hook on boundary detection,
   and when Module 7 was marked complete the hook did not actually write the
   section, so it never landed in the file. In both cases the append "succeeds"
   without verification, so the gap is silent — and it omits the modules where the
   bulk of working code was produced.

2. **PDF rendered only the outline.** The first working recap PDF (2.5 KB)
   contained only headings — every body line (Information Shared bullets,
   Questions, Answers, Actions Taken, table rows) was missing. The inline renderer
   drew cells with `multi_cell(w=0)`, which derives width from the current
   x-position; after certain cells the x-position advanced toward the right margin,
   so any line that needed to wrap raised `FPDFException: Not enough horizontal
   space to render a single character`. That exception was caught and swallowed by
   a fallback, so wrapping lines vanished while short single-line headings
   survived, producing an outline-only PDF that still reported success.

This bugfix makes recap append synchronous and verified, reconciles and backfills
the recap against `config/bootcamp_progress.json` (`modules_completed`) at track
completion, renders PDF cells at full width without swallowing exceptions, and
verifies the rendered output by round-tripping its text before reporting success.
Correct behavior — sections that already exist and persisted, and PDFs whose body
content renders within available width — must be preserved.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when the bug is triggered:

1.1 WHEN a module is completed and the recap section is appended, THEN the system reports success without verifying that a `## Module N:` heading for the just-completed module actually exists in `docs/bootcamp_recap.md`, so a write that did not persist goes undetected.

1.2 WHEN the recap append happens in an earlier session and the write does not persist across the session boundary, THEN the section is silently absent and nothing later detects or repairs the gap.

1.3 WHEN the final module (e.g., Module 7) is marked complete and the `module-recap-append` agentStop hook fires on boundary detection, THEN the hook does not write the recap section and the section never lands in the file, yet module/track completion proceeds.

1.4 WHEN the track is completed, THEN the system does not reconcile `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed`, so per-module sections missing for any reason remain absent in the final deliverable.

1.5 WHEN the recap PDF is rendered and a body line is wide enough to wrap, THEN the inline renderer's `multi_cell(w=0)` derives width from the advanced x-position and raises `FPDFException: Not enough horizontal space to render a single character`.

1.6 WHEN that rendering exception is raised, THEN it is caught and swallowed by a fallback, so the wrapping body line is dropped while short single-line headings survive.

1.7 WHEN PDF generation finishes after dropping body lines, THEN the system reports success based on exit code and file existence, producing an outline-only PDF that omits Information Shared bullets, Questions, Answers, Actions Taken, and table rows.

### Expected Behavior (Correct)

What should happen instead:

2.1 WHEN a module is completed and the recap section is appended, THEN the system SHALL perform the append as a synchronous step of the module-completion workflow (not solely via the agentStop hook) and SHALL verify that a `## Module N:` heading for the just-completed module exists in `docs/bootcamp_recap.md`, retrying or backfilling if it does not, before reporting success.

2.2 WHEN a recap append cannot be confirmed present in the file (including writes lost across a session boundary), THEN the system SHALL detect the missing section and backfill it rather than reporting silent success.

2.3 WHEN the final module of a track is marked complete, THEN the system SHALL write its recap section exactly as for any other module; track completion (graduation/celebration) SHALL NOT suppress the per-module recap section.

2.4 WHEN the track is completed, THEN the system SHALL reconcile `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed` and SHALL backfill any missing per-module section so every completed module has a `## Module N:` section.

2.5 WHEN the recap PDF is rendered, THEN the system SHALL render every cell at the left margin with an explicit full width (`set_x(l_margin)` followed by `multi_cell(epw, ...)`) so wrapping never runs out of horizontal space.

2.6 WHEN a rendering exception occurs during PDF generation, THEN the system SHALL NOT silently swallow it; it SHALL fail loudly or log the failure rather than dropping content and reporting success.

2.7 WHEN the PDF is written, THEN the system SHALL verify the artifact by round-tripping its text (e.g., extracting text and asserting it contains the expected per-module sections and at least a minimum body-line count) before reporting success.

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved:

3.1 WHEN a per-module recap section already exists and persisted correctly, THEN the system SHALL CONTINUE TO preserve existing recap content byte-for-byte without duplicating, overwriting, or reordering it out of chronological order.

3.2 WHEN reconciliation runs at track completion and the recap is already consistent with `modules_completed`, THEN the system SHALL CONTINUE TO be idempotent and make no spurious changes.

3.3 WHEN recap PDF body content fits within the available width (no wrapping failure), THEN the system SHALL CONTINUE TO render all headings and body lines as it does today.

3.4 WHEN the optional `fpdf2` dependency is absent, THEN the system SHALL CONTINUE TO degrade gracefully — keep the Markdown output and print a `pip install fpdf2` hint — without raising.

3.5 WHEN any other completion hook runs (celebration, journal entry, etc.), THEN the system SHALL CONTINUE TO behave exactly as before; this fix SHALL NOT alter their behavior.
