# Requirements Document

## Introduction

Auto-generate a graduation certificate in both Markdown and HTML formats when a bootcamper completes their bootcamp track. The certificate summarizes the project name, completion date, modules completed with outcomes, entity resolution results, skills demonstrated, and next steps. Generation is triggered automatically at track completion without prompting the user. The script lives at `senzing-bootcamp/scripts/generate_graduation_certificate.py`, uses Python 3.11+ stdlib only, accepts arguments via `argparse`, and exposes a `main(argv=None)` entry point. Output is written to the `docs/graduation/` directory. The steering file `senzing-bootcamp/steering/module-completion.md` is updated to invoke the script during the "Path Completion Celebration" section.

## Glossary

- **Certificate_Generator**: The Python script `senzing-bootcamp/scripts/generate_graduation_certificate.py` responsible for producing graduation certificate files.
- **Progress_File**: The JSON file `config/bootcamp_progress.json` containing module completion state.
- **Preferences_File**: The YAML file `config/bootcamp_preferences.yaml` containing user choices (language, track, etc.).
- **Journal_File**: The Markdown file `docs/bootcamp_journal.md` containing per-module journal entries.
- **Graduation_Directory**: The output directory `docs/graduation/` where certificate files are written.
- **Track_Completion**: The state where all modules in the bootcamper's selected track have been marked complete in the Progress_File.

## Requirements

### Requirement 1: Certificate Generation Trigger

**User Story:** As a bootcamper, I want a graduation certificate generated automatically when I complete my track, so that I receive recognition without extra steps.

#### Acceptance Criteria

1. WHEN Track_Completion is detected during the Path Completion Celebration workflow, THE module-completion steering SHALL invoke the Certificate_Generator script.
2. THE module-completion steering SHALL invoke the Certificate_Generator without prompting the bootcamper for confirmation.
3. IF the Certificate_Generator fails, THEN THE module-completion steering SHALL log a warning message and continue the completion flow without blocking subsequent steps.

### Requirement 2: Script Interface

**User Story:** As a developer, I want the Certificate_Generator to follow project conventions, so that it integrates consistently with the existing script ecosystem.

#### Acceptance Criteria

1. THE Certificate_Generator SHALL use Python 3.11+ standard library only with no third-party dependencies.
2. THE Certificate_Generator SHALL accept command-line arguments via `argparse` with a `main(argv=None)` entry point.
3. THE Certificate_Generator SHALL accept a `--progress-file` argument specifying the path to the Progress_File (default: `config/bootcamp_progress.json`).
4. THE Certificate_Generator SHALL accept a `--preferences-file` argument specifying the path to the Preferences_File (default: `config/bootcamp_preferences.yaml`).
5. THE Certificate_Generator SHALL accept a `--journal-file` argument specifying the path to the Journal_File (default: `docs/bootcamp_journal.md`).
6. THE Certificate_Generator SHALL accept an `--output-dir` argument specifying the Graduation_Directory path (default: `docs/graduation/`).
7. THE Certificate_Generator SHALL exit with code 0 on success and a non-zero code on failure.

### Requirement 3: Output Format

**User Story:** As a bootcamper, I want my graduation certificate in both Markdown and HTML formats, so that I can view it in any context and share it easily.

#### Acceptance Criteria

1. WHEN invoked successfully, THE Certificate_Generator SHALL produce a Markdown file named `graduation_certificate.md` in the Graduation_Directory.
2. WHEN invoked successfully, THE Certificate_Generator SHALL produce an HTML file named `graduation_certificate.html` in the Graduation_Directory.
3. THE Certificate_Generator SHALL create the Graduation_Directory if it does not already exist.
4. THE Certificate_Generator SHALL generate the HTML file using only Python standard library modules without external template engines or HTML libraries.
5. THE Certificate_Generator SHALL produce valid HTML5 with inline CSS styling in the HTML output.

### Requirement 4: Certificate Content — Identity and Dates

**User Story:** As a bootcamper, I want my certificate to show my project name and completion date, so that the certificate is personalized and timestamped.

