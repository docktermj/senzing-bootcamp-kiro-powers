# Implementation Tasks: enforce-visualization-step

## Task 1: Create the gate-module3-visualization hook

- [x] Create `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook` with the preToolUse hook JSON that gates Module 3 completion on `web_service` and `web_page` checkpoint presence
- [x] Validate the hook JSON has required fields: `name`, `version`, `when` (type: preToolUse, toolTypes: ["write"]), `then` (type: askAgent, prompt)
- [x] Verify the hook prompt includes the skip-step exception (checks for `skipped_steps["3.9"]`)

## Task 2: Add mandatory gate marker to Step 9 in module-03-system-verification.md

- [x] Add `⛔ MANDATORY GATE` line immediately after the Step 9 heading in `senzing-bootcamp/steering/module-03-system-verification.md`
- [x] Text: `⛔ MANDATORY GATE — This step cannot be skipped without explicit bootcamper request via the skip-step protocol. The visualization is the "wow moment" of Module 3.`

## Task 3: Add pre-report validation to Step 10

- [x] Insert a pre-report validation paragraph at the beginning of Step 10 (Verification Report Generation) in `senzing-bootcamp/steering/module-03-system-verification.md`
- [x] The validation checks for `web_service` and `web_page` checkpoint entries before compiling the report
- [x] If entries are missing: instruct agent to STOP and return to Step 9
- [x] If entries show "failed": include failure in report and proceed (attempted but failed is acceptable for report generation)

## Task 4: Update success criteria checkpoint count

- [x] Update the Success Criteria section in `senzing-bootcamp/steering/module-03-system-verification.md` to reference "10 verification checkpoint entries" instead of "8 verification checks"
- [x] List all 10 entries explicitly: mcp_connectivity, truthset_acquisition, sdk_initialization, code_generation, build_compilation, data_loading, results_validation, database_operations, web_service, web_page

## Task 5: Register hook in hook-categories.yaml

- [x] Add `gate-module3-visualization` to the module 3 list in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] Place it between `enforce-visualization-offers` and `verify-demo-results` (alphabetical order within the module)

## Task 6: Run validation suite

- [x] Run `python3 senzing-bootcamp/scripts/validate_power.py` to confirm power structure is valid
- [x] Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` to confirm hook registry is consistent with hook-categories.yaml
- [x] Run `pytest` to confirm no regressions in existing tests
