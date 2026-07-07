# Design Document

## Overview

This feature turns the bootcamp's three crown-jewel deliverables — the Q&A transcript
(`docs/bootcamp_transcript.md`), the recap (`docs/bootcamp_recap.md`), and a rendered recap
document (`docs/bootcamp_recap.pdf` or its HTML fallback) — from best-effort, silently-skippable
outputs into an **enforced completion invariant**. Today each artifact is produced by a chain of
non-blocking steering steps and bundled scripts; when a bundled script is absent, when `fpdf2`
is missing, or when a hook misses, the deliverable is silently dropped with only a warning.

The design closes that gap with three coordinated changes that **extend existing machinery
rather than replace it**:

1. A single self-contained orchestrator script, `ensure_graduation_artifacts.py`, that guarantees
   all three artifacts exist and are non-empty at any stopping point — reconstructing each from
   always-present sources, reusing the existing reconcile/backfill/render helpers, and only
   regenerating when an artifact is absent, empty, or stale (idempotent otherwise).
2. Two small generation gaps filled: (a) the transcript renderer gains an "ensure" mode that
   always writes a non-empty transcript (including a "no Q&A history" record when no source data
   exists), and (b) a new stdlib-only HTML renderer (`recap_html_render.py`) produces a shareable
   `docs/bootcamp_recap.html` when `fpdf2` is unavailable.
3. A new `agentStop` enforcement hook, `enforce-critical-artifacts`, that runs the orchestrator at
   track-completion/graduation stopping points and **blocks the "done" state** until all three
   artifacts exist and are non-empty — the same enforcement pattern as `enforce-gate-on-stop`.

A mandatory post-graduation announcement step is added to `graduation.md` so the bootcamper is
always told the recap exists, where it is, and what it contains.

### Goals

- Guarantee the transcript, recap Markdown, and a rendered recap document are always present and
  non-empty at every stopping point (Requirements 1, 3, 4).
- Enforce this as a hard invariant that blocks completion, not a warning (Requirement 2).
- Keep generation self-contained: stdlib-only, `fpdf2` optional/lazy, no dependency on any bundled
  generation script being materialized (Requirement 6).
- Announce the recap to the bootcamper as a mandatory closing step (Requirement 5).

### Non-Goals

- Changing how per-module recap sections are captured during modules (the `module-recap-append`
  hook and `qa-transcript.md` event emission are unchanged).
- Introducing a full Markdown-to-HTML/PDF engine; rendering reuses the existing block-oriented
  renderer and a minimal HTML serializer.
- Adding any per-write hook or per-write process spawn (the `qa-transcript.md` decoupling is
  preserved).

## Architecture

### Where this fits in the existing flow

Track completion (`module-completion-track.md`) and graduation (`graduation.md`) already run a
reconcile-then-render sequence for the recap and transcript, but every step is explicitly
non-blocking. This feature adds an enforcement layer *on top of* that sequence:

```
                          agentStop
                              |
        +---------------------+---------------------+
        |  existing agentStop hooks (unchanged)     |
        |  ask-bootcamper -> module-recap-append -> |
        |  celebration -> enforce-gate-on-stop -> ..|
        +---------------------+---------------------+
                              |
                 enforce-critical-artifacts (NEW, agentStop)
                              |  (only at a stopping point)
                              v
              python scripts/ensure_graduation_artifacts.py
                              |
          +-------------------+-----------------------+
          v                   v                       v
   Transcript guarantee  Recap guarantee        Rendered-recap guarantee
   (reconcile + render   (completion_artifacts  (PDF via existing chain,
    + ensure-nonempty)    --backfill)            else HTML fallback)
          |                   |                       |
          +-------------------+-----------------------+
                              v
                     GuaranteeReport (JSON)
                              |
             all present & non-empty? --no--> BLOCK "done", name missing
                              |yes
                              v
                    silent (already valid)
```

At graduation, the same orchestrator is invoked by the graduation workflow, and a mandatory
closing announcement (Requirement 5) reports the recap to the bootcamper.

### Idempotence and staleness (Requirements 2.5, 2.6)

The orchestrator never blindly regenerates. For each artifact it computes whether the artifact is
**absent**, **empty**, or **stale**, where *stale* means the artifact's last-modified time is
earlier than the newest last-modified time among its source inputs (Requirement 2.2). Only then
does it regenerate (at most once per artifact per run, Requirement 2.3). An artifact that is
present, non-empty, and not stale is left untouched, so re-running at repeated stopping points is
a no-op that leaves already-valid artifacts byte-for-byte unchanged.

