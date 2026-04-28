# Tasks

## Task 1: Create data models and manifest infrastructure

- [x] 1.1 Create `senzing-bootcamp/scripts/export_results.py` with `ArtifactEntry` and `ArtifactManifest` dataclasses, including `by_type()`, `by_module()`, `total_size()`, `type_counts()`, and `is_empty()` methods
- [x] 1.2 Implement `QualityScore` dataclass with `band` property (green ≥80, yellow ≥70, red <70), `PerformanceMetrics`, `EntityStatistics`, and `ExportMetrics` dataclasses
- [x] 1.3 Implement `ProgressData` dataclass with fields for `modules_completed`, `current_module`, `language`, `data_sources`, and `track`
- [x] 1.4 Implement `ModuleFilter.validate_modules()` that partitions a list of integers into valid (1–12) and invalid, and `ModuleFilter.filter()` that returns a new manifest with only matching module artifacts (plus module=None artifacts)

## Task 2: Implement artifact discovery

- [x] 2.1 Implement `ArtifactDiscovery.__init__()` and `scan()` orchestrator that calls all `_scan_*` methods and assembles an `ArtifactManifest` with ISO 8601 timestamp
- [x] 2.2 Implement `_scan_journal()` and `_scan_progress()` to find `docs/bootcamp_journal.md` and `config/bootcamp_progress.json`, returning `ArtifactEntry` or `None`
- [x] 2.3 Implement `_scan_data_files()` to scan `data/transformed/` for `.jsonl` files and `data/raw/` for all files, associating modules based on path
- [x] 2.4 Implement `_scan_visualizations()` to find HTML files containing entity graph/dashboard content markers (d3, force, graph, dashboard, svg)
- [x] 2.5 Implement `_scan_source_code()` to scan `src/` for files matching the chosen language extension, inferring module from subdirectory name
- [x] 2.6 Implement `_scan_docs()` to scan `docs/` for markdown files, classifying quality reports, performance reports, entity stats, and general documentation

## Task 3: Implement metrics extraction

- [x] 3.1 Implement `MetricsExtractor.extract_quality_scores()` that parses quality score data (overall + sub-scores) from documentation artifacts using regex patterns, accepting a `file_reader` callable
- [x] 3.2 Implement `MetricsExtractor.extract_performance()` that parses loading throughput, query response times, and database type from performance report artifacts
- [x] 3.3 Implement `MetricsExtractor.extract_entity_stats()` that parses total records, total entities, match counts, cross-source matches, and duplicate counts from entity resolution artifacts

## Task 4: Implement HTML rendering

- [x] 4.1 Implement `HTMLRenderer._render_head()` with inline CSS styles (no external references), responsive layout, and print-friendly styles
- [x] 4.2 Implement `HTMLRenderer._render_toc()` that generates a table of contents with anchor links to each present section
- [x] 4.3 Implement `SummaryGenerator.generate()` that produces a plain-language executive summary HTML fragment containing track, module count, quality bands (when available), entity stats (when available), and artifact summary
- [x] 4.4 Implement `HTMLRenderer._render_module_table()` that renders all 12 modules with completion status (completed/in progress/not started), progress percentage, and language
- [x] 4.5 Implement `HTMLRenderer._render_quality_section()`, `_render_performance_section()`, and `_render_entity_stats_section()` that render metric sections with the actual values, omitting sections when data is None/empty
- [x] 4.6 Implement `HTMLRenderer._render_journal_section()` that converts journal markdown to HTML preserving module-by-module structure, and `_render_visualizations_section()` that lists each visualization with filename and description
- [x] 4.7 Implement `HTMLRenderer._render_footer()` with generation timestamp and script version, and `HTMLRenderer.render()` orchestrator that assembles all sections with semantic HTML elements (header, main, section, table, nav)

## Task 5: Implement ZIP assembly

