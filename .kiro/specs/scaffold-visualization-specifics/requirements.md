# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion G ("Module 3 — System Verification") of the
> Senzing Bootcamp improvement review (`x.md`). Requirements below are a starting point for
> refinement, not a finished spec. NOTE: the review mentions `generate_scaffold`, which is a Senzing
> **MCP server tool**, not a local script. This spec targets moving the visualization specifics into
> generated scaffold output (from the MCP scaffold tool and/or the local
> `scripts/generate_standalone_demo.py`) rather than restating them in steering prose.

## Introduction

Module 3's visualization is described in heavy prescriptive detail across steering prose (Python
stdlib HTTP server, D3.js v7 from CDN, `function(){}` callback syntax, SVG dimensions, edge-key
mapping between links and nodes). Several specs (`visualization-enhancements`,
`module3-visualization-fixes`) deliberately mandate these specifics in steering to prevent
silent-failure classes (e.g. mismatched edge keys producing a blank graph).

Keeping this much implementation detail in always-relevant steering prose is costly (context budget)
and brittle (it must be restated and kept in sync everywhere the visualization appears). The review
suggests pushing these specifics into **generated scaffold output** — the code the scaffold tool
emits — so the constraints live in one authoritative, executable place and the steering can shrink
to intent plus a pointer. This turns a "rich source of silent-failure lessons" into scaffolded code
that is correct by construction.

This is a refactor of where the specifics live, not a change to the visualization behavior. The
Module 3 Step 9 mandatory gate and the "always create a visualization" rule are unchanged.

## Glossary

- **Visualization_Specifics**: the prescriptive implementation constraints — stdlib HTTP server,
  D3.js v7, callback syntax, SVG dimensions, link/node edge-key mapping — currently in steering
  prose.
- **Scaffold_Output**: the code emitted by the Senzing MCP scaffold tool and/or the local
  `scripts/generate_standalone_demo.py`, delivered to the bootcamper as a starting artifact.
- **Steering_Pointer**: the reduced steering content that states the visualization intent and points
  to the Scaffold_Output instead of re-deriving the specifics inline.

### Assumptions / Open questions (to resolve during refinement)

- The MCP scaffold tool is server-side; this power cannot change its output directly. The refinement
  must determine which specifics can move into the **local** `generate_standalone_demo.py` output
  and which must remain as steering guidance because they depend on the server-side scaffold.

## Requirements

### Requirement 1: Move visualization specifics into generated output

**User Story:** As a maintainer, I want the visualization implementation specifics to live in
generated scaffold code, so that they are correct by construction and not duplicated across steering
prose.

#### Acceptance Criteria

1. THE Visualization_Specifics that can be embedded in locally generated code SHALL be emitted by
   `scripts/generate_standalone_demo.py` (and any other local visualization generator) so the
   bootcamper receives working code rather than prose instructions to hand-assemble it.
2. THE generated code SHALL encode the edge-key mapping between D3 links and nodes correctly, so the
   known blank-graph silent failure cannot occur in the scaffolded output.
3. WHERE a specific depends on the server-side MCP scaffold tool and cannot be embedded locally, THE
   spec SHALL document that dependency and keep the minimal steering guidance needed for it.

### Requirement 2: Reduce steering prose to intent plus pointer

**User Story:** As a maintainer, I want the Module 3 visualization steering to shrink to intent and
a pointer, so that the context budget improves and the specifics have a single source of truth.

#### Acceptance Criteria

1. WHEN the Visualization_Specifics are relocated into Scaffold_Output, THE Module 3 visualization
   steering SHALL be reduced to a Steering_Pointer (intent + reference to the generated artifact)
   rather than restating the full specifics.
2. THE feature SHALL update the affected steering file token counts in
   `senzing-bootcamp/steering/steering-index.yaml` to reflect the reduction.
3. THE reduction SHALL NOT remove any constraint that is not fully guaranteed by the Scaffold_Output
   (no lost silent-failure protection).

### Requirement 3: Preserve visualization behavior and gates

**User Story:** As a product owner, I want the "wow moment" and its gate unchanged by this refactor.

#### Acceptance Criteria

1. THE feature SHALL NOT weaken the Module 3 Step 9 mandatory visualization gate or the
   "always create a visualization" rule.
2. THE relocated specifics SHALL produce a visualization functionally equivalent to today's
   (same stdlib server pattern, D3 v7, working edge-key mapping).
3. THE feature SHALL stay consistent with `module3-first-visualization-guarantee` (the opt-out /
   deferred first-visualization guarantee is unaffected).

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the relocated specifics do not regress into a
blank-graph or missing-constraint state.

#### Acceptance Criteria

1. THE feature SHALL include tests asserting the generated visualization output contains the correct
   edge-key mapping and the required structural elements, and that no relocated constraint is silently
   dropped from both the steering and the generated output.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
