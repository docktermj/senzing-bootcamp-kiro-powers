---
inclusion: manual
---

# Graduation Workflow

This steering file guides the agent through transitioning a completed bootcamp project into a production-ready codebase. Load it when the bootcamper accepts the graduation offer at track completion, or when they say "run graduation" or "graduate."

The workflow has three preparatory steps followed by five sequential steps:

0. **Markdown Normalization Pass** — Normalize the bootcamp's Markdown artifacts into the schema their consumers expect, before any derived artifact is generated (non-blocking)
0a. **Recap Reconciliation & Backfill** — Reconcile `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed` and backfill any missing per-module `## Module N:` section, so every completed module is present **before** the PDF is rendered (non-blocking, idempotent)
0b. **Recap PDF, Q&A Transcript & Docs Index Generation** — Generate a PDF of the now-normalized, reconciled bootcamp recap document, the ordered Q&A transcript, and the `docs/` index (all non-blocking)
1. **Production Project Structure** — Copy production-relevant code into a clean `production/` directory, excluding bootcamp scaffolding
2. **Production Configuration Files** — Generate `.env.production`, `.env.example`, `docker-compose.yml`, a CI/CD pipeline, and `.gitignore`
3. **Production README** — Generate a production-ready `README.md` with no bootcamp language
4. **Migration Checklist** — Generate `MIGRATION_CHECKLIST.md` with conditional items based on completed modules
5. **Git Repository Initialization** — Optionally initialize a new git repo in `production/`

A graduation report (`GRADUATION_REPORT.md`) is always generated at the end, even if individual steps encountered errors.

Each step requires bootcamper confirmation before proceeding. Do not skip ahead.

## Pre-checks

Before starting any steps, gather the bootcamper's context:

1. **Read preferences:** Load `config/bootcamp_preferences.yaml` and extract: `language`, `track`, `platform`, `data_sources`, `database_type`.

2. **Read progress:** Load `config/bootcamp_progress.json` and extract: `modules_completed`, `current_module`.

3. **Fallback if files are missing:** Inform the bootcamper, prompt for **language** and **database type**, use sensible defaults for everything else (track: unknown, platform: GitHub Actions, data_sources: []).

Store these values for use throughout the workflow. Proceed to Step 0.

## Step 0: Markdown Normalization Pass

Before generating any derived artifact (recap PDF, reports), run a single normalization pass over the bootcamp's Markdown artifacts. During the modules, Markdown is written free-form; this step rewrites each artifact into the schema its consumer expects and applies CommonMark style fixes once, across all files. This step is **non-blocking** — graduation continues regardless of the outcome, in the same spirit as the recap PDF step and the always-generated `GRADUATION_REPORT.md`.

**Procedure:**

1. Run the normalization script over the known Markdown artifacts:

   ```bash
   python scripts/normalize_markdown.py
   ```

   With no arguments the script targets the known artifacts that exist: `docs/bootcamp_recap.md`, `docs/bootcamp_journal.md`, the mapper docs, and other `docs/*.md` artifacts. Files with a known consumer schema (today: `docs/bootcamp_recap.md`) are rewritten to conform to that schema; all other files are style-normalized only and never have content dropped. Writes are atomic (temp file then replace), so a mid-write failure cannot corrupt or truncate the original.

2. **Report a one-line summary** of how many files were normalized, plus any per-file warnings the script emitted (for example, content that could not be confidently mapped into a consumer schema and was retained verbatim).

3. **Handle outcomes gracefully (warn and continue):**
   - If the script reports warnings for individual files: surface them in the summary and proceed. Warnings never block graduation.
   - If the script fails for any reason: inform the bootcamper of the failure reason, leave the original files untouched, and proceed to Step 0b anyway.

**Fallback when normalization is skipped or fails:** If this pass does not run, or fails for `docs/bootcamp_recap.md`, the recap PDF step (Step 0b) still runs against the original file and relies on the tolerant parser and raw-Markdown fallback delivered by the paired `recap-pdf-content-loss-fix` work, so a schema or style mismatch never silently drops content.

Proceed to Step 0a.

## Step 0a: Recap Reconciliation & Backfill

