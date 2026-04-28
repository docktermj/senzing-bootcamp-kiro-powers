# Tasks

## Task 1: Create `measure_steering.py` core functions

- [x] 1.1 Create `senzing-bootcamp/scripts/measure_steering.py` with `calculate_token_count(filepath)` that reads a file and returns `round(len(content) / 4)`
- [x] 1.2 Add `classify_size(token_count)` that returns `small` (<500), `medium` (500–2000), or `large` (>2000)
- [x] 1.3 Add `scan_steering_files(steering_dir)` that scans all `.md` files and returns a dict of `{filename: {token_count, size_category}}`
- [x] 1.4 Add `print_summary(file_metadata, total_tokens)` that prints a formatted table to stdout with each file's name, token count, size category, and the total

## Task 2: Add YAML update logic to `measure_steering.py`

- [x] 2.1 Add `load_yaml_content(index_path)` that reads the raw YAML text of `steering-index.yaml`
- [x] 2.2 Add `update_index(index_path, file_metadata, total_tokens)` that writes `file_metadata` and `budget` sections into the YAML file, preserving all existing content (`modules`, `keywords`, `languages`, `deployment`, `references`)
- [x] 2.3 Add `main()` with argparse: default mode runs scan + update + print summary; `--check` flag runs validation mode
- [x] 2.4 Add `check_counts(index_path, calculated)` that compares stored vs. calculated token counts and returns mismatches exceeding 10% tolerance; exits non-zero if any found, without modifying the file

## Task 3: Extend `steering-index.yaml` with token metadata

- [x] 3.1 Run `measure_steering.py` to populate `file_metadata` and `budget` sections in `senzing-bootcamp/steering/steering-index.yaml`
- [x] 3.2 Verify all existing sections (`modules`, `keywords`, `languages`, `deployment`, `references`) are preserved unchanged

## Task 4: Add Context Budget section to `agent-instructions.md`

- [x] 4.1 Append a `## Context Budget` section to `senzing-bootcamp/steering/agent-instructions.md` with rules for consulting `file_metadata` before loading, tracking cumulative token count, preferring small/medium files, warn threshold (60%) behavior, critical threshold (80%) behavior, retention priority order, and large-file announcement rule

## Task 5: Extend `validate_power.py` with steering index schema validation

- [x] 5.1 Add `check_steering_index_metadata()` function to `senzing-bootcamp/scripts/validate_power.py` that validates `file_metadata` mapping exists, every `.md` file has a valid entry, `size_category` is one of `small`/`medium`/`large`, and `budget` mapping has all required fields
- [x] 5.2 Call `check_steering_index_metadata()` from `main()` in the existing validation flow

## Task 6: Integrate token count validation into CI

- [x] 6.1 Add a "Validate steering token counts" step to `.github/workflows/validate-power.yml` that runs `python senzing-bootcamp/scripts/measure_steering.py --check`, positioned after "Validate power integrity" and before "Run tests"

## Task 7: Update POWER.md documentation

- [x] 7.1 Add context budget tracking to the "What's New" section in `senzing-bootcamp/POWER.md`
- [x] 7.2 Add `measure_steering.py` to the "Useful Commands" section with examples for update mode and `--check` mode
- [x] 7.3 Add context budget threshold descriptions (60% warn, 80% critical) to the steering files documentation area

## Task 8: Write property-based and unit tests

- [x] 8.1 Create `tests/test_measure_steering.py` with property-based tests for Properties 1–8 using Hypothesis (min 100 examples each)
- [x] 8.2 Add example-based unit tests for `--check` mode non-modification, agent-instructions.md content validation, CI workflow step ordering, and POWER.md documentation checks
- [x] 8.3 Add integration test that runs `measure_steering.py` against the real steering directory then verifies `--check` passes
