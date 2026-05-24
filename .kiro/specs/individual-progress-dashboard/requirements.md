# Requirements Document

## Introduction

A standalone Python script (`progress_dashboard.py`) that reads bootcamp progress, preferences, and module dependency data to generate a self-contained HTML dashboard at `docs/progress/dashboard.html`. The dashboard visualizes module completion status, artifacts produced, dependency-aware next steps, and a preferences summary card. The script uses Python 3.11+ stdlib only, provides an argparse CLI, and has no imports from `status.py` or other project scripts.

## Glossary

- **Dashboard_Generator**: The `progress_dashboard.py` script that reads input files and produces HTML output
- **Progress_File**: The JSON file at `config/bootcamp_progress.json` containing module completion state
- **Preferences_File**: The YAML file at `config/bootcamp_preferences.yaml` containing user choices
- **Dependencies_File**: The YAML file at `config/module-dependencies.yaml` containing module dependency graph
- **Dashboard_Output**: The self-contained HTML file written to `docs/progress/dashboard.html`
- **Module_Completion**: A module listed in the `modules_completed` array of the Progress_File
- **Artifact**: A file or output produced during a completed module (tracked in `step_history`)
- **Next_Step**: A module whose hard prerequisites are all satisfied but is not yet completed
- **Preferences_Card**: A visual section of the Dashboard_Output showing language, track, database type, and deployment target

## Requirements

### Requirement 1: CLI Interface

**User Story:** As a bootcamp user, I want to run the dashboard generator from the command line with sensible defaults, so that I can produce a dashboard without complex configuration.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL accept an optional `--progress` argument specifying the path to the Progress_File, defaulting to `config/bootcamp_progress.json` relative to the script's parent directory.
2. THE Dashboard_Generator SHALL accept an optional `--preferences` argument specifying the path to the Preferences_File, defaulting to `config/bootcamp_preferences.yaml` relative to the script's parent directory.
3. THE Dashboard_Generator SHALL accept an optional `--dependencies` argument specifying the path to the Dependencies_File, defaulting to `config/module-dependencies.yaml` relative to the script's parent directory.
4. THE Dashboard_Generator SHALL accept an optional `--output` argument specifying the path to the Dashboard_Output, defaulting to `docs/progress/dashboard.html` relative to the script's parent directory.
5. WHEN invoked with `--help`, THE Dashboard_Generator SHALL display usage information describing all arguments and exit with code 0.
6. WHEN the Dashboard_Generator completes successfully, THE Dashboard_Generator SHALL exit with code 0.
7. IF a required input file does not exist, THEN THE Dashboard_Generator SHALL print an error message identifying the missing file and exit with code 1.

### Requirement 2: Progress File Parsing

**User Story:** As a bootcamp user, I want the dashboard to read my progress data accurately, so that the dashboard reflects my actual completion state.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL parse the Progress_File as JSON containing at minimum the keys `current_module`, `modules_completed`, `current_step`, `language`, and `step_history`.
2. WHEN the Progress_File contains a `modules_completed` array, THE Dashboard_Generator SHALL treat each integer entry as a completed module number.
3. WHEN the Progress_File contains a `step_history` object, THE Dashboard_Generator SHALL extract artifact references from the step entries.
4. IF the Progress_File contains invalid JSON, THEN THE Dashboard_Generator SHALL print an error message and exit with code 1.

### Requirement 3: Preferences File Parsing

**User Story:** As a bootcamp user, I want the dashboard to display my chosen preferences, so that I can confirm my configuration at a glance.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL parse the Preferences_File using a custom minimal YAML parser without importing PyYAML.
2. THE Dashboard_Generator SHALL extract the `language`, `track`, `database_type`, and `deployment_target` fields from the Preferences_File.
3. WHEN a preference field has a value of `null` or is absent, THE Dashboard_Generator SHALL display that field as "Not set" in the Preferences_Card.

### Requirement 4: Dependencies File Parsing

