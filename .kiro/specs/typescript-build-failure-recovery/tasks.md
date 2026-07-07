# Implementation Plan: TypeScript Build-From-Source Failure Recovery

## Overview

Add a dedicated **Recovery_Branch** to the Module 2 TypeScript build-from-source path. The feature
is **steering-driven**: its shipped deliverable is new steering content and flow in
`senzing-bootcamp/steering/module-02-sdk-setup.md` Step 3 Phase 3 (referencing
`lang-typescript.md`), plus the mandatory `steering-index.yaml` token-count sync. There is no new
runtime script and no new hook. The branch recognizes a Mid_Build_Failure, routes to recovery
instead of generic error handling, summarizes the failure in plain language against a known-cause
table, offers a fix / retry / Fallback_Path triad, resumes or continues Module 2, and guarantees a
non-looping continuation so a build failure is never a dead end.

Because the surface is steering content, the testable specification is a small pure **reference
model** of the recovery decision graph (failure-cause classes → recovery options → continuations),
encoded test-only in `senzing-bootcamp/tests/test_typescript_build_failure_recovery.py`. Work
proceeds bottom-up: scaffold the reference model, then the classification/routing, presentation, and
transition functions (each with its property test placed right after implementation), then author
the shipped steering subsection, sync the steering index, and finally add the content/flow tests
that read the **real** steering files. All test code targets Python 3.11+ stdlib + Hypothesis and
follows the project test conventions. The steering content honors the power's no-hardcoded-URL /
MCP-only-facts rule and does not modify `lang-typescript.md` (referenced only).

## Tasks

- [x] 1. Scaffold the test module and reference model
  - [x] 1.1 Create the test file skeleton and reference-model types
    - Create `senzing-bootcamp/tests/test_typescript_build_failure_recovery.py` with the
      `sys.path` insertion convention, stdlib imports (`enum`, `dataclasses`), Hypothesis imports,
      and a module docstring describing the feature and reference model
    - Define the reference-model types exactly as specified in the design's Components section:
      the `CauseClass`, `Option`, and `State` enums and the frozen `Recovery` dataclass
      (`cause`, `summary`, `fix_reference`, `options`)
    - Add typed function stubs for `classify_failure`, `route`, `build_recovery`, `transition`, and
      `continuations`
    - _Requirements: 5.2_

- [x] 2. Implement failure classification and routing
  - [x] 2.1 Implement `classify_failure` and `route`
    - Implement `classify_failure(signal: str) -> CauseClass`: a **total** mapping from a raw
      build-failure signal to a `CauseClass` using the known-cause table (`NODE_VERSION`,
      `NATIVE_ADDON`, `TOOLCHAIN`, `MODULE_SYSTEM`, `PKG_MANAGER`), with any non-matching signal
      classifying as `UNKNOWN`
    - Implement `route(signal: str) -> State`: every Mid_Build_Failure signal (recognized or not)
      returns `State.RECOVERY`
    - Add the `st_failure_signal()` strategy: known-pattern signals for each cause class plus
      arbitrary non-matching strings that must classify as `UNKNOWN`
    - _Requirements: 1.1_

  - [x] 2.2 Write property test for routing to the Recovery_Branch
    - **Property 1: Every Mid_Build_Failure routes to the Recovery_Branch** — for any
      Mid_Build_Failure signal from `st_failure_signal()`, `route(signal)` is `State.RECOVERY`,
      never the module's generic error handling
    - **Validates: Requirements 1.1**

