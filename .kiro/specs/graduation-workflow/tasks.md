# Tasks

## Task 1: Create the graduation steering file

- [x] 1.1 Create `senzing-bootcamp/steering/graduation.md` with YAML frontmatter (`inclusion: manual`) and an introductory section explaining the graduation workflow purpose and the five sequential steps
- [ ] 1.2 Write the Pre-checks section: instructions for the agent to read `config/bootcamp_preferences.yaml` (language, track, platform, data sources) and `config/bootcamp_progress.json` (modules completed), with fallback instructions to prompt the bootcamper for language and database type if files are missing
- [ ] 1.3 Write Step 1 (Production Project Structure): instructions to check if `production/` exists (ask overwrite/merge/abort), copy production-relevant files from `src/{transform,load,query,utils}`, `data/transformed/`, `database/` (structure with `.gitkeep`), and the dependency file — while excluding bootcamp scaffolding (`bootcamp_progress.json`, `bootcamp_preferences.yaml`, `bootcamp_journal.md`, `data/samples/`, `data/raw/`, `src/quickstart_demo/`, `logs/`, `backups/`, `monitoring/`, `docs/feedback/`) — and present a summary of copied/excluded files before proceeding
- [ ] 1.4 Write Step 2 (Production Configuration Files): instructions to generate `.env.production` (placeholder values only), `.env.example` (safe example values with comments), `docker-compose.yml` (parameterized by database type from preferences), ask the bootcamper which CI/CD platform they use and generate the appropriate pipeline file (`.github/workflows/ci.yml`, `azure-pipelines.yml`, or `.gitlab-ci.yml` with lint/test/build/deploy stages), and generate a language-appropriate `.gitignore`
- [ ] 1.5 Write Step 3 (Production README): instructions to generate `production/README.md` with sections for project overview, prerequisites, installation, configuration, usage (loading data, running queries), project structure, and contributing guidelines — parameterized by language and database type, referencing data sources from preferences, and containing no bootcamp-specific language — then present for review before proceeding
- [ ] 1.6 Write Step 4 (Migration Checklist): instructions to generate `production/MIGRATION_CHECKLIST.md` with six sections (Database, Security, Licensing, Performance, Data, Deployment) using `- [ ]` checkboxes, with conditional logic to reference existing Module 10–12 artifacts when completed (Path D) or flag uncovered areas when not completed
- [ ] 1.7 Write Step 5 (Git Repository Initialization): instructions to ask the bootcamper if they want a new git repo, check git availability, run `git init` + initial commit with message "Initial production project from Senzing Bootcamp graduation" if accepted, and skip gracefully if declined or git unavailable
- [ ] 1.8 Write the Graduation Report section: instructions to always generate `production/GRADUATION_REPORT.md` with Summary (track, modules, language, database type), Files Generated (list with descriptions), Files Excluded (list with reasons), Next Steps (prioritized recommendations referencing the migration checklist), and a generation timestamp — noting any step failures encountered

## Task 2: Integrate graduation offer into module-completion.md

- [ ] 2.1 Update `senzing-bootcamp/steering/module-completion.md` Path Completion Celebration section to add the graduation offer after the export-results offer and before existing post-completion options: "🎓 Would you like to run the graduation workflow? It will help you turn your bootcamp project into a production-ready codebase — clean structure, production configs, CI/CD pipeline, and a migration checklist."
- [ ] 2.2 Add `skip_graduation` check logic to `module-completion.md`: instruct the agent to read `skip_graduation` from `config/bootcamp_preferences.yaml` and skip the graduation offer if set to `true`
- [ ] 2.3 Add decline-and-remember logic to `module-completion.md`: when the bootcamper declines the graduation offer, instruct the agent to ask "Would you like me to remember this choice so I don't ask again?" and set `skip_graduation: true` in preferences if confirmed

## Task 3: Update steering-index.yaml and POWER.md

- [ ] 3.1 Add `graduate: graduation.md` and `graduation: graduation.md` keyword entries to `senzing-bootcamp/steering/steering-index.yaml`
- [ ] 3.2 Add `graduation.md` to the "Module Completion" section of Available Steering Files in `senzing-bootcamp/POWER.md` with description: "Post-track graduation workflow — transitions bootcamp project to production structure"
- [ ] 3.3 Add a note in the `senzing-bootcamp/POWER.md` Quick Start section mentioning that after completing any track, the graduation workflow is offered to help transition to production

## Task 4: Document export-results integration

- [ ] 4.1 Add a comment block at the end of `senzing-bootcamp/steering/graduation.md` documenting the export-results integration contract: when `production/GRADUATION_REPORT.md` exists, the export script should include it as a "Graduation" section in the HTML report; when `--format zip` is used and `production/` exists, include contents under `artifacts/production/`
- [ ] 4.2 Update `senzing-bootcamp/steering/module-completion.md` to ensure the export-results offer is presented before the graduation offer in the Path Completion Celebration flow