Source-input mapping used for staleness:

| Artifact | Source inputs |
|---|---|
| `docs/bootcamp_transcript.md` | `config/session_log.jsonl`, `docs/bootcamp_recap.md` |
| `docs/bootcamp_recap.md` | `config/bootcamp_progress.json`, per-module artifacts under `docs/progress/` |
| Rendered recap (`.pdf`/`.html`) | `docs/bootcamp_recap.md` |

Because the transcript render writes a fresh `Generated at` timestamp on every run, unconditional
regeneration would break byte-for-byte idempotence; the staleness gate is what preserves it.

### Self-containment (Requirement 6)

The orchestrator imports the existing sibling modules by the documented `sys.path` insert pattern
(`completion_artifacts`, `reconcile_transcript`, `generate_transcript`, `generate_recap_pdf`,
`generate_recap_pdf_inline`, `recap_pdf_render`, and the new `recap_html_render`). All logic is
reachable without any bundled *generation* script being present, because the reconstruction paths
(recap backfill from progress, transcript reconstruction from recap Q&R pairs, HTML render from
recap Markdown) live in scripts that ship with the power and use only stdlib (plus lazy `fpdf`).
When a source is genuinely absent, the orchestrator degrades to the documented placeholder /
error path rather than skipping.

## Components and Interfaces

### 1. `scripts/ensure_graduation_artifacts.py` (NEW) — Guarantee orchestrator

Self-contained, stdlib-only entry point that guarantees the three artifacts. It is the single
thing the enforcement hook and the graduation/track-completion steering invoke.

```python
GUARANTEED_ARTIFACTS = ("transcript", "recap_md", "rendered_recap")

@dataclass
class ArtifactStatus:
    key: str                 # "transcript" | "recap_md" | "rendered_recap"
    path: str                # resolved output path (rendered_recap = .pdf or .html)
    exists: bool
    non_empty: bool
    regenerated: bool        # True if this run (re)generated it
    error: str | None        # non-None when regeneration failed

@dataclass
class GuaranteeReport:
    artifacts: list[ArtifactStatus]
    @property
    def all_satisfied(self) -> bool: ...   # every artifact exists and is non_empty
    @property
    def missing(self) -> list[str]: ...    # keys of artifacts not satisfied

def is_stale(artifact: Path, sources: list[Path]) -> bool: ...
def is_non_empty(path: Path, *, min_body: bool = False) -> bool: ...

def ensure_transcript(log, recap, output) -> ArtifactStatus: ...
def ensure_recap_md(progress, recap, journal, progress_dir) -> ArtifactStatus: ...
def ensure_rendered_recap(recap, pdf_out, html_out) -> ArtifactStatus: ...

def ensure_all(paths: ArtifactPaths) -> GuaranteeReport: ...

def main(argv: list[str] | None = None) -> int: ...
```

CLI:

- `python scripts/ensure_graduation_artifacts.py` — ensure/regenerate as needed; prints a
  human-readable summary; exit 0 when all satisfied, 1 when any artifact could not be produced.
- `--check` — verify only (no regeneration); exit 1 naming missing artifacts. Used to confirm the
  invariant without side effects.
- `--json` — emit the `GuaranteeReport` as JSON (consumed by the hook prompt and tests).
- Path overrides: `--log`, `--recap`, `--transcript`, `--progress`, `--journal`, `--progress-dir`,
  `--pdf`, `--html` (canonical defaults matching the existing scripts).

Behavior per artifact:

- **`ensure_transcript`** (Req 1): if the transcript is present, non-empty, and not stale -> no-op.
  Otherwise run `reconcile_transcript.main()` (backfills the log from recap Q&R pairs), then render
  via `generate_transcript` in *ensure* mode so a non-empty transcript is always written — a normal
  transcript when Q&A pairs exist, or a "no Q&A history was available" record when none do
  (Req 1.7/1.8). On any failure, leave an existing transcript unchanged and record the error
  (Req 1.9).
- **`ensure_recap_md`** (Req 3): if present, non-empty (has >=1 `## Module N` section), and not
  stale -> no-op. Otherwise run `completion_artifacts.backfill_recap_sections()` to reconstruct
  from `bootcamp_progress.json` + module artifacts, preserving existing bytes. If progress and all
  module artifacts are absent/unreadable, leave any existing recap unchanged and record the error
  (Req 3.3).
