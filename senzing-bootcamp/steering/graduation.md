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

1. **Read preferences**: Load `config/bootcamp_preferences.yaml` and extract: `language`, `track`, `platform`, `data_sources`, `database_type`.

2. **Read progress**: Load `config/bootcamp_progress.json` and extract: `modules_completed`, `current_module`.

3. **Fallback if files are missing**: Inform the bootcamper, prompt for **language** and **database type**, use sensible defaults for everything else (track: unknown, platform: GitHub Actions, data_sources: []).

Store these values for use throughout the workflow. Proceed to Step 1.

## Step 1: Production Project Structure

If `production/` already exists, ask the bootcamper: Overwrite, Merge, or Abort. WAIT for response. If abort, stop and generate the graduation report noting the abort.

Create `production/` and copy production-relevant files per the file copy table. Exclude bootcamp scaffolding per the exclusion table.

#[[file:senzing-bootcamp/steering/graduation-reference.md]]

Present a summary of files copied, excluded, and directories created. Ask: "Does this look right? Ready to proceed to Step 2?" WAIT for confirmation.

## Step 2: Production Configuration Files

Generate the following files in `production/` using the language and database type from pre-checks. See the reference file for templates and details for each file.

#[[file:senzing-bootcamp/steering/graduation-reference.md]]

Generate: `.env.production` (placeholders only), `.env.example` (safe example values), `docker-compose.yml` (parameterized by database type), CI/CD pipeline (ask bootcamper which platform — WAIT for response), and `.gitignore` (language-appropriate).

Ask: "Configuration files generated. Ready to proceed to Step 3 (Production README)?" WAIT for confirmation.

## Step 3: Production README

Generate `production/README.md` parameterized by language, database type, and data sources. **Do not use bootcamp-specific language** — no "bootcamp", "module", "track", or "bootcamper."

Required sections: Project Overview, Prerequisites, Installation, Configuration, Usage, Project Structure, Contributing.

Show the generated README to the bootcamper for review. WAIT for confirmation or revision requests. Apply any requested changes before proceeding.

## Step 4: Migration Checklist

Generate `production/MIGRATION_CHECKLIST.md` with six sections (Database, Security, Licensing, Performance, Data, Deployment) using `- [ ]` checkboxes. Apply conditional logic based on whether Modules 10–12 were completed — see the reference file for base items and conditional rules.

#[[file:senzing-bootcamp/steering/graduation-reference.md]]

Ask: "Migration checklist generated. Ready to proceed to Step 5 (Git initialization)?" WAIT for confirmation.

## Step 5: Git Repository Initialization (Optional)

Ask: "Would you like me to initialize a new git repository in the `production/` directory?" WAIT for response.

**If accepted**: Check `git --version`. If unavailable, inform and skip. If available, run `git init`, `git add .`, and `git commit -m "Initial production project from Senzing Bootcamp graduation"`. If any command fails, inform and continue.

**If declined**: Skip to the graduation report.

## Graduation Report

**Always generate this file**, regardless of whether individual steps encountered errors. See the reference file for the full report template.

#[[file:senzing-bootcamp/steering/graduation-reference.md]]

If any step encountered errors, add a "⚠️ Issues Encountered" section.

Present completion:

> 🎓 **Graduation complete!** Your production project is ready in `production/`.
>
> Check `production/GRADUATION_REPORT.md` for a full summary, and work through `production/MIGRATION_CHECKLIST.md` to prepare for deployment.
>
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
