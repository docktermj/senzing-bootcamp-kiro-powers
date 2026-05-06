# Tasks: Smarter Context Budget Warnings

## Task 1: Add Context Budget Management section to agent-instructions.md

- [x] 1.1 Read the current `senzing-bootcamp/steering/agent-instructions.md` to find the existing context budget references
- [x] 1.2 Add a "### Context Budget Management" subsection documenting the retention priority order (6 tiers)
- [x] 1.3 Document warn threshold behavior (60%): identify candidates, show token savings, ask before unloading
- [x] 1.4 Document critical threshold behavior (80%): automatically unload completed-module steering, report what was freed
- [x] 1.5 Document the "keep everything loaded" override: suppresses auto-unload for current session only
- [x] 1.6 Document reload-on-demand: unloaded files can be reloaded if bootcamper revisits a completed module
- [x] 1.7 Document phase-based splitting suggestion as last resort when budget is still critical after unloading

## Task 2: Add --simulate flag to measure_steering.py

- [x] 2.1 Read the current `senzing-bootcamp/scripts/measure_steering.py` to understand its argument structure and data access
- [x] 2.2 Add `--simulate` flag to argparse
- [x] 2.3 Implement simulation logic: for each module, compute which files would be loaded (agent-instructions + module steering + language file + accumulated completed modules)
- [x] 2.4 Output per-module cumulative token counts and percentage of reference_window
- [x] 2.5 Show peak with and without unloading strategy
- [x] 2.6 Read token counts from steering-index.yaml file_metadata

## Task 3: Write tests

- [x] 3.1 Create `senzing-bootcamp/tests/test_smart_context_budget.py`
- [x] 3.2 Unit test: agent-instructions.md contains "Context Budget Management" section
- [x] 3.3 Unit test: agent-instructions.md documents all 6 retention priority tiers
- [x] 3.4 Unit test: agent-instructions.md documents warn (60%) and critical (80%) behaviors
- [x] 3.5 Unit test: measure_steering.py accepts `--simulate` flag without error
- [x] 3.6 Unit test: --simulate output contains "Peak without unloading" and "Peak with unloading" lines
- [x] 3.7 Property test: simulated token counts are always non-negative
- [x] 3.8 Property test: peak with unloading is always ≤ peak without unloading

## Task 4: Validate

- [x] 4.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified steering files
- [x] 4.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify budgets
- [x] 4.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --simulate` to verify output format
- [x] 4.4 Run `pytest senzing-bootcamp/tests/test_smart_context_budget.py -v`
