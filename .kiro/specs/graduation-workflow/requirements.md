# Requirements Document

## Introduction

The senzing-bootcamp power currently ends each track with a celebration message and a retrospective (via `module-completion.md` and `lessons-learned.md`), then points the user to the passive `AFTER_BOOTCAMP.md` guide. There is no active workflow that helps the bootcamper transition their bootcamp project into a production-ready codebase. Bootcamp projects contain scaffolding artifacts (sample data, demo scripts, bootcamp journal, progress tracking files) that are useful during learning but inappropriate for production. This feature adds a graduation workflow — a new `steering/graduation.md` steering file — that triggers after track completion and walks the bootcamper through generating a clean production project structure, production configuration files, a production README, a migration checklist, and optionally initializing a new git repository. The workflow integrates with the existing export-results feature to include a graduation report alongside the bootcamp export.

## Glossary

- **Graduation_Workflow**: The multi-step agent workflow defined in `senzing-bootcamp/steering/graduation.md` that guides a bootcamper through transitioning bootcamp artifacts into a production project.
- **Production_Directory**: A new directory (default: `production/`) created within the bootcamp project that contains only production-relevant code, configuration, and documentation — with all bootcamp scaffolding removed.
- **Bootcamp_Scaffolding**: Files and directories that exist solely for the bootcamp learning experience and are not needed in production, including `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, `data/samples/`, `data/raw/`, `src/quickstart_demo/`, `logs/`, `monitoring/` (if empty), and `backups/`.
- **Production_Config**: Environment-specific configuration files generated during graduation, including `.env.production`, `docker-compose.yml`, and a CI/CD pipeline definition file (e.g., `.github/workflows/ci.yml`, `azure-pipelines.yml`, or `.gitlab-ci.yml`).
- **Migration_Checklist**: A markdown file (`production/MIGRATION_CHECKLIST.md`) that documents every change needed to move from bootcamp to production, with checkboxes for each item.
- **Graduation_Report**: A summary document (`production/GRADUATION_REPORT.md`) generated at the end of the graduation workflow that records what was produced, what was excluded, and recommended next steps.
- **Production_README**: A generated `production/README.md` file that documents the production project — its purpose, setup instructions, usage, and architecture — without bootcamp-specific language.
- **Progress_Data**: The JSON structure stored in `config/bootcamp_progress.json` that tracks module completion state, current module, language choice, and data sources.
- **Bootcamp_Preferences**: The YAML configuration at `config/bootcamp_preferences.yaml` that stores the bootcamper's chosen language, track, platform, and other preferences.
- **Agent**: The AI agent running the senzing-bootcamp power that executes steering file instructions and interacts with the bootcamper.

## Requirements

### Requirement 1: Graduation Steering File

**User Story:** As a power maintainer, I want the graduation workflow defined in a steering file, so that the agent can load and execute it consistently after track completion.

#### Acceptance Criteria

1. THE Graduation_Workflow SHALL be defined in a steering file at `senzing-bootcamp/steering/graduation.md`.
2. THE steering file SHALL include YAML frontmatter with `inclusion: manual` so that it is loaded on-demand rather than automatically.
3. THE steering file SHALL define five sequential steps: generate production project structure, create production configuration files, generate a Production_README, create a Migration_Checklist, and offer git repository initialization.
4. THE steering file SHALL instruct the Agent to present each step to the bootcamper and wait for confirmation before proceeding.
5. THE steering file SHALL instruct the Agent to read the Bootcamp_Preferences to determine the bootcamper's chosen language, track, platform, and data sources before generating any artifacts.

### Requirement 2: Graduation Trigger

**User Story:** As a bootcamper who just completed a track, I want the graduation workflow offered to me automatically, so that I have a guided path to production readiness.

#### Acceptance Criteria

1. WHEN a bootcamper completes the final module of their chosen track (Path A: Module 3, Path B: Module 8, Path C: Module 8, Path D: Module 12), THE Agent SHALL offer the graduation workflow after the path completion celebration and lessons-learned retrospective defined in `module-completion.md`.
2. THE Agent SHALL present the graduation offer as: "🎓 Would you like to run the graduation workflow? It will help you turn your bootcamp project into a production-ready codebase — clean structure, production configs, CI/CD pipeline, and a migration checklist."
3. WHEN the bootcamper accepts the graduation offer, THE Agent SHALL load `steering/graduation.md` and begin the workflow.
4. WHEN the bootcamper declines the graduation offer, THE Agent SHALL acknowledge the decision and continue with the existing post-completion options without loading the steering file.

### Requirement 3: Skip Graduation Flag

**User Story:** As a bootcamper who does not want the graduation workflow, I want a way to suppress the graduation offer, so that I am not prompted after every track completion.

#### Acceptance Criteria

1. THE Bootcamp_Preferences SHALL support a `skip_graduation` boolean field (default: `false`).
2. WHEN `skip_graduation` is set to `true` in the Bootcamp_Preferences, THE Agent SHALL not offer the graduation workflow after track completion.
3. WHEN the bootcamper declines the graduation offer, THE Agent SHALL ask: "Would you like me to remember this choice so I don't ask again?" and set `skip_graduation` to `true` if the bootcamper confirms.
4. THE bootcamper SHALL be able to manually trigger the graduation workflow at any time by saying "run graduation" or "graduate" regardless of the `skip_graduation` setting.

### Requirement 4: Production Project Structure Generation (Step 1)

**User Story:** As a bootcamper, I want the graduation workflow to generate a clean production project structure, so that I have a codebase free of bootcamp scaffolding.

#### Acceptance Criteria

1. WHEN Step 1 of the Graduation_Workflow executes, THE Agent SHALL create a `production/` directory in the project root.
2. THE Agent SHALL copy production-relevant source code from `src/transform/`, `src/load/`, and `src/query/` into `production/src/` while preserving the subdirectory structure.
3. THE Agent SHALL copy production-relevant utility code from `src/utils/` into `production/src/utils/`.
4. THE Agent SHALL copy transformed data files from `data/transformed/` into `production/data/`.
5. THE Agent SHALL exclude Bootcamp_Scaffolding from the Production_Directory: `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, `data/samples/`, `data/raw/`, `src/quickstart_demo/`, `logs/`, `backups/`, `monitoring/` (if it contains only bootcamp-generated content), and `docs/feedback/`.
6. THE Agent SHALL copy the `database/` directory structure (without the actual database file) into `production/database/` and include a `.gitkeep` file.
7. THE Agent SHALL copy the language-appropriate dependency file (e.g., `requirements.txt`, `pom.xml`, `Cargo.toml`, `package.json`) from the project root into `production/`.
8. THE Agent SHALL present a summary of copied and excluded files to the bootcamper before proceeding to Step 2.
9. IF the `production/` directory already exists, THEN THE Agent SHALL ask the bootcamper whether to overwrite, merge, or abort before proceeding.

