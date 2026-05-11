# Bugfix Requirements Document

## Introduction

During Module 0 (Onboarding), the agent creates the project directory structure as its first setup action. On Windows, the agent uses `mkdir dir1 dir2 dir3...` syntax which fails because PowerShell's `mkdir` (an alias for `New-Item`) does not accept multiple positional path arguments. This produces a confusing error ("A positional parameter cannot be found that accepts argument 'data\transformed'") as the bootcamper's very first interaction with the bootcamp, creating a poor first impression and undermining confidence in the tool.

The `project-structure.md` steering file already documents the correct cross-platform patterns (a Python `os.makedirs` loop and a PowerShell `ForEach-Object` pipeline), but the agent does not reliably use them. The root cause is that the steering file presents three alternative commands without explicit platform-selection logic, and the agent defaults to the familiar Linux `mkdir` syntax even on Windows.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent creates the project directory structure on Windows during onboarding THEN the system issues a single `mkdir` command with multiple space-separated path arguments, which fails with "A positional parameter cannot be found that accepts argument" error.

1.2 WHEN the initial `mkdir` command fails on Windows THEN the agent may retry with an incorrectly quoted PowerShell pipeline that also fails due to quoting or escaping issues, producing additional error output.

1.3 WHEN directory creation fails on Windows THEN the bootcamper sees a wall of error text on their first interaction with the bootcamp before any directories are successfully created.

### Expected Behavior (Correct)

2.1 WHEN the agent creates the project directory structure on Windows during onboarding THEN the system SHALL use either the cross-platform Python `os.makedirs` loop or the PowerShell `ForEach-Object` pipeline as documented in `project-structure.md`, creating each directory individually without error.

2.2 WHEN the agent creates directories on Windows THEN the system SHALL succeed on the first attempt without producing error output or requiring retries.

2.3 WHEN directory creation completes on Windows THEN the system SHALL have created all required directories (`data/raw`, `data/transformed`, `data/samples`, `data/backups`, `data/temp`, `database`, `licenses`, `src/transform`, `src/load`, `src/query`, `src/utils`, `tests`, `backups`, `docs/feedback`, `config`, `logs`, `monitoring`, `scripts`) and proceed to the next onboarding step cleanly.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent creates the project directory structure on Linux or macOS during onboarding THEN the system SHALL CONTINUE TO use the `mkdir -p` command with brace expansion to create all directories in a single command.

3.2 WHEN the project directories already exist at onboarding time THEN the system SHALL CONTINUE TO skip directory creation and proceed to the next setup action without error.

3.3 WHEN directory creation succeeds on any platform THEN the system SHALL CONTINUE TO produce the same final directory layout as documented in `project-structure.md`.

3.4 WHEN the agent loads `project-structure.md` during onboarding THEN the system SHALL CONTINUE TO follow the documented structure and create all required subdirectories regardless of platform.
