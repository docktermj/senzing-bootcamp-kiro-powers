# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion F ("Module 2 — SDK Setup") of the Senzing Bootcamp
> improvement review (`x.md`). Requirements below are a starting point for refinement, not a
> finished spec.

## Introduction

In Module 2 (SDK Setup), the TypeScript path can require building the SDK from source — a long,
multi-step, failure-prone process (native addon compilation, `node-gyp`, toolchain and Node version
sensitivity). The module warns that the path is long, and the `language-specific-troubleshooting`
spec adds reactive TypeScript troubleshooting content to `lang-typescript.md`. But a mid-build
failure today has no dedicated recovery branch in the Module 2 flow beyond generic error handling —
the bootcamper can be left staring at a raw build error with no guided next step.

This feature adds a dedicated **build-from-source recovery branch** for the TypeScript path in
Module 2: when the build fails partway, the flow recognizes the failure, offers targeted recovery
options (fix the common cause, retry, or fall back to a prebuilt/alternative path), and resumes SDK
setup without the bootcamper having to diagnose the toolchain unaided.

## Glossary

- **Build_From_Source_Path**: the Module 2 TypeScript branch that compiles the Senzing SDK (and its
  native addon) from source.
- **Mid_Build_Failure**: a non-zero exit or error during the build after it has started but before
  the SDK is usable (e.g. `node-gyp`/native compilation failure, missing toolchain, incompatible
  Node version).
- **Recovery_Branch**: the new guided decision point that handles a Mid_Build_Failure with targeted
  options instead of generic error handling.
- **Fallback_Path**: an alternative to building from source (e.g. a prebuilt package or a supported
  install route) offered when the build cannot be repaired quickly.

## Requirements

### Requirement 1: Detect and route a mid-build failure

**User Story:** As a TypeScript bootcamper, I want the bootcamp to notice when the SDK build fails
partway, so that I get guided help instead of a raw error.

#### Acceptance Criteria

1. WHEN the Build_From_Source_Path produces a Mid_Build_Failure, THE Module 2 flow SHALL route to
   the Recovery_Branch rather than falling through to generic error handling.
2. THE Recovery_Branch SHALL summarize what failed in plain language (the build stage and the likely
   cause) before offering options.
3. WHERE the failure matches a known common cause (e.g. missing build toolchain, `node-gyp`
   prerequisites, unsupported Node version), THE Recovery_Branch SHALL name that specific cause.

### Requirement 2: Offer targeted recovery options

**User Story:** As a bootcamper facing a build failure, I want clear next steps, so that I can
recover without deep toolchain expertise.

#### Acceptance Criteria

1. THE Recovery_Branch SHALL offer, at minimum: fix-the-common-cause guidance, a retry of the build,
   and a Fallback_Path when the build cannot be repaired quickly.
2. WHEN the bootcamper chooses retry after applying a fix, THE flow SHALL re-run the build and,
   on success, resume the normal Module 2 SDK-setup sequence.
3. WHEN the bootcamper chooses the Fallback_Path, THE flow SHALL proceed via the alternative and
   continue Module 2 without requiring a successful from-source build.
4. THE recovery guidance for external/toolchain knowledge SHALL come from the Senzing MCP server
   (`sdk_guide` / docs tools) or existing `lang-typescript.md` content, not hard-coded external URLs
   in steering files.

### Requirement 3: Consistency with existing troubleshooting

**User Story:** As a maintainer, I want the recovery branch to build on the existing TypeScript
troubleshooting content rather than duplicate it.

#### Acceptance Criteria

1. THE Recovery_Branch SHALL reference the reactive TypeScript troubleshooting content added by
   `language-specific-troubleshooting` (in `lang-typescript.md`) for the detailed fixes.
2. THE feature SHALL keep the TypeScript-maturity framing consistent with
   `typescript-language-maturity`.
3. THE feature SHALL update any affected steering file token counts in
   `senzing-bootcamp/steering/steering-index.yaml`.

### Requirement 4: Non-blocking dead-ends

**User Story:** As a bootcamper, I want to never be stuck at a build error with no path forward.

#### Acceptance Criteria

1. THE Recovery_Branch SHALL always present at least one path that lets Module 2 continue (retry
   after fix, or Fallback_Path), so the build failure is never a dead end.
2. IF all recovery options are exhausted, THEN the flow SHALL clearly state the current blocker and
   the support/next-step options rather than looping on the same error.

### Requirement 5: Test coverage

**User Story:** As a maintainer, I want tests so the recovery branch does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests (e.g. steering-content/flow assertions) verifying that a
   TypeScript mid-build failure routes to the Recovery_Branch, that the branch offers fix/retry/
   fallback options, and that a non-blocking continuation path always exists.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   the appropriate `tests/` directory.