### Requirement 5: Production Configuration File Generation (Step 2)

**User Story:** As a bootcamper, I want production configuration files generated for me, so that I have a starting point for deploying my entity resolution pipeline.

#### Acceptance Criteria

1. WHEN Step 2 of the Graduation_Workflow executes, THE Agent SHALL generate a `.env.production` file in `production/` containing environment variable placeholders for database connection strings, Senzing license paths, log levels, and any API keys — with no actual secrets, only descriptive placeholder values.
2. THE Agent SHALL generate a `docker-compose.yml` file in `production/` that defines services for the Senzing application and its database, using the database type (SQLite or PostgreSQL) from the bootcamper's configuration.
3. THE Agent SHALL generate a CI/CD pipeline definition file in `production/` appropriate to the bootcamper's platform preference: `.github/workflows/ci.yml` for GitHub Actions (default), `azure-pipelines.yml` for Azure DevOps, or `.gitlab-ci.yml` for GitLab CI.
4. WHEN generating the CI/CD pipeline, THE Agent SHALL ask the bootcamper which CI/CD platform they use before generating the file.
5. THE CI/CD pipeline file SHALL include stages for linting, testing, building a container image, and a placeholder deployment stage.
6. THE Agent SHALL generate a `.env.example` file in `production/` that mirrors `.env.production` with safe example values and comments explaining each variable.
7. THE Agent SHALL generate a `.gitignore` file in `production/` appropriate for the bootcamper's chosen language, excluding `.env.production`, database files, and build artifacts.

