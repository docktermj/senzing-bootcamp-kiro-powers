# Senzing Bootcamp Hooks

This directory contains pre-configured Kiro hooks to support the Senzing Bootcamp workflow. There are 29 hooks total.

## Hook Name Style Guide

The `name` field is user-facing — the Kiro UI renders it as "Ask Kiro Hook {name}". Every hook's `name` MUST follow the pattern `"to {verb phrase}"` (lowercase, no trailing period) so the full UI string reads as a natural sentence. Examples:

- ✅ `"to check code style"` → "Ask Kiro Hook to check code style"
- ✅ `"to remind you to run tests"` → "Ask Kiro Hook to remind you to run tests"
- ❌ `"Code Style Check"` → "Ask Kiro Hook Code Style Check" (jargony)
- ❌ `"I will check code style"` → "Ask Kiro Hook I will check code style" (first-person)

## Available Hooks

Hooks marked ⭐ are installed during onboarding as critical hooks; the others are installed when the associated module starts.

### Critical Hooks (installed during onboarding)

### 1. Ask Bootcamper (`ask-bootcamper.kiro.hook`) ⭐

**Trigger:** When the agent finishes working (agentStop)
**Action:** Consolidated four-phase hook — (1) produces a recap and closing 👉 question when work was done and no question is already pending; (2) enforces step sequencing and module transition validation; (3) audits MCP-first compliance for Senzing content; (4) detects compound questions and applies silent self-correction
**Use case:** Owns all closing questions, step sequencing enforcement, MCP-first compliance, and question format enforcement

### 2. Review Bootcamper Input (`review-bootcamper-input.kiro.hook`) ⭐

**Trigger:** On every message submission (promptSubmit)
**Action:** Reviews each message for feedback or status trigger phrases and routes to the feedback workflow or the inline status display
**Use case:** Deterministic feedback capture and status lookup

### 3. Code Style Check (`code-style-check.kiro.hook`) ⭐

**Trigger:** When source code files are edited (`src/**/*.py`, `src/**/*.java`, `src/**/*.cs`, `src/**/*.rs`, `src/**/*.ts`, `src/**/*.js`)
**Action:** Checks for language-appropriate coding standards and suggests fixes
**Use case:** Ensures all generated code follows proper conventions for the chosen language

### 4. CommonMark Validation (`commonmark-validation.kiro.hook`) ⭐

**Trigger:** When Markdown files are edited
**Action:** Checks for CommonMark compliance and auto-fixes issues
**Use case:** Ensures consistent Markdown formatting across all documentation

### 5. Write Policy Gate (`write-policy-gate.kiro.hook`) ⭐

