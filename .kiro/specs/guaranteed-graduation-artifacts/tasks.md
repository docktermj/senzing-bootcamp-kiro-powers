# Implementation Plan

## Overview

This plan implements the guaranteed-graduation-artifacts feature by extending existing bootcamp
machinery: a stdlib-only HTML fallback renderer, an "ensure" mode for the transcript renderer, a
self-contained guarantee orchestrator (`ensure_graduation_artifacts.py`), a new `agentStop`
enforcement hook that blocks completion until the three artifacts exist and are non-empty, and
steering updates for the mandatory post-graduation announcement. Tasks are ordered so leaf
generators land first, then the orchestrator that composes them, then the enforcement hook and
steering that invoke it.

## Tasks

- [x] 1. Add the stdlib-only HTML fallback renderer
- [x] 1.1 Create `senzing-bootcamp/scripts/recap_html_render.py`
  - Implement `markdown_to_html_body(body_text)` reusing `recap_pdf_render.split_blocks` and the QR schema literals, serializing headings/prose/lists/code blocks to HTML with `html.escape`.
  - Implement `render_markdown_html(body_text, output_path, *, title="Bootcamp Recap")` writing a single self-contained `.html` (inline `<style>`, no external URLs).
  - Follow python-conventions: shebang, `from __future__ import annotations`, stdlib only, no top-level `fpdf` import, `main(argv=None)` argparse CLI with `--input`/`--output`, exit 0/1.
  - _Requirements: 4.3, 4.5, 4.6, 6.1_
- [x] 1.2 Write `senzing-bootcamp/tests/test_recap_html_render.py`
  - Assert output is non-empty, contains every `## Module N` section from the source, escapes HTML-special characters, contains no external URLs, and that the module imports without `fpdf` installed.
  - _Requirements: 4.3, 4.5, 4.6_

- [x] 2. Add "ensure" mode to the transcript renderer
- [x] 2.1 Extend `senzing-bootcamp/scripts/generate_transcript.py`
  - Add pure helper `render_empty_transcript(generated_at)` returning a non-empty document with the metadata header plus an explicit "no Q&A history was available" record.
  - Add `--ensure` flag; when set and there are no Q&A events, write `render_empty_transcript(...)` instead of writing nothing. Preserve default behavior (writes nothing on no events) when `--ensure` is absent.
  - On write/reconstruct failure leave any existing transcript unchanged (no partial overwrite).
  - _Requirements: 1.7, 1.8, 1.9_
- [x] 2.2 Write `senzing-bootcamp/tests/test_transcript_ensure_mode.py`
  - `--ensure` with an empty/absent log writes a non-empty placeholder transcript; default mode still writes nothing (backward compat); `render_empty_transcript` output is non-empty and contains the "no Q&A history" record.
  - _Requirements: 1.7, 1.8_

- [x] 3. Build the guarantee orchestrator
- [x] 3.1 Create `senzing-bootcamp/scripts/ensure_graduation_artifacts.py` core model and helpers
  - Define `ArtifactPaths`, `ArtifactStatus`, `GuaranteeReport` (with `all_satisfied`/`missing`) dataclasses.
  - Implement `is_non_empty(path, *, min_body=False)` (recap variant requires at least one `## Module N` section; PDF variant reuses `recap_pdf_render` round-trip verification) and `is_stale(artifact, sources)` (mtime vs newest source mtime).
  - Import sibling modules via the documented `sys.path` insert pattern.
  - _Requirements: 2.2, 6.1_
- [x] 3.2 Implement `ensure_transcript`
  - No-op when transcript is present, non-empty, and not stale (sources: `session_log.jsonl`, `recap.md`).
  - Otherwise run `reconcile_transcript.main()` then render via `generate_transcript` in `--ensure` mode; record error and preserve existing transcript on failure.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_
- [x] 3.3 Implement `ensure_recap_md`
  - No-op when recap is present, non-empty (at least one `## Module N`), and not stale (sources: `bootcamp_progress.json`, `docs/progress/`).
  - Otherwise reconstruct via `completion_artifacts.backfill_recap_sections()`; when progress and all module artifacts are absent/unreadable, leave existing recap unchanged and record source-unavailable error.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_
