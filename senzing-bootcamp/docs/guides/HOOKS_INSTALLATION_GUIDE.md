# Senzing Bootcamp Hooks - Installation Guide

## Automatic Installation

Hooks are created automatically during onboarding. The agent reads hook definitions from the Hook Registry in `onboarding-flow.md` and calls the `createHook` tool for each one — no manual action needed.

- **Critical Hooks** (8) are created during initial setup
- **Module Hooks** (11) are created when you reach the relevant module

No files are copied. The `createHook` tool creates hooks programmatically, so hooks work whether the power was installed via Kiro's power system or cloned from the source repository.

## Manual Reinstallation

If hooks need to be recreated (e.g., after clearing `.kiro/hooks/`):

```text
"Please recreate the bootcamp hooks"
```

The agent will read the Hook Registry from `onboarding-flow.md` and recreate all Critical Hooks using the `createHook` tool. Module Hooks are recreated when you start the associated module.

## What Gets Installed

19 pre-configured hooks:

### Critical Hooks (created during onboarding)

| Hook | Trigger | Purpose |
| ---- | ------- | ------- |
| Ask Bootcamper | Agent stops (agentStop) | Recaps accomplishments and asks what to do next |
| Code Style Check | Save source code (fileEdited) | Check language-appropriate coding standards |
| CommonMark Validation | Save Markdown (fileEdited) | Check CommonMark compliance |
| Enforce Feedback File Path | Before write (preToolUse) | Ensure feedback goes to correct file |
| Enforce Working Directory Paths | Before write (preToolUse) | Block /tmp and external paths |
| Feedback Submission Reminder | Agent stops (agentStop) | Remind to share saved feedback after track completion |
| Review Bootcamper Input | Every message (promptSubmit) | Detect feedback trigger phrases |
| Verify Senzing Facts Before Writing | Before write (preToolUse) | Verify facts via MCP tools |

### Module Hooks (created when module starts)

| Hook | Module | Trigger | Purpose |
| ---- | ------ | ------- | ------- |
| Validate Data Files | 4 | New file in data/raw/ (fileCreated) | Check file format, encoding, readability |
| Senzing Data Quality Check | 5 | Save transformation program (fileEdited) | Remind to validate quality |
| Analyze After Mapping | 5 | New file in data/transformed/ (fileCreated) | Run analyze_record for quality metrics |
| Backup Database Before Loading | 6 | Save loading program (fileEdited) | Remind to backup database |
| Run Tests After Code Change | 6 | Save src/ code files (fileEdited) | Remind to run tests |
| Verify Generated Code Runs | 6 | New source file created (fileCreated) | Run code on sample data |
| Offer Entity Graph Visualization | 7 | New query file (fileCreated) | Offer interactive visualization |
| Enforce Visualization Offers | 7 | Agent stops (agentStop) | Catch missed Module 7 offers |
| Deployment Phase Gate | 11 | After task (postTaskExecution) | Packaging-to-deployment gate |
| Backup Project on Request | Any | Manual trigger (userTriggered) | Run project backup script |
| Git Commit Reminder | Any | Manual trigger (userTriggered) | Suggest descriptive commit |

## Customization

Hooks are managed through the Kiro hooks system. Common changes:

- **Disable a hook:** Delete the hook file from `.kiro/hooks/`
- **Recreate hooks:** Ask the agent: "Please recreate the bootcamp hooks"

## Support

- Full hook details: `senzing-bootcamp/steering/hook-registry.md`
- Hook source files: `senzing-bootcamp/hooks/README.md`
- Kiro docs: [https://kiro.dev/docs/hooks/](https://kiro.dev/docs/hooks/)
