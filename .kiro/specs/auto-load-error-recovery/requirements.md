# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power includes two steering files — `common-pitfalls.md` and `recovery-from-mistakes.md` — that contain solutions to known issues. These files use `inclusion: manual`, meaning the agent only loads them when explicitly asked. When bootcampers hit errors during shell commands, the agent does not automatically consult these resources, leading to longer debugging cycles and repeated troubleshooting of known problems.

This feature adds a `postToolUse` hook that triggers after shell command execution. When a command exits with non-zero status, the hook prompts the agent to consult the pitfalls and recovery steering files, match the error against known solutions, and provide targeted guidance. If no known solution matches, the agent falls back to normal troubleshooting. The hook only activates during active bootcamp modules to avoid interference with unrelated work.

## Glossary

- **Error_Recovery_Hook**: A JSON hook file (`.kiro.hook` extension) that triggers after shell command execution to detect failures and consult known-solution steering files.
- **Shell_Command**: Any command executed via the `shell` tool type in the Kiro IDE, producing an exit code.
- **Non_Zero_Exit**: A shell command result where the exit code is not zero, indicating failure.
- **Pitfalls_File**: The steering file at `senzing-bootcamp/steering/common-pitfalls.md` containing known issues organized by module and symptom.
- **Recovery_File**: The steering file at `senzing-bootcamp/steering/recovery-from-mistakes.md` containing step-by-step recovery procedures for common mistakes.
- **Known_Solution**: An error pattern documented in the Pitfalls_File or Recovery_File with a corresponding fix or recovery procedure.
- **Bootcamp_Progress**: The JSON file at `config/bootcamp_progress.json` that tracks the current module and step.
- **Hook_Categories_File**: The YAML file at `senzing-bootcamp/hooks/hook-categories.yaml` that maps hooks to their associated modules.
- **Active_Bootcamp_Session**: A state where `config/bootcamp_progress.json` exists and contains a valid current module number (1–11).

## Requirements

### Requirement 1: Hook File Creation

**User Story:** As a power maintainer, I want an `error-recovery-context` hook file in the hooks directory, so that shell command failures automatically trigger consultation of known-solution resources.

#### Acceptance Criteria

1. THE Error_Recovery_Hook SHALL be stored at `senzing-bootcamp/hooks/error-recovery-context.kiro.hook` as valid JSON
2. THE Error_Recovery_Hook SHALL contain a `name` field with value "Auto-Load Error Recovery Context"
3. THE Error_Recovery_Hook SHALL contain a `version` field with value "1.0.0"
4. THE Error_Recovery_Hook SHALL contain a `description` field summarizing its purpose of detecting shell failures and consulting pitfalls/recovery steering files
5. THE Error_Recovery_Hook SHALL contain a `when` object with `type` field set to "postToolUse"
6. THE Error_Recovery_Hook SHALL contain a `when` object with `toolTypes` field set to `["shell"]`
7. THE Error_Recovery_Hook SHALL contain a `then` object with `type` field set to "askAgent" and a non-empty `prompt` field

### Requirement 2: Failure Detection Logic

**User Story:** As a bootcamper, I want the hook to detect when my shell commands fail, so that I get help without having to explicitly ask for it.

#### Acceptance Criteria

1. WHEN a shell command completes with a Non_Zero_Exit, THE Error_Recovery_Hook prompt SHALL instruct the agent to identify the error from the command output
2. WHEN a shell command completes with exit code zero, THE Error_Recovery_Hook prompt SHALL instruct the agent to produce no output and take no action
3. THE Error_Recovery_Hook prompt SHALL instruct the agent to extract the error message, exit code, and command context from the tool execution result

### Requirement 3: Pitfalls and Recovery Consultation

**User Story:** As a bootcamper, I want the agent to automatically check known solutions when my commands fail, so that I get targeted fixes for documented problems instead of generic troubleshooting.

#### Acceptance Criteria