**Trigger:** Before any file write operation (preToolUse)
**Action:** Consolidated write-time policy hook that performs four checks in a single interception: (1) blocks direct SQL against the Senzing database (G2C.db or internal tables), instructing the agent to rewrite using SDK methods; (2) enforces the single-question rule for `.question_pending` writes, preventing compound questions; (3) validates file path policies — feedback must go to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` and no files may be written outside the working directory; (4) enforces root file placement rules, blocking source code and data files from the project root. Uses a fast path for normal writes (proceeds silently) and slow paths only for violations.
**Use case:** Unified write-time enforcement of SQL blocking, question quality, file path policies, and root placement — avoids quadruple-firing on every write operation

### Module Hooks (installed when the associated module starts)

### 6. Validate Business Problem (`validate-business-problem.kiro.hook`) — Module 1

**Trigger:** After task execution (postTaskExecution)
**Action:** Validates that data sources, matching criteria, and success metrics are documented before proceeding to Module 2
**Use case:** Gate check for Module 1 completion

### 7. Verify SDK Setup (`verify-sdk-setup.kiro.hook`) — Module 2

**Trigger:** When configuration or database files are edited (`config/senzing_config.*`, `config/bootcamp_preferences.yaml`, `database/*.*`)
**Action:** Re-verifies SDK initialization and database access during Module 2
**Use case:** Catches config regressions during SDK setup

### 8. Verify Demo Results (`verify-demo-results.kiro.hook`) — Module 3

**Trigger:** After task execution (postTaskExecution)
**Action:** Verifies that system verification produced entity resolution results matching the Senzing TruthSet expected output
**Use case:** Gate check for Module 3 (System Verification) before proceeding to Module 4

### 9. Gate Module 3 Visualization (`gate-module3-visualization.kiro.hook`) — Module 3

**Trigger:** Before any file write operation (preToolUse)
**Action:** Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present, or the step was explicitly skipped
**Use case:** Ensures the visualization "wow moment" is not accidentally bypassed

### 10. Enforce Mandatory Gate (`enforce-mandatory-gate.kiro.hook`) — Module 3

**Trigger:** Before any file write operation (preToolUse)
**Action:** Blocks step advancement past a ⛔ mandatory gate step in `bootcamp_progress.json` when the corresponding checkpoint is missing and no `skipped_steps` entry exists
**Use case:** Proactive guard that fires before the agent advances past a mandatory gate, ensuring unconditional execution of ⛔ steps

### 11. Enforce Gate on Stop (`enforce-gate-on-stop.kiro.hook`) — Module 3

**Trigger:** When the agent finishes working (agentStop)
**Action:** After each agent turn during Module 3, verifies that Step 9 (⛔ mandatory gate) has been executed if the agent has reached or passed it; forces immediate execution if the gate checkpoint is missing
**Use case:** Catches mandatory gate violations retroactively when the preToolUse guard was bypassed

### 12. Validate Data Files (`validate-data-files.kiro.hook`) — Module 4

**Trigger:** When new files are created in `data/raw/`
**Action:** Checks file format, encoding, and basic readability
**Use case:** Catches bad data files early before they cause mapping or loading failures

### 13. Data Quality Check (`data-quality-check.kiro.hook`) — Module 5

**Trigger:** When transformation programs are saved (`src/transform/*.*`)
**Action:** Reminds to validate data quality after transformation changes
**Use case:** Ensures transformation edits don't degrade data quality

### 14. Analyze After Mapping (`analyze-after-mapping.kiro.hook`) — Module 5

**Trigger:** When new files are created in `data/transformed/` (`*.jsonl`, `*.json`)
**Action:** Validates transformed data with `analyze_record` for quality score >70% and Entity Specification conformance; verifies the per-source mapping spec exists
**Use case:** Catches bad mappings early before Module 6 loading

### 15. Enforce Mapping Specification (`enforce-mapping-spec.kiro.hook`) — Module 5

**Trigger:** When new files are created in `data/transformed/`
**Action:** Blocks progression until `docs/{source_name}_mapper.md` exists for each transformed source
**Use case:** Guarantees every mapped data source has a per-source mapping specification markdown

### 16. Backup Before Load (`backup-before-load.kiro.hook`) — Module 6

**Trigger:** When loading programs are modified (`src/load/*.*`)
**Action:** Reminds to backup the database before running loads
**Use case:** Prevents data loss from failed loads

### 17. Run Tests After Change (`run-tests-after-change.kiro.hook`) — Module 6

**Trigger:** When source code files are modified in `src/load/`, `src/query/`, or `src/transform/`
**Action:** Reminds the agent to run the test suite to verify the change
**Use case:** Catches regressions after code changes

### 18. Verify Generated Code (`verify-generated-code.kiro.hook`) — Module 6

**Trigger:** When new source files are created in `src/transform/`, `src/load/`, or `src/query/`
**Action:** Prompts the agent to run the new code on sample data and verify it works before moving on
**Use case:** Catches broken code before the user tries to run it manually

### 19. Enforce Visualization Offers (`enforce-visualization-offers.kiro.hook`) — Modules 3, 5, 7, 8

**Trigger:** When the agent finishes working (agentStop) during a visualization-capable module
**Action:** Checks the visualization tracker and surfaces any missed visualization offers before the conversation ends
**Use case:** Safety net to ensure visualization checkpoints are always offered

### 20. Validate Benchmark Results (`validate-benchmark-results.kiro.hook`) — Module 8

**Trigger:** When benchmark scripts are edited (`tests/performance/*.*`)
**Action:** Validates that benchmark scripts produce parseable output with required metrics (records/sec, latency percentiles)
**Use case:** Ensures performance results are comparable across runs

### 21. Security Scan on Save (`security-scan-on-save.kiro.hook`) — Module 9

**Trigger:** When security-related files are modified (`src/security/*.*`, `config/*credentials*`, `config/*secret*`, `.env*`)
**Action:** Reminds the agent to re-run the language-appropriate vulnerability scanner
**Use case:** Catches regressions introduced during Module 9 hardening

### 22. Validate Alert Configuration (`validate-alert-config.kiro.hook`) — Module 10

**Trigger:** When monitoring configuration files are created (`monitoring/alerts/*.*`, `monitoring/dashboards/*.*`)
**Action:** Validates alert rule syntax (name, condition, severity, action) and dashboard metric references
**Use case:** Catches malformed alert rules before deployment

### 23. Deployment Phase Gate (`deployment-phase-gate.kiro.hook`) — Module 11

**Trigger:** After task execution (postTaskExecution)
**Action:** Checks if current module is 11, then displays the packaging-complete summary and asks whether to proceed to deployment or stop
**Use case:** Enforces the packaging-to-deployment phase gate — prevents blending the two phases

### Any-Module Hooks (installed during onboarding)

### 24. Backup Project on Request (`backup-project-on-request.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Runs the project backup script
**Use case:** Quick project backups without typing a command
**How to use:** Click the "Backup Project on Request" button in the Kiro Agent Hooks explorer view, or say "backup my project" to the agent directly

### 25. Error Recovery Context (`error-recovery-context.kiro.hook`)

**Trigger:** After shell command execution (postToolUse, shell)
**Action:** On non-zero exit codes, consults `common-pitfalls.md` and `recovery-from-mistakes.md` to surface targeted recovery guidance; calls `explain_error_code` for SENZ errors
**Use case:** Turns raw command failures into actionable fixes

### 26. Git Commit Reminder (`git-commit-reminder.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Suggests a descriptive git commit based on the current module
**Use case:** Reminds users to commit progress after completing a module

### 27. Module Completion Celebration (`module-completion-celebration.kiro.hook`)

**Trigger:** When the agent finishes working (agentStop)
**Action:** On detecting a new entry in `modules_completed`, displays a brief celebration banner and offers the next module
**Use case:** Marks module boundaries and orients the bootcamper toward the next step

### 28. Module Recap Append (`module-recap-append.kiro.hook`)

**Trigger:** When the agent finishes working (agentStop)
**Action:** On detecting a new entry in `modules_completed`, appends a structured recap section to `docs/bootcamp_recap.md` capturing information shared, questions asked, answers given, and actions taken
**Use case:** Builds a running record of the bootcamp experience for PDF generation at graduation

### 29. Session Log Events (`session-log-events.kiro.hook`)

**Trigger:** After write operations (postToolUse)
**Action:** Logs file create, modify, delete, and MCP tool call actions to the session log after write operations complete
**Use case:** Enables progressive session tracking for the completion summary

## Installation

**Note:** These hooks use file patterns like `data/transformed/*.jsonl` and `src/load/*` that assume the bootcamp project directory structure exists. Run the bootcamp setup (say "start the bootcamp") before installing hooks, or the file-based triggers won't match anything.

The `.kiro.hook` files in this directory are the canonical hook definitions. The Hook Registry is split across three files that must be kept in sync with these hook definitions:

- `hook-registry.md` — summary with hook IDs, event types, and descriptions
- `hook-registry-critical.md` — full prompts for critical hooks (created during onboarding)
- `hook-registry-modules.md` — full prompts for module-specific hooks

### Option 1: Automatic (Recommended)

Hooks are created automatically during onboarding. The agent reads the full hook definitions from `hook-registry-critical.md` (loaded via `onboarding-flow.md`) and calls the `createHook` tool for each hook. No manual action needed.

### Option 2: Ask the Agent

```text
"Please recreate the bootcamp hooks"
```

### Option 3: Copy Hook Files (Development Environments Only)

This method only works when the `senzing-bootcamp/hooks/` directory is available (e.g., when working from a cloned repository, not from an installed power).

```bash
# Linux/macOS: Copy all hooks to your project
cp senzing-bootcamp/hooks/*.kiro.hook .kiro/hooks/

# Or copy individual hooks
cp senzing-bootcamp/hooks/data-quality-check.kiro.hook .kiro/hooks/
```

```powershell
# Windows (PowerShell)
Copy-Item senzing-bootcamp\hooks\*.kiro.hook .kiro\hooks\
```

### Option 4: Use Kiro Command Palette

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Import Hook"
4. Select hook file from `senzing-bootcamp/hooks/`

## Enabling/Disabling Hooks

Hooks are enabled by default when copied to `.kiro/hooks/`. To disable a hook:

1. Open the hook file in `.kiro/hooks/`
2. Set `"enabled": false` in the JSON
3. Or delete the hook file

## Customizing Hooks

You can customize any hook by editing the JSON file:

- **patterns**: Change which files trigger the hook
- **prompt**: Modify what the agent says
- **command**: Change what command runs
- **timeout**: Adjust command timeout

## Recommended Hooks by Module

### All Modules (critical and any-module hooks)

- ✅ Ask Bootcamper
- ✅ Review Bootcamper Input
- ✅ Code Style Check
- ✅ CommonMark Validation
- ✅ Write Policy Gate
- ✅ Backup Project on Request
- ✅ Error Recovery Context
- ✅ Git Commit Reminder
- ✅ Module Completion Celebration
- ✅ Module Recap Append
- ✅ Session Log Events

### Module 1 (Business Problem)

- ✅ Validate Business Problem

### Module 2 (SDK Setup)

- ✅ Verify SDK Setup

### Module 3 (System Verification)

- ✅ Verify Demo Results
- ✅ Gate Module 3 Visualization
- ✅ Enforce Mandatory Gate
- ✅ Enforce Gate on Stop
- ✅ Enforce Visualization Offers

### Module 4 (Data Collection)

- ✅ Validate Data Files

### Module 5 (Data Quality & Mapping)

- ✅ Data Quality Check
- ✅ Analyze After Mapping
- ✅ Enforce Mapping Specification
- ✅ Enforce Visualization Offers

### Module 6 (Data Processing)

- ✅ Backup Before Load
- ✅ Run Tests After Change
- ✅ Verify Generated Code

### Module 7 (Query, Visualize, and Discover)

- ✅ Enforce Visualization Offers

### Module 8 (Performance Testing)

- ✅ Validate Benchmark Results
- ✅ Enforce Visualization Offers

### Module 9 (Security Hardening)

- ✅ Security Scan on Save

### Module 10 (Monitoring)

- ✅ Validate Alert Configuration

### Module 11 (Deployment)

- ✅ Deployment Phase Gate

## Troubleshooting

**Hook not triggering?**

- Check that the file pattern matches your files
- Verify the hook is in `.kiro/hooks/` directory
- Check that the hook JSON is valid
- Look for errors in Kiro's output panel

**Hook triggering too often?**

- Adjust the file patterns to be more specific
- Consider using `userTriggered` instead of `fileEdited`

**Command timeout?**

- Increase the `timeout` value in seconds
- Or set `timeout: 0` to disable timeout

## Support

For more information about Kiro hooks, see:

- Kiro documentation: <https://kiro.dev/docs/hooks/>
- Command Palette: "Open Kiro Hook UI"
- Ask the agent: "How do I create a hook?"
