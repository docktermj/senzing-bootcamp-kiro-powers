# Design Document

## Overview

This feature moves Markdown formatting out of the per-edit hot path and into a single
graduation-time normalization step. During modules the agent writes Markdown_Artifacts in whatever
natural structure suits the moment; at graduation a new `normalize_markdown.py` script rewrites each
artifact into the schema its consumer expects and applies CommonMark style fixes once, across all
files, before any Derived_Artifact (recap PDF) is generated. The existing per-save
`commonmark-validation` hook is re-scoped from `fileEdited` to `userTriggered` so its style checks
survive but no longer fire on every `.md` write.

The design has four moving parts:

1. **`normalize_markdown.py`** — a new stdlib-only script that performs the Normalization_Pass:
   schema normalization for files with a known Consumer_Schema (today: the recap) plus deterministic
   CommonMark style fixes for every targeted file.
2. **Graduation flow ordering** — `steering/graduation.md` gains an explicit normalization step that
   runs before the recap-PDF step (current Step 0), feeding the PDF generator normalized input.
3. **Hook re-scope** — `commonmark-validation.kiro.hook` changes its trigger to `userTriggered`, with
   the cascade of registry/steering/test updates that the project's hook conventions require.
4. **Content-preservation guarantees** — the normalizer never writes in place until it has a complete
   output, retains unmapped content, and warns when content cannot be mapped — paired with the
   tolerant parser/fallback delivered by `recap-pdf-content-loss-fix`.

This design depends on `recap-pdf-content-loss-fix` for the tolerant recap parser and raw-Markdown
fallback. Where the two overlap, this spec assumes that fix is in place: the normalizer's job is to
*produce* schema-conforming Markdown, and the tolerant parser is the safety net if normalization is
skipped or only partially succeeds.

## Architecture

```text
                          GRADUATION FLOW (steering/graduation.md)
   ┌──────────────────────────────────────────────────────────────────────────┐
   │  Step 0 (NEW): Markdown Normalization Pass                                  │
   │     python scripts/normalize_markdown.py                                    │
   │        ├─ for each known artifact + Consumer_Schema → schema-normalize      │
   │        ├─ for every targeted .md            → CommonMark style fix          │
   │        ├─ atomic write (temp file → replace) → never corrupt original       │
   │        └─ warn on unmapped content / skipped files (non-blocking)           │
   │                                                                             │
   │  Step 0b (was Step 0): Recap PDF Generation                                 │
   │     python scripts/generate_recap_pdf.py   ← consumes normalized recap      │
   │                                                                             │
   │  Steps 1–5 + Graduation Report (unchanged)                                  │
   └──────────────────────────────────────────────────────────────────────────┘

   HOOKS
     commonmark-validation.kiro.hook : fileEdited(**/*.md) → userTriggered
        (style checks preserved, no longer per-save)

   REUSE
     normalize_markdown.py → generate_recap_pdf.parse_recap_markdown / format_recap_document
                              (recap schema round-trip)
     validate_commonmark.py → unchanged CI validator (markdownlint-cli)
```

### Why a new script rather than extending `validate_commonmark.py`

`validate_commonmark.py` is not a reusable style-fix library: it shells out to `markdownlint-cli`
(an npm tool that may be absent), takes no arguments, and exits via `sys.exit`. The actual CommonMark
*fixes* today are performed by the agent following the `commonmark-validation` hook's `askAgent`
prompt. To run a deterministic, offline normalization pass we add `normalize_markdown.py`, which
implements the same small set of style rules as stdlib text transforms (no npm dependency) and reuses
the recap parser/formatter for structural normalization. `validate_commonmark.py` stays as-is for CI
(it validates; it does not fix).

## Components and Interfaces

### `senzing-bootcamp/scripts/normalize_markdown.py`

Follows the project script pattern: `#!/usr/bin/env python3`, `from __future__ import annotations`,
stdlib-only, `main(argv=None)`, argparse, exit 0 on success / 1 on error.

