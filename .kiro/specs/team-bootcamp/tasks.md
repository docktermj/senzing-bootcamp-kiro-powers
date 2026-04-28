# Tasks

## Task 1: Team Config Validator Module

- [x] 1.1 Create `senzing-bootcamp/scripts/team_config_validator.py` with `TeamMember` and `TeamConfig` dataclasses
- [x] 1.2 Implement `parse_team_yaml(content: str) -> dict` — a minimal YAML parser for the restricted `team.yaml` schema (string scalars, lists of dicts, no anchors/aliases), stdlib only
- [x] 1.3 Implement `validate_team_config(raw: dict) -> list[str]` — validates required fields (`team_name`, `members`, `mode`), member field presence (`id`, `name`), unique member IDs, valid mode values, and `repo_path` requirement in distributed mode
- [x] 1.4 Implement `load_and_validate(path: str) -> TeamConfig` — reads file, parses, validates, raises `TeamConfigError` on failure
- [x] 1.5 Implement `PathResolver` class with `progress_path()`, `feedback_path()`, `preferences_path()`, `journal_path()` methods that return correct paths for both co-located and distributed modes
- [x] 1.6 Write property-based tests for config validation (Property 1) and path resolution (Property 2) in `senzing-bootcamp/scripts/test_team_config_validator.py` using Hypothesis

## Task 2: Team Dashboard Script

- [x] 2.1 Create `senzing-bootcamp/scripts/team_dashboard.py` with CLI argument parsing (`--output` defaulting to `exports/team_dashboard.html`)
- [x] 2.2 Implement `collect_member_progress()` — reads each member's progress file via `PathResolver`, returns "No data available" for missing/unreadable files
- [x] 2.3 Implement `compute_team_stats()` — computes average completion %, total modules completed, lowest-completion module, fully-completed member count
- [x] 2.4 Implement `collect_er_stats()` — reads `er_stats` from progress files for members who completed Module 6+, returns "Not yet available" for others
- [x] 2.5 Implement `render_dashboard_html()` — generates self-contained HTML with inline CSS, semantic elements (`<header>`, `<main>`, `<section>`, `<table>`, `<nav>`), responsive layout, team summary, per-member table, module heatmap (green/yellow/gray), ER comparison section with highlights, navigation bar, and generation timestamp in footer
- [x] 2.6 Write property-based tests for dashboard content (Property 3), team stats (Property 5), and ER comparison highlights (Property 6) in `senzing-bootcamp/scripts/test_team_dashboard.py`

## Task 3: Merge Feedback Script

- [x] 3.1 Create `senzing-bootcamp/scripts/merge_feedback.py` with CLI argument parsing (`--output` defaulting to `docs/feedback/TEAM_FEEDBACK_REPORT.md`)
- [x] 3.2 Implement `parse_feedback_file(content: str) -> list[FeedbackEntry]` — parses the feedback markdown template to extract improvement entries with title, date, module, priority, category, and body
- [x] 3.3 Implement `compute_feedback_stats()` and `merge_feedback()` — computes priority/category breakdowns and generates the consolidated markdown report grouped by member
- [x] 3.4 Implement `main()` — loads team config, reads feedback files via `PathResolver`, handles missing files as "No feedback submitted", prints output path and entry count on completion
- [x] 3.5 Write property-based tests for feedback statistics (Property 4) in `senzing-bootcamp/scripts/test_merge_feedback.py`

## Task 4: Extend status.py for Team Mode

- [x] 4.1 Add team mode detection to `status.py` — check for `config/team.yaml`, import `team_config_validator`
- [x] 4.2 Add `--member <id>` CLI argument — when provided in team mode, display that member's individual progress using their member-specific progress file
- [x] 4.3 Add team summary display — when team mode is active and no `--member` argument, show each member's current module and completion count followed by overall team statistics
- [x] 4.4 Write example-based unit tests for the new team mode behavior in `senzing-bootcamp/scripts/test_status_team.py`

## Task 5: Onboarding Integration

- [x] 5.1 Update `senzing-bootcamp/steering/onboarding-flow.md` to include team detection logic — check for `config/team.yaml`, present member list, ask user to identify themselves
- [x] 5.2 Add team welcome banner instructions to the onboarding steering file — display team name and member count when team mode is active
- [x] 5.3 Document the onboarding team flow in `senzing-bootcamp/docs/guides/COLLABORATION_GUIDE.md` — add a "Team Mode Setup" section explaining `config/team.yaml` creation and the onboarding experience

## Task 6: Documentation and Integration

- [x] 6.1 Create a sample `config/team.yaml.example` file showing both co-located and distributed mode configurations
- [x] 6.2 Update `senzing-bootcamp/POWER.md` — add team dashboard and merge feedback commands to the "Useful Commands" section, mention team mode in the overview
- [x] 6.3 Update `senzing-bootcamp/docs/guides/COLLABORATION_GUIDE.md` — add sections for team config setup, dashboard generation, feedback merging, and co-located vs. distributed mode guidance
