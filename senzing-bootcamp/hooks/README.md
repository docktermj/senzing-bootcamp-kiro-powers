# Senzing Bootcamp Hooks

This directory contains pre-configured Kiro hooks to support the Senzing Bootcamp workflow. There are 26 hooks total, all in the Kiro 1.0 `v1` JSON schema.

Each hook ships as a `.json` file whose top-level object is the `v1` wrapper:

```json
{
  "version": "v1",
  "hooks": [
    { "name": "...", "trigger": "...", "matcher": "...", "action": { "type": "agent", "prompt": "..." } }
  ]
}
```

The `trigger` is a Kiro 1.0 event name (for example `PostFileSave`, `Stop`, `PreToolUse`), the `matcher` is a single regular expression that scopes the hook (a file-path regex for file triggers or a tool-name regex for tool triggers, omitted for unscoped triggers), and the `action` is either `{"type": "agent", "prompt": ...}` or `{"type": "command", "command": ...}`.

Kiro 1.0 removed the legacy manual (`userTriggered`) trigger, so the three former manual hooks are now slash-command steering files. See [Manual Hooks (now slash commands)](#manual-hooks-now-slash-commands).

## Hook Name Style Guide

The `name` field is user-facing — the Kiro UI renders it as "Ask Kiro Hook {name}". Every hook's `name` MUST follow the pattern `"to {verb phrase}"` (lowercase, no trailing period) so the full UI string reads as a natural sentence. Examples:

- ✅ `"to check code style"` → "Ask Kiro Hook to check code style"
- ✅ `"to remind you to run tests"` → "Ask Kiro Hook to remind you to run tests"
- ❌ `"Code Style Check"` → "Ask Kiro Hook Code Style Check" (jargony)
- ❌ `"I will check code style"` → "Ask Kiro Hook I will check code style" (first-person)

## Available Hooks

Hooks marked ⭐ are installed during onboarding as critical hooks; the others are installed when the associated module starts.

### Critical Hooks (installed during onboarding)

### 1. Ask Bootcamper (`ask-bootcamper.json`) ⭐

**Trigger:** When the agent finishes working (`Stop`)
**Matcher:** none (unscoped trigger)
**Action:** Consolidated five-phase hook — (0) on module completion, appends the structured recap section to `docs/bootcamp_recap.md` (folded in from the former `module-recap-append` hook); (1) produces a recap and closing 👉 question when work was done and no question is already pending; (2) enforces step sequencing and module transition validation; (3) audits MCP-first compliance for Senzing content; (4) detects compound questions and applies silent self-correction
**Use case:** Owns module recap capture, all closing questions, step sequencing enforcement, MCP-first compliance, and question format enforcement

### 2. Review Bootcamper Input (`review-bootcamper-input.json`) ⭐

**Trigger:** On every message submission (`UserPromptSubmit`)
**Matcher:** none (unscoped trigger)
**Action:** Reviews each message for feedback or status trigger phrases and routes to the feedback workflow or the inline status display
**Use case:** Deterministic feedback capture and status lookup

### 3. Code Style Check (`code-style-check.json`) ⭐

**Trigger:** When source code files are saved (`PostFileSave`)
**Matcher:** `^(?:src/(?:.*/)?[^/]*\.py|src/(?:.*/)?[^/]*\.java|src/(?:.*/)?[^/]*\.cs|src/(?:.*/)?[^/]*\.rs|src/(?:.*/)?[^/]*\.ts|src/(?:.*/)?[^/]*\.js)$`
**Action:** Checks for language-appropriate coding standards and suggests fixes
**Use case:** Ensures all generated code follows proper conventions for the chosen language

### 4. Write Policy Gate (`write-policy-gate.json`) ⭐

**Trigger:** Before any write tool call (`PreToolUse`)
**Matcher:** `fs_write|str_replace|fs_append`
**Action:** Consolidated write-time policy hook that performs four checks in a single interception: (1) blocks direct SQL against the Senzing database (G2C.db or internal tables), instructing the agent to rewrite using SDK methods; (2) enforces the single-question rule for `.question_pending` writes, preventing compound questions; (3) validates file path policies — feedback must go to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` and no files may be written outside the working directory; (4) enforces root file placement rules, blocking source code and data files from the project root. Uses a fast path for normal writes (proceeds silently) and slow paths only for violations.
**Use case:** Unified write-time enforcement of SQL blocking, question quality, file path policies, and root placement — avoids quadruple-firing on every write operation

### Module Hooks (installed when the associated module starts)

### 5. Validate Business Problem (`validate-business-problem.json`) — Module 1

**Trigger:** After task execution (`PostTaskExec`)
**Matcher:** none (unscoped trigger)
**Action:** Validates that data sources, matching criteria, and success metrics are documented before proceeding to Module 2
**Use case:** Gate check for Module 1 completion

### 6. Verify SDK Setup (`verify-sdk-setup.json`) — Module 2

**Trigger:** When configuration or database files are saved (`PostFileSave`)
**Matcher:** `^(?:config/senzing_config\.[^/]*|config/bootcamp_preferences\.yaml|database/[^/]*\.[^/]*)$`
**Action:** Re-verifies SDK initialization and database access during Module 2
**Use case:** Catches config regressions during SDK setup

### 7. Verify Demo Results (`verify-demo-results.json`) — Module 3

**Trigger:** After task execution (`PostTaskExec`)
**Matcher:** none (unscoped trigger)
**Action:** Verifies that system verification produced entity resolution results matching the Senzing TruthSet expected output
**Use case:** Gate check for Module 3 (System Verification) before proceeding to Module 4

### 8. Gate Module 3 Visualization (`gate-module3-visualization.json`) — Module 3

**Trigger:** Before any write tool call (`PreToolUse`)
**Matcher:** `fs_write|str_replace|fs_append`
**Action:** Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present, or the step was explicitly skipped
**Use case:** Ensures the visualization "wow moment" is not accidentally bypassed

### 9. Enforce Mandatory Gate (`enforce-mandatory-gate.json`) — Module 3

**Trigger:** Before any write tool call (`PreToolUse`)
**Matcher:** `fs_write|str_replace|fs_append`
**Action:** Blocks step advancement past a ⛔ mandatory gate step in `bootcamp_progress.json` when the corresponding checkpoint is missing and no `skipped_steps` entry exists
**Use case:** Proactive guard that fires before the agent advances past a mandatory gate, ensuring unconditional execution of ⛔ steps

### 10. Enforce Gate on Stop (`enforce-gate-on-stop.json`) — Module 3

**Trigger:** When the agent finishes working (`Stop`)
**Matcher:** none (unscoped trigger)
**Action:** After each agent turn during Module 3, verifies that Step 9 (⛔ mandatory gate) has been executed if the agent has reached or passed it; forces immediate execution if the gate checkpoint is missing
**Use case:** Catches mandatory gate violations retroactively when the `PreToolUse` guard was bypassed

### 11. Validate Data Files (`validate-data-files.json`) — Module 4

**Trigger:** When new files are created in `data/raw/` (`PostFileCreate`)
**Matcher:** `^(?:data/raw/[^/]*\.[^/]*)$`
**Action:** Checks file format, encoding, and basic readability
**Use case:** Catches bad data files early before they cause mapping or loading failures

### 12. Data Quality Check (`data-quality-check.json`) — Module 5

**Trigger:** When transformation programs are saved (`PostFileSave`)
**Matcher:** `^(?:src/transform/[^/]*\.[^/]*)$`
**Action:** Reminds to validate data quality after transformation changes
**Use case:** Ensures transformation edits don't degrade data quality

### 13. Analyze After Mapping (`analyze-after-mapping.json`) — Module 5

**Trigger:** When new files are created in `data/transformed/` (`PostFileCreate`)
**Matcher:** `^(?:data/transformed/[^/]*\.jsonl|data/transformed/[^/]*\.json)$`
**Action:** Validates transformed data with `analyze_record` for quality score >70% and Entity Specification conformance; verifies the per-source mapping spec exists
**Use case:** Catches bad mappings early before Module 6 loading

### 14. Enforce Mapping Specification (`enforce-mapping-spec.json`) — Module 5

**Trigger:** When new files are created in `data/transformed/` (`PostFileCreate`)
**Matcher:** `^(?:data/transformed/[^/]*\.jsonl|data/transformed/[^/]*\.json)$`
**Action:** Blocks progression until `docs/{source_name}_mapper.md` exists for each transformed source
**Use case:** Guarantees every mapped data source has a per-source mapping specification markdown

### 15. Backup Before Load (`backup-before-load.json`) — Module 6

**Trigger:** When loading programs are saved (`PostFileSave`)
**Matcher:** `^(?:src/load/[^/]*\.[^/]*)$`
**Action:** Reminds to backup the database before running loads
**Use case:** Prevents data loss from failed loads

### 16. Run Tests After Change (`run-tests-after-change.json`) — Module 6

**Trigger:** When source code files are saved in `src/load/`, `src/query/`, or `src/transform/` (`PostFileSave`)
**Matcher:** `^(?:src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*|src/transform/[^/]*\.[^/]*)$`
**Action:** Reminds the agent to run the test suite to verify the change
**Use case:** Catches regressions after code changes

### 17. Verify Generated Code (`verify-generated-code.json`) — Module 6

**Trigger:** When new source files are created in `src/transform/`, `src/load/`, or `src/query/` (`PostFileCreate`)
**Matcher:** `^(?:src/transform/[^/]*\.[^/]*|src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*)$`
**Action:** Prompts the agent to run the new code on sample data and verify it works before moving on
**Use case:** Catches broken code before the user tries to run it manually

### 18. Enforce Visualization Offers (`enforce-visualization-offers.json`) — Modules 3, 5, 7, 8

**Trigger:** When the agent finishes working (`Stop`) during a visualization-capable module
**Matcher:** none (unscoped trigger)
**Action:** Checks the visualization tracker and surfaces any missed visualization offers before the conversation ends
**Use case:** Safety net to ensure visualization checkpoints are always offered

### 19. Validate Benchmark Results (`validate-benchmark-results.json`) — Module 8

**Trigger:** When benchmark scripts are saved (`PostFileSave`)
**Matcher:** `^(?:tests/performance/[^/]*\.[^/]*)$`
**Action:** Validates that benchmark scripts produce parseable output with required metrics (records/sec, latency percentiles)
**Use case:** Ensures performance results are comparable across runs

### 20. Security Scan on Save (`security-scan-on-save.json`) — Module 9

**Trigger:** When security-related files are saved (`PostFileSave`)
**Matcher:** `^(?:src/security/[^/]*\.[^/]*|config/[^/]*credentials[^/]*|config/[^/]*secret[^/]*|\.env[^/]*)$`
**Action:** Reminds the agent to re-run the language-appropriate vulnerability scanner
**Use case:** Catches regressions introduced during Module 9 hardening

### 21. Validate Alert Configuration (`validate-alert-config.json`) — Module 10

**Trigger:** When monitoring configuration files are created (`PostFileCreate`)
**Matcher:** `^(?:monitoring/alerts/[^/]*\.[^/]*|monitoring/dashboards/[^/]*\.[^/]*)$`
**Action:** Validates alert rule syntax (name, condition, severity, action) and dashboard metric references
**Use case:** Catches malformed alert rules before deployment

### 22. Deployment Phase Gate (`deployment-phase-gate.json`) — Module 11

**Trigger:** After task execution (`PostTaskExec`)
**Matcher:** none (unscoped trigger)
**Action:** Checks if current module is 11, then displays the packaging-complete summary and asks whether to proceed to deployment or stop
**Use case:** Enforces the packaging-to-deployment phase gate — prevents blending the two phases

### Any-Module Hooks (installed during onboarding)

### 23. Error Recovery Context (`error-recovery-context.json`)

**Trigger:** After a shell command runs (`PostToolUse`)
**Matcher:** `execute_bash`
**Action:** On non-zero exit codes, consults `common-pitfalls.md` and `recovery-from-mistakes.md` to surface targeted recovery guidance; calls `explain_error_code` for SENZ errors
**Use case:** Turns raw command failures into actionable fixes

### 24. Module Completion Celebration (`module-completion-celebration.json`)

**Trigger:** When the agent finishes working (`Stop`)
**Matcher:** none (unscoped trigger)
**Action:** On detecting a new entry in `modules_completed`, displays a brief celebration banner and offers the next module
**Use case:** Marks module boundaries and orients the bootcamper toward the next step

### 25. Session Log Events (`session-log-events.json`)

**Trigger:** After write tool calls (`PostToolUse`)
**Matcher:** `fs_write|str_replace|fs_append`
**Action:** Runs a command (`action.type` of `command`, with a 10-second timeout) that logs file create, modify, delete, and MCP tool call actions to the session log after write operations complete
**Use case:** Enables progressive session tracking for the completion summary

### 26. Enforce Critical Artifacts (`enforce-critical-artifacts.json`)

**Trigger:** When the agent finishes working (`Stop`)
**Matcher:** none (unscoped trigger)
**Action:** A deterministic `command` hook that runs `python3 senzing-bootcamp/scripts/ensure_graduation_artifacts.py --stop-hook`. The script gates itself — it does nothing while `config/.question_pending` exists and no-ops away from a track-end stopping point (module 7 or 11 completed) — then regenerates any absent, empty, or stale crown-jewel artifact (Q&A transcript, recap Markdown, and the rendered recap PDF). The recap PDF has a stdlib tier and a no-data floor, so a valid `docs/bootcamp_recap.pdf` is produced even offline and even with no captured module data. It always exits 0 and never blocks the stop.
**Use case:** Guarantees the transcript, recap, and rendered recap "trophy" PDF are produced by the runtime itself — not left to the agent to remember — so the completion artifacts can never be silently skipped

## Manual Hooks (now slash commands)

Kiro 1.0 removed the manual (`userTriggered`) hook trigger, so the three former manual hooks no longer ship as hook files. They are now manual-invocation steering files (slash commands) under `senzing-bootcamp/steering/`. Invoke each by name:

- `/backup-project` — run the project backup on request (replaces the former `backup-project-on-request` hook). See `steering/slash-backup-project.md`.
- `/git-commit` — remind and help you commit module progress (replaces the former `git-commit-reminder` hook). See `steering/slash-git-commit.md`.
- `/commonmark-validation` — validate and fix Markdown CommonMark compliance in one pass (replaces the former `commonmark-validation` hook). See `steering/slash-commonmark-validation.md`.

## Installation

**Note:** These hooks use matchers like `^(?:data/transformed/[^/]*\.jsonl)$` and `^(?:src/load/[^/]*\.[^/]*)$` that assume the bootcamp project directory structure exists. Run the bootcamp setup (say "start the bootcamp") before installing hooks, or the file-based triggers won't match anything.

The `.json` files in this directory are the canonical Kiro 1.0 hook definitions. Each file wraps a single hook in the `v1` envelope (`{"version": "v1", "hooks": [ ... ]}`). The Hook Registry is split across three files that must be kept in sync with these hook definitions:

- `hook-registry.md` — summary with hook IDs, triggers, and descriptions
- `hook-registry-critical.md` — full prompts for critical hooks (created during onboarding)
- `hook-registry-module-NN.md` (and `hook-registry-module-any.md`) — full prompts for module-specific hooks, one slice per module

### Option 1: Automatic (Recommended)

Hooks are created automatically during onboarding. The agent reads the full hook definitions from `hook-registry-critical.md` (loaded via `onboarding-flow.md`) and creates each hook as a `v1` definition in `.kiro/hooks/` using the `createHook` capability. No manual action needed.

### Option 2: Ask the Agent

```text
"Please recreate the bootcamp hooks"
```

### Option 3: Run the Installer Script (Development Environments Only)

This method only works when the `senzing-bootcamp/hooks/` directory is available (e.g., when working from a cloned repository, not from an installed power). The installer copies the shipped `*.json` v1 hook files into `.kiro/hooks/` and reports how many were installed:

```bash
# Install every shipped v1 hook
python3 senzing-bootcamp/scripts/install_hooks.py --all

# Or install only the essential set (critical + capture-critical hooks)
python3 senzing-bootcamp/scripts/install_hooks.py --essential
```

Run it with no flag for an interactive menu that lets you pick hooks individually.

### Option 4: Copy Hook Files (Development Environments Only)

You can also copy the `*.json` v1 hook files directly:

```bash
# Linux/macOS: copy all v1 hooks into your project
cp senzing-bootcamp/hooks/*.json .kiro/hooks/

# Or copy an individual hook
cp senzing-bootcamp/hooks/data-quality-check.json .kiro/hooks/
```

```powershell
# Windows (PowerShell)
Copy-Item senzing-bootcamp\hooks\*.json .kiro\hooks\
```

### Option 5: Use Kiro Command Palette

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Import Hook"
4. Select a `.json` hook file from `senzing-bootcamp/hooks/`

## Enabling/Disabling Hooks

Hooks are enabled by default when installed into `.kiro/hooks/`. To disable a hook:

1. Open the `.json` file in `.kiro/hooks/`
2. Set `"enabled": false` in the hook entry
3. Or delete the hook file

## Customizing Hooks

You can customize any hook by editing the `.json` file:

- **matcher**: change the regular expression that scopes which files or tools trigger the hook
- **prompt**: modify what the agent says (for `agent` actions)
- **command**: change what command runs (for `command` actions)
- **timeout**: adjust the command timeout (for `command` actions)

## Recommended Hooks by Module

### All Modules (critical and any-module hooks)

- ✅ Ask Bootcamper
- ✅ Review Bootcamper Input
- ✅ Code Style Check
- ✅ Write Policy Gate
- ✅ Error Recovery Context
- ✅ Module Completion Celebration
- ✅ Session Log Events
- ✅ Enforce Critical Artifacts

The former `backup-project-on-request`, `git-commit-reminder`, and `commonmark-validation` hooks are now the `/backup-project`, `/git-commit`, and `/commonmark-validation` slash commands — invoke them by name instead of installing them.

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

- Check that the `matcher` regex matches your files or tool names
- Verify the hook is in the `.kiro/hooks/` directory
- Check that the hook JSON is valid (`version` is `v1` and `hooks` is an array)
- Look for errors in Kiro's output panel

**Hook triggering too often?**

- Tighten the `matcher` regex to be more specific
- Consider narrowing the trigger (for example, use `PostFileCreate` instead of `PostFileSave` if you only care about new files)

**Command timeout?**

- Increase the `timeout` value in seconds
- Or set `timeout: 0` to disable the timeout

## Support

For more information about Kiro hooks, see:

- Kiro documentation: <https://kiro.dev/docs/hooks/>
- Command Palette: "Open Kiro Hook UI"
- Ask the agent: "How do I create a hook?"
