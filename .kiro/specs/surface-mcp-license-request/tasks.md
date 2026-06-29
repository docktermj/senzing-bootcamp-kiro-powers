# Implementation Plan

## Overview

This plan surfaces the in-flow MCP license-request option in Module 2 Step 5, mirroring the
tested Module 1 Step 6d branch. The work is test-first: add a failing guidance-validation
test, edit the Step 5c no-license branch and the Module 2 companion doc, then turn the
suite and CI checks green. No application/runtime code is involved; all edits are steering,
documentation, and a new test.

## Tasks

- [x] 1. Add the failing guidance-validation test (red)
  - Create `senzing-bootcamp/tests/test_module2_license_request_option.py`, mirroring `senzing-bootcamp/tests/test_license_request_option.py` (stdlib + Hypothesis, class-based, region-extraction helpers). Follow the repo Python conventions (`from __future__ import annotations`, `X | None` hints, profile-driven Hypothesis settings).
  - Extract the Step 5c no-license sub-branch from `module-02-sdk-setup.md` and the "Senzing License Requirements" section from `docs/modules/MODULE_2_SDK_SETUP.md` as test regions.
  - Assert the Step 5c behaviors: three ordered selectable paths with the in-flow description (MCP server, evaluation license, email, download link); `get_capabilities` gate with the 30s window; available vs unavailable/error/timeout branches and the unavailable-session message; disabled-by-default messaging and `mcp.json`/`disabledTools` enable + re-verify + decline fallback; single `license_request` invocation, success email guidance, route to Step 5d, failure no-retry fallback; MCP-sourced license facts.
  - Assert the doc section satisfies R5.1–R5.5, and add scope/security guards (no hardcoded MCP URL in edited regions; no hardcoded validity-period figures; Step 5 pointing-question and STOP marker counts unchanged).
  - Run the test and confirm the new assertions FAIL against current (unfixed) content.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. Add the availability gate and three-path presentation to Step 5c
  - In `senzing-bootcamp/steering/module-02-sdk-setup.md`, restructure the `### 5c. Handle the response` "no license" block: before presenting paths, call `get_capabilities` within the same Step 5 interaction and wait for a response, error, or 30s (design C1, Architecture).
  - Present the in-flow MCP request path first, the external request path second, and the apply-an-existing-license path third, as distinct individually selectable options, with the in-flow description (MCP server, evaluation license, email delivery, download link). Retain the existing external-contact text as the external request path and point apply-existing at Step 5d.
  - Encode the omit-and-notify behavior for unavailable / error / timeout / unrecognized `submit_feedback` value, the selection handling, and the unrecognized-response re-presentation.
  - _Requirements: 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.4_

- [x] 3. Add the disabled-by-default enablement and invocation steps to Step 5c
  - Add the disabled-by-default messaging, the `senzing-bootcamp/mcp.json` / `disabledTools` removal-and-save instructions, the re-verify-via-`get_capabilities` step, and the decline fallback (design C1; mirror Module 1 Step 6d wording for R7.1–R7.3).
  - Add the single `submit_feedback` `license_request` invocation, the success email-check guidance, the route to Step 5d on confirmed receipt, and the failure (error/timeout) non-completion + remaining-paths + no-auto-retry handling.
  - Add the already-licensed routing: if a license was already configured/applied earlier in the session (or the bootcamper indicated a file/Base64 key in 5b), omit the in-flow option and route to apply-existing.
  - Ensure validity-period / record-capacity figures are MCP-sourced with the unavailable fallback, and that no MCP URL or hardcoded validity figures are introduced.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 6.1, 6.2, 6.3, 7.2, 7.3, 7.5_

- [x] 4. Document the in-flow option in the Module 2 companion doc
  - In the "Senzing License Requirements" section of `senzing-bootcamp/docs/modules/MODULE_2_SDK_SETUP.md`, expand the existing in-flow bullet into a full description (design C3): identify it as an in-flow MCP path available outside the Step 5 flow; state email delivery with a download link; name the `submit_feedback` tool and `license_request` category; state the tool is disabled by default (non-functional until enabled); give the enable instruction (remove `submit_feedback` from `disabledTools` in `senzing-bootcamp/mcp.json`).
  - Preserve the existing external-channel and base64/`.lic` instructions; keep license facts MCP-sourced (no hardcoded figures).
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5. Run the test suite and CI checks (green)
  - Re-run `test_module2_license_request_option.py` and confirm all assertions now PASS.
  - Run the existing `test_license_request_option.py` to confirm Module 1 behavior is unaffected.
  - Run the CI validators that touch steering/docs: `measure_steering.py --check` (token budget) and `validate_commonmark.py` (CommonMark), then the full `pytest` suite (default `fast` profile locally; `HYPOTHESIS_PROFILE=thorough` to match CI).
  - Fix any token-budget or CommonMark issues introduced by the added guidance before closing the task.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 7.4, 7.5_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1"],
      "description": "Add the failing guidance-validation test (red)."
    },
    {
      "wave": 2,
      "tasks": ["2", "3", "4"],
      "description": "Steering edits to Step 5c (Tasks 2-3) and the Module 2 doc (Task 4); all depend on Task 1. Task 3 builds on Task 2's restructured Step 5c, so sequence 2 before 3; Task 4 is independent of 2-3."
    },
    {
      "wave": 3,
      "tasks": ["5"],
      "description": "Run the suite and CI checks to turn the tests green; depends on Tasks 2-4."
    }
  ]
}
```

- Task 1 first (red test).
- Task 2 then Task 3 (Task 3 edits the Step 5c block Task 2 restructures); Task 4 is the doc edit and can run anytime after Task 1.
- Task 5 last, once Tasks 2–4 are complete.

## Notes

- Tests assert steering/doc content (not runtime execution), consistent with the existing
  `test_license_request_option.py` lock-in pattern.
- Mirror the Module 1 Step 6d wording wherever R7 requires consistency, so the cross-module
  consistency assertions hold.
- Respect the per-file token budgets in `steering-index.yaml`; keep the added Step 5c
  guidance concise (Task 5 verifies via `measure_steering.py --check`).
- Never hardcode the MCP server URL or license validity/capacity figures — facts are
  MCP-sourced at runtime.