- [x] 3.4 Implement `ensure_rendered_recap`
  - Only when `recap.md` is non-empty. Attempt PDF chain (`generate_recap_pdf` then `generate_recap_pdf_inline`); on `fpdf2` available + PDF written set `rendered_recap` to the `.pdf`.
  - On `fpdf2` unavailable or PDF failure, render `.html` via `recap_html_render`; emit exact `pip install fpdf2` hint (and PDF-failed note) to stdout; set `rendered_recap` to the `.html`.
  - When recap source is absent/empty, produce no rendered recap and emit source-unavailable error.
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 6.4_
- [x] 3.5 Implement `ensure_all` and the CLI `main`
  - `ensure_all(paths)` runs the three ensure functions (each regenerating at most once), builds `GuaranteeReport`; failures in one artifact never suppress the others.
  - CLI: default ensure/regenerate (exit 0 when satisfied, 1 otherwise), `--check` (no side effects, exit 1 naming missing), `--json` (emit report), plus path overrides. `main` never raises for a per-artifact failure.
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 6.3, 6.5, 6.7_
- [x] 3.6 Write `senzing-bootcamp/tests/test_ensure_graduation_artifacts_unit.py`
  - Cover no-op-when-valid, absent/empty/stale regeneration per artifact, `--check` side-effect-free, and each error path preserving prior artifacts.
  - _Requirements: 2.1, 2.2, 2.3, 3.3, 4.7, 6.3_
- [x] 3.7 Write `senzing-bootcamp/tests/test_ensure_graduation_artifacts_properties.py`
  - Properties over synthetic workspaces: guaranteed presence, byte-for-byte idempotence on valid input, at-most-once regeneration, `--check` writes nothing, rendered-recap PDF-vs-HTML selection, failure isolation, enforcement completeness (see design Correctness Properties 1-8).
  - Use `st_`-prefixed strategies and profile-driven example counts (no inline `@settings(max_examples=...)`).
  - _Requirements: 1.1, 2.5, 2.6, 2.7, 4.2, 4.3, 4.8_

- [x] 4. Add and register the enforcement hook
- [x] 4.1 Create `senzing-bootcamp/hooks/enforce-critical-artifacts.kiro.hook`
  - Valid schema: `name`, `version`, `description`, `when.type: agentStop`, `then.type: askAgent`.
  - Prompt: defer on `config/.question_pending`; detect stopping point (Module 7 for Core / Module 11 for Advanced in `modules_completed`, or graduation complete); run `ensure_graduation_artifacts.py --json`; block with the mandatory-gate marker naming missing artifacts when `all_satisfied` is false; silent when satisfied. No unescaped user input.
  - _Requirements: 2.1, 2.3, 2.4, 2.6, 2.7_