1. WHEN a Non_Zero_Exit is detected, THE Error_Recovery_Hook prompt SHALL instruct the agent to read `senzing-bootcamp/steering/common-pitfalls.md`
2. WHEN a Non_Zero_Exit is detected, THE Error_Recovery_Hook prompt SHALL instruct the agent to read `senzing-bootcamp/steering/recovery-from-mistakes.md`
3. WHEN the error matches a Known_Solution in the Pitfalls_File, THE Error_Recovery_Hook prompt SHALL instruct the agent to present the documented fix directly to the bootcamper
4. WHEN the error matches a Known_Solution, THE Error_Recovery_Hook prompt SHALL instruct the agent to cite which section of the pitfalls or recovery file the solution came from
5. WHEN the error does not match any Known_Solution, THE Error_Recovery_Hook prompt SHALL instruct the agent to fall back to normal troubleshooting without claiming a known solution exists

### Requirement 4: Module-Scoped Activation

**User Story:** As a bootcamper, I want the error recovery hook to only trigger during bootcamp work, so that it does not interfere when I am doing unrelated development in the same workspace.

#### Acceptance Criteria

1. THE Error_Recovery_Hook prompt SHALL instruct the agent to check whether `config/bootcamp_progress.json` exists before consulting pitfalls files
2. WHEN `config/bootcamp_progress.json` does not exist, THE Error_Recovery_Hook prompt SHALL instruct the agent to produce no output and take no action
3. WHEN `config/bootcamp_progress.json` exists and contains a valid module number, THE Error_Recovery_Hook prompt SHALL instruct the agent to scope its pitfall lookup to the current module section first
4. WHEN the current module section has no matching pitfall, THE Error_Recovery_Hook prompt SHALL instruct the agent to also check the "General Pitfalls" and "Troubleshooting by Symptom" sections

### Requirement 5: Hook Categories Registration

**User Story:** As a power maintainer, I want the error recovery hook registered in `hook-categories.yaml` under the `any` module category, so that the sync script correctly catalogs it and it is available across all modules.

#### Acceptance Criteria

1. THE Hook_Categories_File SHALL list "error-recovery-context" in the `any` list under `modules`
2. WHEN `sync_hook_registry.py --verify` is executed, THE sync script SHALL pass without errors after the new hook and category entry are added
3. THE Hook_Categories_File SHALL maintain existing entries unchanged (no removals or reorderings of other hooks)

### Requirement 6: Hook Schema Compliance

**User Story:** As a power maintainer, I want the error recovery hook to pass all existing validation checks, so that CI remains green and the hook integrates with existing infrastructure.

#### Acceptance Criteria

1. WHEN parsed by `sync_hook_registry.py`, THE sync script SHALL successfully parse the Error_Recovery_Hook file without errors
2. WHEN validated by `test_hooks.py`, THE Error_Recovery_Hook SHALL pass all structural validation checks (required fields present, valid event type, valid action type)
3. THE Error_Recovery_Hook SHALL use a `when.type` value that exists in the `VALID_EVENT_TYPES` set defined in `test_hooks.py`
4. THE Error_Recovery_Hook SHALL use a `then.type` value of "askAgent"
5. THE Error_Recovery_Hook `then.prompt` field SHALL be a non-empty string

### Requirement 7: Prompt Quality and Specificity

**User Story:** As a bootcamper, I want the error recovery guidance to be specific and actionable, so that I can resolve issues quickly without wading through irrelevant information.

#### Acceptance Criteria

1. THE Error_Recovery_Hook prompt SHALL instruct the agent to present only the matching pitfall and fix, not the entire pitfalls file content
2. THE Error_Recovery_Hook prompt SHALL instruct the agent to include the specific command or action needed to resolve the issue when a Known_Solution is found
3. WHEN multiple pitfalls could match, THE Error_Recovery_Hook prompt SHALL instruct the agent to present the most specific match based on the current module context
4. THE Error_Recovery_Hook prompt SHALL instruct the agent to use `explain_error_code` from the Senzing MCP server when the error contains a SENZ error code prefix
