---
inclusion: manual
---

# Graduation Workflow

This steering file guides the agent through transitioning a completed bootcamp project into a production-ready codebase. Load it when the bootcamper accepts the graduation offer at track completion, or when they say "run graduation" or "graduate."

The workflow has five sequential steps:

1. **Production Project Structure** — Copy production-relevant code into a clean `production/` directory, excluding bootcamp scaffolding
2. **Production Configuration Files** — Generate `.env.production`, `.env.example`, `docker-compose.yml`, a CI/CD pipeline, and `.gitignore`
3. **Production README** — Generate a production-ready `README.md` with no bootcamp language
4. **Migration Checklist** — Generate `MIGRATION_CHECKLIST.md` with conditional items based on completed modules
5. **Git Repository Initialization** — Optionally initialize a new git repo in `production/`

A graduation report (`GRADUATION_REPORT.md`) is always generated at the end, even if individual steps encountered errors.

Each step requires bootcamper confirmation before proceeding. Do not skip ahead.

## Pre-checks

Before starting any steps, gather the bootcamper's context:

1. **Read preferences:** Load `config/bootcamp_preferences.yaml` and extract: `language`, `track`, `platform`, `data_sources`, `database_type`.

2. **Read progress:** Load `config/bootcamp_progress.json` and extract: `modules_completed`, `current_module`.

3. **Fallback if files are missing:** Inform the bootcamper, prompt for **language** and **database type**, use sensible defaults for everything else (track: unknown, platform: GitHub Actions, data_sources: []).

Store these values for use throughout the workflow. Proceed to Step 1.

## Step 1: Production Project Structure

If `production/` already exists, ask the bootcamper: Overwrite, Merge, or Abort. WAIT for response. If abort, stop and generate the graduation report noting the abort.

Create `production/` and copy production-relevant files:

| Source | Destination | Notes |
|--------|-------------|-------|
| `src/transform/**` | `production/src/transform/` | All transform code |
| `src/load/**` | `production/src/load/` | All loading code |
| `src/query/**` | `production/src/query/` | All query code |
| `src/utils/**` | `production/src/utils/` | Utility modules |
| `data/transformed/**` | `production/data/` | Transformed data files |
| `database/` (structure only) | `production/database/.gitkeep` | Empty placeholder |
| `requirements.txt` / `pom.xml` / `Cargo.toml` / `package.json` / `*.csproj` | `production/` | Language dependency file |

If a source directory does not exist, skip silently. If a file copy fails, log and continue.