This is the **final safety net for per-module recap completeness (Path A)**. Each module's recap section is appended-and-verified synchronously at module completion (see `module-completion-artifacts.md`) and the track-completion celebration already runs the same reconciliation pass (see `module-completion-track.md`). This step re-runs that reconciliation here, immediately **before** the PDF is rendered, so any section still missing at graduation — a write lost across a session boundary, a final-module hook miss, or a recap reconstructed in Step 0b.1 — is backfilled before the deliverable is produced. This step is **non-blocking** and **idempotent**: on an already-consistent recap it makes no changes.

**Ordering invariant:** reconcile/backfill the recap (this step) **then** render the PDF (Step 0b). The PDF is never rendered from an unreconciled recap.

**Procedure:**

1. Reconcile `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed` and backfill any missing per-module section by running the recap backfill applier:

   ```bash
   python scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --journal docs/bootcamp_journal.md --progress-dir docs/progress --backfill
   ```

   The applier computes a pure set difference (`plan_backfill`): it appends a `## Module N:` section for every completed module that lacks one — appending around existing content, **never rewriting** the bytes of sections that already persisted (Req 3.1) — and re-runs cleanly on a consistent recap with no changes (Req 3.2). It self-creates the recap file with a minimal header if it does not yet exist. After writing it verifies that every completed module now has a section and **exits non-zero**, naming the still-missing modules, if any gap remains — so a silent gap can never pass through to the PDF.

   - If it reports `Backfilled recap sections for modules: [...]`, inform the bootcamper: "🧩 Reconciled the recap — backfilled sections for modules: [...]."
   - If it reports `Recap already complete; no sections backfilled.`, proceed silently.

2. **Handle outcomes gracefully (warn and continue):** if the applier cannot run or exits non-zero (file-system error, or a gap it could not close), log a warning naming the reason (and any still-missing modules) and proceed to Step 0b anyway — the recap Markdown and the tolerant PDF parser remain the backstop. Reconciliation never blocks graduation.

Proceed to Step 0b.

## Step 0b: Recap PDF Generation

Generate a PDF version of the bootcamper's recap document for sharing. This step consumes the normalized, reconciled `docs/bootcamp_recap.md` produced by Steps 0 and 0a (or, if normalization was skipped or failed, the original file via the tolerant parser/raw-Markdown fallback). This step is **non-blocking** — graduation continues regardless of the outcome.

**Note:** Independent of this recap PDF, the completion-summary document (`docs/completion_summary.md`) is **always** generated during the post-completion/graduation flow via `generate_completion_summary.py` (triggered by `completion-summary-offer.md`). That generation is **non-blocking** — in the same spirit as this recap PDF step and the always-generated `GRADUATION_REPORT.md`, any failure logs a warning and graduation continues.

**Procedure:**

### Step 0b.1: Recap Document Recovery

Before generating the PDF, validate that the recap document exists and is usable. Do NOT silently skip — treat a missing recap as a recoverable error.

1. **Check if `docs/bootcamp_recap.md` exists.**

2. **If `docs/bootcamp_recap.md` does NOT exist:**

   a. Check if `config/bootcamp_progress.json` exists and contains a non-empty `modules_completed` array.

   b. **If progress data is available** (file exists and `modules_completed` is non-empty):
      - Regenerate `docs/bootcamp_recap.md` from the progress data and module artifacts produced during the bootcamp.
      - For each module in `modules_completed`, reconstruct a recap section using available module artifacts (files created, code produced, documentation generated during that module).
      - Display message to the bootcamper: "⚠️ Recap document was not found and has been reconstructed from available progress data."
      - Proceed to Step 0b.2 (validation).

   c. **If progress data is NOT available** (progress file missing or `modules_completed` is empty):
      - Display message to the bootcamper: "⚠️ Cannot generate recap PDF — the recap document is missing and there is insufficient progress data to reconstruct it. Skipping PDF generation."
      - Skip PDF generation entirely and proceed to Step 0b.4.

3. **If `docs/bootcamp_recap.md` exists:** Proceed to Step 0b.2 (validation).

### Step 0b.2: Recap Document Validation

Before generating the PDF, validate that the recap document contains content matching the bootcamper's progress.

1. Read `config/bootcamp_progress.json` and extract the `modules_completed` array.

2. Check that `docs/bootcamp_recap.md` contains at least one markdown heading matching the pattern `## Module N:` where N is a module number present in the `modules_completed` array.

3. **If valid** (at least one matching `## Module N:` heading found): Proceed to Step 0b.3 (PDF generation).