#### Acceptance Criteria

1. THE Certificate_Generator SHALL include the project name derived from the workspace directory name in the certificate.
2. THE Certificate_Generator SHALL include the completion date in ISO 8601 format (YYYY-MM-DD) in the certificate.
3. THE Certificate_Generator SHALL include the track name (Core Bootcamp or Advanced Topics) read from the Preferences_File in the certificate.

### Requirement 5: Certificate Content — Modules Completed

**User Story:** As a bootcamper, I want my certificate to list all modules I completed with their outcomes, so that I have a record of my learning journey.

#### Acceptance Criteria

1. THE Certificate_Generator SHALL list each completed module by number and name as recorded in the Progress_File.
2. THE Certificate_Generator SHALL include a brief outcome description for each module derived from the Journal_File entries.
3. IF the Journal_File does not exist or lacks an entry for a completed module, THEN THE Certificate_Generator SHALL use the module name from the Progress_File without an outcome description.

### Requirement 6: Certificate Content — ER Results Summary

**User Story:** As a bootcamper, I want my certificate to summarize my entity resolution results, so that I can demonstrate the practical outcomes of the bootcamp.

#### Acceptance Criteria

1. THE Certificate_Generator SHALL include an entity resolution results summary section in the certificate.
2. WHEN the Journal_File contains ER-related entries (entity counts, match rates, data sources loaded), THE Certificate_Generator SHALL extract and include those metrics.
3. IF no ER metrics are available from the Journal_File, THEN THE Certificate_Generator SHALL include a placeholder stating that ER results were not recorded.

### Requirement 7: Certificate Content — Skills and Next Steps

**User Story:** As a bootcamper, I want my certificate to list skills demonstrated and recommended next steps, so that I understand what I achieved and where to go next.

#### Acceptance Criteria

1. THE Certificate_Generator SHALL include a skills-demonstrated section derived from the modules completed (mapping module names to skill categories).
2. THE Certificate_Generator SHALL include a next-steps section with recommendations based on the completed track.
3. WHEN the completed track is Core Bootcamp, THE Certificate_Generator SHALL recommend advanced topics (performance, security, monitoring, deployment) as next steps.
4. WHEN the completed track is Advanced Topics, THE Certificate_Generator SHALL recommend production deployment and ongoing operations as next steps.

### Requirement 8: Steering File Integration

**User Story:** As a power maintainer, I want the module-completion steering to invoke the certificate generator at the right point in the workflow, so that certificates are produced seamlessly.

#### Acceptance Criteria

1. THE module-completion steering SHALL invoke the Certificate_Generator in the "Path Completion Celebration" section after the analytics offer and before the graduation offer.
2. WHEN the Certificate_Generator completes successfully, THE module-completion steering SHALL display the output file paths to the bootcamper.
3. THE module-completion steering SHALL present the certificate generation result as a single informational line (e.g., "🎓 Graduation certificate generated at docs/graduation/").

### Requirement 9: Data Source Resilience

**User Story:** As a bootcamper, I want the certificate to generate even if some data sources are incomplete, so that partial progress still produces a certificate.

#### Acceptance Criteria

1. IF the Progress_File does not exist, THEN THE Certificate_Generator SHALL exit with a non-zero code and print an error message to stderr.
2. IF the Preferences_File does not exist, THEN THE Certificate_Generator SHALL use default values (track: "Unknown", language: "Unknown").
3. IF the Journal_File does not exist, THEN THE Certificate_Generator SHALL generate the certificate without outcome descriptions or ER metrics.
4. THE Certificate_Generator SHALL not raise unhandled exceptions for missing or malformed input files.

### Requirement 10: Idempotent Output

**User Story:** As a bootcamper, I want re-running the certificate generator to overwrite previous output cleanly, so that I always have the latest version.

#### Acceptance Criteria

1. WHEN the Graduation_Directory already contains certificate files, THE Certificate_Generator SHALL overwrite the existing files without error.
2. THE Certificate_Generator SHALL produce identical output when run multiple times with the same input data.