**User Story:** As a bootcamp user, I want the dashboard to understand module dependencies, so that it can recommend valid next steps.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL parse the Dependencies_File using a custom minimal YAML parser without importing PyYAML.
2. THE Dashboard_Generator SHALL extract the `modules` section containing module numbers, names, and `requires` arrays.
3. THE Dashboard_Generator SHALL extract the `gates` section containing transition requirements between modules.

### Requirement 5: Module Completion Display

**User Story:** As a bootcamp user, I want to see which modules I have completed, which is in progress, and which remain, so that I can gauge my overall progress.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL display all modules from the Dependencies_File with a visual indicator of their completion status: completed, in-progress, or not-started.
2. WHEN a module number appears in the `modules_completed` array, THE Dashboard_Generator SHALL mark that module as completed.
3. WHEN the `current_module` field matches a module number, THE Dashboard_Generator SHALL mark that module as in-progress.
4. THE Dashboard_Generator SHALL display a progress summary showing the count of completed modules out of total modules.

### Requirement 6: Artifacts Display

**User Story:** As a bootcamp user, I want to see what artifacts I have produced during the bootcamp, so that I can review my outputs.

#### Acceptance Criteria

1. WHEN the `step_history` contains entries with artifact references, THE Dashboard_Generator SHALL list those artifacts in the Dashboard_Output grouped by module.
2. WHEN no artifacts exist in the step_history, THE Dashboard_Generator SHALL display a message indicating no artifacts have been produced yet.

### Requirement 7: Dependency-Aware Next Steps

**User Story:** As a bootcamp user, I want the dashboard to recommend which modules I can start next based on my completed prerequisites, so that I follow a valid learning path.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL compute Next_Steps by identifying modules whose `requires` array entries are all present in `modules_completed`.
2. THE Dashboard_Generator SHALL exclude completed modules and the current in-progress module from the Next_Steps list.
3. WHEN a module has a `gates` entry, THE Dashboard_Generator SHALL display the gate requirements alongside the Next_Step recommendation.
4. WHEN no Next_Steps are available and modules remain incomplete, THE Dashboard_Generator SHALL display a message indicating which prerequisites are blocking progress.
5. WHEN all modules are completed, THE Dashboard_Generator SHALL display a congratulatory completion message.

### Requirement 8: Preferences Summary Card

**User Story:** As a bootcamp user, I want to see my chosen language, track, database type, and deployment target in a summary card, so that I can verify my configuration.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL render a Preferences_Card section in the Dashboard_Output.
2. THE Preferences_Card SHALL display the `language` value from the Preferences_File.
3. THE Preferences_Card SHALL display the `track` value from the Preferences_File.
4. THE Preferences_Card SHALL display the `database_type` value from the Preferences_File.
5. THE Preferences_Card SHALL display the `deployment_target` value from the Preferences_File.

### Requirement 9: Self-Contained HTML Output

**User Story:** As a bootcamp user, I want the dashboard to be a single HTML file with no external dependencies, so that I can open it in any browser without a server.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL produce a single HTML file containing all CSS inline within a `<style>` element.
2. THE Dashboard_Generator SHALL produce valid HTML5 markup.
3. THE Dashboard_Output SHALL render correctly when opened directly from the filesystem without a web server.
4. THE Dashboard_Generator SHALL create the output directory if it does not already exist.

### Requirement 10: Standalone Implementation

**User Story:** As a developer, I want the dashboard script to be fully self-contained, so that it can be maintained independently of other scripts.

#### Acceptance Criteria

1. THE Dashboard_Generator SHALL have zero imports from `status.py` or any other script in the `scripts/` directory.
2. THE Dashboard_Generator SHALL use only Python 3.11+ standard library modules.
3. THE Dashboard_Generator SHALL follow the project script pattern: shebang, `from __future__ import annotations`, argparse CLI with `main(argv=None)` signature, and `if __name__ == "__main__": main()` entry point.