### Requirement 6: Production README Generation (Step 3)

**User Story:** As a bootcamper, I want a production-ready README generated for my project, so that other developers can understand and use the codebase without bootcamp context.

#### Acceptance Criteria

1. WHEN Step 3 of the Graduation_Workflow executes, THE Agent SHALL generate a `production/README.md` file.
2. THE Production_README SHALL include sections for: project overview, prerequisites, installation instructions, configuration, usage (loading data, running queries), project structure, and contributing guidelines.
3. THE Production_README SHALL reference the bootcamper's chosen language and database type in the prerequisites and installation sections.
4. THE Production_README SHALL describe the data sources used in the project, derived from the Bootcamp_Preferences and Progress_Data.
5. THE Production_README SHALL not contain bootcamp-specific language such as "bootcamp", "module", "track", or "bootcamper".
6. THE Agent SHALL present the generated Production_README to the bootcamper for review before proceeding to Step 4.

### Requirement 7: Migration Checklist Generation (Step 4)

**User Story:** As a bootcamper, I want a checklist of everything that needs to change for production, so that I do not miss critical steps when deploying.

#### Acceptance Criteria

1. WHEN Step 4 of the Graduation_Workflow executes, THE Agent SHALL generate a `production/MIGRATION_CHECKLIST.md` file.
2. THE Migration_Checklist SHALL include a "Database" section with items for: replacing the evaluation database with a production database, configuring connection pooling, and setting up automated backups.
3. THE Migration_Checklist SHALL include a "Security" section with items for: replacing placeholder secrets in `.env.production`, configuring TLS, reviewing access controls, and removing any hardcoded credentials from source code.
4. THE Migration_Checklist SHALL include a "Licensing" section with items for: obtaining a production Senzing license and configuring the license path.
5. THE Migration_Checklist SHALL include a "Performance" section with items for: tuning database parameters for production data volumes, configuring multi-threaded loading, and setting up monitoring.
6. THE Migration_Checklist SHALL include a "Data" section with items for: validating production data sources, setting up data ingestion pipelines, and configuring error handling for bad records.
7. THE Migration_Checklist SHALL include a "Deployment" section with items for: configuring the CI/CD pipeline with real credentials, setting up staging and production environments, and defining a rollback procedure.
8. WHEN the bootcamper completed Modules 10–12 (Path D), THE Migration_Checklist SHALL reference the security hardening, monitoring, and deployment artifacts already produced during those modules.
9. WHEN the bootcamper did not complete Modules 10–12, THE Migration_Checklist SHALL include additional items flagging that security hardening, monitoring, and deployment packaging were not covered during the bootcamp.
10. THE Migration_Checklist SHALL use markdown checkboxes (`- [ ]`) for each item so the bootcamper can track completion.

### Requirement 8: Git Repository Initialization (Step 5)

**User Story:** As a bootcamper, I want the option to initialize a new git repository for my production project, so that I can start with a clean version history.

#### Acceptance Criteria

1. WHEN Step 5 of the Graduation_Workflow executes, THE Agent SHALL ask the bootcamper: "Would you like me to initialize a new git repository in the production/ directory?"
2. WHEN the bootcamper accepts, THE Agent SHALL run `git init` in the `production/` directory.
3. WHEN the bootcamper accepts, THE Agent SHALL create an initial commit with the message "Initial production project from Senzing Bootcamp graduation".
4. WHEN the bootcamper declines, THE Agent SHALL skip git initialization and proceed to the graduation report.
5. IF git is not available on the system, THEN THE Agent SHALL inform the bootcamper that git was not found and skip the initialization step.

