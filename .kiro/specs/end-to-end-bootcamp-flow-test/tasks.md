# Tasks: End-to-End Bootcamp Flow Test

## Task 1: Config Parsers and Data Models

- [x] 1.1 Create `senzing-bootcamp/tests/test_e2e_bootcamp_flow.py` with imports, sys.path setup, and dataclass definitions (`BootcampConfig`, `ModuleConfig`, `TrackConfig`, `GateConfig`)
- [x] 1.2 Implement `_parse_module_dependencies()` — minimal YAML parser for `module-dependencies.yaml` that returns a `BootcampConfig` instance with modules, tracks, and gates
- [x] 1.3 Implement `_parse_steering_index()` — reuse the `parse_steering_index` pattern from `test_module_transition_properties.py` to parse `steering-index.yaml`
- [x] 1.4 Add module-level constants: parse both config files at import time, define `MODULE_ARTIFACTS` dict mapping module numbers to their expected filesystem paths

## Task 2: Test Infrastructure Helpers

- [x] 2.1 Implement `_create_module_artifacts(root: Path, module_num: int)` — creates all filesystem artifacts that `validate_module.py` checks for a given module
- [x] 2.2 Implement `_ProgressManager` class — wraps progress read/write/complete_module operations scoped to a `tmp_path` root
- [x] 2.3 Implement `_evaluate_gate(root: Path, gate_key: str, config: BootcampConfig)` — checks source module artifacts exist to determine if gate allows transition
- [x] 2.4 Implement `_resolve_steering(module_num: int, phase: str | None, steering_index: dict)` — returns the steering file path for a module/phase combination

## Task 3: Hypothesis Strategies

- [x] 3.1 Define `st_module_with_prereqs()` — draws from modules with non-empty `requires` lists
- [x] 3.2 Define `st_any_module()` — draws from all module numbers in config
- [x] 3.3 Define `st_gate_key()` — draws from all gate keys defined in config
- [x] 3.4 Define `st_track_and_position()` — draws a track name and a valid index within that track's module list
- [x] 3.5 Define `st_steering_module()` — draws from all module numbers in steering index
- [x] 3.6 Define `st_multi_phase_module()` — draws from modules with phases in steering index
- [x] 3.7 Define `st_skippable_module()` and `st_non_skippable_module()` — draws from modules with non-null/null `skip_if`
- [x] 3.8 Define `st_valid_progress_state()` — generates random valid progress state dicts for round-trip testing

## Task 4: Property-Based Tests

- [x] 4.1 Implement `TestProgressStateProperties.test_progress_round_trip` — Property 1: write then read produces identical object
- [x] 4.2 Implement `TestPrerequisiteProperties.test_missing_prereqs_cause_failure` — Property 2: missing prerequisites cause validation failure
- [x] 4.3 Implement `TestPrerequisiteProperties.test_present_prereqs_allow_success` — Property 3: present prerequisites allow validation success
- [x] 4.4 Implement `TestGateProperties.test_gate_allows_iff_artifacts_present` — Property 4: gate allows transition iff source artifacts exist
- [x] 4.5 Implement `TestProgressStateProperties.test_transition_updates_state` — Property 5: module transition updates progress correctly
- [x] 4.6 Implement `TestSteeringResolutionProperties.test_resolver_returns_correct_path` — Property 6: steering resolver returns correct file path
- [x] 4.7 Implement `TestSteeringResolutionProperties.test_all_steering_files_exist` — Property 7: all referenced steering files exist on disk
- [x] 4.8 Implement `TestPhaseTransitionProperties.test_step_ranges_contiguous` — Property 8: phase step ranges are contiguous and non-overlapping
- [x] 4.9 Implement `TestPhaseTransitionProperties.test_phase_traversal_order` — Property 9: advancing phases yields correct next steering file
- [x] 4.10 Implement `TestSkipConditionProperties.test_skip_condition_evaluation` — Property 10: skip allows bypass, null skip prevents bypass

## Task 5: Integration Tests

- [x] 5.1 Implement `TestTrackFlowIntegration.test_quick_demo_track` — walk modules 2, 3 creating artifacts, validating, checking gates and progress
- [x] 5.2 Implement `TestTrackFlowIntegration.test_core_bootcamp_track` — walk modules 1-7 creating artifacts, validating, checking gates and progress
- [x] 5.3 Implement `TestTrackFlowIntegration.test_advanced_topics_track` — walk modules 1-11 creating artifacts, validating, checking gates and progress
- [x] 5.4 Implement `TestConfigParsing` — smoke tests for YAML parsing and error handling edge cases (malformed input, missing files)

## Task 6: Verification and Cleanup

- [x] 6.1 Run the full test file with `pytest senzing-bootcamp/tests/test_e2e_bootcamp_flow.py -v` and fix any failures
- [x] 6.2 Verify all 10 property tests pass with 100 examples each
- [x] 6.3 Verify all 3 integration tests pass
- [x] 6.4 Run the existing test suite to confirm no regressions: `pytest senzing-bootcamp/tests/ -x --timeout=120`