- **`ensure_rendered_recap`** (Req 4): only when `docs/bootcamp_recap.md` is non-empty. Attempt the
  existing PDF chain (`generate_recap_pdf` -> `generate_recap_pdf_inline`). If `fpdf2` is available
  and a PDF is written -> `rendered_recap = docs/bootcamp_recap.pdf`. If `fpdf2` is unavailable, or a
  PDF path reports the missing dependency, or PDF generation fails, render
  `docs/bootcamp_recap.html` via the new `recap_html_render` and set `rendered_recap` to it
  (Req 4.3, 4.8, 2.7). Emit the exact `pip install fpdf2` hint to stdout when falling back
  (Req 4.4). If the recap source is absent/empty, produce no rendered recap and emit the
  source-unavailable error (Req 4.7).

### 2. `scripts/generate_transcript.py` (MODIFY) — add ensure mode

Add an `--ensure` flag (default off, preserving current behavior and existing tests). When
`--ensure` is set and there are no Q&A events, instead of writing nothing, write a non-empty
transcript containing the metadata header plus an explicit record that no Q&A history was
available (Req 1.7, 1.8). The existing full-overwrite render is unchanged for the has-events case.
A new pure helper `render_empty_transcript(generated_at) -> str` produces the placeholder document
so it is unit-testable without touching the filesystem.

```python
def render_empty_transcript(generated_at: str) -> str: ...   # NEW, non-empty placeholder
# main() gains: parser.add_argument("--ensure", action="store_true")
```

### 3. `scripts/recap_html_render.py` (NEW) — stdlib HTML fallback renderer

The HTML analogue of `recap_pdf_render.py`, with **no `fpdf` dependency at all** (pure stdlib), so
a shareable rendered recap is always producible when `fpdf2` is absent (Req 4.3). It reuses the
block model already established in `recap_pdf_render` (`split_blocks`, the QR schema literals) and
serializes each block to safe HTML via `html.escape`.

```python
def render_markdown_html(body_text: str, output_path: str, *, title: str = "Bootcamp Recap") -> None:
    """Render recap Markdown to a self-contained HTML document (stdlib only)."""

def markdown_to_html_body(body_text: str) -> str:  # block -> <h2>/<p>/<ul>/<pre> serialization
    ...
```

The output is a single self-contained `.html` file (inline `<style>`, no external URLs) whose body
reflects every per-module section present in the source recap (Req 4.6). It never imports `fpdf`.

### 4. `hooks/enforce-critical-artifacts.kiro.hook` (NEW) — enforcement gate

An `agentStop` hook (`then.type: askAgent`) modeled on `enforce-gate-on-stop.kiro.hook`. Its prompt:

1. Defer entirely if `config/.question_pending` exists (defer to `ask-bootcamper`), matching the
   convention of every other `agentStop` hook.
2. **Stopping-point detection.** Read `config/bootcamp_progress.json`. Only proceed when a
   stopping point is reached: the bootcamper's track end appears in `modules_completed`
   (Module 7 for Core, Module 11 for Advanced) or the graduation workflow has completed. If not a
   stopping point, produce no output.
3. **Ensure + verify.** Run
   `python senzing-bootcamp/scripts/ensure_graduation_artifacts.py --json` and parse the report.
   The orchestrator regenerates any absent/empty/stale artifact from always-present sources
   (Req 2.2, 2.4).
4. **Block on failure.** If the report's `all_satisfied` is false, output a blocking message
   prefixed with the mandatory-gate marker, naming each missing/empty artifact by identity and
   instructing that "done" must not be reported until they exist (Req 2.3). This mirrors the
   `MANDATORY GATE VIOLATION` wording of the existing gate hooks.
5. **Silent when satisfied.** When all three artifacts are present and non-empty, produce no
   output (the invariant holds; regeneration of already-valid artifacts was a no-op).

The hook contains no unescaped user input (security steering): it invokes a fixed script and reads
machine state only.

### 5. Steering updates

- **`steering/graduation.md`** — Add a mandatory closing step (after the existing Step 0b and the
  graduation steps) that runs `ensure_graduation_artifacts.py` as the enforced guarantee and then
  performs the **mandatory post-graduation announcement** (Req 5): state that the recap exists, its
  path (`docs/bootcamp_recap.md`) and the rendered-recap path (`.pdf` when `fpdf2` is available,
  otherwise `.html`), and summarize that it contains, per module, Information Shared, Questions &
  Responses, and Actions Taken. The announcement runs exactly once, reports only artifacts
  confirmed to exist, and triggers regeneration first if any are missing (Req 5.4, 5.5, 5.6).
