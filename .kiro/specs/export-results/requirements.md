# Requirements Document

## Introduction

The senzing-bootcamp power currently has no mechanism for bootcampers to package and share their completed work. After finishing a track, all artifacts — the bootcamp journal, quality scores, performance metrics, entity resolution statistics, and visualizations — exist as scattered files across the project directory. Sharing results with colleagues or stakeholders requires manually collecting files and explaining context. This feature adds a `scripts/export_results.py` script that bundles bootcamp artifacts into a self-contained HTML report or ZIP archive, with an executive summary suitable for stakeholders, module filtering, and integration into the module-completion workflow.

## Glossary

- **Export_Script**: The Python script at `senzing-bootcamp/scripts/export_results.py` that generates shareable reports from bootcamp artifacts.
- **HTML_Report**: A single self-contained HTML file produced by the Export_Script that includes all report content, styles, and embedded data with no external dependencies.
- **ZIP_Archive**: A ZIP file produced by the Export_Script that contains the HTML_Report alongside copies of raw artifact files (visualizations, data files, source code).
- **Bootcamp_Journal**: The markdown file at `docs/bootcamp_journal.md` that records per-module completion entries, artifacts produced, and bootcamper reflections.
- **Progress_Data**: The JSON structure stored in `config/bootcamp_progress.json` that tracks module completion state, current module, language choice, and data sources.
- **Quality_Score**: The 0–100 weighted score produced during Module 5 that measures data completeness, consistency, format compliance, and uniqueness.
- **Performance_Metrics**: Throughput and timing measurements produced during Modules 6, 7, and 9 — including records-per-second, wall-clock loading time, and query response times.
- **Entity_Statistics**: Entity resolution outcome data produced during Modules 6–8 — including total entities resolved, match counts, cross-source matches, and duplicate counts.
- **Visualization_Artifact**: An HTML or image file in the project directory containing entity graphs, dashboards, or other visual outputs produced during Module 8.
- **Executive_Summary**: A generated section at the top of the HTML_Report that summarizes the bootcamp outcome in non-technical language suitable for stakeholders.
- **Module_Filter**: A command-line option (`--modules`) that restricts the export to artifacts from specific modules.
- **Artifact_Manifest**: An internal data structure built by the Export_Script that catalogs all discovered artifacts, their source modules, types, and file paths before report generation.

## Requirements

### Requirement 1: Export Script Location and Invocation

**User Story:** As a bootcamper, I want a single script I can run to export my bootcamp results, so that I can share my work without manually collecting files.

#### Acceptance Criteria

1. THE Export_Script SHALL reside at `senzing-bootcamp/scripts/export_results.py`.
2. THE Export_Script SHALL be executable from the project root via `python senzing-bootcamp/scripts/export_results.py` or `python scripts/export_results.py` (when scripts are copied locally).
3. THE Export_Script SHALL depend only on the Python standard library (no third-party packages).
4. THE Export_Script SHALL be cross-platform, supporting Linux, macOS, and Windows.
5. THE Export_Script SHALL accept a `--format` argument with values `html` (default) or `zip`.
6. THE Export_Script SHALL accept a `--modules` argument with a comma-separated list of module numbers (e.g., `--modules 1,2,3`) to restrict the export to specific modules.
7. THE Export_Script SHALL accept an `--output` argument specifying the output file path, defaulting to `exports/bootcamp_report_{timestamp}.html` or `exports/bootcamp_report_{timestamp}.zip`.

### Requirement 2: Artifact Discovery

**User Story:** As a bootcamper, I want the export to automatically find all my bootcamp artifacts, so that I do not have to manually list which files to include.

#### Acceptance Criteria

1. WHEN the Export_Script runs, THE Export_Script SHALL scan the project directory for the Bootcamp_Journal at `docs/bootcamp_journal.md`.
2. WHEN the Export_Script runs, THE Export_Script SHALL read the Progress_Data from `config/bootcamp_progress.json` to determine completed modules, current module, chosen language, and data sources.
3. WHEN the Export_Script runs, THE Export_Script SHALL scan `data/transformed/` for transformed data files and `data/raw/` for source data file names.
4. WHEN the Export_Script runs, THE Export_Script SHALL scan for Visualization_Artifacts by checking for HTML files in the project directory tree that contain entity graph or dashboard content.
5. WHEN the Export_Script runs, THE Export_Script SHALL scan `src/` for source code files matching the chosen language extension.
6. WHEN the Export_Script runs, THE Export_Script SHALL scan `docs/` for quality assessment reports, lessons learned, and stakeholder summaries.
7. WHEN an expected artifact file does not exist, THE Export_Script SHALL skip the missing artifact and note its absence in the report rather than raising an error.
8. THE Export_Script SHALL build an Artifact_Manifest cataloging each discovered artifact with its file path, associated module number, artifact type, and file size.

