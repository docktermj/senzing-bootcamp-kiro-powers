# Tasks: Budget Threshold Consistency

## Task 1: Update measure_steering.py to derive thresholds from percentages

- [x] 1.1 Read the current `measure_steering.py` to understand how it computes threshold checks
- [x] 1.2 Update the threshold computation to read `reference_window`, `warn_threshold_pct`, and `critical_threshold_pct` from the budget section and compute absolute values as `reference_window * pct / 100`
- [x] 1.3 Remove any hardcoded threshold values (120000, 160000) if present
- [x] 1.4 Verify `python3 senzing-bootcamp/scripts/measure_steering.py --check` still passes

## Task 2: Update agent-instructions.md

- [x] 2.1 Replace absolute token references (120k, 160k, 120000, 160000) in the Context Budget section with percentage-based language ("60% of context budget", "80% of context budget")
- [x] 2.2 Verify the retention priority list and other budget-related instructions remain unchanged

## Task 3: Update STEERING_INDEX.md documentation

- [x] 3.1 Update the Budget section in `senzing-bootcamp/docs/guides/STEERING_INDEX.md` to explain that percentage fields are authoritative and absolute thresholds are derived as `reference_window × (pct / 100)`
- [x] 3.2 Add an example showing the derivation: "With reference_window: 200000 and warn_threshold_pct: 60, the warn threshold is 120,000 tokens"

## Task 4: Validate

- [x] 4.1 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and confirm exit code 0
- [x] 4.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified markdown files
- [x] 4.3 Run `pytest senzing-bootcamp/tests/` to confirm no regressions
