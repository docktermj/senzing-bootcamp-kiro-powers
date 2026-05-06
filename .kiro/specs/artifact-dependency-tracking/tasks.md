# Tasks: Cross-Module Artifact Dependency Tracking

## Task 1: Create module-artifacts.yaml

- [x] 1.1 Create `senzing-bootcamp/config/module-artifacts.yaml` with version "1" and module entries for Modules 4-7 (the core pipeline)
- [x] 1.2 Define Module 4 produces: `data/raw/` (directory), `config/data_sources.yaml` (file)
- [x] 1.3 Define Module 5 produces: `data/transformed/` (directory); requires_from Module 4
- [x] 1.4 Define Module 6 produces: `src/load/` (directory); requires_from Module 5
- [x] 1.5 Define Module 7 produces: `src/query/` (directory); requires_from Module 6
- [x] 1.6 Add entries for Modules 8-11 with appropriate produces/requires_from (these may have fewer concrete artifacts)

## Task 2: Extend validate_module.py with --artifacts flag

- [x] 2.1 Read the current `senzing-bootcamp/scripts/validate_module.py` to understand its argument structure
- [x] 2.2 Add `--artifacts` flag to argparse that accepts a module number
- [x] 2.3 Implement artifact checking logic: read module-artifacts.yaml, resolve requires_from for the given module, check each path exists on disk
- [x] 2.4 For directory artifacts, verify the directory exists and is non-empty
- [x] 2.5 Output a summary table: artifact path, source module, status (✅ present / ❌ missing)
- [x] 2.6 Exit code: 0 if all required artifacts present, 1 if any required artifact missing (optional artifacts produce warnings but don't affect exit code)

## Task 3: Add artifact check instruction to agent-instructions.md

- [x] 3.1 Add instruction to the Module Steering section: "Before displaying the module banner for Modules 4-11, read `config/module-artifacts.yaml` and check prerequisites"
- [x] 3.2 Document the three recovery options the agent should offer when artifacts are missing
- [x] 3.3 Document that the check is advisory — the bootcamper can always skip

## Task 4: Integrate with data source registry

- [x] 4.1 Add logic to the artifact check: if `config/data_sources.yaml` exists, read registered source file paths and verify they exist in `data/raw/`
- [x] 4.2 Report any registered sources whose files are missing as additional warnings

## Task 5: Create MODULE_ARTIFACTS.md documentation

- [x] 5.1 Create `senzing-bootcamp/docs/guides/MODULE_ARTIFACTS.md` with schema documentation for module-artifacts.yaml
- [x] 5.2 Document field definitions: version, modules, produces (path, type, description, required), requires_from
- [x] 5.3 Add a complete example showing the Module 4-7 pipeline
- [x] 5.4 Add the file to `docs/guides/README.md` Reference Documentation section

## Task 6: Write tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_artifact_dependency_tracking.py`
- [x] 6.2 Property test: all modules in manifest have valid numbers (1-11)
- [x] 6.3 Property test: requires_from only references modules with lower numbers (no circular deps)
- [x] 6.4 Property test: all produces paths are relative (no leading /)
- [x] 6.5 Unit test: validate_module.py accepts --artifacts flag
- [x] 6.6 Unit test: missing file correctly detected
- [x] 6.7 Unit test: non-empty directory check works
- [x] 6.8 Unit test: optional artifacts produce warnings not errors

## Task 7: Validate

- [x] 7.1 Run `pytest senzing-bootcamp/tests/test_artifact_dependency_tracking.py -v`
- [x] 7.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on new/modified markdown
- [x] 7.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