- [x] 5.1 Implement `ZIPAssembler.should_exclude()` that checks file paths against exclusion patterns (__pycache__, *.pyc, .env, .git, node_modules, database/)
- [x] 5.2 Implement `ZIPAssembler.build_manifest_json()` that serializes the artifact manifest to JSON with generated_at, version, artifact_count, total_size_bytes, and per-artifact metadata
- [x] 5.3 Implement `ZIPAssembler.assemble()` that creates a ZIP archive with HTML report at root, manifest.json, and artifacts organized into subdirectories by type using TYPE_TO_DIR mapping

## Task 6: Implement CLI and progress reporting

- [x] 6.1 Implement CLI entry point with argparse supporting `--format {html,zip}` (default html), `--modules M1,M2,...`, and `--output PATH` with default `exports/bootcamp_report_{timestamp}.{ext}`
- [x] 6.2 Implement progress reporting: print artifact category counts during discovery, print output file path/size/artifact count on completion, print warnings for missing progress data or no artifacts found
- [x] 6.3 Implement error handling: create output directory if missing, exit code 1 on no artifacts or write failure, skip unreadable artifacts with logged errors, handle malformed progress JSON gracefully

## Task 7: Module-completion workflow integration

- [x] 7.1 Update `senzing-bootcamp/steering/module-completion.md` to add an export option in the Next-Step Options presented after track completion: "Would you like to export a shareable report of your bootcamp results?"
- [x] 7.2 Update `senzing-bootcamp/POWER.md` Useful Commands section to list `export_results.py` with usage examples

## Task 8: Property-based tests

- [x] 8.1 Create `senzing-bootcamp/scripts/test_export_results.py` with Hypothesis strategies for `ArtifactEntry`, `ArtifactManifest`, `ProgressData`, `QualityScore`, `PerformanceMetrics`, `EntityStatistics`, `ExportMetrics`, and module number lists
- [x] 8.2 PBT: Property 1 — Module number validation partitions correctly (Req 1.6, 10.3)
- [x] 8.3 PBT: Property 2 — Artifact discovery finds all matching files (Req 2.3, 2.5, 2.7)
- [x] 8.4 PBT: Property 3 — Visualization detection is content-based (Req 2.4)
- [x] 8.5 PBT: Property 4 — Manifest entries have complete metadata (Req 2.8)
- [x] 8.6 PBT: Property 5 — Module completion table reflects progress state (Req 3.1–3.5)
- [x] 8.7 PBT: Property 6 — Metric sections appear if and only if data exists (Req 4.1–4.4)
- [x] 8.8 PBT: Property 7 — Executive summary contains required information (Req 7.1–7.5)
- [x] 8.9 PBT: Property 8 — HTML report is self-contained (Req 8.1, 8.2)
- [x] 8.10 PBT: Property 9 — Module filter returns correct artifact subset (Req 10.1, 10.2)
- [x] 8.11 PBT: Property 10 — ZIP archive contains correct structure (Req 9.1–9.3, 6.2)
- [x] 8.12 PBT: Property 11 — ZIP exclusion patterns filter correctly (Req 9.4)
- [x] 8.13 PBT: Property 12 — Graceful degradation on read errors (Req 2.7, 12.6)

## Task 9: Unit tests for edge cases and integration points

- [x] 9.1 Unit test: CLI argument parsing — --format html/zip, invalid format, --output path, default timestamp path (Req 1.5, 1.7)
- [x] 9.2 Unit test: journal with multi-module structure preserves headings; journal absent omits section with note (Req 5.2, 5.3)
- [x] 9.3 Unit test: no visualizations omits section; semantic HTML elements present (Req 6.3, 8.3)
- [x] 9.4 Unit test: TOC contains anchor links; footer contains timestamp and version (Req 8.4, 8.5)
- [x] 9.5 Unit test: ZIP reports file path and size; no --modules includes all artifacts (Req 9.5, 10.4)
- [x] 9.6 Unit test: modules with no artifacts noted in table; missing progress file warning; empty project exits 1; output dir auto-created (Req 10.5, 12.3, 12.4, 12.5)