- [x] 3. Implement the recovery presentation
  - [x] 3.1 Implement `build_recovery`
    - Implement `build_recovery(cause: CauseClass) -> Recovery`: `summary` is a non-empty
      plain-language string naming the cause (the cause name for known causes, "an unrecognized
      build failure" for `UNKNOWN`); `fix_reference` is the corresponding `lang-typescript.md`
      "Common Environment Issues" entry title (a general section + MCP `search_docs` pointer for
      `UNKNOWN`); `options` always contains `{FIX, RETRY, FALLBACK}`
    - Add the `st_cause_class()` strategy (`sampled_from` the `CauseClass` enum)
    - _Requirements: 1.2, 1.3, 2.1, 3.1_

  - [x] 3.2 Write property test for the summary naming the matched cause
    - **Property 2: The summary names the matched common cause** — for any cause class,
      `build_recovery(cause)` produces a non-empty summary that names that cause, and every known
      common cause maps to a known-cause entry
    - **Validates: Requirements 1.2, 1.3**

  - [x] 3.3 Write property test for the fix / retry / fallback triad
    - **Property 3: Every recovery offers the fix / retry / fallback triad** — for any cause class,
      the offered options include at minimum fix-the-common-cause, retry, and Fallback_Path
    - **Validates: Requirements 2.1**

- [x] 4. Implement state transitions and continuations
  - [x] 4.1 Implement `transition` and `continuations`
    - Implement `transition(state: State, option: Option, retry_ok: bool) -> State` per the
      design's transition table: `(RECOVERY, RETRY, retry_ok=True) -> RESUME_MODULE2`,
      `(RECOVERY, RETRY, retry_ok=False) -> RECOVERY`, `(RECOVERY, FIX, _) -> RECOVERY`,
      `(RECOVERY, FALLBACK, _) -> CONTINUE_MODULE2`, and options-exhausted -> `BLOCKED_WITH_SUPPORT`
    - Implement `continuations(recovery: Recovery) -> frozenset[Option]` returning
      `recovery.options & {RETRY, FALLBACK}` (never empty while the branch is active)
    - Add the `st_retry_sequence()` strategy: sequences of failed-then-eventual retry outcomes
    - _Requirements: 2.2, 2.3, 4.1, 4.2_

  - [x] 4.2 Write property test for chosen paths continuing Module 2
    - **Property 4: Chosen recovery paths continue Module 2** — retry after a successful build
      transitions to `RESUME_MODULE2`; the Fallback_Path transitions to `CONTINUE_MODULE2` without
      requiring a successful from-source build
    - **Validates: Requirements 2.2, 2.3**

  - [x] 4.3 Write property test for the never-a-dead-end guarantee
    - **Property 5: A build failure is never a dead end** — for any cause class and any
      `st_retry_sequence()` of failed retries, `continuations(recovery)` is non-empty while the
      branch is active
    - **Validates: Requirements 4.1**

  - [x] 4.4 Write property test for the exhaustion terminal state
    - **Property 6: Exhausting options reaches a distinct, non-looping terminal state** — for any
      recovery whose options are all exhausted, the flow transitions to `BLOCKED_WITH_SUPPORT`,
      distinct from `RECOVERY` and not re-entering the originating error
    - **Validates: Requirements 4.2**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Author the Recovery_Branch steering subsection
  - [x] 6.1 Add the "Recovery: build-from-source failures (TypeScript)" subsection to
        `module-02-sdk-setup.md` Step 3 Phase 3
    - Insert the subsection immediately after the from-source build sequence, on the TypeScript
      path only, with the seven agent-instruction elements from the design: (1) **Detection /
      routing** — a Mid_Build_Failure enters this branch and does not fall through to the generic
      Error Handling block (Req 1.1); (2) **Plain-language summary** naming the single most likely
      cause, placed before the options (Req 1.2, 1.3); (3) the **known-cause table** (`NODE_VERSION`,
      `NATIVE_ADDON`, `TOOLCHAIN`, `MODULE_SYSTEM`, `PKG_MANAGER`) mapping each cause to its
      `lang-typescript.md` "Common Environment Issues" entry (Req 1.3, 3.1); (4) the **fix / retry /
      Fallback_Path options** (Req 2.1); (5) **Sourcing** from `lang-typescript.md` and MCP
      `sdk_guide` / `search_docs` with **no hardcoded external URLs** (Req 2.4, 3.1); (6)
      **Resumption** on retry-success into Phase 3 → Step 4, and **Fallback continuation** of
      Module 2 without a from-source build (Req 2.2, 2.3); (7) **No dead end** plus a non-looping
      "blocker + support / next-step" terminal state when options are exhausted (Req 4.1, 4.2)
    - Keep the TypeScript-maturity framing consistent with `typescript-language-maturity`; leave the
      module's generic Error Handling block and `lang-typescript.md` unchanged (referenced only)
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 4.1, 4.2_

- [x] 7. Sync the steering index
  - [x] 7.1 Update `steering-index.yaml` token counts and re-check
    - Update the `token_count` for `module-02-sdk-setup.md` in **both** entries (the module-tree
      entry near line 22 and the flat `files:` entry near line 470) to the newly measured value, and
      re-check `size_category` (stays `large`; no split triggered per the split-exclusion note)
    - Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm it passes
    - _Requirements: 3.3_

- [x] 8. Content and flow tests over the real steering
  - [x] 8.1 Write property test for MCP/lang-typescript sourcing with no hardcoded URLs
    - **Property 7: Recovery guidance is MCP/lang-typescript-sourced with no hardcoded URLs** — for
      any line of the Recovery_Branch subsection in the **real** `module-02-sdk-setup.md`, no
      hardcoded external `http(s)://` URL appears, and the subsection references the MCP tools
      (`sdk_guide` / `search_docs`) and `lang-typescript.md`
    - **Validates: Requirements 2.4**

  - [x] 8.2 Write property test for named-cause → lang-typescript.md mapping
    - **Property 8: Every named cause maps to a lang-typescript.md troubleshooting entry** — for any
      known common cause named by the branch, a corresponding entry exists in the **real**
      `lang-typescript.md` "Common Environment Issues" section
    - **Validates: Requirements 3.1**

  - [x] 8.3 Write content/flow unit and example tests over the real steering
    - Cover: **routing pre-empt** (a `gyp ERR!` example enters the Recovery_Branch, not the generic
      SENZ / `common-pitfalls.md` path); **summary-before-options ordering** in the subsection;
      **option triad present** (fix, retry, Fallback_Path listed); **resume vs. continue**
      (retry-success resumes Phase 3 → Step 4; Fallback_Path continues Module 2);
      **maturity-framing consistency** with `typescript-language-maturity`; **terminal-state
      content** (states a blocker + support/next-step options, does not instruct re-running the same
      failing command). Use synthetic, PII-free fixtures only
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.2, 4.2_

  - [x] 8.4 Write the steering-index token-sync smoke check
    - Assert `steering-index.yaml` `token_count` for `module-02-sdk-setup.md` (both entries) matches
      the measured count; equivalently that `measure_steering.py --check` passes. A single
      deterministic check, not a property
    - _Requirements: 3.3_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- The reference model (enums, `Recovery`, and the five functions) is **test-only** — it is the
  machine-checkable specification of the shipped steering, not a runtime script or hook.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Model-level properties (1–6) exercise the pure reference model; content properties (7–8) read the
  **real** steering files (`module-02-sdk-setup.md`, `lang-typescript.md`).
- Tests live in `senzing-bootcamp/tests/test_typescript_build_failure_recovery.py`, are class-based,
  and each property task references its property number and validated requirement clause for
  traceability.
- Steering content honors the power's security rules: no hardcoded external URLs (MCP-only facts);
  `lang-typescript.md` is referenced, never modified.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "6.1"] },
    { "id": 5, "tasks": ["7.1"] },
    { "id": 6, "tasks": ["8.1", "8.2", "8.3", "8.4"] }
  ]
}
```
