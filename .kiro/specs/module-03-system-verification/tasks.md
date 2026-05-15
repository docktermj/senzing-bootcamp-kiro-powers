# Implementation Plan: Module 03 — System Verification

## Overview

Redesign Module 3 from "Quick Demo" to "System Verification." Replace the existing steering file with a deterministic verification pipeline using TruthSet data. Update all references across the bootcamp (module dependencies, onboarding flow, steering index, documentation). Add property-based and unit tests validating the new structure.

## Tasks

- [x] 1. Create the new Module 3 steering file
  - [x] 1.1 Create `senzing-bootcamp/steering/module-03-system-verification.md` with Phase 1 (Verification Pipeline)
    - Create the new steering file with YAML frontmatter (`inclusion: manual`)
    - Include module header (prerequisites: Module 2, before/after framing, language instruction)
    - Write Phase 1 steps 1–9:
      - Step 1: MCP Connectivity Check (call `search_docs`, 10s timeout, retry once on failure)
      - Step 2: TruthSet Acquisition (call `get_sample_data` for TruthSet, save to `src/system_verification/truthset_data.jsonl`, validate line count and JSON format)
      - Step 3: SDK Initialization (generate via `generate_scaffold(workflow='initialize')`, save to `verify_init.[ext]`, execute with 30s timeout)
      - Step 4: Code Generation (generate via `generate_scaffold(workflow='full_pipeline')`, save to `verify_pipeline.[ext]`, validate non-empty with structural elements)
      - Step 5: Build/Compile (language-specific build commands table, 120s timeout, Python uses `py_compile`)
      - Step 6: Data Loading (execute verification script, 120s timeout, progress indicator, match expected record count)
      - Step 7: Deterministic Results Validation (query entities, check count within ±5%, verify 3 known matches, confirm entity count < record count)
      - Step 8: Database Operations (verify write count, read by entity ID, search by attributes, 30s timeout each)
      - Step 9: Web Service + Page (generate web service via MCP, start service, verify health endpoint HTTP 200 within 10s, verify entity query endpoint, verify HTML page accessible)
    - Each step includes a checkpoint write to `config/bootcamp_progress.json`
    - _Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 12_

  - [x] 1.2 Add Phase 2 (Report & Close) and supporting sections to the steering file
    - Write Phase 2 steps 10–12:
      - Step 10: Verification Report Generation (structured pass/fail for all 8 checks, success banner or failure list with Fix_Instructions, persist to `config/bootcamp_progress.json` with ISO 8601 timestamp)
      - Step 11: Cleanup (terminate web service within 5s, display test-only message, purge TruthSet from database)
      - Step 12: Module Close (follow `module-completion.md` workflow, journal entry, reflection question, transition to Module 1)
    - Add Error Handling section (SENZ error codes → `explain_error_code`, common-pitfalls.md, cross-module resources)
    - Add Success Criteria section
    - Add Agent Rules section (must use TruthSet only, database path `database/G2C.db`, no dataset choice, all checks execute regardless of failures)
    - _Requirements: 10, 11, 13_

- [x] 2. Update module references across the bootcamp
  - [x] 2.1 Update `senzing-bootcamp/config/module-dependencies.yaml`
    - Change Module 3 name from "Quick Demo" to "System Verification"
    - Update `skip_if` to "Already familiar with Senzing and system verified"
    - Update gate `"3->4"` requires to "System verification passed or skipped"
    - _Requirements: 11.1, 11.2, 11.3, 11.5_

  - [x] 2.2 Update `senzing-bootcamp/steering/onboarding-flow.md` Module 3 references
    - In Step 5 (Track Selection), replace "Quick Demo" with "System Verification" in track descriptions
    - Update the gate conditions table entry for 3→4
    - Update any other mentions of "Quick Demo" or "Module 3" name
    - _Requirements: 11.1_

  - [x] 2.3 Update `senzing-bootcamp/steering/steering-index.yaml`
    - Replace the `module-03-quick-demo.md` entry with `module-03-system-verification.md`
    - Update the description and token budget estimate
    - _Requirements: 11.1_

  - [x] 2.4 Update `senzing-bootcamp/steering/visualization-protocol.md` Module 3 checkpoint
    - Update the `m3_demo_results` checkpoint context from "these entity resolution demo results" to "these system verification results"
    - Update the trigger from "Demo results displayed successfully" to "Verification results displayed successfully"
    - _Requirements: 7, 8_

