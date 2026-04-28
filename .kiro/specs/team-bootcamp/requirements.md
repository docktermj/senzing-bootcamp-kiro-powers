# Requirements Document

## Introduction

The senzing-bootcamp power currently supports only single-user bootcamp sessions. The `COLLABORATION_GUIDE.md` provides team workflow advice (branch naming, code review, splitting work) but the actual infrastructure — progress tracking, configuration, feedback, and onboarding — is entirely single-user. There is no way for a team to share a configuration, compare entity resolution results across members working with different data sources, or consolidate individual feedback into a team report.

This feature adds multi-user / team bootcamp support: a shared team configuration file (`config/team.yaml`), a dashboard script (`scripts/team_dashboard.py`) that generates an HTML overview of all team members' progress, a merge script (`scripts/merge_feedback.py`) that consolidates individual feedback files into a team report, team-level progress tracking alongside individual progress, a comparison view showing how different members' entity resolution results differ, and onboarding integration that detects team mode and configures accordingly. Both co-located (shared repository) and distributed (separate repositories) team setups are supported.

## Glossary

- **Team_Config**: The YAML configuration file at `config/team.yaml` that defines the team name, member list, shared data sources, and team mode (co-located or distributed).
- **Team_Member**: An entry in the Team_Config that identifies a bootcamp participant by a unique member identifier, display name, and optional repository path (for distributed mode).
- **Dashboard_Script**: The Python script at `senzing-bootcamp/scripts/team_dashboard.py` that reads team and individual progress data and generates an HTML dashboard.
- **Team_Dashboard**: The self-contained HTML file produced by the Dashboard_Script that shows all team members' progress, module completion, and comparison data.
- **Merge_Script**: The Python script at `senzing-bootcamp/scripts/merge_feedback.py` that combines individual feedback files into a consolidated team feedback report.
- **Team_Feedback_Report**: The consolidated markdown file produced by the Merge_Script that aggregates all team members' individual feedback entries.
- **Individual_Progress**: The per-member progress data stored in `config/bootcamp_progress.json` (single-user format) that tracks module completion, current module, language, and data sources.
- **Team_Progress**: An aggregated view of all team members' Individual_Progress data, including per-member status and team-level completion statistics.
- **Co-located_Mode**: A team setup where all members work in the same shared repository and their progress files coexist in the same directory tree.
- **Distributed_Mode**: A team setup where each member works in a separate repository clone and progress data is collected by specifying paths to each member's repository.
- **ER_Comparison**: A side-by-side view in the Team_Dashboard that shows how entity resolution outcomes (entity counts, match counts, cross-source matches) differ across team members working with different data sources or configurations.
- **Onboarding_Detector**: The logic within the onboarding flow that checks for the presence of a Team_Config file and activates team mode when found.

## Requirements

### Requirement 1: Team Configuration File

**User Story:** As a team lead, I want a single configuration file that defines my team and shared settings, so that all team tooling knows who is on the team and how the team is organized.

#### Acceptance Criteria