```python
@dataclass
class NormalizationResult:
    path: str
    changed: bool          # output differs from input
    schema_applied: bool   # a Consumer_Schema was matched and applied
    warnings: list[str]    # unmapped content / skipped reasons
    error: str | None      # set when this file failed (flow continues)

# --- Consumer-schema registry -------------------------------------------------
# Maps a target path to the function that rewrites it to its Consumer_Schema.
# Adding a new schema = adding one entry; files not listed are style-only.
SCHEMA_NORMALIZERS: dict[str, Callable[[str], tuple[str, list[str]]]]
# e.g. {"docs/bootcamp_recap.md": normalize_recap}

def normalize_recap(content: str) -> tuple[str, list[str]]:
    """Round-trip the recap through the PDF generator's schema.

    Reuses generate_recap_pdf.parse_recap_markdown + format_recap_document so the
    output matches exactly what the PDF parser expects. Any content the parser
    cannot place (prose/extra headings) is retained verbatim and reported as a
    warning rather than dropped.
    """

def apply_commonmark_fixes(content: str) -> str:
    """Deterministic stdlib style fixes mirroring the hook prompt:
    MD022 (blank lines around headings), MD031 (blank lines around fenced code),
    MD032 (blank lines around lists), MD040 (language on fenced code, default 'text'),
    and bold-label colon spacing (**Label:**). CHANGELOG.md keeps the MD024 exception
    (duplicate headings allowed)."""

def normalize_file(path: str) -> NormalizationResult:
    """Read → (schema-normalize if registered) → style-fix → atomic write.
    On any exception: return a result with error set; never raise to the caller."""

def normalize_paths(paths: Iterable[str]) -> list[NormalizationResult]: ...

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    # --paths / positional files (default: known artifacts that exist)
    # --dir  (normalize all *.md under a directory)
    # --check (report only; exit 1 if any file would change — for CI use)

def main(argv: list[str] | None = None) -> int: ...
```

**Default target set** (only those that exist are processed): `docs/bootcamp_recap.md`,
`docs/bootcamp_journal.md`, mapper docs under `docs/`, and other `docs/*.md` artifacts. The recap is
the only entry in `SCHEMA_NORMALIZERS` for v1; everything else is style-only (Requirement 2.4).

**Atomic write** (Requirement 3.5): write the normalized text to a sibling temp file in the same
directory, then `os.replace()` over the original. If the process dies mid-write, the original is
untouched.

**Warnings** (Requirements 3.4, 2.5): collected per file and printed to stderr; a non-empty
`error`/`warnings` set never aborts the run. `main` returns 0 even when individual files warn; it
returns 1 only for argument/usage errors so the graduation step stays non-blocking.

### Graduation flow change — `senzing-bootcamp/steering/graduation.md`

Insert a new **Step 0: Markdown Normalization Pass** before the existing recap-PDF step (which becomes
Step 0b), described as:

- Run `python scripts/normalize_markdown.py` over the known Markdown_Artifacts.
- Non-blocking: report a one-line summary of files normalized and any warnings; on failure, log and
  continue (consistent with the existing recap-PDF and `GRADUATION_REPORT.md` non-blocking spirit).
- Then proceed to recap-PDF generation, which now consumes the normalized `docs/bootcamp_recap.md`.

The in-module authoring guidance (the steering that tells the agent how to write recap/journal/mapper
docs during modules) is updated to state: write Markdown free-form during the bootcamp; structural
formatting happens once at graduation (Requirements 1.3, 7.2).

### Hook re-scope — `senzing-bootcamp/hooks/commonmark-validation.kiro.hook`

Change `when.type` from `fileEdited` (patterns `**/*.md`) to `userTriggered`. The `then.askAgent`
prompt is preserved (same MD022/MD031/MD032/MD040 + bold-label-colon checks and the CHANGELOG MD024
exception) but re-framed to validate all Markdown in one pass when manually triggered or invoked by
the graduation normalization step. The hook `name` MUST continue to start with `"to "` to satisfy the
governance regex (`"name":\s*"to\s"`), e.g. `"to check Markdown style"` is retained.

Because hook metadata is tracked in several places, the re-scope cascades to:

| Artifact | Change |
|---|---|
| `hooks/commonmark-validation.kiro.hook` | `when.type` → `userTriggered`; bump `version` to `2.0.0` |
| `hooks/hooks.lock.yaml` | regenerate via `sync_hook_registry.py --write` (event_type/version) |
| `hooks/hook-categories.yaml` | unchanged (stays in `critical`) unless category policy requires otherwise |
| `steering/hook-registry.md`, `steering/hook-registry-critical.md` | update the `fileEdited → askAgent` descriptor to `userTriggered → askAgent` |
| `steering/onboarding-flow.md` | update the disabled-hook description wording |
| `scripts/install_hooks.py` | update description string if it encodes the trigger |
| `POWER.md` generated hooks block | regenerate via `generate_power_docs.py` if it records the trigger |
| `docs/guides/ARCHITECTURE.md`, `hooks/README.md` | update the trigger description |

`sync_hook_registry.py --verify` and `validate_governance_rules.py` must pass after the change.

## Data Models

No new persistent data model. The normalizer operates on Markdown text and the existing recap data
model (`RecapHeader` / `RecapSection` / `RecapDocument` from `generate_recap_pdf.py`). The only new
in-memory type is `NormalizationResult` (above), used for reporting.

## Error Handling