- **`steering/module-completion-track.md`** — Note that the always-run recap PDF / transcript
  renders are now backed by the enforced guarantee (`ensure_graduation_artifacts.py`), and that the
  HTML fallback is produced when `fpdf2` is absent. The reconcile-then-render ordering and
  non-blocking-of-the-celebration behavior are preserved; the enforcement gate is what makes the
  deliverables guaranteed.
- **`steering/qa-transcript.md`** — unchanged (event emission stays decoupled from writes); a short
  cross-reference notes the transcript is now guaranteed at stopping points via reconstruction.

### 6. Hook registry wiring (Requirement 6.4)

Registering the new hook requires, per the established process:

1. `hooks/enforce-critical-artifacts.kiro.hook` (the JSON file above).
2. Add `enforce-critical-artifacts` under the `any` bucket in `hooks/hook-categories.yaml` and an
   `agentstop_order` entry. Ordering rationale: it must run **after** `module-recap-append`
   (so the recap section exists to reconstruct/verify from) and after the celebration/gate hooks;
   place it at the end of the `agentstop_order` list (lowest precedence for output, highest step
   number) so its blocking output only appears once higher-priority gate output is clear and the
   recap capture has run.
3. Run `python3 scripts/sync_hook_registry.py --write` to regenerate `hooks/hooks.lock.yaml`,
   `steering/hook-registry.md`, `steering/hook-registry-critical.md`, and the per-module registry
   slices. CI runs `sync_hook_registry.py --verify`, so this must be in sync.

## Data Models

### `ArtifactPaths`

Resolved, overridable canonical paths, defaulting to the values already used across the codebase:

```python
@dataclass
class ArtifactPaths:
    log: str = "config/session_log.jsonl"
    recap: str = "docs/bootcamp_recap.md"
    transcript: str = "docs/bootcamp_transcript.md"
    progress: str = "config/bootcamp_progress.json"
    journal: str = "docs/bootcamp_journal.md"
    progress_dir: str = "docs/progress"
    pdf: str = "docs/bootcamp_recap.pdf"
    html: str = "docs/bootcamp_recap.html"
```

### `GuaranteeReport` JSON shape (hook/test contract)

```json
{
  "all_satisfied": false,
  "missing": ["rendered_recap"],
  "artifacts": [
    {"key": "transcript", "path": "docs/bootcamp_transcript.md",
     "exists": true, "non_empty": true, "regenerated": false, "error": null},
    {"key": "recap_md", "path": "docs/bootcamp_recap.md",
     "exists": true, "non_empty": true, "regenerated": true, "error": null},
    {"key": "rendered_recap", "path": "docs/bootcamp_recap.html",
     "exists": false, "non_empty": false, "regenerated": false,
     "error": "recap source unavailable"}
  ]
}
```

`non_empty` uses the requirements' definition: for the recap it additionally requires at least one
`## Module N` section; for the rendered PDF it reuses `recap_pdf_render.MIN_BODY_LINES` round-trip
verification.

## Error Handling

| Condition | Handling | Requirement |
|---|---|---|
| Transcript render/reconstruct fails | Leave existing transcript unchanged; record `error`; do not partial-overwrite | 1.9 |
| No Q&A source data at all | Write non-empty "no Q&A history was available" transcript | 1.7, 1.8 |
| Recap progress + all module artifacts absent/unreadable | Leave existing recap unchanged; record source-unavailable `error` | 3.3 |
| `fpdf2` unavailable | Render HTML fallback; emit exact `pip install fpdf2` hint to stdout | 4.3, 4.4 |
| `fpdf2` present but PDF render fails | Render HTML fallback; emit "PDF failed, HTML produced" to stdout | 4.8 |
| Recap source absent/empty when rendering | Produce no rendered recap; emit source-unavailable error to stdout | 4.7 |
| Any required source missing during generation | Stop that artifact, record error identifying source, preserve other artifacts | 6.3 |
| `fpdf2` absent generally | Still generate all Markdown artifacts; skip only PDF; no unhandled exception | 6.4 |
| Artifact still missing after one regeneration attempt | Hook blocks "done", retains valid artifacts, names missing ones | 2.3, 2.4 |

The orchestrator itself never raises out of `main()` for a per-artifact failure: it records the
error in the report and returns exit 1 so the *hook* — not an unhandled traceback — is what blocks
completion. Secrets/PII are excluded from all generated content by reusing the existing
`redact_secrets` (transcript) and the recap hook's no-secrets contract (Req 6.5, 6.7).

## Correctness Properties

These properties are the invariants the property-based tests quantify over. Each names the
requirement(s) it protects.

