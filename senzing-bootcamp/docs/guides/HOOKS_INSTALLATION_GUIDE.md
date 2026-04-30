# Senzing Bootcamp Hooks - Installation Guide

## Automatic Installation

Hooks are created automatically during onboarding. The agent reads hook definitions from the Hook Registry in `onboarding-flow.md` and calls the `createHook` tool for each one — no manual action needed. Critical hooks (7) are created during initial setup; module-specific hooks (11) are created when you reach the relevant module.

## Manual Reinstallation

If hooks need to be recreated (e.g., after clearing `.kiro/hooks/`):

### Method 1: Ask the Agent

```text
"Please recreate the bootcamp hooks"
```

The agent will read the Hook Registry from `onboarding-flow.md` and recreate all Critical Hooks using the `createHook` tool.

### Method 2: Kiro UI

1. Open Command Palette (`Cmd/Ctrl + Shift + P`)
2. Search: "Open Kiro Hook UI"
3. Click "Import Hook"
4. Navigate to `senzing-bootcamp/hooks/` (available in development environments only)

## What Gets Installed

18 pre-configured hooks:

| Hook | Trigger | Purpose |
| ---- | ------- | ------- |
| Review Bootcamper Input | Every message (promptSubmit) | Detect feedback trigger phrases |
| Enforce Feedback File Path | Before write (preToolUse) | Ensure feedback goes to correct file |
| Enforce Working Directory | Before write (preToolUse) | Block /tmp and external paths |
| Verify Senzing Facts | Before write (preToolUse) | Verify facts via MCP tools |
| Code Style Check | Save source code (fileEdited) | Check coding standards |
| Summarize Progress on Stop | Agent stops (agentStop) | Summarize what was accomplished |
| CommonMark Validation | Save Markdown (fileEdited) | Check CommonMark compliance |
| Data Quality Check | Save transformation program (fileEdited) | Remind to validate quality |
| Validate Senzing JSON | Save transformed data (fileEdited) | Validate with analyze_record |
| Analyze After Mapping | New file in data/transformed/ (fileCreated) | Run analyze_record |
| Backup Before Load | Save loading program (fileEdited) | Remind to backup database |
| Run Tests After Change | Save src/ code files (fileEdited) | Remind to run tests |
| Verify Generated Code | New source file created (fileCreated) | Run code on sample data |
| Offer Entity Graph Visualization | New query file (fileCreated) | Offer interactive visualization |
| Enforce Visualization Offers | Agent stops (agentStop) | Catch missed Module 8 offers |
| Module 12 Phase Gate | After task (postTaskExecution) | Packaging-to-deployment gate |
| Backup Project on Request | Manual trigger (userTriggered) | Run project backup script |
| Git Commit Reminder | Manual trigger (userTriggered) | Suggest descriptive commit |

## Customization

Edit hook files in `.kiro/hooks/`. Common changes:

- **Disable a hook:** Delete the file from `.kiro/hooks/`
- **File patterns:** Modify the hook's file patterns to match your project structure

## Uninstalling

```bash
# Linux / macOS
rm .kiro/hooks/*.kiro.hook

# Windows (PowerShell)
Remove-Item .kiro\hooks\*.kiro.hook
```

## Support

- Full hook details: `senzing-bootcamp/hooks/README.md`
- Kiro docs: <https://kiro.dev/docs/hooks/>