4. **If invalid** (no matching `## Module N:` headings found):

   a. Check if `config/bootcamp_progress.json` exists and contains a non-empty `modules_completed` array.

   b. **If progress data is available:** Regenerate `docs/bootcamp_recap.md` from progress data and module artifacts. Display message: "⚠️ Recap document was incomplete and has been reconstructed from available progress data."

   c. **If progress data is NOT available:** Display message: "⚠️ Cannot generate recap PDF — the recap document has no valid module sections and there is insufficient progress data to reconstruct it. Skipping PDF generation." Skip PDF generation and proceed to Step 0b.4.

### Step 0b.3: PDF Generation

Generate `docs/bootcamp_recap.pdf` from `docs/bootcamp_recap.md` using a helper-first, inline-fallback decision. The bundled helper lives in the installed power's directory and may not resolve at a workspace-relative path, so never assume it ran — confirm a PDF was actually written before claiming success. This step pairs with the `recap-pdf-content-loss-fix` (tolerant parser + raw-Markdown fallback), `graduation-markdown-normalization` (Step 0 normalization), and `missing-bundled-scripts` (graceful degradation + file-independent inline render) work.

A PDF was written only when the script prints a `PDF generated:` line to stdout and exits 0; any other outcome (exit 1, no `PDF generated:` line) means no PDF exists.

**Preference order (most → least structured), each non-blocking:**

1. **Bundled `generate_recap_pdf.py`** — full structured render (cover page + per-module pages). Preferred first; used whenever it can run and write a PDF.
2. **`generate_recap_pdf_inline.py`** — self-contained inline generator. It reuses the shared `generate_recap_pdf` parser/renderer when that module is importable, otherwise it falls through to the file-independent path below. Used when the bundled helper does not write a PDF for a reason other than missing `fpdf2`.
3. **File-independent inline render** — `recap_pdf_render.render_markdown_pdf`, reached from inside the inline generator when no bundled generator file is importable. It renders the raw recap Markdown straight to PDF with **no dependency on any bundled generator file**, so a recap PDF is still produced when both bundled generators are absent (as long as `fpdf2` is installed). `fpdf` is imported lazily inside this render path only; when `fpdf2` is absent the path degrades gracefully (Markdown recap retained, `pip install fpdf2` hint printed) and never hard-fails.

1. **Prefer the bundled helper.** Attempt:

   ```bash
   python scripts/generate_recap_pdf.py
   ```

   This converts `docs/bootcamp_recap.md` into `docs/bootcamp_recap.pdf`, rendering a cover page (bootcamp title, bootcamper name, completion date, total duration) and per-module pages with formatted headings, lists, and code blocks.

   - If it runs and writes the PDF (exit 0 with a `PDF generated:` line), inform the bootcamper: "📄 Recap PDF generated at `docs/bootcamp_recap.pdf`." Proceed to Step 0b.4.
   - If the bundled script cannot be located or run — the path does not resolve, the file is missing, or it errors before writing a PDF — do not stop and do not report success. Fall back inline (step 2).
   - If it reports `fpdf2` is not installed, go to graceful degradation (step 3).

2. **Fall back to the inline generator.** When the bundled helper is unavailable or did not write a PDF (for a reason other than missing `fpdf2`), run the self-contained inline fallback against the existing recap Markdown:

   ```bash
   python scripts/generate_recap_pdf_inline.py --input docs/bootcamp_recap.md --output docs/bootcamp_recap.pdf
   ```

   This path does not depend on the bundled `generate_recap_pdf.py` being importable from the workspace; it reads `docs/bootcamp_recap.md` and renders the same recap content (reusing the shared renderer when available, otherwise the file-independent `recap_pdf_render.render_markdown_pdf` raw-Markdown render path so no content is dropped and no bundled generator file is required). Its success signal is the same: a `PDF generated:` line on stdout and exit 0.

   - On success, state plainly that an inline generation path was used: "📄 Recap PDF generated at `docs/bootcamp_recap.pdf` (generated via the inline fallback path)." Do not imply the bundled script ran. Proceed to Step 0b.4.
   - If the inline generator reports `fpdf2` is not installed, go to graceful degradation (step 3).
   - If it fails for any other reason (exit 1, no `PDF generated:` line), follow the skip/failure messaging (step 4).

3. **Graceful degradation when `fpdf2` is absent.** If either path reports that `fpdf2` is not installed, PDF generation is skipped — this is expected and never blocks graduation. Inform the bootcamper that the PDF was not generated because the optional `fpdf2` dependency is missing, and suggest `pip install fpdf2` to enable it. Then follow the skip/failure messaging (step 4).