### Requirement 3: Module Completion Status

**User Story:** As a bootcamper, I want the report to show which modules I completed and my overall progress, so that readers understand the scope of my work.

#### Acceptance Criteria

1. THE HTML_Report SHALL include a module completion table listing all 12 modules with their names, completion status (completed, in progress, or not started), and completion date where available.
2. WHEN the Progress_Data contains a `modules_completed` list, THE HTML_Report SHALL mark those modules as completed.
3. WHEN the Progress_Data contains a `current_module` value for a module not in `modules_completed`, THE HTML_Report SHALL mark that module as in progress.
4. THE HTML_Report SHALL display an overall progress percentage calculated as `completed modules / 12 × 100`.
5. THE HTML_Report SHALL display the chosen programming language from the Progress_Data.

### Requirement 4: Quality Scores and Metrics Display

**User Story:** As a bootcamper, I want the report to include my data quality scores and performance metrics, so that stakeholders can see the quantitative outcomes of my work.

#### Acceptance Criteria

1. WHEN quality assessment data exists in `docs/` (quality score reports from Module 5), THE HTML_Report SHALL include a quality scores section showing the overall score and sub-scores (completeness, consistency, format compliance, uniqueness) for each data source.
2. WHEN performance metrics exist in project artifacts (from Modules 6, 7, or 9), THE HTML_Report SHALL include a performance section showing loading throughput, query response times, and database type.
3. WHEN Entity_Statistics exist in project artifacts (from Modules 6–8), THE HTML_Report SHALL include an entity resolution statistics section showing total records loaded, total entities resolved, and match counts.
4. WHEN quality, performance, or entity statistics data is not available, THE HTML_Report SHALL omit the corresponding section rather than displaying empty or placeholder content.

### Requirement 5: Bootcamp Journal Inclusion

**User Story:** As a bootcamper, I want my bootcamp journal included in the report, so that readers can see my learning journey and reflections.

#### Acceptance Criteria

1. WHEN the Bootcamp_Journal exists, THE HTML_Report SHALL include the full journal content rendered as formatted HTML.
2. WHEN the Bootcamp_Journal contains per-module entries, THE HTML_Report SHALL preserve the module-by-module structure with headings, artifact lists, and bootcamper takeaways.
3. WHEN the Bootcamp_Journal does not exist, THE HTML_Report SHALL omit the journal section and note that no journal was recorded.

### Requirement 6: Visualization Embedding

**User Story:** As a bootcamper, I want my entity graphs and dashboards included in the report, so that stakeholders can see visual results without needing separate files.

#### Acceptance Criteria

1. WHEN Visualization_Artifacts (HTML files containing entity graphs or dashboards) exist in the project, THE HTML_Report SHALL embed a screenshot-style reference or inline iframe for each visualization.
2. WHEN the `--format zip` option is used, THE ZIP_Archive SHALL include copies of all discovered Visualization_Artifact files alongside the HTML_Report.
3. WHEN no Visualization_Artifacts are found, THE HTML_Report SHALL omit the visualizations section.
4. THE HTML_Report SHALL list each included visualization with its filename and a description of what it shows.

### Requirement 7: Executive Summary Generation

**User Story:** As a bootcamper, I want the report to include a stakeholder-friendly executive summary, so that I can share results with non-technical colleagues.

#### Acceptance Criteria

1. THE HTML_Report SHALL include an Executive_Summary section at the top of the report before detailed content.
2. THE Executive_Summary SHALL state the bootcamp track completed (A, B, C, or D) and the number of modules finished.
3. WHEN Quality_Score data is available, THE Executive_Summary SHALL include the overall data quality assessment (green/yellow/red band) for each data source.
4. WHEN Entity_Statistics are available, THE Executive_Summary SHALL include the total records processed and total entities resolved.
5. THE Executive_Summary SHALL list the key artifacts produced during the bootcamp (source code, transformed data, documentation).
6. THE Executive_Summary SHALL use plain language without Senzing-specific jargon, defining technical terms where they appear.

