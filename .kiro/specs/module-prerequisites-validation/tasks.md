# Tasks: Module Prerequisites Validation

## Task 1: Create Core Parsing Functions

- [x] 1.1 Create `senzing-bootcamp/scripts/validate_prerequisites.py` with shebang, docstring, `from __future__ import annotations`, and stdlib imports
- [x] 1.2 Implement `parse_gate_key(key: str) -> tuple[int, int] | None` to extract source and destination module numbers from `"N->M"` format
- [x] 1.3 Implement `extract_keywords(requirement: str) -> list[str]` to split on commas, strip whitespace, and lowercase each token
- [x] 1.4 Implement `Finding` dataclass with `level`, `description`, and `format()` method
- [x] 1.5 Implement `ModuleInfo` and `GateInfo` dataclasses for parsed graph structure

## Task 2: Implement YAML Parsing and Index Loading

- [x] 2.1 Implement `load_dependency_graph(path: Path) -> dict` using a minimal YAML parser (stdlib only) to extract modules, gates, and tracks sections
- [x] 2.2 Implement `load_steering_index(path: Path) -> dict[int, list[str]]` to parse `steering-index.yaml` and build module-to-files mapping (handling both simple string entries and multi-phase dict entries)
- [x] 2.3 Implement `load_steering_content(steering_dir: Path, files: list[str]) -> str` to concatenate content from multiple steering files
- [x] 2.4 Add error handling for missing files (exit code 1 with descriptive message) and unparseable content

## Task 3: Implement Validation Checks

- [x] 3.1 Implement module reference cross-validation: verify each `requires` module number and each gate source/destination exists in the steering index
- [x] 3.2 Implement keyword presence check: for each gate, extract keywords from requirements and search source module's steering content (case-insensitive)
- [x] 3.3 Implement `count_checkpoints(content: str) -> int` to count `**Checkpoint:**` patterns in steering content
- [x] 3.4 Implement `has_success_criteria(content: str) -> bool` to detect "Success Criteria" headings or `✅` markers
- [x] 3.5 Implement checkpoint coverage validation: report ERROR if source module has zero checkpoints with an outgoing gate, WARNING if no success criteria

## Task 4: Implement CLI and Output

- [x] 4.1 Implement `validate_prerequisites(graph_path, steering_index_path, steering_dir) -> list[Finding]` orchestrator function
- [x] 4.2 Implement `main(argv=None)` with argparse: `--warnings-as-errors`, `--graph`, `--steering-index`, `--steering-dir` flags
- [x] 4.3 Implement output formatting: each finding on a separate line, summary line with error/warning counts
- [x] 4.4 Implement exit code logic: 1 if errors (or warnings with `--warnings-as-errors`), 0 otherwise
- [x] 4.5 Verify the script runs successfully against the real project files: `python senzing-bootcamp/scripts/validate_prerequisites.py`

## Task 5: CI Integration

- [x] 5.1 Add `Validate module prerequisites` step to `.github/workflows/validate-power.yml` after `sync_hook_registry.py --verify` and before `pytest`
- [x] 5.2 Verify the step command is `python senzing-bootcamp/scripts/validate_prerequisites.py`

## Task 6: Write Property-Based Tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_prerequisites_validation_properties.py` with Hypothesis strategies (`st_gate_key`, `st_gate_requirement`, `st_dependency_graph`, `st_steering_index`, `st_steering_content`, `st_finding_set`)
- [x] 6.2 [PBT] Implement Property 1: Gate parsing correctness — *For any* valid gate key string matching "N->M", the parser correctly extracts both module numbers, and for any valid dependency graph, the parser extracts all gates without exceptions. **Feature: module-prerequisites-validation, Property 1: Gate Parsing Correctness**
- [x] 6.3 [PBT] Implement Property 2: Keyword extraction produces normalized tokens — *For any* non-empty gate requirement string, keyword extraction produces a non-empty list of lowercase tokens with no leading/trailing whitespace. **Feature: module-prerequisites-validation, Property 2: Keyword Extraction Produces Normalized Tokens**
- [x] 6.4 [PBT] Implement Property 3: Module reference cross-validation — *For any* dependency graph and steering index, the validator reports an ERROR for each missing module reference and zero errors when all references exist. **Feature: module-prerequisites-validation, Property 3: Module Reference Cross-Validation**
- [x] 6.5 [PBT] Implement Property 4: Keyword presence detection — *For any* steering content and keywords, the validator reports a WARNING for each missing keyword and zero warnings when all are present. **Feature: module-prerequisites-validation, Property 4: Keyword Presence Detection**
- [x] 6.6 [PBT] Implement Property 5: Checkpoint and success criteria detection — *For any* steering content with N checkpoint patterns, the counter returns N; zero checkpoints with an outgoing gate produces an ERROR; missing success criteria produces a WARNING. **Feature: module-prerequisites-validation, Property 5: Checkpoint and Success Criteria Detection**
- [x] 6.7 [PBT] Implement Property 6: Exit code correctness — *For any* set of findings, exit code is 1 iff errors exist (or warnings exist with --warnings-as-errors), 0 otherwise. **Feature: module-prerequisites-validation, Property 6: Exit Code Correctness**

## Task 7: Write Unit Tests

- [x] 7.1 Create `senzing-bootcamp/tests/test_prerequisites_validation_unit.py` with example-based tests for error/warning message formats
- [x] 7.2 Add tests for file-not-found and parse-error edge cases
- [x] 7.3 Add tests for `--warnings-as-errors` flag behavior
- [x] 7.4 Add smoke test running against real project files (module-dependencies.yaml + steering-index.yaml + steering/)
- [x] 7.5 Add performance assertion: validator completes in < 10 seconds for 11 modules

## Task 8: Final Verification

- [x] 8.1 Run full test suite (`python -m pytest senzing-bootcamp/tests/test_prerequisites_validation_properties.py senzing-bootcamp/tests/test_prerequisites_validation_unit.py -v --tb=short`) and confirm all tests pass
- [x] 8.2 Run the validator script manually and confirm exit code 0 on the current project
- [x] 8.3 Verify `validate_dependencies.py` still passes independently (no regressions)
