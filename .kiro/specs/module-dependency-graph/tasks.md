# Tasks

## Task 1: Create the dependency graph YAML file

- [x] 1.1 Create `senzing-bootcamp/config/module-dependencies.yaml` with the `metadata` section containing `version: "1.0.0"` and `last_updated` (ISO 8601 date), and the `modules` section with entries for all 11 modules (keyed by integer 1–11), each containing `name` (string), `requires` (list of integer module numbers), and `skip_if` (string or null), matching the prerequisite relationships currently documented in `module-prerequisites.md`
- [x] 1.2 Add the `tracks` section to the dependency graph with entries for all four tracks (Quick Demo, Fast Track, Complete Beginner, Full Production), each containing `name`, `description`, and `modules` (ordered list of integers), matching the track definitions in `onboarding-flow.md`
- [x] 1.3 Add the `gates` section to the dependency graph with entries for all 10 module transitions (`1->2` through `10->11`), each containing a `requires` list of string conditions, matching the validation gate conditions in `onboarding-flow.md`; encode the implicit rule that Module 2 (SDK Setup) is automatically inserted before any module requiring the SDK

## Task 2: Create the validation script with core infrastructure

- [x] 2.1 Create `senzing-bootcamp/scripts/validate_dependencies.py` with the `Violation` dataclass (`level`, `description`, `format()` method), `load_dependency_graph(path)` function that loads and parses the YAML file (exits with code 1 if missing or unparseable), and CLI entry point `main()` that runs all checks, prints violations in `{level}: {description}` format, prints a summary line with error/warning counts, and exits with code 0 (no errors) or 1 (errors found)
- [x] 2.2 Implement `validate_schema(graph)` that verifies: (a) `metadata` section exists with `version` (string) and `last_updated` (string), (b) `modules` section exists with each entry having `name` (string), `requires` (list), `skip_if` (string or null), (c) `tracks` section exists with each entry having `name`, `description`, `modules`, (d) `gates` section exists with each entry having `requires`; reports ERROR for each missing or invalid field

## Task 3: Implement structural validation checks

- [x] 3.1 Implement `validate_no_cycles(graph)` using Kahn's algorithm for topological sort: (a) build adjacency list from `requires` fields, (b) detect cycles by checking if all nodes are visited, (c) report ERROR identifying the modules involved in any cycle
- [x] 3.2 Implement `validate_references(graph)` that: (a) collects all module numbers from `requires` lists, `tracks` module lists, and `gates` keys, (b) verifies each referenced number exists in the `modules` section, (c) reports ERROR for each dangling reference identifying the section and missing module number
- [x] 3.3 Implement `validate_topological_order(graph)` that: (a) for each track, iterates through its module list, (b) verifies no module appears before any of its prerequisites in the list, (c) reports ERROR identifying the track and the out-of-order module

## Task 4: Implement cross-reference validation checks

- [x] 4.1 Implement `validate_steering_files(graph, steering_dir)` that: (a) for each module number in the graph, checks for a corresponding `module-NN-*.md` file in the steering directory, (b) reports ERROR for each module number without a matching file
- [x] 4.2 Implement `validate_prerequisites_file(graph, prereqs_path)` that: (a) parses the dependency table in `module-prerequisites.md`, (b) extracts prerequisite relationships from the table, (c) compares with the `requires` fields in the graph, (d) reports ERROR for each discrepancy identifying the module and the difference
- [x] 4.3 Implement `validate_onboarding_flow(graph, onboarding_path)` that: (a) parses track definitions from `onboarding-flow.md`, (b) compares module sequences with the `tracks` section of the graph, (c) reports ERROR for each discrepancy identifying the track and the difference
- [x] 4.4 Implement `run_all_checks(graph_path, steering_dir)` that calls all validation functions, collects violations, and returns `(violations, exit_code)` where exit_code is 0 if no errors, else 1

## Task 5: Update steering files with authoritative source references

- [x] 5.1 Add a note at the top of the "Quick Reference: Dependencies" section in `senzing-bootcamp/steering/module-prerequisites.md` stating that the authoritative source for prerequisite data is `config/module-dependencies.yaml`, and directing maintainers to update the graph first and run the validation script
- [x] 5.2 Add a note in the "Track Selection" section of `senzing-bootcamp/steering/onboarding-flow.md` stating that track definitions are derived from `config/module-dependencies.yaml`
- [x] 5.3 Add a note in the "Validation Gates" section of `senzing-bootcamp/steering/onboarding-flow.md` stating that gate conditions are derived from `config/module-dependencies.yaml` and directing maintainers to update the graph first and run the validation script

## Task 6: Property-based tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_dependency_graph_properties.py` with Hypothesis strategies for generating random directed graphs (with and without cycles), random module reference sets, random track orderings, and random YAML schema structures
- [x] 6.2 PBT: Property 1 — Cycle Detection Correctness: for any directed graph, `validate_no_cycles` reports an error iff the graph contains a cycle (Req 3.1, 6.1, 6.2)
- [x] 6.3 PBT: Property 2 — Dangling Reference Detection: for any graph with references to existing and non-existing modules, `validate_references` reports exactly the dangling ones (Req 3.2, 6.3, 6.4)
- [x] 6.4 PBT: Property 3 — Topological Order Validation: for any graph and track, `validate_topological_order` reports an error iff the track violates prerequisite ordering (Req 3.3)
- [x] 6.5 PBT: Property 4 — Schema Validation Completeness: for any YAML structure, `validate_schema` reports errors for all missing/invalid fields and no errors for valid structures (Req 6.5, 6.6)
- [x] 6.6 PBT: Property 5 — Exit Code Correctness: for any set of violations, exit code is 0 iff zero errors (Req 4.3, 4.4)
- [x] 6.7 PBT: Property 6 — Violation Output Format: for any Violation, formatted output matches `{ERROR|WARNING}: {description}` (Req 4.5)

## Task 7: Example-based unit tests and integration tests

- [x] 7.1 Create `senzing-bootcamp/tests/test_dependency_graph_unit.py` with unit tests: (a) real graph parses without error, (b) real graph has 11 modules, (c) real graph has 4 tracks, (d) real graph has 10 gates, (e) real graph has no cycles, (f) real graph has no dangling references, (g) reference notes exist in module-prerequisites.md and onboarding-flow.md
- [x] 7.2 Add integration test: full validation run on real graph + steering files exits with code 0; script runs with only stdlib + PyYAML; summary line format is correct
- [x] 7.3 Run all tests and verify they pass