### Requirement 8: HTML Report Self-Containment

**User Story:** As a bootcamper, I want the HTML report to work as a single file with no external dependencies, so that I can email it or share it on any platform.

#### Acceptance Criteria

1. THE HTML_Report SHALL embed all CSS styles inline within a `<style>` tag in the HTML `<head>`.
2. THE HTML_Report SHALL not reference any external stylesheets, scripts, or fonts.
3. THE HTML_Report SHALL use semantic HTML elements (`<header>`, `<main>`, `<section>`, `<table>`, `<nav>`) for structure.
4. THE HTML_Report SHALL include a table of contents with anchor links to each report section.
5. THE HTML_Report SHALL include a generation timestamp and the Export_Script version in the footer.
6. THE HTML_Report SHALL be viewable in any modern web browser without requiring a web server.

### Requirement 9: ZIP Archive Format

**User Story:** As a bootcamper, I want a ZIP option that bundles the report with all raw artifacts, so that I can share a complete package including source files.

#### Acceptance Criteria

1. WHEN the `--format zip` option is used, THE Export_Script SHALL create a ZIP_Archive containing the HTML_Report at the archive root.
2. THE ZIP_Archive SHALL include a `artifacts/` directory containing copies of all discovered artifact files organized by type (e.g., `artifacts/visualizations/`, `artifacts/data/`, `artifacts/source/`, `artifacts/docs/`).
3. THE ZIP_Archive SHALL include a `manifest.json` file listing all included files with their original paths, artifact types, associated modules, and file sizes.
4. THE ZIP_Archive SHALL exclude files matching common exclusion patterns (`__pycache__`, `.pyc`, `.env`, `.git`, `node_modules`, `database/`).
5. WHEN the ZIP_Archive is created, THE Export_Script SHALL report the archive file path and total size.

### Requirement 10: Module Filtering

**User Story:** As a bootcamper, I want to export results for specific modules only, so that I can share a focused report on a particular phase of my work.

#### Acceptance Criteria

1. WHEN the `--modules` argument is provided with a comma-separated list of module numbers, THE Export_Script SHALL include only artifacts associated with the specified modules.
2. WHEN the `--modules` argument is provided, THE HTML_Report SHALL indicate which modules are included in the report header.
3. WHEN the `--modules` argument specifies a module number outside the 1–12 range, THE Export_Script SHALL print a warning and ignore the invalid module number.
4. WHEN the `--modules` argument is not provided, THE Export_Script SHALL include artifacts from all completed modules.
5. WHEN the `--modules` argument specifies modules that have no associated artifacts, THE Export_Script SHALL include those modules in the completion table but note that no artifacts were found.

### Requirement 11: Module-Completion Workflow Integration

**User Story:** As a bootcamper finishing a track, I want the option to export my results as part of the completion workflow, so that sharing is a natural next step after finishing.

#### Acceptance Criteria

1. THE module-completion steering file (`module-completion.md`) SHALL include an export option in the Next-Step Options presented after track completion.
2. THE export option SHALL be presented as: "Would you like to export a shareable report of your bootcamp results?"
3. WHEN the bootcamper selects the export option, THE Agent SHALL run the Export_Script with the appropriate format and present the output file path.
4. THE export option SHALL be presented only at track completion (after the path completion celebration), not after every individual module.

### Requirement 12: Error Handling and User Feedback

**User Story:** As a bootcamper, I want clear feedback when running the export, so that I know what was included and can troubleshoot any issues.

#### Acceptance Criteria

1. THE Export_Script SHALL print a progress summary during execution showing each artifact category discovered and the count of files found.
2. WHEN the export completes, THE Export_Script SHALL print the output file path, file size, and a count of artifacts included.
3. IF the Progress_Data file does not exist, THEN THE Export_Script SHALL print a warning that no progress data was found and generate a minimal report with whatever artifacts are discoverable.
4. IF no artifacts are found in any category, THEN THE Export_Script SHALL print a warning and exit with a non-zero exit code rather than generating an empty report.
5. IF the output directory does not exist, THEN THE Export_Script SHALL create the output directory before writing the report.
6. IF a file read error occurs for any individual artifact, THEN THE Export_Script SHALL log the error, skip the artifact, and continue processing remaining artifacts.
