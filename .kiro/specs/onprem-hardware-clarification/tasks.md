# Implementation Plan: On-Premises Hardware Clarification

## Overview

Add a hardware clarification question to Module 8 steering that fires when deployment_target is "on_premises," store the answer in preferences, and reference it in Modules 9 and 11.

## Tasks

- [x] 1. Add hardware clarification question to Module 8 steering
  - [x] 1.1 Locate the Module 8 performance testing steering file (likely `senzing-bootcamp/steering/module-08-performance-testing.md` or similar)
  - [x] 1.2 Add a conditional hardware clarification block at the start of hardware-dependent work (before benchmarking):
    - Condition: `deployment_target == "on_premises"` AND `hardware_target` not already stored in preferences
    - Question: "👉 Will you deploy to this machine, or a different on-premises server? If different, what are the specs (CPU cores, RAM, storage type, database server)?"
    - Include 🛑 STOP hard-stop block after the question
    - Include instructions to store the answer in `config/bootcamp_preferences.yaml`
    - _Requirements: 1, 2_

- [x] 2. Add hardware answer handling logic to Module 8
  - [x] 2.1 After the question, add instructions for processing the bootcamper's response:
    - If "this machine": store `hardware_target: current_machine`, proceed with current specs
    - If different server + specs: store `hardware_target: different_server` with `production_specs`, proceed with provided specs
    - If different server but specs unknown: ask follow-up for missing details
    - _Requirements: 3, 4_

- [x] 3. Add hardware reference to Module 9 steering
  - [x] 3.1 Locate the Module 9 steering file
  - [x] 3.2 Add a conditional block at the start of hardware-dependent work:
    - Read `hardware_target` from preferences
    - If "different_server": use `production_specs` for recommendations, note benchmark vs target difference
    - If "current_machine": use current machine specs
    - Do NOT re-ask the hardware question
    - _Requirements: 4, 5_

- [x] 4. Add hardware reference to Module 11 steering
  - [x] 4.1 Locate the Module 11 deployment steering file
  - [x] 4.2 Add the same conditional block as Module 9 (read stored answer, use appropriate specs)
    - _Requirements: 4, 5_

- [x] 5. Ensure non-on-premises deployments are unaffected
  - [x] 5.1 Verify the conditional is `deployment_target == "on_premises"` — cloud targets (AWS, Azure, GCP) should never trigger this question
    - _Requirements: 6_

- [x] 6. Final verification
  - Confirm Module 8 contains the hardware clarification question with correct conditional
  - Confirm the question has 👉 marker and 🛑 STOP block
  - Confirm Modules 9 and 11 reference stored answer without re-asking
  - Confirm cloud deployment targets are unaffected
  - Run any existing steering validation scripts

## Notes

- The hardware clarification is asked once and stored — not repeated across modules
- This fix only affects on-premises deployments; cloud deployments have their own sizing workflows
- No Python code changes — only steering markdown edits and a preferences schema addition
