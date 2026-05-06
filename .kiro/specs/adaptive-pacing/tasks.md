# Tasks: Adaptive Pacing Based on Session Analytics

## Task 1: Implement pacing classification in analyze_sessions.py

- [x] 1.1 Read the current `senzing-bootcamp/scripts/analyze_sessions.py` to understand existing data structures and functions
- [x] 1.2 Add a `classify_pacing(entries: list[dict]) -> dict[int, str]` function that computes per-module metrics and returns a mapping of module number to pacing category ("struggled", "comfortable", "normal")
- [x] 1.3 Implement the classification logic: correction_density > 0.3 OR time > 2× median → "struggled"; density < 0.1 AND time < median → "comfortable"; else "normal"
- [x] 1.4 Handle edge cases: empty entries list returns empty dict, single module returns "normal" (no median comparison possible), modules with zero turns are skipped
- [x] 1.5 Add a `merge_with_overrides(computed: dict, overrides: dict) -> dict` function that applies manual pacing_overrides from preferences, with overrides taking precedence

## Task 2: Add Adaptive Pacing section to agent-instructions.md

- [x] 2.1 Add an "### Adaptive Pacing" subsection to the Module Steering section of `senzing-bootcamp/steering/agent-instructions.md`
- [x] 2.2 Document the three pacing categories and their effects on agent behavior (explanation depth, "why" framing, proactive offers)
- [x] 2.3 Document the override mechanism: "slow down" → set current module to "struggled", "speed up" → set current module to "comfortable"
- [x] 2.4 Document integration with verbosity control: pacing adjusts baseline but never reduces below explicit verbosity preference

## Task 3: Update session-resume.md to read session analytics

- [x] 3.1 Add instruction to Step 1 (Read All State Files) in `senzing-bootcamp/steering/session-resume.md` to read `config/session_log.jsonl` if it exists
- [x] 3.2 Add instruction to compute pacing classifications from session analytics and store in working memory
- [x] 3.3 Add instruction to read `pacing_overrides` from `config/bootcamp_preferences.yaml` and merge with computed classifications

## Task 4: Add pacing_overrides to preferences schema

- [x] 4.1 Update `senzing-bootcamp/steering/agent-instructions.md` State & Progress section to document the `pacing_overrides` key in `bootcamp_preferences.yaml`
- [x] 4.2 Document the schema: mapping of module number (int) to pacing category string ("struggled", "comfortable", "normal")

## Task 5: Write property-based tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_adaptive_pacing.py` with Hypothesis strategies for session log entries (valid module numbers, turn/correction events, timestamps)
- [x] 5.2 Property test: classification is deterministic — same inputs always produce same output
- [x] 5.3 Property test: manual overrides always take precedence over computed values
- [x] 5.4 Property test: empty session log produces empty classification dict
- [x] 5.5 Property test: all returned values are in {"struggled", "comfortable", "normal"}
- [x] 5.6 Property test: modules with zero turns are never classified (excluded from output)

## Task 6: Write unit tests

- [x] 6.1 Unit test: module with correction_density 0.5 → "struggled"
- [x] 6.2 Unit test: module with time > 2× median → "struggled"
- [x] 6.3 Unit test: module with density 0.05 and time < median → "comfortable"
- [x] 6.4 Unit test: module with density 0.2 and normal time → "normal"
- [x] 6.5 Unit test: single completed module → "normal" (no median comparison)
- [x] 6.6 Unit test: merge_with_overrides correctly applies manual overrides

## Task 7: Validate

- [x] 7.1 Run `pytest senzing-bootcamp/tests/test_adaptive_pacing.py -v` and confirm all tests pass
- [x] 7.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified steering files
- [x] 7.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets
