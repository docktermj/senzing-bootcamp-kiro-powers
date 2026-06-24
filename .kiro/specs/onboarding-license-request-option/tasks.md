# Implementation Plan

## Overview

Add the in-flow MCP license-request path as a third licensing option in the Module 0 onboarding
overview (`senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`, Step 5), and add a
focused test asserting the third option is present and no URLs are introduced. This is a
documentation-only change; the authoritative offer/gating logic stays in Module 1.

## Tasks

- [x] 1. Write the content test (before editing the steering file)
  - Create `senzing-bootcamp/tests/test_onboarding_license_request_option.py` (stdlib + pytest,
    `from __future__ import annotations`, class-based, per `python-conventions.md`)
  - **test_overview_mentions_in_flow_mcp_request**: read the steering file and assert the Step 5
    overview licensing content references requesting an evaluation license through the Senzing MCP
    server (Property 1)
  - **test_overview_mentions_apply_existing_license**: assert the apply/bring-your-own path is
    still present (Property 1)
  - **test_no_urls_in_licensing_content**: assert the licensing region contains no MCP URL and no
    external URL (Property 2)
  - Run on the unedited file: the first test FAILS (the line only mentions built-in + bring your
    own), the others PASS — documents the gap
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Rewrite the onboarding licensing bullet
  - Edit the Step 5 "Bootcamp Introduction" overview list in
    `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`
  - Replace `- Built-in 500-record eval license; bring your own for more` with wording that
    presents three options (built-in default, apply existing license, in-flow MCP request) and
    points to Module 1 for the offer/gating, per the design's proposed wording
  - Frame the built-in license as the default the bootcamper already has; do not introduce a new
    hardcoded validity/capacity figure for the requested license
  - Refer to the Senzing MCP server by name only — no MCP URL, no external URL
  - Do not claim the in-flow request is always available or always succeeds
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 3.1, 3.2_

- [x] 3. Verify tests, CommonMark, and token budget
  - Run `pytest senzing-bootcamp/tests/test_onboarding_license_request_option.py` — all tests PASS
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` — passes
  - Run `python senzing-bootcamp/scripts/measure_steering.py --check`; if the edit pushes
    `onboarding-phase1b-intro-language.md` over budget, update its entry in
    `senzing-bootcamp/steering/steering-index.yaml` and re-run until it passes
  - _Requirements: 3.3, 4.1, 4.2_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3"] }
  ]
}
```

- **Wave 0** — `[1]`: write the content test against the unedited steering file (the
  in-flow-MCP assertion FAILS, documenting the gap).
- **Wave 1** — `[2]`: rewrite the onboarding licensing bullet.
- **Wave 2** — `[3]`: verify tests, CommonMark, and the steering token budget.

## Notes

- Documentation-only change to one steering file plus one stdlib pytest module; no new CI step.
- The authoritative in-flow license-request offer and `get_capabilities` gating stay in Module 1
  (`module1-license-request-option`); the onboarding overview is only a pointer to it.
- Refer to the Senzing MCP server by name only — no MCP URL, no external URL (security gate).
