# Implementation Plan: License Capacity Framing

## Overview

This plan refactors the pure framing surface in `scripts/volume_utils.py` so the
built-in 500-record evaluation license is presented as a *default the bootcamper
already has* plus *expansion paths*, with downsizing as one option. All Senzing
facts (capacity, validity) are passed in by the agent from the MCP server and are
omitted when unavailable — never hardcoded. The helper changes are guarded by
Hypothesis property tests; the steering and docs reframing is guarded by
content/example tests. Work proceeds from the pure helper outward to the markdown
touchpoints, ending with tests that lock in the cross-document consistency.

Language: Python 3.11+ (stdlib only), pytest + Hypothesis, following the repo's
script and test conventions.

## Tasks

- [x] 1. Refactor the license framing helper in `scripts/volume_utils.py`
  - [x] 1.1 Add framing value object and expansion-path constants
    - Add `from dataclasses import dataclass` and define the frozen
      `LicenseFramingContext` dataclass (`capacity: int | None`,
      `validity: str | None`, `submit_feedback_available: bool`,
      `has_existing_license: bool`, `mention_downsizing: bool = True`)
    - Define the stable, ordered path id constants `PATH_APPLY_EXISTING`,
      `PATH_EXTERNAL_REQUEST`, `PATH_IN_FLOW_MCP`
    - _Requirements: 2.1, 1.3_

  - [x] 1.2 Implement `build_expansion_paths(submit_feedback_available, has_existing_license)`
    - Always include apply-existing and external-request, in canonical order
    - Include in-flow MCP path only when `submit_feedback_available` is True AND
      `has_existing_license` is False
    - Return the ordered list of path ids
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 1.3 Write property test for expansion-path selection
    - **Property 2: Expansion-path selection is correct**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - New file `senzing-bootcamp/tests/test_license_framing.py`; use the
      `sys.path` insertion pattern; cross-product `st.booleans()` for both flags;
      `@settings(max_examples=100)`; tag with
      `# Feature: license-capacity-framing, Property 2: ...`

  - [x] 1.4 Implement `build_license_framing(...)`
    - Keyword-only `capacity`, `validity`, `submit_feedback_available`,
      `has_existing_license`, `mention_downsizing`
    - Describe the limit as a built-in evaluation license the bootcamper already
      has; never use hard-cap / fixed-maximum phrasing
    - Render a description for every path id from `build_expansion_paths(...)`
    - Include `capacity`/`validity` verbatim only when provided; when `None`,
      omit the figure and state it is currently unavailable from the MCP server
    - Position expansion options before/alongside any downsizing mention
    - Refer to "the Senzing MCP server" by name only — no MCP or external URLs
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 3.2, 4.4_

  - [x] 1.5 Refactor `get_license_guidance(tier, *, capacity=None, validity=None, submit_feedback_available=False, has_existing_license=False)`
    - Keep positional `tier` for backward compatibility; add keyword-only
      fact/flag params with safe defaults (figure-omitted, in-flow-omitted)
    - Return `None` when `tier is None`
    - Delegate non-demo tiers to `build_license_framing`; remove the hardcoded
      "500-record" string and the hardcoded MCP server URL from all tiers (the URL
      lives only in `mcp.json`)
    - Demo tier states the built-in evaluation license is sufficient for the
      stated volume, including the figure only if the agent supplies it
    - _Requirements: 1.3, 1.4, 4.4_

