# Tasks: "Where Am I?" Quick Status Command

## Task 1: Create inline-status.md steering file

- [x] 1.1 Create `senzing-bootcamp/steering/inline-status.md` with YAML frontmatter (`inclusion: manual`)
- [x] 1.2 Write the response format template with 📍 emoji, module/step position, track completion, data sources, and next milestone
- [x] 1.3 Document the track completion calculation logic (completed modules + partial credit for current module)
- [x] 1.4 Document edge cases: no progress file, between modules, track not selected
- [x] 1.5 Include the list of trigger phrases that activate this response

## Task 2: Update steering-index.yaml

- [x] 2.1 Add keyword entries mapping status trigger phrases to `inline-status.md`: "where am I", "status", "what step am I on", "show progress", "how far along am I"
- [x] 2.2 Add `file_metadata` entry for `inline-status.md` with token count and size category
- [x] 2.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py` to compute accurate token count

## Task 3: Update review-bootcamper-input hook

- [x] 3.1 Read the current `senzing-bootcamp/hooks/review-bootcamper-input.kiro.hook` to understand its prompt structure
- [x] 3.2 Add status trigger phrase detection to the hook prompt (alongside existing feedback trigger detection)
- [x] 3.3 Add output instruction: when status trigger detected, output "STATUS_TRIGGER_DETECTED" so the agent knows to respond with inline status format
- [x] 3.4 Update `senzing-bootcamp/steering/hook-registry.md` to reflect the updated review-bootcamper-input prompt

## Task 4: Write tests

- [x] 4.1 Create `senzing-bootcamp/tests/test_where_am_i_status.py`
- [x] 4.2 Unit test: `inline-status.md` exists and has `inclusion: manual` frontmatter
- [x] 4.3 Unit test: steering-index.yaml contains keyword entries for all 5 trigger phrases
- [x] 4.4 Unit test: review-bootcamper-input hook prompt contains status trigger phrases
- [x] 4.5 Unit test: inline-status.md contains response template with required elements (📍, track, data sources, 👉)
- [x] 4.6 Property test: track completion percentage calculation always returns 0-100 for valid inputs
- [x] 4.7 Unit test: hook-registry.md entry for review-bootcamper-input mentions status triggers

## Task 5: Validate

- [x] 5.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on new/modified files
- [x] 5.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
- [x] 5.3 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
- [x] 5.4 Run `pytest senzing-bootcamp/tests/test_where_am_i_status.py -v`
