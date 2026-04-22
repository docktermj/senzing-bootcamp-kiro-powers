# Requirements Document

## Introduction

User-facing guide documents that help bootcamp participants get started, track progress, collaborate as a team, install hooks, and continue learning after the bootcamp. All guides live in `senzing-bootcamp/docs/guides/`.

## Glossary

- **Guide_System**: The collection of user-facing markdown guide files in `senzing-bootcamp/docs/guides/`
- **Bootcamp_User**: A developer working through the Senzing Bootcamp modules
- **Hook**: A Kiro automation file (`.kiro.hook`) that triggers agent actions on IDE events

## Requirements

### Requirement 1: Getting Started and Onboarding Guides

**User Story:** As a bootcamp user, I want quick-start instructions, an onboarding checklist, and a progress tracker, so that I can begin the bootcamp confidently and track my completion.

#### Acceptance Criteria

1. THE Guide_System SHALL provide a Quick Start guide (`QUICK_START.md`) that documents all four learning paths (Quick Demo, Fast Track, Complete Beginner, Full Production) with module sequences, skip-ahead options, and quick commands.
2. THE Guide_System SHALL provide an Onboarding Checklist (`ONBOARDING_CHECKLIST.md`) that lists environment prerequisites (language runtime, git, disk space, RAM) and describes what the agent automates during setup.
3. THE Guide_System SHALL provide a Progress Tracker (`PROGRESS_TRACKER.md`) that lists all 13 modules (0–12) with status indicators and supports auto-generation via `scripts/status.py --sync`.
4. THE Guide_System SHALL provide a Hooks Installation Guide (`HOOKS_INSTALLATION_GUIDE.md`) that documents automatic installation, four manual installation methods, the 11 pre-configured hooks, customization options, and uninstall instructions.

### Requirement 2: Post-Bootcamp and Team Collaboration Guides

**User Story:** As a bootcamp user, I want guidance on production maintenance and team workflows, so that I can operate my deployment and collaborate effectively after completing the bootcamp.

#### Acceptance Criteria

1. THE Guide_System SHALL provide an After Bootcamp guide (`AFTER_BOOTCAMP.md`) that covers production maintenance cadence (daily/weekly/monthly/quarterly), scaling strategies, adding new data sources, keeping Senzing updated, advanced topics, and community resources.
2. THE Guide_System SHALL provide a Collaboration Guide (`COLLABORATION_GUIDE.md`) that documents team roles, git workflow conventions (branch naming, commit format, .gitignore rules), code review checklists, data sharing policies, and bootcamp-specific collaboration patterns for data mapping and query work.