1. THE Team_Config SHALL be a YAML file located at `config/team.yaml` in the project root.
2. THE Team_Config SHALL contain a `team_name` field (string) identifying the team.
3. THE Team_Config SHALL contain a `members` field (list) where each entry includes a `id` (unique string identifier), a `name` (display name), and an optional `repo_path` (filesystem path to the member's repository root, used in Distributed_Mode).
4. THE Team_Config SHALL contain a `mode` field with a value of `colocated` or `distributed`.
5. THE Team_Config SHALL contain an optional `shared_data_sources` field (list of strings) identifying data source names the team shares.
6. WHEN the `mode` is `distributed`, THE Team_Config SHALL require a `repo_path` for each Team_Member.
7. WHEN the `mode` is `colocated`, THE Team_Config SHALL store each member's progress at `config/progress_{member_id}.json` instead of a single `bootcamp_progress.json`.
8. IF the Team_Config contains duplicate member `id` values, THEN THE tooling that reads the Team_Config SHALL report a validation error identifying the duplicate identifiers.
9. IF the Team_Config is missing required fields (`team_name`, `members`, `mode`), THEN THE tooling that reads the Team_Config SHALL report a validation error identifying the missing fields.

### Requirement 2: Team Dashboard Generation

**User Story:** As a team lead, I want an HTML dashboard showing all team members' bootcamp progress, so that I can track the team's overall status at a glance.

#### Acceptance Criteria

1. THE Dashboard_Script SHALL reside at `senzing-bootcamp/scripts/team_dashboard.py`.
2. THE Dashboard_Script SHALL be executable from the project root via `python senzing-bootcamp/scripts/team_dashboard.py` or `python scripts/team_dashboard.py` (when scripts are copied locally).
3. THE Dashboard_Script SHALL depend only on the Python standard library (no third-party packages).
4. THE Dashboard_Script SHALL be cross-platform, supporting Linux, macOS, and Windows.
5. WHEN the Dashboard_Script runs, THE Dashboard_Script SHALL read the Team_Config from `config/team.yaml`.
6. WHEN the `mode` is `colocated`, THE Dashboard_Script SHALL read each member's progress from `config/progress_{member_id}.json`.
7. WHEN the `mode` is `distributed`, THE Dashboard_Script SHALL read each member's progress from `{repo_path}/config/bootcamp_progress.json`.
8. THE Team_Dashboard SHALL include a team summary section showing the team name, total members, overall team completion percentage (average of all members' module completion), and the count of members who have completed all modules in their track.
9. THE Team_Dashboard SHALL include a per-member progress table listing each Team_Member's name, current module, number of completed modules, chosen language, and completion percentage.
10. THE Team_Dashboard SHALL include a module heatmap showing which modules each member has completed, using color coding (completed, in progress, not started) in a members-by-modules grid.
11. THE Dashboard_Script SHALL accept an `--output` argument specifying the output file path, defaulting to `exports/team_dashboard.html`.
12. THE Team_Dashboard SHALL be a self-contained HTML file with all CSS inline, no external dependencies, viewable in any modern browser without a web server.
13. THE Team_Dashboard SHALL include a generation timestamp in the footer.
14. IF a member's progress file does not exist or is unreadable, THEN THE Dashboard_Script SHALL display that member as "No data available" in the dashboard rather than raising an error.

### Requirement 3: Feedback Merge

**User Story:** As a team lead, I want to combine all team members' individual feedback files into one consolidated report, so that I can submit a single comprehensive feedback document to the power author.

#### Acceptance Criteria

1. THE Merge_Script SHALL reside at `senzing-bootcamp/scripts/merge_feedback.py`.
2. THE Merge_Script SHALL be executable from the project root via `python senzing-bootcamp/scripts/merge_feedback.py` or `python scripts/merge_feedback.py` (when scripts are copied locally).
3. THE Merge_Script SHALL depend only on the Python standard library (no third-party packages).
4. THE Merge_Script SHALL be cross-platform, supporting Linux, macOS, and Windows.
5. WHEN the `mode` is `colocated`, THE Merge_Script SHALL scan for feedback files matching `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_{member_id}.md` for each Team_Member.
6. WHEN the `mode` is `distributed`, THE Merge_Script SHALL read each member's feedback from `{repo_path}/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.
7. THE Team_Feedback_Report SHALL be a markdown file written to `docs/feedback/TEAM_FEEDBACK_REPORT.md`.
8. THE Team_Feedback_Report SHALL include a header with the team name, generation date, and count of members whose feedback was included.
9. THE Team_Feedback_Report SHALL organize feedback entries grouped by Team_Member, with each member's section headed by their display name.
10. THE Team_Feedback_Report SHALL include a summary section listing the total number of feedback entries, a breakdown by priority (High, Medium, Low), and a breakdown by category (Documentation, Workflow, Tools, UX, Bug, Performance, Security).
11. WHEN a member has no feedback file or the file contains no improvement entries, THE Merge_Script SHALL note that member as "No feedback submitted" in the report rather than raising an error.
12. THE Merge_Script SHALL accept an `--output` argument specifying the output file path, overriding the default location.
13. WHEN the merge completes, THE Merge_Script SHALL print the output file path and the count of feedback entries merged.

### Requirement 4: Team-Level Progress Tracking

**User Story:** As a team member, I want my individual progress tracked separately from other team members while still contributing to team-level statistics, so that the team can see both individual and collective progress.

#### Acceptance Criteria

1. WHEN team mode is active and the `mode` is `colocated`, THE onboarding flow SHALL create a member-specific progress file at `config/progress_{member_id}.json` instead of `config/bootcamp_progress.json`.
2. THE member-specific progress file SHALL use the same JSON schema as the existing `bootcamp_progress.json` (containing `modules_completed`, `current_module`, `language`, and `data_sources` fields).
3. WHEN team mode is active, THE `status.py` script SHALL accept an optional `--member` argument specifying the member identifier to display that member's individual progress.
4. WHEN team mode is active and no `--member` argument is provided, THE `status.py` script SHALL display a team summary showing each member's current module and completion count, followed by overall team statistics.
5. THE Dashboard_Script SHALL compute team-level statistics: total modules completed across all members, average completion percentage, and the module with the lowest completion rate across the team.
6. WHEN the `mode` is `distributed`, THE Individual_Progress for each member SHALL remain at the standard `config/bootcamp_progress.json` path within each member's own repository.

### Requirement 5: Entity Resolution Comparison View

**User Story:** As a team member, I want to compare my entity resolution results with other team members' results, so that I can understand how different data sources or configurations affect entity resolution outcomes.

#### Acceptance Criteria

1. THE Team_Dashboard SHALL include an ER_Comparison section that displays a side-by-side comparison of entity resolution outcomes across team members.
2. THE ER_Comparison SHALL show, for each member who has completed Module 6 or later: total records loaded, total entities resolved, duplicate count, and cross-source match count (where available from Module 7+).
3. WHEN the `mode` is `colocated`, THE Dashboard_Script SHALL read entity resolution statistics from each member's progress file or from member-specific artifact directories.
4. WHEN the `mode` is `distributed`, THE Dashboard_Script SHALL read entity resolution statistics from `{repo_path}/config/bootcamp_progress.json` or artifact files in each member's repository.
5. THE ER_Comparison SHALL highlight the member with the highest entity resolution rate (entities resolved / records loaded) and the member with the most cross-source matches.
6. WHEN a member has not yet reached Module 6, THE ER_Comparison SHALL display "Not yet available" for that member rather than omitting the member.
7. THE ER_Comparison SHALL include a column showing each member's data sources so that readers can understand why results differ.

### Requirement 6: Onboarding Integration

**User Story:** As a team member starting the bootcamp, I want the onboarding flow to automatically detect team mode and configure my session accordingly, so that I do not have to manually set up team-specific settings.

#### Acceptance Criteria

1. WHEN the onboarding flow begins, THE Onboarding_Detector SHALL check for the existence of `config/team.yaml`.
2. WHEN `config/team.yaml` exists and is valid, THE onboarding flow SHALL present the list of Team_Members and ask the bootcamper to identify themselves by selecting their member identifier.
3. WHEN the bootcamper selects a member identifier, THE onboarding flow SHALL create or update the member-specific progress file (`config/progress_{member_id}.json` in Co-located_Mode, or `config/bootcamp_progress.json` in Distributed_Mode).
4. WHEN team mode is active, THE onboarding flow SHALL display the team name and the number of other team members alongside the standard welcome banner.
5. WHEN `config/team.yaml` does not exist, THE onboarding flow SHALL proceed with the standard single-user onboarding without any team-related prompts.
6. IF the bootcamper's selected member identifier does not match any entry in the Team_Config, THEN THE onboarding flow SHALL ask the bootcamper to choose from the available member identifiers or add themselves to the Team_Config.

### Requirement 7: Co-located Mode Support

**User Story:** As a team working in a shared repository, I want all team members' data to coexist in the same project directory without conflicts, so that we can collaborate without overwriting each other's progress.

#### Acceptance Criteria

1. WHEN the `mode` is `colocated`, THE team tooling SHALL store each member's progress at `config/progress_{member_id}.json`.
2. WHEN the `mode` is `colocated`, THE team tooling SHALL store each member's feedback at `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_{member_id}.md`.
3. WHEN the `mode` is `colocated`, THE team tooling SHALL store each member's bootcamp preferences at `config/preferences_{member_id}.yaml`.
4. WHEN the `mode` is `colocated`, THE team tooling SHALL store each member's bootcamp journal at `docs/bootcamp_journal_{member_id}.md`.
5. THE Co-located_Mode file naming convention SHALL use the member `id` from the Team_Config as the suffix, ensuring unique file paths for each member.

### Requirement 8: Distributed Mode Support

**User Story:** As a team where each member works in their own repository clone, I want the team tooling to collect data from each member's repository, so that we can generate team views without requiring a shared repository.

#### Acceptance Criteria

1. WHEN the `mode` is `distributed`, THE Dashboard_Script SHALL access each member's repository using the `repo_path` specified in the Team_Config.
2. WHEN the `mode` is `distributed`, THE Merge_Script SHALL access each member's feedback file using the `repo_path` specified in the Team_Config.
3. WHEN the `mode` is `distributed`, each member's repository SHALL use the standard single-user file paths (`config/bootcamp_progress.json`, `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`) without member-specific suffixes.
4. IF a member's `repo_path` does not exist or is not accessible, THEN THE Dashboard_Script and Merge_Script SHALL report a warning for that member and continue processing remaining members.
5. WHEN the `mode` is `distributed`, THE Team_Config file SHALL exist in a designated coordinator repository from which the team scripts are run.

### Requirement 9: Team Configuration Validation

**User Story:** As a team lead, I want the team configuration validated before any team operation runs, so that errors in the configuration are caught early with clear messages.

#### Acceptance Criteria

1. WHEN any team script (Dashboard_Script or Merge_Script) starts, THE script SHALL validate the Team_Config before proceeding.
2. THE validation SHALL verify that `team_name` is a non-empty string.
3. THE validation SHALL verify that `members` is a non-empty list with at least two entries.
4. THE validation SHALL verify that each member has a non-empty `id` and `name`.
5. THE validation SHALL verify that all member `id` values are unique.
6. WHEN the `mode` is `distributed`, THE validation SHALL verify that each member has a non-empty `repo_path`.
7. IF validation fails, THEN THE script SHALL print a descriptive error message identifying the specific validation failure and exit with a non-zero exit code.
8. THE validation SHALL verify that the `mode` field is either `colocated` or `distributed`.

### Requirement 10: Team Dashboard Styling and Usability

**User Story:** As a team lead reviewing the dashboard, I want the HTML dashboard to be well-organized and easy to read, so that I can quickly assess team status.

#### Acceptance Criteria

1. THE Team_Dashboard SHALL use a responsive layout that is readable on screens from 768px to 1920px width.
2. THE Team_Dashboard SHALL use color coding consistently: green for completed modules, yellow for in-progress modules, and gray for not-started modules.
3. THE Team_Dashboard SHALL include a navigation bar or table of contents linking to each dashboard section (team summary, member progress, module heatmap, ER comparison).
4. THE Team_Dashboard SHALL use semantic HTML elements (`<header>`, `<main>`, `<section>`, `<table>`, `<nav>`) for structure.
5. THE Team_Dashboard SHALL display the team name prominently in the page header.
