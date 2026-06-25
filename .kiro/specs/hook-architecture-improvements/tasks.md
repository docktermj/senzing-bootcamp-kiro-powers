# Implementation Plan: Hook Architecture Improvements

## Overview

This plan implements the three independent-but-related themes from the design:

- **Theme A — agentStop ordering & documentation.** Add a machine-readable `agentstop_order`
  mapping to `hook-categories.yaml`, author a `manual`-inclusion `hook-architecture.md` steering
  doc (precedence list, rationale, closing-question ownership, question-pending silence,
  gate-violation > celebration precedence, no-engine-change non-goal), register it in
  `steering-index.yaml`, and add behavior-preserving question-pending guard text to the four
  agentStop hooks that lack an explicit check.
- **Theme B — hook-prompt deduplication.** Author a stdlib-only fragment source
  (`hook_prompt_fragments.py`) and a sibling composer (`compose_hook_prompts.py`) whose
  `--write` output is **byte-identical** to the current on-disk gate hooks (a proven no-op
  refactor), with a `--verify` drift gate wired into CI *before* the existing sync-verify step.
- **Theme C — capture-hook install reliability.** Repair `install_hooks.py` (derive the set from
  the real `*.kiro.hook` glob, drop the three consolidated hooks, add the five current hooks,
  define `ESSENTIAL` and `CAPTURE_CRITICAL`, add non-interactive `--all`/`--essential` flags),
  document capture-critical createHook coverage and the session-start warn-on-absence check.

All code is Python 3.11+ stdlib-only. Tests use pytest + Hypothesis with the repo conventions:
`from __future__ import annotations`, modern type hints, class-based organization, `st_`-prefixed
strategies, `@settings(max_examples=20)`, and the `sys.path` script-import pattern. Per
`structure.md`, tests that read **real hook files / real config** live in the repo-root `tests/`;
script-behavior tests live in `senzing-bootcamp/tests/`. The three themes are largely independent
and may be implemented in parallel; tests are placed right after the component they validate.

## Tasks