- [x] 4.2 Register the hook
  - Add `enforce-critical-artifacts` to the `any` bucket in `senzing-bootcamp/hooks/hook-categories.yaml` and add an `agentstop_order` entry at the end of the list (after `enforce-visualization-offers`) with a rationale.
  - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write` to regenerate `hooks.lock.yaml` and the `hook-registry*.md` steering slices.
  - _Requirements: 6.4_
- [x] 4.3 Write hook tests
  - `senzing-bootcamp/tests/test_enforce_critical_artifacts_hook.py`: JSON schema, `when.type == agentStop`, `then.type == askAgent`, `.question_pending` deferral, stopping-point gate, mandatory-gate blocking marker naming missing artifacts.
  - `senzing-bootcamp/tests/test_enforce_critical_artifacts_registry.py`: hook present in `hook-categories.yaml` (`any` + `agentstop_order`) and `hooks.lock.yaml` in sync.
  - _Requirements: 2.1, 2.3, 2.6, 2.7, 6.4_

- [x] 5. Wire the guarantee and announcement into steering
- [x] 5.1 Update `senzing-bootcamp/steering/graduation.md`
  - Add a mandatory closing step that runs `ensure_graduation_artifacts.py` (enforced guarantee) and performs the post-graduation announcement: recap exists, path `docs/bootcamp_recap.md` and rendered-recap path (`.pdf` if `fpdf2` available else `.html`), and the per-module contents (Information Shared, Questions & Responses, Actions Taken). Announcement runs exactly once, reports only confirmed-existing artifacts, and triggers regeneration first if any are missing.
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
- [x] 5.2 Update `senzing-bootcamp/steering/module-completion-track.md` and `qa-transcript.md`
  - Note the always-run recap PDF / transcript renders are backed by the enforced guarantee and the HTML fallback; preserve reconcile-then-render ordering and non-blocking-of-the-celebration behavior. Add a short cross-reference in `qa-transcript.md` (event emission stays decoupled from writes).
  - _Requirements: 2.4, 4.3_
- [x] 5.3 Extend graduation/track-completion steering tests
  - Assert the mandatory closing announcement is present and names the recap path and per-module contents.
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 6. Validate the full change set
  - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`, `validate_power.py`, `measure_steering.py --check`, and `validate_commonmark.py`.
  - Run `python -m pytest senzing-bootcamp/tests/ tests/` and fix any failures.
  - _Requirements: 6.1, 6.4_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1.1", "2.1", "3.1"],
      "rationale": "Independent leaf generators and the orchestrator core model; no dependencies."
    },
    {
      "wave": 2,
      "tasks": ["1.2", "2.2", "3.2", "3.3", "3.4"],
      "rationale": "Leaf tests depend on 1.1/2.1; ensure_* functions depend on 3.1 (and 3.2 on 2.1, 3.4 on 1.1)."
    },
    {
      "wave": 3,
      "tasks": ["3.5"],
      "rationale": "ensure_all + CLI compose the three ensure functions from wave 2."
    },
    {
      "wave": 4,
      "tasks": ["3.6", "3.7", "4.1"],
      "rationale": "Orchestrator tests depend on 3.5; the hook (4.1) invokes the orchestrator CLI."
    },
    {
      "wave": 5,
      "tasks": ["4.2", "5.1", "5.2"],
      "rationale": "Hook registration depends on 4.1; steering wiring depends on the orchestrator (3.5)."
    },
    {
      "wave": 6,
      "tasks": ["4.3", "5.3"],
      "rationale": "Hook and steering tests depend on their registration/edits in wave 5."
    },
    {
      "wave": 7,
      "tasks": ["6"],
      "rationale": "Full validation runs after every implementation and test task is complete."
    }
  ]
}
```

```text
1.1 recap_html_render ----------------------> 3.4 ensure_rendered_recap --+
2.1 transcript --ensure --------------------> 3.2 ensure_transcript ------+
3.1 orchestrator core ----+--> 3.2                                        |
                          +--> 3.3 ensure_recap_md --------------------- -+--> 3.5 ensure_all + CLI
                          +--> 3.4                                        |
1.2, 2.2 leaf tests  (depend on 1.1, 2.1)                                 |
3.6, 3.7 orchestrator tests  (depend on 3.5) <----------------------------+
      |
      v
4.1 hook --> 4.2 register --> 4.3 hook tests
      |
      v
5.1 graduation.md --+
5.2 track/qa steering --+--> 5.3 steering tests
      |
      v
6. validate  (depends on all above)
```

- Task 1 and the core of Task 3 (3.1) are independent and can start in parallel.
- Task 3.4 depends on 1.1; Task 3.2 depends on 2.1; all of 3.2-3.4 depend on 3.1.
- Task 3.5 depends on 3.2, 3.3, 3.4. Orchestrator tests (3.6, 3.7) depend on 3.5.
- Task 4 depends on 3.5 (the hook invokes the orchestrator). Task 5 depends on 3.5. Task 6 is last.

## Notes

- Every new script is Python 3.11+ stdlib-only; `fpdf` is imported lazily inside render functions
  only, never at module top level (`recap_html_render` never imports `fpdf` at all).
- Reuse existing helpers (`reconcile_transcript`, `completion_artifacts.backfill_recap_sections`,
  `generate_recap_pdf`, `generate_recap_pdf_inline`, `recap_pdf_render`) rather than duplicating
  their logic; the orchestrator only adds the staleness gate, HTML fallback selection, and the
  non-empty transcript placeholder.
- Adding the hook requires the full registry sync (`sync_hook_registry.py --write`); CI runs
  `--verify`, so `hooks.lock.yaml` and the `hook-registry*.md` slices must be regenerated in the
  same change (Task 4.2).
- Do not hand-set `@settings(max_examples=...)` in property tests; example counts come from the
  active Hypothesis profile.
- Steering edits must not introduce external URLs; reference local docs via `#[[file:]]` if needed.
