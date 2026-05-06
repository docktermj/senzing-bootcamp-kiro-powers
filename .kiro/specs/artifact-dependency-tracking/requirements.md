# Requirements: Cross-Module Artifact Dependency Tracking

## Overview

Modules 4→5→6→7 form a tight pipeline (collect data → map → load → query) where each module depends on artifacts produced by earlier modules. Currently there's no validation that prerequisite artifacts are intact when starting a later module. This feature adds lightweight artifact readiness checks at module start to catch issues early.

## Requirements

1. A new configuration file `config/module-artifacts.yaml` defines expected artifacts per module: file paths (relative to working directory), file type (yaml, json, csv, py, etc.), and which module produces them
2. The artifact manifest covers at minimum: Module 4 outputs (data source files in `data/raw/`), Module 5 outputs (mapping specs in `config/`), Module 6 outputs (loading scripts in `src/load/`, loaded database), Module 7 outputs (query scripts in `src/query/`)
3. At module start, before displaying the module banner, the agent checks whether all artifacts from prerequisite modules exist on disk
4. If all prerequisite artifacts are present, the agent proceeds normally with no additional output
5. If artifacts are missing, the agent reports: which files are missing, which prerequisite module produced them, and offers three options: (a) go back and complete the prerequisite step, (b) skip the check and proceed anyway, (c) run `rollback_module.py` to reset to a clean state
6. The artifact check is advisory, not blocking — the bootcamper can always choose to proceed
7. The check validates file existence only, not file content correctness (content validation is the responsibility of individual module steps)
8. The `validate_module.py` script is extended with an `--artifacts` flag that performs the same check from the command line
9. The artifact manifest supports optional artifacts (marked `required: false`) that produce warnings instead of errors when missing
10. The `module-artifacts.yaml` file is documented in `docs/guides/` with field definitions and examples
11. The artifact check integrates with the data source registry — if `config/data_sources.yaml` exists, it cross-references registered sources against expected Module 4 outputs

## Non-Requirements

- This does not validate artifact content quality (that's the module's job)
- This does not automatically fix missing artifacts
- This does not change module dependency ordering (that's in module-dependencies.yaml)
- This does not apply to Modules 1-3 (they produce documentation, not pipeline artifacts)