- [x] 1. Theme A — agentStop ordering and documentation
  - [x] 1.1 Add the `agentstop_order` mapping to `hook-categories.yaml`
    - Edit `senzing-bootcamp/hooks/hook-categories.yaml`
    - Add an `agentstop_order` block listing exactly the five agentStop hook ids
      (`ask-bootcamper`, `module-recap-append`, `module-completion-celebration`,
      `enforce-gate-on-stop`, `enforce-visualization-offers`), each with an integer `order`
      (contiguous 1..5) and a one-sentence `rationale`, exactly as in the design's
      `agentstop_order` example
    - List no hook whose `when.type` is not `agentStop`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 Author the `hook-architecture.md` steering document
    - Create `senzing-bootcamp/steering/hook-architecture.md` with `manual` inclusion frontmatter
    - Record the ordered precedence list of the five agentStop hooks and the intended precedence
      semantics; include a written rationale per hook position and point to `agentstop_order` in
      `hook-categories.yaml` as the machine-readable source
    - State that `ask-bootcamper` is the closing-question owner and that all other agentStop hooks
      defer closing-question emission to it, resolving conflicts in its favor
    - State the question-pending silence rule (while `config/.question_pending` exists, every
      agentStop hook emits zero output)
    - State the single-winner precedence rule, the explicit gate-violation > celebration example
      (`enforce-gate-on-stop` outranks `module-completion-celebration`), and the no-stacking rule
    - State the non-goal/assumption: the power does not modify the IDE engine or its dispatch
      order; determinism comes from per-hook guards plus the documented precedence
    - Record the Theme C capture-critical designation
      (`session-log-events`, `module-recap-append`, `ask-bootcamper`) and the both-paths coverage
      statement
    - _Requirements: 1.1, 1.2, 1.3, 2.2, 2.3, 3.1, 3.2, 3.3, 4.2, 8.6, 10.1, 10.5, 10.6_

  - [x] 1.3 Register the steering doc in `steering-index.yaml` and keep `--check` green
    - Edit `senzing-bootcamp/steering/steering-index.yaml` to add an entry for
      `hook-architecture.md` with its token budget
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and adjust the recorded
      budget so the check exits 0
    - _Requirements: 1.4_

  - [x] 1.4 Add behavior-preserving question-pending guard text to the four agentStop hooks and refresh mirrors
    - Edit the four agentStop hook prompts lacking an explicit check —
      `senzing-bootcamp/hooks/module-recap-append.kiro.hook`,
      `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`,
      `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`,
      `senzing-bootcamp/hooks/enforce-visualization-offers.kiro.hook` — adding a leading no-op
      clause: if `config/.question_pending` exists, produce no output and defer to `ask-bootcamper`
    - Keep the addition additive/behavior-preserving (only widens existing silence conditions; no
      change to output in any non-pending state); do not touch `ask-bootcamper`
    - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write` to refresh the three
      mirror docs and `hooks.lock.yaml` (version bumps), then confirm
      `sync_hook_registry.py --verify` exits 0
    - _Requirements: 2.1, 2.4, 3.4, 4.3, 4.4_

  - [x] 1.5 Write property test for the agentstop_order mapping
    - Create `tests/test_agentstop_order_properties.py` reading the real hooks dir and
      `hook-categories.yaml`
    - **Property 1: agentstop_order lists exactly the agentStop hooks** — assert the set of
      `agentstop_order` ids equals the set of hook ids whose `when.type == agentStop` (iff, no more,
      no fewer)
    - **Validates: Requirements 1.5**

  - [x] 1.6 Write property test for agentStop guard text
    - Create `tests/test_agentstop_guard_text_properties.py` reading the real agentStop hook prompts
    - **Property 2: Every agentStop hook has a question-pending silence guard** — assert each
      `agentStop` hook's `then.prompt` references `config/.question_pending` paired with a
      no-output / defer-to-`ask-bootcamper` clause
    - **Validates: Requirements 2.4**

  - [x] 1.7 Write doc-prose example test for the steering document
    - Create `tests/test_hook_architecture_doc.py` reading the real `hook-architecture.md`
    - Assert the doc records the precedence list and semantics, per-hook rationale, closing-question
      ownership and conflict resolution, the gate-violation > celebration example, the no-stacking
      rule, the cannot-control-order assumption, the sibling-script decision, and the
      capture-critical / both-paths statements
    - _Requirements: 1.1, 1.2, 1.3, 2.2, 2.3, 3.1, 3.2, 3.3, 4.2, 8.6, 10.1, 10.5, 10.6_

- [x] 2. Checkpoint - Theme A
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Theme B — hook-prompt deduplication
  - [x] 3.1 Create the fragment source `hook_prompt_fragments.py`
    - Create `senzing-bootcamp/scripts/hook_prompt_fragments.py` (stdlib-only,
      `from __future__ import annotations`) exposing `FRAGMENTS: dict[str, str]`
    - Define `module3_condition_a` (the CONDITION A checkpoint check shared verbatim by all three
      gate hooks) and three distinct ⛔ fragments — `module3_gate_on_stop_violation`,
      `module3_block_completion`, `module3_block_advancement` — using multi-line literals that are
      **byte-identical** to the corresponding text in the current on-disk gate hooks (including the
      guard text finalized in task 1.4 for `enforce-gate-on-stop`)
    - This module is the sole authoritative location for each shared fragment's text
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [x] 3.2 Create the prompt composer `compose_hook_prompts.py`
    - Create `senzing-bootcamp/scripts/compose_hook_prompts.py` following the repo script pattern
      (shebang, `from __future__ import annotations`, docstring, `argparse`, `main(argv=None)`,
      `if __name__ == "__main__": sys.exit(main())`)
    - Hold a per-hook `HOOK_TEMPLATES` (gate-hook id → template with `{{fragment:NAME}}` markers +
      per-hook literal text) and read `name`/`version`/`description`/`when` from the current files
      so the `when` block is preserved unchanged
    - Implement `compose_prompt(template, fragments)` (replace every `{{fragment:NAME}}` verbatim,
      leaving no residual `{{fragment:` substring) and `compose_hook(hook_id, fragments)` (full hook
      dict with expanded `then.prompt`)
    - Implement `--write` (default) writing `<hooks-dir>/<id>.kiro.hook` with byte-identical JSON
      formatting (`indent=2`, `ensure_ascii=False`, trailing newline) and `--verify` (compose in
      memory, compare against on-disk bytes, collect every drifted hook, exit 1 listing each drifted
      id, else exit 0)
    - Raise `UnknownFragmentError` for an undefined marker; `main` reports
      `ERROR: unknown fragment '<name>' referenced by hook '<hook_id>'` to stderr and returns 1
    - Add `--hooks-dir`/`--fragments` options; exit code 0 on success and 1 on error
    - _Requirements: 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 8.2, 8.3_

  - [x] 3.3 Compose-write and prove the byte-identical no-op refactor
    - Run `python3 senzing-bootcamp/scripts/compose_hook_prompts.py --write` and confirm
      `git diff` is empty for the three gate hooks
      (`gate-module3-visualization.kiro.hook`, `enforce-mandatory-gate.kiro.hook`,
      `enforce-gate-on-stop.kiro.hook`), proving introducing the composer changes no bytes
    - Confirm `compose_hook_prompts.py --verify` exits 0, then confirm
      `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` still exits 0
    - Confirm the three `preToolUse`/`toolTypes: ["write"]` and gate hooks
      (`gate-module3-visualization`, `enforce-mandatory-gate`, `write-policy-gate`) are retained
    - _Requirements: 8.1, 8.4, 8.5_

  - [x] 3.4 Wire the composer verify step into CI
    - Edit `.github/workflows/validate-power.yml` to add a "Verify composed hook prompts are in
      sync" step running `compose_hook_prompts.py --verify` **before** the existing
      "Verify hook registry is in sync" (`sync_hook_registry.py --verify`) step; keep the sync step
      unchanged and after it
    - _Requirements: 7.4_

  - [x] 3.5 Write property tests for the composer logic
    - Create `senzing-bootcamp/tests/test_compose_hook_prompts_properties.py` (composer logic over
      generated templates/fragments)
    - **Property 3: Composition fully expands fragments and leaves no residual markers** —
      **Validates: Requirements 6.1, 6.2**
    - **Property 5: Unknown fragment references are reported and fail (exit 1 + name)** —
      **Validates: Requirements 6.5**
    - **Property 8: Composed hooks are schema-valid and preserve the `when` block** —
      **Validates: Requirements 8.2, 8.3**

  - [x] 3.6 Write unit/CLI example tests for the composer
    - Create `senzing-bootcamp/tests/test_compose_hook_prompts_unit.py`
    - Cover `--write` into a temp dir (6.3), `main(argv=None)` + argparse + exit 0/1 contract (6.4),
      `--verify` compare path (7.1), and the fragment-source contract (single source / fragments
      present / marker references / stdlib-only import)
    - _Requirements: 6.3, 6.4, 5.1, 5.2, 5.4, 5.5_

  - [x] 3.7 Write no-op refactor property tests against the real on-disk hooks
    - Create `tests/test_compose_no_op_refactor.py` (composer output vs real `.kiro.hook` files)
    - **Property 4: Shared fragments expand byte-identically across hooks** —
      **Validates: Requirements 7.5**
    - **Property 6: Composition is a byte-identical no-op refactor (verify exits 0 on canonical
      repo)** — **Validates: Requirements 8.1, 7.2**
    - **Property 7: Any drift from the composed source is detected and reported (exit 1 + hook id)**
      — **Validates: Requirements 7.3**

  - [x] 3.8 Write compose→sync integration test
    - Create `senzing-bootcamp/tests/test_compose_sync_integration.py`
    - Assert that after `compose_hook_prompts.py --write`, `sync_hook_registry.py --verify` exits 0
      (composer-before-sync ordering holds)
    - _Requirements: 8.5_

  - [x] 3.9 Write CI-step presence test
    - Create `tests/test_ci_compose_verify.py` reading `.github/workflows/validate-power.yml`
    - Assert the composer `--verify` step is present and ordered before the `sync_hook_registry.py
      --verify` step
    - _Requirements: 7.4_

- [x] 4. Checkpoint - Theme B
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Theme C — capture-hook install reliability
  - [x] 5.1 Repair `install_hooks.py`
    - Edit `senzing-bootcamp/scripts/install_hooks.py`
    - Derive the authoritative installed set from `power_hooks.glob("*.kiro.hook")`; demote the
      hardcoded list to a non-authoritative display-metadata overlay; read each hook's display name
      from its `name` field (matching the "to {verb phrase}" pattern)
    - Remove the three consolidated hooks (`enforce-file-path-policies`, `enforce-single-question`,
      `block-direct-sql`) from metadata and `ESSENTIAL`
    - Add the five current hooks (`write-policy-gate`, `session-log-events`, `module-recap-append`,
      `enforce-mandatory-gate`, `enforce-gate-on-stop`) to metadata with accurate descriptions
    - Define `CAPTURE_CRITICAL = {"session-log-events", "module-recap-append", "ask-bootcamper"}`
      and `ESSENTIAL` = critical hooks (from `hook-categories.yaml`) ∪ `CAPTURE_CRITICAL`
    - Refactor the interactive body into `run_interactive(...)`; add an `argparse`
      `main(argv=None)` with non-interactive `--all` and `--essential` flags that never call
      `input()`, exit 0 on success, and exit 1 reporting the missing directory when `power_hooks` is
      absent; retain interactive mode when no flag is supplied
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.3, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 5.2 Document capture-critical createHook coverage in onboarding
    - Edit `senzing-bootcamp/steering/agent-instructions.md` to add `module-recap-append` and
      `session-log-events` to the onboarding createHook-from-registry set (alongside the existing
      critical `ask-bootcamper`), so all capture-critical hooks are created at session start
    - _Requirements: 10.1, 10.2, 10.5_

  - [x] 5.3 Document the session-start warn-on-absence check
    - Edit `senzing-bootcamp/steering/session-resume-phase2-setup-recovery.md` to specify that,
      after the `hooks_installed` check, the agent inspects `.kiro/hooks` and warns which
      capture-critical hooks are absent and how to install them (createHook from registry, or
      `python3 senzing-bootcamp/scripts/install_hooks.py --essential`); advisory, never blocking
    - Add a cross-reference to this behavior from `agent-instructions.md`'s Hooks section
    - _Requirements: 10.4, 10.6_

  - [x] 5.4 Write property tests for the installer logic
    - Create `senzing-bootcamp/tests/test_install_hooks_properties.py` (installer logic over temp
      hook dirs)
    - **Property 9: Installer discovered set equals the hook-file set** —
      **Validates: Requirements 9.3, 12.1**
    - **Property 13: Non-interactive modes never read stdin and exit 0** —
      **Validates: Requirements 11.3, 11.4, 12.4**
    - **Property 14: Missing hooks directory under a non-interactive flag fails cleanly (exit 1 +
      path)** — **Validates: Requirements 11.5**

  - [x] 5.5 Write property tests against the real hooks directory
    - Create `tests/test_install_hooks_real_set_properties.py` (installer vs the real hooks dir)
    - **Property 10: No consolidated hook is referenced by the installer** —
      **Validates: Requirements 9.1, 12.2**
    - **Property 11: Installer display names match each hook's `name` field ("to {verb phrase}")** —
      **Validates: Requirements 9.4**
    - **Property 12: Capture-critical hooks are in both install sets (all + essential)** —
      **Validates: Requirements 10.3, 12.3**

  - [x] 5.6 Write installer mode/metadata unit tests
    - Create `senzing-bootcamp/tests/test_install_hooks_modes_unit.py`
    - Cover `--all` (11.1), `--essential` (11.2), interactive-retained-when-no-flag (11.6), the
      five current hooks present in metadata with accurate names (9.2), and the
      derivation-adopted/discovery-driven set (9.5)
    - _Requirements: 11.1, 11.2, 11.6, 9.2, 9.5_

  - [x] 5.7 Write capture-critical coverage example test
    - Create `tests/test_capture_critical_coverage.py` reading the onboarding steering + registry
      and the session-resume doc
    - Assert `module-recap-append` and `session-log-events` are in the onboarding createHook set
      (10.2) and that the session-start warn-on-absence behavior is documented (10.4)
    - _Requirements: 10.2, 10.4_

- [x] 6. Final checkpoint - Run CI validators
  - Run the new test files for all three themes and confirm they pass
  - Run `python3 senzing-bootcamp/scripts/compose_hook_prompts.py --verify` and confirm exit 0
  - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm exit 0
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`,
    `validate_power.py`, and `validate_commonmark.py` to confirm nothing regressed
  - Confirm no third-party dependency and no external server URL was added; confirm the three
    `preToolUse`/`toolTypes: ["write"]` hooks remain present
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core
  implementation, the byte-identical compose-write, CI wiring, and documentation are never optional.
- Each leaf task lists the files it touches and the specific requirement sub-clauses it satisfies.
- Each property-test sub-task names its design **Property** number and the requirement clauses it
  validates; property tests use `@settings(max_examples=20)` and carry the
  `# Feature: hook-architecture-improvements, Property {n}` tag comment.
- Theme B is a proven byte-identical no-op refactor: the fragment source and composer templates are
  authored against the on-disk hooks *after* Theme A's guard-text edit (task 1.4) so that
  `enforce-gate-on-stop` composes byte-for-byte.
- Tests reading real hook files / real config live in repo-root `tests/`; script-behavior tests live
  in `senzing-bootcamp/tests/`, per `structure.md`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "5.1", "5.2"] },
    { "id": 1, "tasks": ["1.3", "1.4", "1.7", "5.3", "5.4", "5.5", "5.6"] },
    { "id": 2, "tasks": ["1.5", "1.6", "3.1", "5.7"] },
    { "id": 3, "tasks": ["3.2"] },
    { "id": 4, "tasks": ["3.3", "3.5", "3.6"] },
    { "id": 5, "tasks": ["3.4", "3.7", "3.8"] },
    { "id": 6, "tasks": ["3.9"] }
  ]
}
```
