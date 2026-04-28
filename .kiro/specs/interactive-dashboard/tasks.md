# Tasks

## Task 1: Create data models

- [x] 1.1 Add `QualityScoreData` dataclass to `status.py` with `source_name`, `overall`, optional sub-scores (`completeness`, `consistency`, `format_compliance`, `uniqueness`), and `band` property (green ≥80, yellow ≥70, red <70)
- [ ] 1.2 Add `PerformanceData` dataclass with optional fields: `loading_throughput_rps`, `query_avg_ms`, `query_p95_ms`, `database_type`, `wall_clock_seconds`
- [ ] 1.3 Add `EntityStatsData` dataclass with optional fields: `total_records`, `total_entities`, `match_count`, `duplicate_count`, `cross_source_matches`
- [ ] 1.4 Add `HealthCheckItem` dataclass with `label`, `path`, and `exists` fields
- [ ] 1.5 Add `DashboardData` dataclass composing all above types plus `modules_completed`, `current_module`, `status`, `language`, `completion_pct`, `completion_timestamps`, `health_score`, `health_total`, `generated_at`, and `has_progress_data`

## Task 2: Implement DashboardDataCollector

- [x] 2.1 Implement `DashboardDataCollector.__init__()` and `collect()` orchestrator that calls all internal methods and assembles a `DashboardData` instance with ISO 8601 `generated_at` timestamp
- [ ] 2.2 Implement `_load_progress()` that reads `config/bootcamp_progress.json` as primary source, falls back to parsing `docs/guides/PROGRESS_TRACKER.md`, and returns default "Not Started" state when neither exists
- [ ] 2.3 Implement `_load_completion_timestamps()` that extracts module completion timestamps from `step_history` in the progress JSON, returning a dict of module number to ISO 8601 string
- [ ] 2.4 Implement `_scan_quality_scores()` that scans project documentation artifacts for quality score data using regex patterns, returning a list of `QualityScoreData`
- [ ] 2.5 Implement `_scan_performance_metrics()` that scans project artifacts for loading throughput, query response times, database type, and wall-clock time, returning `PerformanceData` or None
- [ ] 2.6 Implement `_scan_entity_stats()` that scans project artifacts for entity resolution statistics (records, entities, matches, duplicates, cross-source), returning `EntityStatsData` or None
- [ ] 2.7 Implement `_check_health()` that checks the 8 project health paths (data/raw, database, src, scripts, .gitignore, .env.example, README.md, backups) and returns health check items with score

## Task 3: Implement DashboardRenderer

- [x] 3.1 Implement `_render_head()` returning `<head>` with inline `<style>` tag containing responsive CSS, card layout, progress bar styles, color-coded bands, and print-friendly styles — no external references
- [ ] 3.2 Implement `_render_header()` returning `<header>` with dashboard title, status badge, programming language (when available), and progress fraction ("X / 12 modules")
- [ ] 3.3 Implement `_render_progress_bar()` returning a `<section>` with a horizontal progress bar filled proportionally to `completion_pct` and displaying the percentage
- [ ] 3.4 Implement `_render_module_cards()` returning a `<section>` with 12 module cards, each showing module number, name, and a completed/in-progress/not-started visual indicator based on `DashboardData` state
- [ ] 3.5 Implement `_render_quality_section()` returning a `<section>` with quality scores per data source showing overall score, color-coded band, and sub-scores when available; returns empty string when `quality_scores` is empty
- [ ] 3.6 Implement `_render_performance_section()` returning a `<section>` with performance metrics (throughput, query times, db type, wall-clock); returns empty string when `performance` is None
- [ ] 3.7 Implement `_render_entity_section()` returning a `<section>` with entity resolution stats (records, entities, matches, duplicates, cross-source); returns empty string when `entity_stats` is None
- [ ] 3.8 Implement `_render_timeline()` returning a `<section>` with completed modules listed chronologically by completion date, showing module number, name, and date; returns empty string when `completion_timestamps` is empty
- [ ] 3.9 Implement `_render_health_section()` returning a `<section>` with 8 health check items showing pass/fail indicators and overall health score as fraction and percentage
- [x] 3.10 Implement `_render_footer()` returning `<footer>` with generation timestamp, and `render()` orchestrator that assembles all sections into a complete HTML document using semantic elements (`<header>`, `<main>`, `<section>`, `<footer>`)

## Task 4: Implement CLI integration and file output

- [x] 4.1 Extend `status.py` `main()` with `argparse` supporting `--html`, `--output` (default `docs/dashboard.html`), `--no-open`, and `--sync` flags, preserving existing terminal output when `--html` is not provided
- [x] 4.2 Implement `generate_dashboard()` function that orchestrates data collection, rendering, file writing (creating output directory if needed), printing file path and size, and auto-opening in browser via `webbrowser.open()` unless `--no-open` is set
- [x] 4.3 Implement error handling: catch write failures (print error, exit non-zero), catch invalid JSON in progress file (print warning, continue), catch browser open failures (print file path), ensure no unhandled exceptions during generation

## Task 5: Property-based tests

- [x] 5.1 Create `senzing-bootcamp/scripts/test_dashboard.py` with Hypothesis strategies for `QualityScoreData`, `PerformanceData`, `EntityStatsData`, `HealthCheckItem`, and `DashboardData`
- [ ] 5.2 PBT: Property 1 — Self-contained HTML output: no external resource references (Req 2.1, 2.2, 2.3)
- [ ] 5.3 PBT: Property 2 — Semantic HTML structure with required elements, charset, and footer timestamp (Req 2.4, 2.6, 12.3)
- [ ] 5.4 PBT: Property 3 — Progress bar reflects completion state with correct percentage and fraction (Req 4.1, 4.2)
- [ ] 5.5 PBT: Property 4 — Module cards reflect correct status for all 12 modules (Req 4.3, 4.4, 4.5, 4.6)
- [ ] 5.6 PBT: Property 5 — Header displays status and language metadata (Req 4.7, 4.8)
- [ ] 5.7 PBT: Property 6 — Quality section conditional rendering with correct values and bands (Req 5.1, 5.2, 5.4, 5.5)
- [ ] 5.8 PBT: Property 7 — Performance section conditional rendering with correct values (Req 6.1–6.6)
- [ ] 5.9 PBT: Property 8 — Entity statistics section conditional rendering with correct values (Req 7.1–7.7)
- [ ] 5.10 PBT: Property 9 — Timeline conditional rendering in chronological order (Req 8.1–8.4)
- [ ] 5.11 PBT: Property 10 — Health section displays all checks with correct indicators and score (Req 9.1–9.3)
- [ ] 5.12 PBT: Property 11 — Quality band classification (Req 5.3)
- [ ] 5.13 PBT: Property 12 — Rendering never raises unhandled exceptions (Req 11.3)

## Task 6: Unit tests for edge cases and integration points

- [ ] 6.1 Unit test: CLI argument parsing — `--html` flag accepted, `--output` custom path, `--no-open` flag, backward compatibility without `--html` (Req 1.1–1.4)
- [ ] 6.2 Unit test: output directory auto-creation, file path and size printed to stdout (Req 1.5, 1.6)
- [ ] 6.3 Unit test: browser auto-open with mocked `webbrowser.open`, `--no-open` suppresses it, browser failure prints file path (Req 3.1–3.3)
- [ ] 6.4 Unit test: progress JSON primary source, markdown fallback, neither-exists shows notice + health only (Req 10.1–10.3)
- [ ] 6.5 Unit test: file read error skips data source, write failure exits non-zero, invalid JSON prints warning and continues (Req 10.5, 11.1, 11.2)
