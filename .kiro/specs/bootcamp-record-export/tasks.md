# Tasks: Bootcamp Record Export

## Task 1: Create data models and core dataclasses

- [x] 1.1 Create `senzing-bootcamp/scripts/record_export.py` with all dataclass definitions: `PreferencesData`, `ProgressData`, `DataSourceEntry`, `MappingDecision`, `LoadingConfig`, `QueryProgram`, `BusinessProblem`, `PerformanceTuning`, `SecurityHardening`, `MonitoringConfig`, `DeploymentDecision`, `CollectedDecisions`, `DecisionManifest`
- [x] 1.2 Add `SCHEMA_VERSION = "1.0"` constant and metadata generation helper that produces `schema_version`, `generated_at` (ISO 8601), and `power_version`
- [x] 1.3 Verify all field names use snake_case and all dataclasses are serializable to dict via `dataclasses.asdict()`

## Task 2: Implement SecuritySanitizer

- [x] 2.1 Implement `SecuritySanitizer` class with `SECRET_PATTERNS` list (API key, connection string, AWS key, token patterns)
- [x] 2.2 Implement `check_value(value: str) -> bool` that returns True if value matches any secret pattern
- [x] 2.3 Implement `relativize_path(path: str, project_root: str) -> str` that converts absolute paths to relative
- [x] 2.4 Implement `scan_for_pii(text: str) -> bool` with heuristic checks for email, phone, SSN patterns
- [x] 2.5 Implement `sanitize(manifest: DecisionManifest) -> tuple[DecisionManifest, list[str]]` that walks all string values, redacts secrets, relativizes paths, and returns warnings
- [x] 2.6 Write property-based test: sanitizer removes all absolute paths (Property 1)
- [x] 2.7 Write property-based test: sanitizer detects secret patterns (Property 2)

## Task 3: Implement DecisionCollector

- [x] 3.1 Implement `collect_preferences()` — reads `config/bootcamp_preferences.yaml`, returns `PreferencesData` or None
- [x] 3.2 Implement `collect_progress()` — reads `config/bootcamp_progress.json`, returns `ProgressData` or None
- [x] 3.3 Implement `collect_data_sources()` — reads `config/data_sources.yaml` or scans `data/raw/` as fallback
- [x] 3.4 Implement `collect_mappings()` — reads mapping spec files from config/ and data/transformed/
- [x] 3.5 Implement `collect_loading_config()` — infers strategy from `src/load/` scripts (single vs multi-source, redo processing)
- [x] 3.6 Implement `collect_query_programs()` — scans `src/query/` for scripts, extracts type and description from comments
- [x] 3.7 Implement `collect_business_problem()` — extracts Module 1 data from `docs/bootcamp_journal.md`
- [x] 3.8 Implement `collect_performance_tuning()`, `collect_security_hardening()`, `collect_monitoring_config()`, `collect_deployment()` — conditional on module completion
- [x] 3.9 Implement `collect_all()` — orchestrates all collectors, populates warnings for missing files
- [x] 3.10 Write property-based test: missing source files produce warnings not failures (Property 10)

## Task 4: Implement ManifestAssembler

- [x] 4.1 Implement `ManifestAssembler.assemble(decisions: CollectedDecisions) -> DecisionManifest` — builds full manifest structure
- [x] 4.2 Implement `_build_metadata()` — generates metadata section with timestamp, schema version, power version
- [x] 4.3 Implement `_build_track_progress()` — builds track progress from ProgressData and PreferencesData
- [x] 4.4 Implement `_build_optional_sections()` — includes performance/security/monitoring/deployment only if module completed
- [x] 4.5 Implement `_build_replay_notes()` — identifies decisions that need manual input on replay
- [x] 4.6 Write property-based test: metadata always present and valid (Property 3)
- [x] 4.7 Write property-based test: optional sections appear only for completed modules (Property 4)
- [x] 4.8 Write property-based test: track progress reflects actual completion state (Property 8)

## Task 5: Implement ManifestWriter

- [x] 5.1 Implement `ManifestWriter.to_yaml(manifest: DecisionManifest) -> str` — serializes manifest to YAML with inline comments
- [x] 5.2 Implement `ManifestWriter.write(manifest, output_path, overwrite)` — writes to disk with overwrite protection
- [x] 5.3 Write property-based test: YAML round-trip (serialize → parse → compare) (Property 7)
- [x] 5.4 Write property-based test: all keys are snake_case (Property 9)

## Task 6: Implement CLI entry point

- [x] 6.1 Add argparse CLI with `--output` (default: `docs/bootcamp_record.yaml`), `--dry-run`, and `--overwrite` arguments
- [x] 6.2 Implement `main()` function: parse args → collect → assemble → sanitize → write, return exit code
- [x] 6.3 Add progress output: print source files read, sections generated, warnings encountered
- [x] 6.4 Add overwrite check: if output file exists and `--overwrite` not set, print message and exit with code 1
- [x] 6.5 Write unit tests for CLI argument parsing and main flow

## Task 7: Integration with module-completion steering

- [x] 7.1 Add record export offer to `steering/module-completion.md` in the "Path Completion Celebration" section, after the export-results option and before the analytics offer
- [x] 7.2 Add trigger text: "Would you like a record of your bootcamp journey? You can share it with your team or use it to replay the same setup on another project."
- [x] 7.3 Add acceptance handler: when bootcamper accepts, agent runs `python3 scripts/record_export.py` and presents output path
- [x] 7.4 Add decline handler: proceed to next step without generating export

## Task 8: Additional property tests and integration tests

- [x] 8.1 Write property-based test: data source entries contain no actual record data (Property 5)
- [x] 8.2 Write property-based test: all paths in manifest are relative after sanitization (Property 6)
- [x] 8.3 Write integration test: full pipeline with fixture data produces valid YAML with expected sections
- [x] 8.4 Write integration test: empty project produces minimal manifest with warnings and replay_notes
- [x] 8.5 Write unit test: overwrite protection behavior (file exists → error without --overwrite)
