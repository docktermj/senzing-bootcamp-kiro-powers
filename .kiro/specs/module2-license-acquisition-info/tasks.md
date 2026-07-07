# Implementation Plan: Module 2 Step 5a License-Acquisition Info

## Overview

This is a **guidance and documentation-only** feature — no application or runtime code changes.
Two artifacts change:

1. `senzing-bootcamp/steering/module-02-sdk-setup.md` — the `### 5a. Explain the built-in evaluation license`
   subsection gains the in-flow MCP license-request mention, names the three acquisition paths, states
   the `submit_feedback`/`license_request` mechanism, carries the availability caveat on that path only,
   stays informational (no `👉`/STOP), directs selection/execution to Step 5c, keeps license figures
   MCP-sourced, and embeds the summarized-explanation instruction.
2. `senzing-bootcamp/tests/test_module2_license_acquisition_info.py` (new) — a stdlib-only,
   class-based guidance-validation test using region extraction over the Step 5a subsection.

Per the design's "Testing Approach Rationale", property-based testing is **not applicable** here
(every acceptance criterion is about static steering content or an external-MCP runtime behavior),
so verification is example-based guidance-validation only.

## Tasks

- [x] 1. Expand the Module 2 Step 5a license explanation (C1)
  - [x] 1.1 Add the three named acquisition paths, the in-flow mechanism, and the availability caveat to the Step 5a subsection
    - Edit `### 5a. Explain the built-in evaluation license` in `senzing-bootcamp/steering/module-02-sdk-setup.md`
    - Retain the existing built-in-evaluation-license explanation text
    - Add an "if you need more than the built-in limit" block that names all three acquisition paths: the in-flow MCP license request, applying an existing license (`.lic` / Base64 → `licenses/g2.lic`), and requesting via Senzing support — the same three paths the Step 5c branch offers, with no path absent from Step 5c
    - State the in-flow path is initiated by the bootcamp invoking the `submit_feedback` MCP tool with the `license_request` category, using the same mechanism wording as the Step 5c branch
    - Attach the Availability_Caveat to the in-flow path only: it depends on `submit_feedback` being both enabled and reported available by the MCP server; `submit_feedback` is disabled by default; the path may be unavailable in a given session and is not guaranteed. Present the apply-existing and support paths without the caveat
    - Keep the Step 5a mention informational only: do NOT add a `👉` pointing question, a STOP marker, or any option-selection/confirmation/execution prompt; direct selection and execution to the Step 5c branch
    - Keep license figures MCP-sourced: any Record_Limit or validity-period figure is retrieved from an MCP tool during the current session and presented exactly as returned; on a missing value or an MCP server unreachable within 30 seconds, omit the figure and tell the bootcamper the value is unavailable from the MCP server — never hardcode a figure or MCP URL
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_

  - [x] 1.2 Embed the summarized-explanation instruction in the Step 5a subsection (C2)
    - In the same Step 5a subsection of `senzing-bootcamp/steering/module-02-sdk-setup.md`, add a behavioral instruction governing the agent's spoken/condensed delivery
    - Require the summary to state that, when more than the Record_Limit is needed, the bootcamp can help request a temporary evaluation license in-flow through the MCP server, in addition to the apply-existing and support paths
    - Require the summary to carry the caveat that the in-flow path depends on `submit_feedback` being available and may be unavailable in a given session
    - _Requirements: 1.5, 2.3_

- [x] 2. Add the guidance-validation test (C4)
  - [x] 2.1 Create `senzing-bootcamp/tests/test_module2_license_acquisition_info.py`
    - Mirror `senzing-bootcamp/tests/test_license_request_option.py`: stdlib only, class-based, region extraction over the Step 5a subsection of `module-02-sdk-setup.md`; build the MCP URL from parts so the test file itself contains no literal URL
    - Assert the in-flow path is presented and names the `submit_feedback` tool + `license_request` category (R1.1, R1.3)
    - Assert all three paths are named (in-flow, apply-existing, support) and that no path is absent from the Step 5c branch (R1.2, R3.5)
    - Assert the Step 5a region contains no `👉` pointing question and no STOP marker, and that the module-wide pointing-question / STOP counts are unchanged (R1.4, R3.3)
    - Assert the summarized-explanation instruction covering the in-flow path and its caveat is present (R1.5, R2.3)
    - Assert the Availability_Caveat (depends on `submit_feedback` enabled + available; disabled by default; may be unavailable; not guaranteed) is stated on the in-flow path, and assert the caveat phrasing is attached only to the in-flow path — apply-existing and support paths appear without it (R2.1, R2.2, R2.4)
    - Cross-check the Step 5a mechanism + availability wording against the Step 5c region to confirm no contradiction (R3.1, R3.2)
    - Assert the Step 5a region directs selection/execution to Step 5c (R3.4)
    - Assert the region instructs MCP-sourced figures with the 30s-unreachable omit-and-notify behavior, plus a negative check for hardcoded record/validity figures (R4.1, R4.2, R4.3, R4.4)
    - Assert no hardcoded MCP server URL appears in the edited region (security/scope guard)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_

- [x] 3. Checkpoint - validate guidance and run tests
  - Ensure all tests pass, ask the user if questions arise.
  - Run the CI pipeline locally to confirm no regressions: `validate_power.py`, `measure_steering.py --check` (steering token budget), `validate_commonmark.py`, `sync_hook_registry.py --verify`, then `python -m pytest senzing-bootcamp/tests/ tests/`

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP. Task 2.1 is the guidance-validation test.
- This feature has no Correctness Properties section in the design, so there are no property-based test tasks — verification is example-based guidance validation only (see the design's "Testing Approach Rationale").
- All edits stay within the Step 5a subsection; Step 5c is unchanged and is the source of truth for the mechanism, availability dependency, and three-path set that Step 5a mirrors.
- No hardcoded MCP URLs or license figures (per `security.md` and `tech.md` MCP-first constraint).
- Each task references specific requirements clauses for traceability.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1"] }
  ]
}
```