### Requirement 9: Graduation Report Generation

**User Story:** As a bootcamper, I want a summary report of what the graduation workflow produced, so that I have a record of the transition from bootcamp to production.

#### Acceptance Criteria

1. WHEN all graduation steps are complete, THE Agent SHALL generate a `production/GRADUATION_REPORT.md` file.
2. THE Graduation_Report SHALL include a "Summary" section listing the track completed, modules finished, chosen language, and database type.
3. THE Graduation_Report SHALL include a "Files Generated" section listing every file created in the `production/` directory with a one-line description of each.
4. THE Graduation_Report SHALL include a "Files Excluded" section listing Bootcamp_Scaffolding files that were intentionally excluded and the reason for each exclusion.
5. THE Graduation_Report SHALL include a "Next Steps" section with prioritized recommendations for moving to production, referencing specific items in the Migration_Checklist.
6. THE Graduation_Report SHALL include a generation timestamp.

### Requirement 10: Export-Results Integration

**User Story:** As a bootcamper, I want the graduation report included in my bootcamp export, so that stakeholders can see both the learning outcomes and the production transition plan.

#### Acceptance Criteria

1. WHEN the export-results feature generates an HTML_Report or ZIP_Archive after the graduation workflow has been completed, THE Export_Script SHALL include the Graduation_Report in the report.
2. WHEN the `--format zip` option is used and the `production/` directory exists, THE ZIP_Archive SHALL include the contents of the `production/` directory under an `artifacts/production/` path.
3. WHEN the graduation workflow has not been completed, THE Export_Script SHALL not include graduation-related content in the report.
4. THE HTML_Report SHALL include a "Graduation" section after the module completion sections, containing the Graduation_Report content rendered as formatted HTML.

### Requirement 11: Module-Completion Integration

**User Story:** As a power maintainer, I want the graduation workflow integrated into the existing module-completion flow, so that the transition is seamless for bootcampers.

#### Acceptance Criteria

1. THE `module-completion.md` steering file SHALL be updated to include the graduation offer in the Path Completion Celebration section, after the lessons-learned retrospective and before the existing post-completion options.
2. THE graduation offer SHALL appear only during path completion (when the bootcamper finishes their track's final module), not after every individual module completion.
3. THE graduation offer SHALL be presented after the export-results offer (if the export-results feature is available), so that the bootcamper can choose to export first and graduate second.
4. WHEN the bootcamper has `skip_graduation` set to `true` in Bootcamp_Preferences, THE Agent SHALL skip the graduation offer entirely during path completion.

### Requirement 12: Error Handling

**User Story:** As a bootcamper, I want the graduation workflow to handle errors gracefully, so that a failure in one step does not prevent me from completing the remaining steps.

#### Acceptance Criteria

1. IF a file copy operation fails during Step 1, THEN THE Agent SHALL log the failure, skip the affected file, and continue copying remaining files.
2. IF a configuration file generation fails during Step 2, THEN THE Agent SHALL inform the bootcamper of the failure and offer to retry or skip the affected file.
3. IF the `production/` directory cannot be created (e.g., permissions error), THEN THE Agent SHALL inform the bootcamper and suggest an alternative directory path.
4. IF the Progress_Data or Bootcamp_Preferences files do not exist, THEN THE Agent SHALL inform the bootcamper that progress data is missing and generate artifacts using sensible defaults (prompting the bootcamper for language and database type).
5. IF git initialization fails during Step 5, THEN THE Agent SHALL inform the bootcamper of the error and continue to the graduation report generation.
6. THE Agent SHALL generate the Graduation_Report regardless of whether individual steps encountered errors, noting any failures in the report.
