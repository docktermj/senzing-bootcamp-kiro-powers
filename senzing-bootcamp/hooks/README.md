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

### 4. Validate Senzing JSON (`validate-senzing-json.kiro.hook`)

**Trigger:** When Senzing JSON output files are modified
**Action:** Suggests validating with analyze_record
**Use case:** Ensures output conforms to SGES

### 5. Backup Project on Request (`backup-project-on-request.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Runs the project backup script
**Use case:** Quick project backups without typing a command
**How to use:** Click the "Backup Project on Request" button in the Kiro Agent Hooks explorer view, or say "backup my project" to the agent directly

### 6. CommonMark Validation (`commonmark-validation.kiro.hook`)

**Trigger:** When Markdown files are edited
**Action:** Checks for CommonMark compliance and auto-fixes issues
**Use case:** Ensures consistent Markdown formatting across all documentation

### 7. Verify Senzing Facts (`verify-senzing-facts.kiro.hook`)

**Trigger:** Before any write operation (preToolUse)
**Action:** Reminds agent to verify Senzing-specific content via MCP tools
**Use case:** Enforces SENZING_INFORMATION_POLICY — prevents writing Senzing facts from training data

### 8. Analyze After Mapping (`analyze-after-mapping.kiro.hook`)

**Trigger:** When new Senzing JSON files are created in `data/transformed/`
**Action:** Reminds agent to run `analyze_record` before proceeding to loading
**Use case:** Catches bad mappings early — validates quality score >70% before Module 6

### 9. Run Tests After Change (`run-tests-after-change.kiro.hook`)

**Trigger:** When source code files are modified in `src/load/`, `src/query/`, or `src/transform/`
**Action:** Reminds agent to run the test suite to verify the change
**Use case:** Catches regressions after code changes in Modules 6-8

### 10. Git Commit Reminder (`git-commit-reminder.kiro.hook`)

**Trigger:** Manual — click the hook button in the Agent Hooks panel
**Action:** Suggests a descriptive git commit based on the current module
**Use case:** Reminds users to commit progress after completing a module
**How to use:** Click the "Git Commit Reminder" button in the Kiro Agent Hooks explorer view

### 11. Enforce Working Directory Paths (`enforce-working-directory.kiro.hook`) ⭐

**Trigger:** Before any file write operation (preToolUse)
**Action:** Checks that file paths don't reference `/tmp`, `%TEMP%`, or any location outside the working directory
**Use case:** Enforces the file storage policy automatically — prevents MCP-generated code from placing files in system temp directories
**Recommended:** Install for all modules

### 12. Summarize Progress on Stop (`summarize-on-stop.kiro.hook`)

**Trigger:** When the agent finishes working (agentStop)
**Action:** Prompts the agent to summarize what it accomplished, which files changed, and what the next step is
**Use case:** Ensures the bootcamper always knows what happened during an agent interaction

### 13. Verify Generated Code (`verify-generated-code.kiro.hook`)

**Trigger:** When new source files are created in `src/transform/`, `src/load/`, or `src/query/`
**Action:** Prompts the agent to run the new code on sample data and verify it works before moving on
**Use case:** Catches broken code before the user tries to run it manually

## Installation

**Note:** These hooks use file patterns like `data/transformed/*.jsonl` and `src/load/*` that assume the bootcamp project directory structure exists. Run the bootcamp setup (say "start the bootcamp") before installing hooks, or the file-based triggers won't match anything.

### Option 1: Use Install Script (Recommended)

```bash
# Interactive installation with guided options
python scripts/install_hooks.py
```

### Option 2: Copy to Workspace Hooks Directory

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

### Option 3: Use Kiro Command Palette

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Import Hook"
4. Select hook file from `senzing-bootcamp/hooks/`

### Option 4: Ask the Agent

Simply ask: "Please install the Senzing Bootcamp hooks from the power directory"

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
- ✅ **Backup Project on Request** (quick backups via voice commands)

### Module 5 (Data Mapping)

- ✅ Code Style Check
- ✅ Data Quality Check
- ✅ Validate Senzing JSON
- ✅ Analyze After Mapping

### Module 6 (Data Loading)

- ✅ Code Style Check
- ✅ Backup Before Load

### Module 8 (Query Programs)

- ✅ Code Style Check

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