4. **Skip/failure messaging — always point to the Markdown recap.** In every case where no PDF was written (bundled helper and inline fallback both unavailable, `fpdf2` absent, or any other error), tell the bootcamper:
   - that the PDF was not generated, and the reason, and
   - that their recap content already exists at `docs/bootcamp_recap.md`.

   Then proceed to Step 0b.4.

5. **No false success.** Only emit the "📄 Recap PDF generated" message when a PDF file was actually written (a `PDF generated:` line with exit 0). Never report PDF success when no PDF exists.

Regardless of outcome, this step is **non-blocking**: proceed to Step 0b.4 and then to Step 1.

### Step 0b.4: Q&A Transcript Reconciliation & Generation

Generate the ordered question→answer transcript from the session log for replay and audit. This step is **non-blocking** — graduation continues regardless of the outcome.

The logged Q&A events are emitted voluntarily by the agent (per `qa-transcript.md`) and are **not** backed by a write-tool hook, so they can silently under-represent the session. Before rendering, reconcile the log against the enforced recap source — mirroring how Step 0a reconciles the recap before the recap PDF is rendered — so the transcript is as complete as the recap's captured Q&A content.

**Ordering invariant:** reconcile the transcript (sub-step 1) **then** render it (sub-step 2). The transcript is never rendered from an unreconciled log.

1. Reconcile the session log against the recap's `### Questions & Responses` pairs by running the transcript reconciliation pass:

   ```bash
   python scripts/reconcile_transcript.py
   ```

   With no arguments the script uses the canonical paths (`docs/bootcamp_recap.md` and `config/session_log.jsonl`). It counts logged `question` events against the recap's Q&R pairs per module and, on a material shortfall, backfills the missing pairs into `config/session_log.jsonl` (reusing the existing `session_logger` completion-event schema) so the subsequent render is complete. The pass is **idempotent** (a no-op when the counts already agree, or when the recap has no Q&R content) and **non-blocking**: it never adds a per-write hook or per-write process spawn, and runs only here at graduation / stopping points.

   This step is **non-blocking regardless of the reconcile script's exit code** — whether it succeeds, no-ops, or exits non-zero after an internally handled error, always proceed to the render in sub-step 2. On a non-zero exit or any warning, log the reason and continue; the render falls back to the existing log content.

2. Run the transcript renderer:

   ```bash
   python scripts/generate_transcript.py
   ```

   This reads the (now-reconciled) `config/session_log.jsonl` and regenerates `docs/bootcamp_transcript.md`, an ordered Q&A record grouped by module. Regeneration overwrites any existing transcript rather than appending to stale content.

3. **Handle outcomes gracefully:**
   - If the script warns there are no Q&A events to render: no transcript is written. Inform the bootcamper and proceed to Step 1.
   - If the script fails for any other reason: inform the bootcamper of the failure reason and proceed to Step 1.

4. On success, inform the bootcamper: "📝 Q&A transcript generated at `docs/bootcamp_transcript.md`."

Proceed to Step 0b.5.

### Step 0b.5: Docs Index Generation

Generate `docs/README.md` — a table of contents describing every top-level file and immediate subdirectory under `docs/` — so the documentation set is self-describing for handoff. This step is **non-blocking** — graduation continues regardless of the outcome, in the same spirit as the recap PDF and Q&A transcript steps.

1. **If `docs/` does not exist**, report that the index was not generated (for example, "📑 Docs index not generated — no `docs/` directory was found.") and proceed to Step 1. This is a success, not an error. When `docs/` does exist, do **not** ask for confirmation that it was found — proceed directly to generation.

2. Otherwise, run the docs index generator through the guarded bundled-script runner:

   ```bash
   python senzing-bootcamp/scripts/run_bundled_script.py generate_docs_index.py
   ```

   The runner performs an existence check before shelling out: when the bundled `generate_docs_index.py` is present it executes unchanged and propagates its own exit code; when it is absent it runs the onboarding self-repair (`preflight.py --fix`) once and re-checks, then degrades to a graceful no-op (exit 0, one-line skip notice) rather than a raw `No such file or directory` error. This enumerates the actual top-level contents of `docs/` at graduation time and regenerates `docs/README.md` as a Markdown table of contents, replacing any existing index. The write is atomic and validated, so a failure never leaves a partial or malformed `docs/README.md`.

