# Tasks: Module Dependency Visualization

## Task 1: Create visualize_dependencies.py script

- [x] 1.1 Create `senzing-bootcamp/scripts/visualize_dependencies.py` with argparse accepting `--format {text,mermaid}` (default: text)
- [x] 1.2 Implement dependency graph loading from `config/module-dependencies.yaml` (with fallback to `senzing-bootcamp/config/module-dependencies.yaml`)
- [x] 1.3 Implement progress loading from `config/bootcamp_progress.json` (optional — default to all locked if missing)
- [x] 1.4 Implement track loading from `config/bootcamp_preferences.yaml` (optional)
- [x] 1.5 Implement module status determination: complete (✅), current (📍), available (🔓), locked (🔒)
- [x] 1.6 Implement prerequisite checking: a module is "available" only if all its prerequisites are complete

## Task 2: Implement ASCII text output

- [x] 2.1 Implement tree-based ASCII rendering using box-drawing characters (├──→, └──→, │)
- [x] 2.2 Show each module with its status emoji and title
- [x] 2.3 Add legend line at bottom: "✅ Complete  📍 Current  🔓 Available  🔒 Locked"
- [x] 2.4 Add track information line showing active track name and progress percentage
- [x] 2.5 Handle the branching structure (Module 7 has multiple dependents: 8, 9, 10, 11)

## Task 3: Implement Mermaid output

- [x] 3.1 Generate Mermaid flowchart TD syntax with node definitions
- [x] 3.2 Apply class definitions based on module status (complete, current, available, locked)
- [x] 3.3 Generate edge definitions from dependency relationships
- [x] 3.4 Add classDef styling (green for complete, blue for current, gray for available/locked)

## Task 4: Add --graph flag to status.py

- [x] 4.1 Read the current `senzing-bootcamp/scripts/status.py` to understand its output structure
- [x] 4.2 Add `--graph` flag to argparse
- [x] 4.3 When --graph is provided, append the ASCII dependency graph after existing status output
- [x] 4.4 Import and call the text rendering function from visualize_dependencies.py

## Task 5: Update steering-index.yaml keywords

- [x] 5.1 Add keyword entries: "learning path", "module map", "dependency graph", "what's next" mapping to `inline-status.md`
- [x] 5.2 Verify keywords don't conflict with existing entries

## Task 6: Write tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_module_dependency_visualization.py`
- [x] 6.2 Unit test: script accepts --format text and --format mermaid
- [x] 6.3 Unit test: text output contains all 11 module names
- [x] 6.4 Unit test: mermaid output contains "flowchart TD" and classDef definitions
- [x] 6.5 Unit test: no progress file → Module 1 shown as available, all others locked
- [x] 6.6 Unit test: completed modules shown with ✅ in text output
- [x] 6.7 Property test: module status is always one of {complete, current, available, locked}
- [x] 6.8 Property test: completed modules are never shown as locked
- [x] 6.9 Property test: current module is never shown as complete
- [x] 6.10 Unit test: status.py accepts --graph flag

## Task 7: Validate

- [x] 7.1 Run `python3 senzing-bootcamp/scripts/visualize_dependencies.py` and verify output renders correctly
- [x] 7.2 Run `python3 senzing-bootcamp/scripts/visualize_dependencies.py --format mermaid` and verify valid Mermaid syntax
- [x] 7.3 Run `pytest senzing-bootcamp/tests/test_module_dependency_visualization.py -v`
- [x] 7.4 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` (if steering-index.yaml was modified)