**Exclude** (do NOT copy): `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, `data/samples/`, `data/raw/`, `src/quickstart_demo/`, `logs/`, `backups/`, `monitoring/`, `docs/feedback/`.

Present a summary of files copied, excluded, and directories created. Ask: "Does this look right? Ready to proceed to Step 2?" WAIT for confirmation.

## Step 2: Production Configuration Files

Generate the following files in `production/` using the language and database type from pre-checks:

- **`.env.production`** — Placeholder values only (no real secrets). Include: `SENZING_ENGINE_CONFIGURATION_JSON`, `SENZING_LICENSE_PATH`, `DATABASE_URL`, `LOG_LEVEL`, `API_KEY`.
- **`.env.example`** — Mirror `.env.production` with safe example values and comments.
- **`docker-compose.yml`** — Parameterized by database type: SQLite (single service + volume mount) or PostgreSQL (app + db service with health check).
- **CI/CD pipeline** — Ask bootcamper which platform (GitHub Actions default, Azure DevOps, GitLab CI). WAIT for response. Pipeline must include: Lint, Test, Build, Deploy (placeholder with manual gate).
- **`.gitignore`** — Language-appropriate. Always include: `.env.production`, `*.db`, `*.sqlite`, `__pycache__/`, `node_modules/`, `target/`, `bin/`, `obj/`, `build/`, `dist/`, `.idea/`, `.vscode/`, `*.log`.

Ask: "Configuration files generated. Ready to proceed to Step 3 (Production README)?" WAIT for confirmation.

## Step 3: Production README

Generate `production/README.md` parameterized by language, database type, and data sources. **Do not use bootcamp-specific language** — no "bootcamp", "module", "track", or "bootcamper."

Required sections: Project Overview, Prerequisites, Installation, Configuration, Usage, Project Structure, Contributing.

Show the generated README to the bootcamper for review. WAIT for confirmation or revision requests. Apply any requested changes before proceeding.

## Step 4: Migration Checklist

Generate `production/MIGRATION_CHECKLIST.md` with six sections (Database, Security, Licensing, Performance, Data, Deployment) using `- [ ]` checkboxes.

**Base items per section:**

- **Database:** Replace eval DB, configure connection pooling, set up backups, test failover, update DATABASE_URL
- **Security:** Replace placeholder secrets, configure TLS/SSL, review access controls, audit for hardcoded credentials, set up secret rotation
- **Licensing:** Obtain production license, configure SENZING_LICENSE_PATH, verify capacity
- **Performance:** Tune DB parameters, configure multi-threaded loading, set up monitoring, run load tests
- **Data:** Validate production sources, configure error handling, set up quality monitoring, document schemas
- **Deployment:** Configure CI/CD, set up staging, set up production, define rollback, configure health checks

**Conditional logic** (check `modules_completed`):

- If Modules 9–11 all completed: Add references to existing security/performance/deployment artifacts. Add: "Review packaging and deployment from Module 11 (check deployment artifacts)". Note at top: "✅ You completed the advanced topics track."
- If NOT all completed: Add ⚠️ items noting these topics were not covered. Add: "⚠️ Packaging and deployment was not covered during the bootcamp — complete these items before deploying". Note at top: "⚠️ Some production topics need extra attention."

Ask: "Migration checklist generated. Ready to proceed to Step 5 (Git initialization)?" WAIT for confirmation.

## Step 5: Git Repository Initialization (Optional)

Ask: "Would you like me to initialize a new git repository in the `production/` directory?" WAIT for response.

**If accepted:** Check `git --version`. If unavailable, inform and skip. If available, run `git init`, `git add .`, and `git commit -m "Initial production project from Senzing Bootcamp graduation"`. If any command fails, inform and continue.

**If declined:** Skip to the graduation report.

## Graduation Report

**Always generate `production/GRADUATION_REPORT.md`**, regardless of whether individual steps encountered errors.

Include: timestamp, track completed, modules finished, language, database type, files generated table, files excluded table, and next steps (fill in secrets, obtain license, work through checklist, configure CI/CD, test with production data).

If any step encountered errors, add a "⚠️ Issues Encountered" section listing what failed and what was skipped.

Present completion:

> 🎓 **Graduation complete!** Your production project is ready in `production/`.
>
> Check `production/GRADUATION_REPORT.md` for a full summary, and work through `production/MIGRATION_CHECKLIST.md` to prepare for deployment.

### Feedback Submission Reminder

Before showing the fallback feedback prompt, check for saved feedback:

1. Check conversation history for the `📋` marker. If it already appears (meaning a feedback reminder was shown during track completion earlier in this session), skip this reminder entirely and go straight to the fallback line below.
2. If no prior reminder was shown, check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists.
3. If it exists, read the file and check for at least one `## Improvement:` heading below the `## Your Feedback` section (headings outside fenced code blocks count as real entries; the template block inside a fenced code block does not).
4. If feedback entries exist, display: "📋 You have feedback saved in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. Would you like to share it with the power author?"
5. If the bootcamper accepts, present the sharing options:

   **How would you like to share your feedback?**

   1. **Email** — Send to <support@senzing.com> with subject "Senzing Bootcamp Power Feedback". I can format the content for easy copy-paste.
   2. **GitHub Issue** — Create an issue on the senzing-bootcamp power repository. I can format it as a markdown-ready issue body.
   3. **Copy path** — I'll show you the full file path so you can share it however you prefer.

   Do not automatically send emails or create GitHub issues — wait for explicit bootcamper confirmation before taking any external action.
6. If the bootcamper declines (says "no", "skip", "not now", or any declining response), proceed without re-prompting about feedback.
7. If the feedback file does not exist, contains no entries, or the reminder was already shown, fall through to the line below.

> Say "bootcamp feedback" if you'd like to share your experience.

<!-- 
  ## Export-Results Integration Contract
  
  This documents how the graduation workflow integrates with the export-results feature.
  The export script (scripts/export_results.py) should honor these conventions:
  
  1. HTML Report: When production/GRADUATION_REPORT.md exists, include its content
     as a "Graduation" section in the HTML report, rendered after the module
     completion sections.
  
  2. ZIP Archive: When the --format zip option is used and the production/ directory
     exists, include the contents of production/ under artifacts/production/ in the
     ZIP archive.
  
  3. No graduation: When the graduation workflow has not been completed (i.e.,
     production/GRADUATION_REPORT.md does not exist), do not include any
     graduation-related content in the export.
  
  This contract is informational — the export script reads these paths at runtime.
  No changes to this steering file are needed to support export integration.
-->
