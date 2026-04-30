# Senzing Bootcamp Hooks

This directory contains pre-configured Kiro hooks to support the Senzing Bootcamp workflow.

## Available Hooks

### 1. Code Style Check (`code-style-check.kiro.hook`) ⭐

**Trigger:** When source code files are edited (`.py`, `.java`, `.cs`, `.rs`, `.ts`, `.js`)
**Action:** Checks for language-appropriate coding standards and suggests fixes
**Use case:** Ensures all generated code follows proper conventions for the chosen language
**Recommended:** Install for all modules that generate code

### 2. Data Quality Check (`data-quality-check.kiro.hook`)

**Trigger:** When transformation programs are saved
**Action:** Reminds to validate data quality
**Use case:** Ensures transformation changes don't degrade data quality

### 3. Backup Before Load (`backup-before-load.kiro.hook`)

**Trigger:** When loading programs are modified
**Action:** Reminds to backup database before running
**Use case:** Prevents data loss from failed loads

### 4. Backup Project on Request (`backup-project-on-request.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Runs the project backup script
**Use case:** Quick project backups without typing a command
**How to use:** Click the "Backup Project on Request" button in the Kiro Agent Hooks explorer view, or say "backup my project" to the agent directly

### 5. CommonMark Validation (`commonmark-validation.kiro.hook`)

**Trigger:** When Markdown files are edited
**Action:** Checks for CommonMark compliance and auto-fixes issues
**Use case:** Ensures consistent Markdown formatting across all documentation

### 6. Verify Senzing Facts (`verify-senzing-facts.kiro.hook`)

**Trigger:** Before any write operation (preToolUse)
**Action:** Reminds agent to verify Senzing-specific content via MCP tools
**Use case:** Enforces SENZING_INFORMATION_POLICY — prevents writing Senzing facts from training data

### 7. Analyze After Mapping (`analyze-after-mapping.kiro.hook`)

**Trigger:** When new Senzing JSON files are created in `data/transformed/`
**Action:** Reminds agent to run `analyze_record` before proceeding to loading
**Use case:** Catches bad mappings early — validates quality score >70% and Entity Spec conformance before Module 6

### 8. Run Tests After Change (`run-tests-after-change.kiro.hook`)

**Trigger:** When source code files are modified in `src/load/`, `src/query/`, or `src/transform/`
**Action:** Reminds agent to run the test suite to verify the change
**Use case:** Catches regressions after code changes in Modules 6-8

### 9. Git Commit Reminder (`git-commit-reminder.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Suggests a descriptive git commit based on the current module
**Use case:** Reminds users to commit progress after completing a module
**How to use:** Click the "Git Commit Reminder" button in the Kiro Agent Hooks explorer view

### 10. Enforce Working Directory Paths (`enforce-working-directory.kiro.hook`) ⭐

**Trigger:** Before any file write operation (preToolUse)
**Action:** Checks that file paths don't reference `/tmp`, `%TEMP%`, or any location outside the working directory
**Use case:** Enforces the file storage policy automatically — prevents MCP-generated code from placing files in system temp directories
**Recommended:** Install for all modules

### 11. Ask Bootcamper (`ask-bootcamper.kiro.hook`) ⭐

**Trigger:** When the agent finishes working (agentStop)
**Action:** Recaps what was accomplished and which files changed, then asks the bootcamper what to do next with a contextual 👉 question
**Use case:** Ensures the bootcamper always knows what happened during an agent interaction and has a clear next step
**Recommended:** Install for all modules

### 12. Verify Generated Code (`verify-generated-code.kiro.hook`)

**Trigger:** When new source files are created in `src/transform/`, `src/load/`, or `src/query/`
**Action:** Prompts the agent to run the new code on sample data and verify it works before moving on
**Use case:** Catches broken code before the user tries to run it manually

### 13. Offer Entity Graph Visualization (`offer-visualization.kiro.hook`)

**Trigger:** When new files are created in `src/query/`
**Action:** Prompts the agent to offer generating an interactive entity graph visualization
**Use case:** Ensures bootcampers are offered the visualization feature during Module 7
**Note:** Works in conjunction with the Enforce Visualization Offers hook (#16) — this hook catches query program creation proactively, while the agentStop hook catches missed offers before the agent closes the conversation

### 14. Review Bootcamper Input (`review-bootcamper-input.kiro.hook`) ⭐

**Trigger:** On every message submission (promptSubmit)
**Action:** Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture
**Use case:** Guarantees feedback is always captured when a bootcamper says "bootcamp feedback" — deterministic, not probabilistic
**Recommended:** Install for all modules

### 15. Deployment Phase Gate (`deployment-phase-gate.kiro.hook`)

**Trigger:** After task execution completes (postTaskExecution)
**Action:** Checks if current module is 11 (deployment), then displays packaging-complete summary and asks whether to proceed to deployment or stop
**Use case:** Enforces the packaging-to-deployment phase gate — prevents the agent from blending packaging and deployment phases together

### 16. Enforce Visualization Offers (`enforce-visualization-offers.kiro.hook`) ⭐

**Trigger:** When the agent finishes working (agentStop)
**Action:** Checks if current module is 7, then verifies both visualization offers (entity graph and results dashboard) were made during the interaction
**Use case:** Safety net for Module 7 — catches missed visualization offers before the agent closes the conversation
**Recommended:** Install for Module 7

### 17. Enforce Feedback File Path (`enforce-feedback-path.kiro.hook`)

**Trigger:** Before any write operation (preToolUse, write)
**Action:** Checks if the agent is writing feedback content and ensures it goes to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
**Use case:** Prevents feedback from being written to the wrong file or submitted externally

## Installation

**Note:** These hooks use file patterns like `data/transformed/*.jsonl` and `src/load/*` that assume the bootcamp project directory structure exists. Run the bootcamp setup (say "start the bootcamp") before installing hooks, or the file-based triggers won't match anything.

The `.kiro.hook` files in this directory are the canonical hook definitions. The Hook Registry in `hook-registry.md` (referenced from `onboarding-flow.md`) must be kept in sync with these files.

### Option 1: Automatic (Recommended)

Hooks are created automatically during onboarding. The agent reads the Hook Registry in `hook-registry.md` (loaded via `onboarding-flow.md`) and calls the `createHook` tool for each hook. No manual action needed.

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

### All Modules

- ✅ **Code Style Check** (ensures code quality for the chosen language)
- ✅ **Review Bootcamper Input** (guarantees feedback is always captured)
- ✅ **Backup Project on Request** (quick backups via voice commands)

### Module 5 (Data Quality & Mapping)

- ✅ Code Style Check
- ✅ Data Quality Check
- ✅ Analyze After Mapping

### Module 6 (Data Loading)

- ✅ Code Style Check
- ✅ Backup Before Load

### Module 7 (Query & Visualize)

- ✅ Code Style Check
- ✅ Enforce Visualization Offers

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