| Condition | Handling |
|---|---|
| A targeted file does not exist | Skip silently; not an error (Requirement 2 default set) |
| Schema normalization raises | Catch per-file; keep original, record `error`, warn, continue (2.5, 3.5) |
| Content cannot be mapped to schema | Retain unmapped content verbatim; add a warning (3.2, 3.4) |
| `os.replace` fails | Record `error`, leave original intact, continue |
| `markdownlint-cli` absent | Irrelevant — normalizer uses stdlib fixes, not markdownlint |
| Normalization skipped/failed for recap | Recap-PDF still runs against original via tolerant parser/fallback (5.3) |

The Normalization_Pass is non-blocking by contract: graduation always proceeds to recap-PDF and the
graduation report regardless of normalizer outcomes.

## Testing Strategy

Tests live in `senzing-bootcamp/tests/` (pytest + Hypothesis), class-based, importing the script via
the documented `sys.path` pattern.

### Unit / example tests

- `normalize_recap` turns a free-form recap (`## Module 1: Business Problem`, prose, no timestamp) into
  schema-conforming Markdown that `parse_recap_markdown` parses into the expected sections.
- A file with no registered Consumer_Schema is style-normalized only and keeps all content.
- Unmappable content produces a warning and is retained in the output (asserted present).
- Atomic write: a simulated failure during write leaves the original file byte-identical.
- Re-scoped hook: load `commonmark-validation.kiro.hook`, assert `when.type == "userTriggered"`, assert
  it is NOT `fileEdited` on `**/*.md`, assert `name` matches `^to `, and assert it is a valid hook
  (`name`/`version`/`when`/`then` present) and present in `hooks.lock.yaml` with the matching
  event_type.
- A normalized recap renders a non-empty PDF body (ties to `recap-pdf-content-loss-fix`).

### Property-based tests

**Property 1 — Content preservation.** *For all* generated free-form Markdown inputs (headings, prose
paragraphs, bullet lists, fenced code blocks in any order), the set of substantive content tokens
(heading texts, list-item texts, code-block bodies, paragraph texts) in `normalize_file` output is a
superset of the input's — nothing is dropped. *Validates Requirements 3.1, 3.2.*

**Property 2 — Idempotence.** *For all* inputs, `apply_commonmark_fixes(apply_commonmark_fixes(x)) ==
apply_commonmark_fixes(x)` and normalizing an already-normalized file reports `changed == False`.
*Validates Requirement 2 (stable output) and guards against churn.*

**Property 3 — Recap round-trip conformance.** *For all* valid `RecapDocument` values, formatting to
Markdown, perturbing headings into free-form, then `normalize_recap` yields Markdown that
`parse_recap_markdown` parses back to an equivalent `RecapDocument` (section identity, list contents,
Q&A pairing, durations preserved). *Validates Requirements 2.3, 5.2.*

## Correctness Properties

These are the invariants the implementation must uphold; each is exercised by a property-based test
(see Testing Strategy).

### Property 1: Content preservation (no silent loss)

*For all* free-form Markdown inputs, every substantive content token (heading text, list-item text,
fenced-code body, paragraph text) present in the input is present in `normalize_file` output.
Normalization may reorder or restructure, but never drops content.

**Validates: Requirements 3.1, 3.2**

### Property 2: Idempotence / stability

*For all* inputs, `apply_commonmark_fixes(apply_commonmark_fixes(x)) == apply_commonmark_fixes(x)`,
and re-normalizing an already-normalized file reports `changed == False`. Running the pass twice is a
no-op the second time.

**Validates: Requirements 2.3, 2.4**

### Property 3: Recap round-trip conformance

*For all* valid `RecapDocument` values, taking `format_recap_document`, perturbing its headings into
free-form shape, then `normalize_recap` produces Markdown that `parse_recap_markdown` parses back into
an equivalent `RecapDocument` — section identity, list contents, Q&A pairing, and durations preserved.

**Validates: Requirements 2.3, 5.2**

### Property 4: Non-blocking pass

*For all* target file sets (including files that raise during normalization), `main` returns 0 and
every original file is either successfully replaced with a complete normalized output or left
byte-identical — never partially written.

**Validates: Requirements 2.5, 3.5**

## Requirements Traceability

| Requirement | Design element |
|---|---|
| 1 (free-form during modules) | Authoring-guidance steering update; no per-edit schema gate |
| 2 (graduation normalization pass) | New Step 0 in `graduation.md`; `normalize_markdown.py`; non-blocking contract |
| 3 (content preservation) | Atomic write, retain-unmapped, warnings; Properties 1 & 3 |
| 4 (re-scope hook) | Hook `userTriggered` change + registry/steering/test cascade |
| 5 (derived artifacts from normalized files) | Step ordering; recap-PDF consumes normalized input; fallback path |
| 6 (normalizer script & conventions) | `normalize_markdown.py` interface; reuse of recap parser; schema docs |
| 7 (steering & docs) | `graduation.md`, authoring guidance, `steering-index.yaml`, cross-ref note |
| 8 (test coverage) | Unit tests + Properties 1–3 + hook validity test + PDF-body test |
```