3. **Handle outcomes gracefully (warn and continue):**
   - On success (exit 0 with a `Wrote docs index:` line on stdout), inform the bootcamper: "📑 Docs index generated at `docs/README.md`." then report the script's one-line summary.
   - If the script fails for any reason (exit 1, or the index was written but its one-line summary cannot be reported), record the failure reason for the "⚠️ Issues Encountered" section of `production/GRADUATION_REPORT.md` and proceed to Step 1 anyway. A failure never blocks graduation.

Proceed to Step 1.

## Step 1: Production Project Structure

If `production/` already exists, ask the bootcamper: Overwrite, Merge, or Abort. WAIT for response. If abort, stop and generate the graduation report noting the abort.

Create `production/` and copy production-relevant files:

| Source | Destination | Notes |
|--------|-------------|-------|
| `src/transform/**` | `production/src/transform/` | All transform code |
| `src/load/**` | `production/src/load/` | All loading code |
| `src/query/**` | `production/src/query/` | All query code |
| `src/utils/**` | `production/src/utils/` | Utility modules |
| `data/transformed/**` | `production/data/` | Transformed data files |
| `database/` (structure only) | `production/database/.gitkeep` | Empty placeholder |
| `requirements.txt` / `pom.xml` / `Cargo.toml` / `package.json` / `*.csproj` | `production/` | Language dependency file |

If a source directory does not exist, skip silently. If a file copy fails, log and continue.

