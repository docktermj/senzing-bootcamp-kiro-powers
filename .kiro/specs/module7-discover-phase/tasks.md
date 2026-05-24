# Tasks

## Task 1: Create the Discover phase steering file

- [x] Create `senzing-bootcamp/steering/module-07-phase2-discover.md` with YAML frontmatter (`inclusion: manual`), phase header, session resumption instruction, and the full Discover phase implementation (steps 4a–4e)
- [x] Implement Step 4a (Data Pattern Analysis): agent instructions to identify multi-record entities (3+ records), cross-source entities, and relationship clusters from the bootcamper's loaded data, with a summary presentation and graceful fallback for limited data
- [x] Implement Step 4b (Why Analysis Introduction): agent instructions to demonstrate `why_entities`/`why_records` with `SZ_INCLUDE_FEATURE_SCORES` and `SZ_INCLUDE_MATCH_KEY_DETAILS` flags, plain-language explanation of features/scores/matching principles, match key breakdown, and practical use cases
- [x] Implement Step 4c (How Analysis Introduction): agent instructions to demonstrate `how_entity` with `SZ_INCLUDE_FEATURE_SCORES` flag on a 3+ record entity, chronological narrative presentation, why-vs-how comparison, and practical use cases
- [x] Implement Step 4d (Relationship Network Exploration): agent instructions to demonstrate `find_network` and `find_path` with flag lookup via `get_sdk_reference`, network structure explanation, and graceful fallback if no relationships exist
- [x] Implement Step 4e (Data-Specific Visualization Suggestions): agent instructions to suggest 2+ visualizations from the catalog (cross-source heatmap, entity size distribution, network graph, match key frequency, feature score distribution), explain relevance, generate if selected using `visualization-guide.md`, and handle decline
- [x] Add checkpoint definitions for each sub-step (4a–4e) writing to `config/bootcamp_progress.json`
- [x] Add early exit flow after each demonstration asking if the bootcamper wants to continue or proceed to module completion
- [x] Add opt-in introduction at the start of the Discover phase asking the bootcamper if they want to proceed, with skip-to-gate handling if declined

## Task 2: Update the Module 7 root steering file

- [x] Add step 4 entry to `senzing-bootcamp/steering/module-07-query-visualize-discover.md` after step 3d, referencing `module-07-phase2-discover.md` as the phase file for the Discover phase
- [x] Update the Success Criteria section to include "✅ Discover phase completed or explicitly skipped"
- [x] Update the Query Completeness Gate to add a check that the Discover phase was either completed or explicitly skipped by the bootcamper before allowing module completion
- [x] Verify the step 4 entry follows the existing agent instruction format (blockquote with `>` for phase file reference)

## Task 3: Update steering-index.yaml

- [x] Convert the module 7 entry in `senzing-bootcamp/steering/steering-index.yaml` from a simple string (`7: module-07-query-visualize-discover.md`) to a phased structure with `root`, `phases.phase1-query-visualize` (existing file, step_range [1, "3d"]), and `phases.phase2-discover` (new file, step_range ["4a", "4e"])
- [x] Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get the actual token counts for both the updated root file and the new phase file
- [x] Update the token counts and size categories in the module 7 phased structure and in the `file_metadata` section
- [x] Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token counts are accurate

## Task 4: Validate with CI checks

- [x] Run `python3 senzing-bootcamp/scripts/validate_power.py` to verify power structure is valid with the new steering file
- [x] Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify both the updated root file and new phase file are valid CommonMark
- [x] Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` to verify hook registry remains in sync
- [x] Run `pytest` to verify all existing tests pass with the new steering file present
