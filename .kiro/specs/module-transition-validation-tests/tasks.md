# Tasks: Module Transition Validation Tests

## Task 1: Create test file with YAML parser and module resolver

- [x] 1.1 Create `senzing-bootcamp/tests/test_module_transition_properties.py` with module docstring, imports (`pytest`, `hypothesis`, `pathlib`, `dataclasses`), and `_STEERING_DIR` / `_INDEX_PATH` constants pointing to `senzing-bootcamp/steering/`
- [x] 1.2 Implement `parse_steering_index(path: Path) -> dict` — a minimal line-based YAML parser that extracts the `modules:` section from `steering-index.yaml`, handling both simple string entries and nested objects with `root`, `phases`, `file`, and `step_range` keys. Raise `FileNotFoundError` if the file is missing and `ValueError` on malformed structure.
- [x] 1.3 Implement `ModuleFiles` dataclass with fields `module_number: int`, `root_file: Path`, `last_phase_file: Path`, `all_phase_files: list[Path]`
- [x] 1.4 Implement `resolve_module_files(module_number: int, entry: str | dict, steering_dir: Path) -> ModuleFiles` — for simple string entries, set `root_file` and `last_phase_file` to the same path; for dict entries, use the `root` key for `root_file` and find the phase with the highest `step_range` end value for `last_phase_file`. Raise `FileNotFoundError` with module number and path if any file does not exist on disk.
- [x] 1.5 Implement three content-checking functions: `has_transition_reference(content: str) -> bool` (checks for `module-transitions.md`), `has_before_after_section(content: str) -> bool` (checks for `**Before/After**`), `has_success_indicator(content: str) -> bool` (checks for `**Success` or `✅`)

## Task 2: Implement Hypothesis strategy and property tests

- [x] 2.1 Parse the steering index at module level into `_MODULES` dict and implement `st_module_number()` strategy using `st.sampled_from()` over the module number keys
- [x] 2.2 [PBT] Implement `TestModuleTransitionProperties.test_transition_reference_in_root_files` — Property 1: *For any* module number drawn from the steering index, the root module file contains `module-transitions.md`. Use `@given(module_num=st_module_number())` with `@settings(max_examples=100)`. Tag: `Feature: module-transition-validation-tests, Property 1: Transition Reference Invariant`
- [x] 2.3 [PBT] Implement `TestModuleTransitionProperties.test_before_after_section_in_root_files` — Property 2: *For any* module number drawn from the steering index, the root module file contains `**Before/After**`. Use `@given(module_num=st_module_number())` with `@settings(max_examples=100)`. Tag: `Feature: module-transition-validation-tests, Property 2: Before/After Section Invariant`
- [x] 2.4 [PBT] Implement `TestModuleTransitionProperties.test_success_indicator_in_appropriate_file` — Property 3: *For any* module number drawn from the steering index, the appropriate file (root for single-file, last phase sub-file for multi-phase) contains `**Success` or `✅`. Use `@given(module_num=st_module_number())` with `@settings(max_examples=100)`. Tag: `Feature: module-transition-validation-tests, Property 3: Success Indicator Invariant`
- [x] 2.5 [PBT] Implement `TestModuleTransitionProperties.test_all_referenced_files_exist` — Property 4: *For any* module number drawn from the steering index, all files referenced by that module entry exist on disk. Use `@given(module_num=st_module_number())` with `@settings(max_examples=100)`. Tag: `Feature: module-transition-validation-tests, Property 4: File Resolution Completeness`

## Task 3: Verify tests pass

- [x] 3.1 Run `pytest senzing-bootcamp/tests/test_module_transition_properties.py -v` and verify all 4 property tests pass. Fix any failures caused by implementation bugs in the parser, resolver, or content checkers.