**Exclude** (do NOT copy): `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, `data/samples/`, `data/raw/`, `src/quickstart_demo/`, `logs/`, `backups/`, `monitoring/`, `docs/feedback/`.

Present a summary of files copied, excluded, and directories created. Ask: "Does this look right? Ready to proceed to Step 2?" WAIT for confirmation.

## Step 2: Production Configuration Files

Generate the following files in `production/` using the language and database type from pre-checks:

- **`.env.production`** — Placeholder values only (no real secrets). Include: `SENZING_ENGINE_CONFIGURATION_JSON`, `SENZING_LICENSE_PATH`, `DATABASE_URL`, `LOG_LEVEL`, `API_KEY`.
- **`.env.example`** — Mirror `.env.production` with safe example values and comments.
- **`docker-compose.yml`** — Parameterized by database type: SQLite (single service + volume mount) or PostgreSQL (app + db service with health check).
- **CI/CD pipeline** — Ask bootcamper which platform (GitHub Actions default, Azure DevOps, GitLab CI). WAIT for response. Pipeline must include: Lint, Test, Build, Deploy (placeholder with manual gate).
- **`.gitignore`** — Language-appropriate. Always include: `.env.production`, `*.db`, `*.sqlite`, `__pycache__/`, `node_modules/`, `target/`, `bin/`, `obj/`, `build/`, `dist/`, `.idea/`, `.vscode/`, `*.log`.

Ask: "Configuration files generated. Ready to proceed to Step 3 (Production README)?" WAIT for confirmation.

## Step 3: Production README

Generate `production/README.md` parameterized by language, database type, and data sources. **Do not use bootcamp-specific language** — no "bootcamp", "module", "track", or "bootcamper."

Required sections: Project Overview, Prerequisites, Installation, Configuration, Usage, Project Structure, Contributing.

Show the generated README to the bootcamper for review. WAIT for confirmation or revision requests. Apply any requested changes before proceeding.

## Step 4: Migration Checklist

Generate `production/MIGRATION_CHECKLIST.md` with six sections (Database, Security, Licensing, Performance, Data, Deployment) using `- [ ]` checkboxes.

**Base items per section:**

- **Database:** Replace eval DB, configure connection pooling, set up backups, test failover, update DATABASE_URL
- **Security:** Replace placeholder secrets, configure TLS/SSL, review access controls, audit for hardcoded credentials, set up secret rotation
- **Licensing:** Obtain production license, configure SENZING_LICENSE_PATH, verify capacity
- **Performance:** Tune DB parameters, configure multi-threaded loading, set up monitoring, run load tests
- **Data:** Validate production sources, configure error handling, set up quality monitoring, document schemas
- **Deployment:** Configure CI/CD, set up staging, set up production, define rollback, configure health checks

**Conditional logic** (check `modules_completed`):

- If Modules 9–11 all completed: Add references to existing security/performance/deployment artifacts. Add: "Review packaging and deployment from Module 11 (check deployment artifacts)". Note at top: "✅ You completed the advanced topics track."
- If NOT all completed: Add ⚠️ items noting these topics were not covered. Add: "⚠️ Packaging and deployment was not covered during the bootcamp — complete these items before deploying". Note at top: "⚠️ Some production topics need extra attention."

Ask: "Migration checklist generated. Ready to proceed to Step 5 (Git initialization)?" WAIT for confirmation.

## Step 5: Git Repository Initialization (Optional)

Ask: "Would you like me to initialize a new git repository in the `production/` directory?" WAIT for response.

**If accepted:** Check `git --version`. If unavailable, inform and skip. If available, run `git init`, `git add .`, and `git commit -m "Initial production project from Senzing Bootcamp graduation"`. If any command fails, inform and continue.

**If declined:** Skip to the graduation report.

## Graduation Report

**Always generate `production/GRADUATION_REPORT.md`**, regardless of whether individual steps encountered errors.

Include: timestamp, track completed, modules finished, language, database type, files generated table, files excluded table, and next steps (fill in secrets, obtain license, work through checklist, configure CI/CD, test with production data).

**Complete Artifact Inventory:** Run `python scripts/generate_artifact_inventory.py` and embed its stdout as a "Complete Artifact Inventory" section in `GRADUATION_REPORT.md`, placed **after** the files-excluded table and **before** the next steps. Unlike the files tables (which cover only the `production/` subset), this section lists every artifact created across all completed modules, grouped by phase, each with a short why-it-matters note and a carry-forward / bootcamp-record tag. This step is **non-blocking**: if the script fails, record the failure under "⚠️ Issues Encountered" and still produce the rest of the report. Do not duplicate or contradict the files-generated/files-excluded tables.

If any step encountered errors, add a "⚠️ Issues Encountered" section listing what failed and what was skipped.

Present completion:

> 🎓 **Graduation complete!** Your production project is ready in `production/`.
>
> Check `production/GRADUATION_REPORT.md` for a full summary, and work through `production/MIGRATION_CHECKLIST.md` to prepare for deployment.
>
> Your bootcamp record also includes `docs/bootcamp_recap.md`, `docs/completion_summary.md`, and the ordered Q&A transcript at `docs/bootcamp_transcript.md`.

### Feedback Submission Reminder

Before showing the fallback feedback prompt, check for saved feedback:

1. Check conversation history for the `📋` marker. If it already appears (meaning a feedback reminder was shown during track completion earlier in this session), skip this reminder entirely and go straight to the fallback line below.
2. If no prior reminder was shown, check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists.
3. If it exists, read the file and check for at least one `## Improvement:` heading below the `## Your Feedback` section (headings outside fenced code blocks count as real entries; the template block inside a fenced code block does not).
4. If feedback entries exist, display: "📋 You have feedback saved in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. Would you like to share it with the power author?"
5. If the bootcamper accepts, present the sharing options:

   **How would you like to share your feedback?**

   1. **Email** — Send to <support@senzing.com> with subject "Senzing Bootcamp Power Feedback". I can format the content for easy copy-paste.
   2. **GitHub Issue** — Create an issue on the senzing-bootcamp power repository. I can format it as a markdown-ready issue body.
   3. **Copy path** — I'll show you the full file path so you can share it however you prefer.

   Do not automatically send emails or create GitHub issues — wait for explicit bootcamper confirmation before taking any external action.
6. If the bootcamper declines (says "no", "skip", "not now", or any declining response), proceed without re-prompting about feedback.
7. If the feedback file does not exist, contains no entries, or the reminder was already shown, fall through to the line below.

> Say "bootcamp feedback" if you'd like to share your experience.

<!-- 
  ## Export-Results Integration Contract
  
  This documents how the graduation workflow integrates with the export-results feature.
  The export script (scripts/export_results.py) should honor these conventions:
  
  1. HTML Report: When production/GRADUATION_REPORT.md exists, include its content
     as a "Graduation" section in the HTML report, rendered after the module
     completion sections.
  
  2. ZIP Archive: When the --format zip option is used and the production/ directory
     exists, include the contents of production/ under artifacts/production/ in the
     ZIP archive.
  
  3. No graduation: When the graduation workflow has not been completed (i.e.,
     production/GRADUATION_REPORT.md does not exist), do not include any
     graduation-related content in the export.
  
  This contract is informational — the export script reads these paths at runtime.
  No changes to this steering file are needed to support export integration.
-->
