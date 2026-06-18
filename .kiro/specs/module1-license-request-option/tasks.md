# Implementation Plan: Module 1 License-Request Option

## Overview

This is content-and-behavior authoring, not application code. The deliverables are edits to
two Markdown artifacts plus a new example-based content-validation test suite:

1. `senzing-bootcamp/steering/module-01-business-problem.md` — Step 6b trigger reference and
   the Step 6d no-license branch (capability verification, tool-enablement, invocation,
   MCP-sourced facts).
2. `senzing-bootcamp/licenses/README.md` — a documented description of the
   License_Request_Option.
3. `senzing-bootcamp/tests/test_license_request_option.py` — a new pytest module (stdlib +
   pytest only, mirroring `test_licensing_guidance.py`) asserting the required content is
   present, correctly scoped, and free of hardcoded MCP URLs and license figures.

Property-based testing does not apply (no pure functions, parsers, or generative input
space). The design has no Correctness Properties section, so testing is example-based
content validation only.

## Tasks

- [x] 1. Author the Module 1 steering edits (Step 6b + Step 6d)
  - [x] 1.1 Add the License_Request_Option reference to the Step 6b trigger
    - Edit `senzing-bootcamp/steering/module-01-business-problem.md`, Step 6b block (around the existing "License Guidance Trigger")
    - Add a sentence naming the in-flow MCP license-request path as one of the available licensing options, alongside the existing apply-existing and external request references
    - Keep the addition concise to respect the Module 1 token budget in `steering-index.yaml`
    - Do not introduce new pointing questions (👉), STOP markers, or hardcoded MCP URLs
    - _Requirements: 1.3_

  - [x] 1.2 Rewrite the Step 6d no-license branch with the capability gate and option behavior
    - Edit the Step 6d block in `senzing-bootcamp/steering/module-01-business-problem.md`; leave Steps 6c and 6e intact
    - Instruct the agent to call `get_capabilities` within the same licensing interaction before presenting options, branching on the decision table: available → present option; unavailable / error / no response within 30s → omit option (Requirements 2.1–2.4)
    - When `submit_feedback` is available, present exactly three distinct, individually selectable paths: License_Request_Option, external request, apply-existing (Requirement 1.1)
    - Describe the License_Request_Option as the MCP in-flow path that generates an evaluation license, delivered by email, with a download link in the email (Requirement 1.2)
    - If the bootcamper already has a license, omit the option and route to the apply-existing path (Requirement 1.4)
    - State that the option requires `submit_feedback` and that `submit_feedback` is disabled by default; give enable instructions pointing at `senzing-bootcamp/mcp.json`, removing `submit_feedback` from `disabledTools`, and saving the file (Requirements 3.1, 3.2)
    - Re-verify via `get_capabilities` after re-enablement; if the bootcamper declines, present only the remaining paths (Requirements 3.3, 3.4)
    - On selection with confirmed availability, invoke `submit_feedback` exactly once with the `license_request` category; on success instruct the email check, then route to Step 6c on receipt; on error/timeout report failure and present the remaining paths without auto-retry (Requirements 4.1–4.4)
    - Where validity period or record capacity is presented, source it from an MCP tool at runtime and omit with an "unavailable from the MCP server" note if retrieval fails — never a hardcoded/training-data figure (Requirements 6.1–6.3)
    - Do not hardcode the MCP server URL; reference the capability generically (per `security.md`)
    - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3_

- [x] 2. Document the option in the licensing reference
  - [x] 2.1 Add a License_Request_Option section to the licensing reference
    - Edit `senzing-bootcamp/licenses/README.md`
    - Describe the option as a path to obtain an evaluation license through the MCP server (Requirement 5.1)
    - State the evaluation license is delivered by email with a download link (Requirement 5.2)
    - State the option invokes the `submit_feedback` MCP tool with the `license_request` category (Requirement 5.3)
    - State that `submit_feedback` is disabled by default (Requirement 5.4)
    - State that enabling the option requires removing `submit_feedback` from the `disabledTools` array in `senzing-bootcamp/mcp.json` (Requirement 5.5)
    - Do not hardcode the MCP server URL or any license validity/capacity figures
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 3. Checkpoint - Verify steering and reference edits
  - Run `senzing-bootcamp/scripts/validate_commonmark.py` and `measure_steering.py --check` against the edited files to confirm Markdown validity and token-budget compliance
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Author the content-validation test suite
  - [x] 4.1 Create the test module and validate the Step 6b/6d steering content
    - Create `senzing-bootcamp/tests/test_license_request_option.py` (stdlib + pytest only, mirroring `test_licensing_guidance.py`: module-level file read, class-based organization, requirement annotations)
    - Add a helper to extract the Step 6b region and assert it names the in-flow MCP license-request path as an available option (R1.3)
    - Add a helper to extract the Step 6d no-license region and assert: three distinct paths referenced (R1.1); option description states MCP server, generates evaluation license, email delivery, download link (R1.2)
    - Assert the `get_capabilities` check is instructed before presenting the option with available/unavailable/30s-timeout/error branches (R2.1–2.4)
    - Assert disabled-by-default messaging, `mcp.json` identification, `disabledTools` removal + save instruction, re-verify after re-enablement, and decline fallback (R3.1–3.4)
    - Assert single-invocation with `license_request` category, email-check success message, Step 6c routing on receipt, and no-auto-retry failure fallback (R4.1–4.4)
    - Assert MCP-sourced facts with an "unavailable" fallback and a negative assertion that no hardcoded validity-period figures (e.g., "30-90 days", "90 days") appear in the 6d region (R6.1–6.3)
    - Add scope/security guards: no `mcp.senzing.com` URL in the edited steering region, and no new 👉 or STOP markers introduced into the 6d region
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3_

  - [x] 4.2 Validate the licensing reference content
    - Add a test class to `senzing-bootcamp/tests/test_license_request_option.py` reading `senzing-bootcamp/licenses/README.md`
    - Assert the reference documents the option as an MCP-server path to an evaluation license (R5.1), email delivery with download link (R5.2), `submit_feedback`/`license_request` invocation (R5.3), disabled-by-default fact (R5.4), and the `disabledTools` removal instruction (R5.5)
    - Add a negative assertion that no `mcp.senzing.com` URL is hardcoded in the reference section
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5. Final checkpoint - Ensure all checks pass
  - Run the full `pytest` suite (including the new content-validation tests) plus `validate_power.py`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP.
- Each task references specific requirements for traceability.
- Checkpoints ensure incremental validation against the existing CI structural checks.
- No property-based tests: the design has no Correctness Properties section; testing is
  example-based content validation following `test_licensing_guidance.py`.
- Tasks 1.1 and 1.2 edit the same steering file and are sequenced into different waves to
  avoid write conflicts; tasks 4.1 and 4.2 write the same test module and are likewise
  sequenced.
- All file placement follows the workspace structure rules (steering under
  `senzing-bootcamp/steering/`, reference under `senzing-bootcamp/licenses/`, tests under
  `senzing-bootcamp/tests/`); stdlib + pytest only; no hardcoded MCP URLs.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["4.1"] },
    { "id": 3, "tasks": ["4.2"] }
  ]
}
```