### Property 1: Guaranteed presence

For any synthetic workspace where an artifact's sources exist, after `ensure_all` that artifact
exists and is non-empty (transcript, recap Markdown, and a rendered recap). When no Q&A source
exists, the transcript still exists and is non-empty (the "no Q&A history" record).

**Validates: Requirements 1.1, 1.7, 1.8, 3.1, 4.1**

### Property 2: Idempotence / no-op on valid input

Running `ensure_all` on a workspace whose artifacts are already present, non-empty, and not stale
changes no file bytes; a second consecutive run is a no-op.

**Validates: Requirements 2.5, 2.6**

### Property 3: Regeneration only when needed, at most once

An artifact is regenerated exactly when it is absent, empty, or stale (its mtime precedes the
newest source mtime), and never more than once per artifact per run.

**Validates: Requirements 2.2, 2.3**

### Property 4: `--check` is side-effect free

The `--check` path never creates, modifies, or deletes any file, and its exit code is 0 iff every
artifact is already satisfied.

**Validates: Requirements 2.1**

### Property 5: Rendered-recap selection

Given a non-empty recap: when `fpdf2` is available the rendered recap is the PDF; when `fpdf2` is
unavailable (or PDF rendering fails) the rendered recap is a non-empty HTML document, and that HTML
satisfies the rendered-recap invariant.

**Validates: Requirements 4.2, 4.3, 4.8, 2.7**

### Property 6: Failure isolation

A failure generating one artifact records an error for that artifact, leaves any pre-existing copy
of it unchanged, and never suppresses generation of the other artifacts.

**Validates: Requirements 1.9, 3.3, 6.3**

### Property 7: Enforcement completeness

`GuaranteeReport.all_satisfied` is true iff all three artifacts exist and are non-empty; when
false, `missing` names every unsatisfied artifact — the exact set the enforcement hook blocks on.

**Validates: Requirements 2.1, 2.3**

### Property 8: Self-containment

Every artifact is producible using only the standard library, with `fpdf` imported lazily and never
at module top level; importing `recap_html_render` never requires `fpdf`.

**Validates: Requirements 6.1, 4.5**

## Testing Strategy

Tests follow the project's pytest + Hypothesis conventions (class-based, `sys.path` import of
scripts, `st_`-prefixed strategies, profile-driven example counts, `Validates: Requirements X.Y`
docstrings). New/updated test modules under `senzing-bootcamp/tests/`:

- `test_ensure_graduation_artifacts_unit.py` — unit tests for `is_stale`, `is_non_empty`,
  `ensure_transcript`/`ensure_recap_md`/`ensure_rendered_recap` against temp dirs covering: all
  artifacts already valid (no-op), each artifact absent/empty/stale (regenerated), and each error
  path leaving prior artifacts intact.
- `test_ensure_graduation_artifacts_properties.py` — properties over synthetic workspaces:
  (1) after `ensure_all`, every artifact whose sources exist is present and non-empty (Req 1,3,4);
  (2) re-running `ensure_all` on an already-valid workspace changes no file bytes (idempotence,
  Req 2.5, 2.6); (3) `--check` never writes; (4) at most one regeneration per artifact per run
  (Req 2.3).
- `test_transcript_ensure_mode.py` — `--ensure` writes a non-empty placeholder when no events;
  default mode still writes nothing (backward compat); `render_empty_transcript` is non-empty and
  contains the "no Q&A history" record (Req 1.7, 1.8).
- `test_recap_html_render.py` — HTML output is non-empty, self-contained (no external URLs),
  imports without `fpdf`, escapes content, and includes every `## Module N` section from the source
  (Req 4.3, 4.5, 4.6).
- `test_enforce_critical_artifacts_hook.py` — validates the hook JSON schema
  (`name`/`version`/`when.type == agentStop`/`then.type == askAgent`), the `.question_pending`
  deferral clause, the stopping-point gate, and that the prompt blocks with the mandatory-gate
  marker naming missing artifacts (Req 2.1, 2.3, 2.6, 2.7).
- `test_enforce_critical_artifacts_registry.py` — the hook is registered in
  `hook-categories.yaml` (`any` bucket + `agentstop_order`) and `hooks.lock.yaml` is in sync
  (mirrors existing registry-preservation tests) (Req 6.4).
- Extend `test_track_completion_pdf_transcript.py` / graduation steering tests to assert the
  mandatory closing announcement is present and names the recap path and contents (Req 5).

All new scripts are validated by the existing CI gate (`validate_power.py`, `measure_steering.py
--check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest).