- [x] 3. Create module documentation
  - [x] 3.1 Create `senzing-bootcamp/docs/modules/MODULE_3_SYSTEM_VERIFICATION.md`
    - Write user-facing documentation explaining:
      - Purpose of Module 3 (system verification gate)
      - Why TruthSet is used (deterministic, known-good outcomes)
      - What each verification step confirms
      - What to do if checks fail
      - How to re-run verification after fixes
    - Follow the pattern of existing module docs
    - _Requirements: 10.3, 10.4_

- [x] 4. Remove or redirect old Module 3 files
  - [x] 4.1 Remove `senzing-bootcamp/steering/module-03-quick-demo.md`
    - Delete the old steering file (replaced by `module-03-system-verification.md`)
    - Verify no other steering files reference `module-03-quick-demo.md` by name
    - _Requirements: 11.1_

  - [x] 4.2 Remove or update `senzing-bootcamp/docs/modules/MODULE_3_QUICK_DEMO.md` if it exists
    - If the file exists, remove it (replaced by `MODULE_3_SYSTEM_VERIFICATION.md`)
    - _Requirements: 11.1_

- [x] 5. Write property-based and unit tests
  - [x] 5.1 Create `senzing-bootcamp/tests/test_system_verification_properties.py` with test infrastructure
    - Create the test file with imports (pytest, hypothesis, pathlib, re)
    - Define helper functions to read the steering file and parse sections
    - Set up the `TestSystemVerificationProperties` class
    - _Requirements: 1.1, 10.2_

  - [x] 5.2 Write property tests
    - **Property 1: No dataset choice offered** — steering file contains no dataset selection prompt, no CORD/Las Vegas/London/Moscow choice language
    - **Property 2: All checks listed** — every check name from the report schema appears in the steering file
    - **Property 3: Artifact paths isolated** — all generated file paths in the steering file are under `src/system_verification/`
    - **Property 4: Timeouts defined** — every verification step references an explicit timeout value
    - **Property 5: Build commands per language** — build command section covers Python, Java, C#, Rust, TypeScript
    - _Requirements: 1.1, 4.1, 4.4, 10.2, 13.1_

  - [x] 5.3 Create `senzing-bootcamp/tests/test_system_verification_unit.py` with unit tests
    - `test_steering_file_uses_truthset_only` — no dataset choice in steering file (Req 1.1)
    - `test_steering_file_has_all_verification_steps` — all 8 check types present (Req 10.2)
    - `test_module_dependencies_updated` — Module 3 name is "System Verification" (Req 11.1)
    - `test_gate_condition_updated` — gate 3→4 references system verification (Req 11.2, 11.5)
    - `test_steering_file_has_web_service_step` — web service generation step exists (Req 7.1)
    - `test_steering_file_has_cleanup_step` — cleanup and purge instructions present (Req 13.4, 13.5)
    - `test_steering_file_references_module_completion` — module close references `module-completion.md` (Req 11.4)
    - `test_onboarding_flow_references_updated` — onboarding flow uses "System Verification" name (Req 11.1)
    - `test_build_commands_for_all_languages` — build table has entries for all 5 languages (Req 4.1, 4.4)
    - `test_verification_report_schema` — report JSON structure matches expected schema (Req 10.5)
    - _Requirements: 1.1, 4.1, 4.4, 7.1, 10.2, 10.5, 11.1, 11.2, 11.4, 11.5, 13.4, 13.5_

- [x] 6. Final checkpoint — Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_system_verification_properties.py senzing-bootcamp/tests/test_system_verification_unit.py -v` and ensure all tests pass. Ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- The steering file is the primary deliverable — it defines agent behavior for Module 3
- All verification code is generated at runtime by the MCP server, not shipped as static files
- TruthSet expected results are retrieved from MCP at runtime, not hardcoded
- The old `module-03-quick-demo.md` is deleted, not preserved alongside the new file
- Tests validate steering file structure and cross-file consistency, not runtime behavior

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "3.1", "4.1", "4.2"] },
    { "id": 2, "tasks": ["5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3"] }
  ]
}
```