- [x] 2. Property tests for the framing helper (`senzing-bootcamp/tests/test_license_framing.py`)
  - [x] 2.1 Write `st_license_framing_context()` strategy and Property 1 test
    - Strategy generates `capacity` (`None` | non-negative int incl. 0 and large),
      `validity` (`None` | text incl. empty/whitespace), and both booleans
    - **Property 1: Framing presents a default license, never a hard cap**
    - **Validates: Requirements 1.1**
    - `@settings(max_examples=100)`; assert default/built-in evaluation phrasing
      present and no hard-cap phrasing ("hard cap", "maximum of", "cannot
      exceed", "you are limited to")

  - [x] 2.2 Write property test that rendered framing includes every selected path
    - **Property 3: Rendered framing includes every selected expansion path**
    - **Validates: Requirements 2.1, 2.2, 2.4**
    - Assert a description renders for each id from `build_expansion_paths`; in-flow
      MCP path absent when its id is not selected; `@settings(max_examples=100)`

  - [x] 2.3 Write property test for sourced-not-hardcoded figures
    - **Property 4: Capacity and validity figures are sourced, never hardcoded**
    - **Validates: Requirements 1.3, 1.4**
    - Provided values appear verbatim; `None` → figure omitted + "unavailable from
      the MCP server" + no substituted number; `@settings(max_examples=100)`

  - [x] 2.4 Write property test for downsizing co-presentation
    - **Property 5: Downsizing is co-presented, never the sole or primary path**
    - **Validates: Requirements 1.2, 3.1, 3.2**
    - With `mention_downsizing` true, expansion options appear before/alongside the
      downsizing mention (first expansion position not after downsizing);
      `@settings(max_examples=100)`

  - [x] 2.5 Write property test for no hardcoded URLs in output
    - **Property 6: Framing output contains no hardcoded MCP or external URL**
    - **Validates: Requirements 4.4**
    - Across `build_license_framing` and `get_license_guidance`, assert no MCP
      server URL and no external web URL appear; `@settings(max_examples=100)`

- [x] 3. Checkpoint - Ensure helper and property tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Reframe steering touchpoints
  - [x] 4.1 Document the canonical framing snippet and reframe Module 4 data collection
    - In `senzing-bootcamp/steering/module-04-data-collection.md`, present the
      default-license-with-expansion-paths framing where dataset size vs. the
      evaluation limit comes up; present downsizing (sampling, CORD subset, smaller
      substitute) as one option alongside expansion, not the only path
    - Keep the existing full-dataset path (no mandatory downsizing gate) and the
      existing sampling / CORD-subset steps
    - Defer to the Module 1 flow's tool-availability checks and MCP fact sourcing
      rather than restating numbers; introduce no hardcoded MCP/external URLs
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.4_

  - [x] 4.2 Reframe Module 6 data-processing steering to use the refactored helper output
    - In `senzing-bootcamp/steering/module-06-data-processing.md` and the
      `module-06-phase*` files, ensure the volume/license guidance step uses the
      refactored `get_license_guidance` framing and remove any hard-cap phrasing
    - Keep consistent with the Module 1 `submit_feedback` availability gate and
      existing-license routing; no hardcoded MCP/external URLs
    - _Requirements: 4.2, 4.4_

  - [x] 4.3 Verify Module 1 discovery reference contract stays consistent
    - In `senzing-bootcamp/steering/module-01-phase1-discovery.md`, leave the
      Steps 6a–6e flow functionally intact; only adjust wording if it embeds a
      hardcoded figure that should come from MCP
    - _Requirements: 2.5, 4.2_

- [x] 5. Reframe user-facing docs
  - [x] 5.1 Reframe QUICK_START and POWER licensing blurbs
    - In `senzing-bootcamp/docs/guides/QUICK_START.md` and
      `senzing-bootcamp/POWER.md`, reframe the licensing text as a default with
      expansion options instead of a hard cap; avoid hard-cap phrasing
    - _Requirements: 4.3_

  - [x] 5.2 Reframe Module 2 and Module 4 companion docs
    - In `senzing-bootcamp/docs/modules/MODULE_2_SDK_SETUP.md`, keep the factual
      SENZ9000-at-501 explanation but frame the limit as the default evaluation
      license with expansion options
    - In `senzing-bootcamp/docs/modules/MODULE_4_DATA_COLLECTION.md`, present the
      limit as default-with-expansion, mirroring the steering change
    - _Requirements: 4.1, 4.3_

- [x] 6. Content and regression tests
  - [x] 6.1 Write content-validation tests (`senzing-bootcamp/tests/test_license_framing_content.py`)
    - Module 4 steering presents default+expansion framing with no hard-cap phrasing
      and retains the full-dataset path and sampling / CORD-subset steps
    - Module 6 and Module 1 steering use consistent framing and the same
      `submit_feedback` availability gate / existing-license routing
    - `QUICK_START.md`, `POWER.md`, `MODULE_2_SDK_SETUP.md`,
      `MODULE_4_DATA_COLLECTION.md` present the default-with-expansion framing
    - Edited steering files contain no hardcoded MCP URL and no external web URL
    - _Requirements: 2.5, 3.1, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

  - [x] 6.2 Update regression assertions in `test_record_volume_guidance_integration.py`
    - Replace assertions depending on the removed "500-record" literal and the
      removed MCP server URL with assertions on the new framing invariants
      (default/evaluation phrasing, no hard-cap phrasing); keep the demo-tier
      "evaluation" mention assertion
    - Ensure the remaining end-to-end and steering-structure assertions still pass
    - _Requirements: 4.2, 4.3_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (test sub-tasks) and can be skipped for a
  faster MVP; core implementation and content tasks are never optional.
- Each task references specific granular requirements for traceability.
- Property tests use Hypothesis with `@settings(max_examples=100)` per the design's
  Testing Strategy and are tagged
  `# Feature: license-capacity-framing, Property {n}: {text}`.
- Property tests target only the pure helper; live MCP interactions (availability
  checks, fact retrieval, 30s timeout) are runtime agent behaviors validated via
  the Module 1 flow, not property-tested.
- `scripts/volume_utils.py` is edited by a single serialized chain (1.1 → 1.5);
  `test_license_framing.py` is built up across waves to avoid write conflicts.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1", "4.2", "4.3", "5.1", "5.2"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["1.5", "6.1"] },
    { "id": 5, "tasks": ["2.1", "6.2"] },
    { "id": 6, "tasks": ["2.2"] },
    { "id": 7, "tasks": ["2.3"] },
    { "id": 8, "tasks": ["2.4"] },
    { "id": 9, "tasks": ["2.5"] }
  ]
}
```
