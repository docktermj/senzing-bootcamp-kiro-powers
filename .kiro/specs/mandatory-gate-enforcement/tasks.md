# Tasks

## Task 1: Create the `enforce-gate-on-stop` hook file

- [x] Create `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook` with the agentStop hook JSON that checks `config/bootcamp_progress.json` after each agent turn during Module 3 and forces Step 9 execution if the mandatory gate checkpoint is missing
- [x] Validate the hook JSON has required fields: `name`, `version`, `description`, `when.type` = `"agentStop"`, `then.type` = `"askAgent"`, `then.prompt` with enforcement logic
- [x] Verify the hook prompt checks: (1) current_module = 3, (2) current_step ≥ 9, (3) checkpoint conditions A and B, (4) outputs blocking message only when neither condition is met

## Task 2: Add pre-advancement verification to Module 3 steering

- [x] Edit `senzing-bootcamp/steering/module-03-system-verification.md` to add a `⛔ PRE-ADVANCEMENT VERIFICATION` blockquote instruction after the Step 9 section, requiring the agent to verify `web_service` and `web_page` checkpoints exist before offering advancement to Module 4
- [x] Ensure the new instruction follows the existing agent instruction format (blockquote with `>`)
- [x] Verify the instruction does not duplicate or conflict with existing mandatory gate language in the same file

## Task 3: Update hook registry with new hook

- [x] Add `enforce-gate-on-stop` entry to the hook table in `senzing-bootcamp/steering/hook-registry.md` with module 3, trigger `agentStop → askAgent`, and description
- [x] Add detailed entry to `senzing-bootcamp/steering/hook-registry-detail.md` with full prompt text and behavior description
- [x] Verify the new entry follows the existing format and ordering conventions in both registry files

## Task 4: Update steering-index.yaml token count

- [x] Measure the updated token count for `module-03-system-verification.md` after the steering reinforcement is added
- [x] Update the `token_count` value for module 3 phase1-verification in `senzing-bootcamp/steering/steering-index.yaml`
- [x] Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify the token count is accurate

## Task 5: Add hook to hook-categories.yaml

- [x] Add `enforce-gate-on-stop` to the appropriate category in `senzing-bootcamp/hooks/hook-categories.yaml` (likely the enforcement/gate category alongside `enforce-mandatory-gate` and `gate-module3-visualization`)
- [x] Verify the entry follows the existing format in the categories file

## Task 6: Validate with CI checks

- [x] Run `python3 senzing-bootcamp/scripts/validate_power.py` to verify power structure is valid
- [x] Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify updated markdown files are valid CommonMark
- [x] Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` to verify hook registry is in sync with hook files
- [x] Run `pytest` to verify all existing tests pass with the new hook file present
