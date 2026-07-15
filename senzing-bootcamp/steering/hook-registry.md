---
inclusion: manual
---

# Hook Registry

26 bootcamp hooks organized by category. Load `hook-registry-critical.md` for full prompt text when creating hooks.

## Critical Hooks (created during onboarding)

| Hook ID | Event Type | Description |
|---------|-----------|-------------|
| ask-bootcamper | Stop → agent | to wait for your answer |
| code-style-check | PostFileSave → agent | to check code style |
| review-bootcamper-input | UserPromptSubmit → agent | to review what you said |
| write-policy-gate | PreToolUse → agent | to process your response |

## Module Hooks (created when module starts)

| Hook ID | Module | Event Type | Description |
|---------|--------|-----------|-------------|
| validate-business-problem | 1 | PostTaskExec → agent | to validate your business problem |
| verify-sdk-setup | 2 | PostFileSave → agent | to verify SDK setup |
| enforce-gate-on-stop | 3 | Stop → agent | to enforce mandatory gate execution on agent stop |
| enforce-mandatory-gate | 3 | PreToolUse → agent | to enforce mandatory gate step execution before advancement |
| enforce-visualization-offers | 3,5,7,8 | Stop → agent | to offer visualizations |
| gate-module3-visualization | 3 | PreToolUse → agent | to gate Module 3 completion on visualization step |
| verify-demo-results | 3 | PostTaskExec → agent | to verify demo results |
| validate-data-files | 4 | PostFileCreate → agent | to validate data files |
| analyze-after-mapping | 5 | PostFileCreate → agent | to analyze mapped data |
| data-quality-check | 5 | PostFileSave → agent | to check data quality |
| enforce-mapping-spec | 5 | PostFileCreate → agent | to enforce the mapping specification |
| backup-before-load | 6 | PostFileSave → agent | to remind you to back up before loading |
| run-tests-after-change | 6 | PostFileSave → agent | to remind you to run tests |
| verify-generated-code | 6 | PostFileCreate → agent | to verify generated code |
| validate-benchmark-results | 8 | PostFileSave → agent | to validate benchmark results |
| security-scan-on-save | 9 | PostFileSave → agent | to run a security scan |
| validate-alert-config | 10 | PostFileCreate → agent | to validate alert configuration |
| deployment-phase-gate | 11 | PostTaskExec → agent | to check the deployment phase gate |
| enforce-critical-artifacts | any | Stop → command | to guarantee critical graduation artifacts on agent stop |
| error-recovery-context | any | PostToolUse → agent | to help recover from errors |
| module-completion-celebration | any | Stop → agent | to celebrate module completion |
| session-log-events | any | PostToolUse → command | to log session events after write operations |

## Hook Creation

To create hooks, load `hook-registry-critical.md` for the full critical hook prompts and `createHook` parameters.

For module hook prompts, resolve `current_module` from `config/bootcamp_progress.json` and load the matching per-module slice `hook-registry-module-<NN>.md` (zero-padded two-digit module number, e.g. `hook-registry-module-03.md`) or `hook-registry-module-any.md` for hooks that apply to any module. Each slice holds the full prompt text and `createHook` parameters for that module's hooks.

If the expected per-module slice is missing at its path, fall back to this summary and report that the per-module slice is unavailable. The tables above list every hook by ID, event flow, module label, and description.
