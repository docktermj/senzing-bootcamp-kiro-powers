# Requirements Document

## Introduction

Kiro IDE 1.0 changes how Agent Hooks are defined and executed. Hooks now use a
versioned `v1` JSON schema stored at `.kiro/hooks/*.json` (a wrapper object
`{"version":"v1","hooks":[{name, trigger, matcher, action}]}`), replacing the
legacy `*.kiro.hook` files. Legacy hooks do not execute under 1.0 until they are
migrated. 1.0 also renames every trigger, restructures the action block,
collapses file-glob patterns and tool-type lists into a single regex matcher,
removes the manual (`userTriggered`) trigger, and introduces a capability-based
permissions model that prompts before write, shell, and MCP operations.

The senzing-bootcamp Kiro Power ships 30 legacy hooks plus a large body of
tooling, configuration, steering, documentation, and CI that encode the legacy
hook schema. This feature migrates the entire Power to Kiro 1.0 so that hooks
execute correctly, CI stays green, onboarding creates 1.0-valid hooks, and
bootcampers are told which permissions to approve so the guided experience does
not stall. Everything under `senzing-bootcamp/` ships to users, so the migration
must keep the shipped artifacts internally consistent.

Migration scope covers: converting the 27 non-manual hooks to `v1` JSON while
preserving behavior and prompt text; converting the 3 manual hooks to
manual-invocation steering files (slash commands); updating validators, tests,
registry/composer generators, installer, configs, steering, and docs in
lockstep; updating the onboarding hook-creation path; documenting the required
permissions and MCP auto-approve; and recording the legacy back-compatibility
decision with a version bump. User- or IDE-side 1.0 features (custom agents,
dockable chat, session export, Agent Focus Mode, session migration) are out of
scope unless a concrete Power impact surfaces.

## Glossary

- **Power**: The senzing-bootcamp Kiro Power — everything shipped under `senzing-bootcamp/`.
- **Legacy_Hook**: A hook defined in the pre-1.0 `*.kiro.hook` JSON schema with a `when` block (`type`, `patterns`, `toolTypes`) and a `then` block (`type` of `askAgent` or `runCommand`, plus `prompt` or `command`).
- **V1_Hook**: A hook expressed in the Kiro 1.0 schema — an entry in a `.kiro/hooks/*.json` file whose top level is `{"version": "v1", "hooks": [ ... ]}` and whose entries contain `name`, `trigger`, `matcher`, and `action`.
- **Trigger**: The 1.0 event name that fires a V1_Hook (for example `PostFileSave`, `Stop`, `PreToolUse`).
- **Matcher**: The single 1.0 regular expression that scopes a V1_Hook — a file-path regex for file triggers or a tool-name regex for tool triggers.
- **Action**: The 1.0 action object of a V1_Hook — `{"type": "agent", "prompt": "..."}` or `{"type": "command", "command": "..."}`.
- **Manual_Hook**: A Legacy_Hook whose trigger is `userTriggered` — `backup-project-on-request`, `git-commit-reminder`, and `commonmark-validation`.
- **Non_Manual_Hook**: Any Legacy_Hook that is not a Manual_Hook (27 hooks).
- **Slash_Command_File**: A manual-invocation steering file that replaces a Manual_Hook and is invoked by name (for example `/backup-project`).
- **Matcher_Translator**: The build-time logic that converts a Legacy_Hook `when.patterns` glob list or `when.toolTypes` category list into a single 1.0 Matcher regex.
- **Hook_Validator**: The validation tooling — `scripts/validate_power.py` (hook checks) and `scripts/test_hooks.py`.
- **Registry_Generator**: `scripts/sync_hook_registry.py`, which generates `steering/hook-registry*.md` and `hooks/hooks.lock.yaml` from the hook definitions.
- **Prompt_Composer**: `scripts/compose_hook_prompts.py`, which composes the Module 3 gate-hook prompts from `scripts/hook_prompt_fragments.py`.
- **Hook_Installer**: `scripts/install_hooks.py`, which copies hook definitions into `.kiro/hooks/`.
- **Onboarding_Flow**: The steering-driven hook-creation path (`steering/onboarding-flow.md`, `steering/agent-instructions.md`, `steering/session-resume-phase2-setup-recovery.md`, and related registry files) that uses the `createHook` capability.
- **Hook_Categories**: `hooks/hook-categories.yaml`, the category and `agentstop_order` mapping.
- **CI_Pipeline**: The GitHub Actions workflow `.github/workflows/validate-power.yml`.
- **Permissions_Doc**: The user-facing documentation describing the 1.0 capability permissions the bootcamp requests.
- **MCP_Config**: `senzing-bootcamp/mcp.json`, the sole source of the Senzing MCP server URL and auto-approve list.
- **Power_Version_Files**: `senzing-bootcamp/VERSION`, the `POWER.md` frontmatter version, and `senzing-bootcamp/CHANGELOG.md`.

## Requirements

### Requirement 1: Convert Non-Manual Hooks to v1 JSON

**User Story:** As a bootcamper on Kiro 1.0, I want the bootcamp hooks to run automatically, so that the guided workflow keeps working without me hand-editing hook files.

#### Acceptance Criteria

1. THE Power SHALL provide a V1_Hook definition for each of the 27 Non_Manual_Hooks.
2. THE Power SHALL store every shipped V1_Hook definition in a `.json` file whose top-level object is `{"version": "v1", "hooks": [ ... ]}`.
3. THE Power SHALL include, for every V1_Hook entry, the `name`, `trigger`, `matcher`, and `action` fields required by the Kiro 1.0 hook schema.
4. THE Power SHALL preserve each Non_Manual_Hook prompt text or command text verbatim in the corresponding V1_Hook Action.
5. THE Power SHALL preserve each Non_Manual_Hook `name` value in the corresponding V1_Hook so the Kiro UI label is unchanged.
6. WHERE a Legacy_Hook specifies a command `timeout`, THE Power SHALL preserve the equivalent timeout in the V1_Hook Action when the 1.0 schema supports a command timeout.
7. IF a Non_Manual_Hook cannot be represented as a schema-valid V1_Hook, THEN THE Power SHALL fail migration with a message naming the hook and the unsupported construct.

### Requirement 2: Apply the 1.0 Trigger and Action Renames

**User Story:** As a Power maintainer, I want the trigger and action renames applied consistently, so that every migrated hook fires on the correct 1.0 event.

#### Acceptance Criteria

1. WHERE a Legacy_Hook uses trigger `fileEdited`, THE Power SHALL set the V1_Hook Trigger to `PostFileSave`.
2. WHERE a Legacy_Hook uses trigger `fileCreated`, THE Power SHALL set the V1_Hook Trigger to `PostFileCreate`.
3. WHERE a Legacy_Hook uses trigger `fileDeleted`, THE Power SHALL set the V1_Hook Trigger to `PostFileDelete`.
4. WHERE a Legacy_Hook uses trigger `agentStop`, THE Power SHALL set the V1_Hook Trigger to `Stop`.
5. WHERE a Legacy_Hook uses trigger `promptSubmit`, THE Power SHALL set the V1_Hook Trigger to `UserPromptSubmit`.
6. WHERE a Legacy_Hook uses trigger `postTaskExecution`, THE Power SHALL set the V1_Hook Trigger to `PostTaskExec`.
7. WHERE a Legacy_Hook uses trigger `preToolUse`, THE Power SHALL set the V1_Hook Trigger to `PreToolUse`.
8. WHERE a Legacy_Hook uses trigger `postToolUse`, THE Power SHALL set the V1_Hook Trigger to `PostToolUse`.
9. WHERE a Legacy_Hook uses action `askAgent` with a `prompt`, THE Power SHALL set the V1_Hook Action to `{"type": "agent", "prompt": <original prompt>}`.
10. WHERE a Legacy_Hook uses action `runCommand` with a `command`, THE Power SHALL set the V1_Hook Action to `{"type": "command", "command": <original command>}`.

### Requirement 3: Translate Patterns and Tool Types to a Single Matcher

**User Story:** As a Power maintainer, I want globs and tool-type lists translated to one regex matcher, so that migrated hooks scope to the same files and tools as before.

#### Acceptance Criteria

1. WHERE a Legacy_Hook specifies `when.patterns` file globs, THE Matcher_Translator SHALL produce a single file-path regex as the V1_Hook Matcher.
2. FOR ALL file paths in a representative sample, THE V1_Hook file-path Matcher SHALL match a path if and only if at least one original glob in `when.patterns` matched that path (glob-to-regex equivalence).
3. WHERE a Legacy_Hook specifies `when.toolTypes` containing `write`, THE Matcher_Translator SHALL produce the tool-name regex `fs_write|str_replace|fs_append` as the V1_Hook Matcher.
4. WHERE a Legacy_Hook trigger has neither `when.patterns` nor `when.toolTypes` (for example `agentStop`, `promptSubmit`, `postTaskExecution`), THE Power SHALL omit the Matcher or set it to an empty value as required by the 1.0 schema for unscoped triggers.
5. FOR ALL Legacy_Hooks with `when.patterns`, translating patterns to a Matcher and evaluating that Matcher SHALL preserve the set of matched sample paths across repeated translation (idempotent translation).
6. IF a `when.patterns` glob or `when.toolTypes` entry cannot be translated to a valid regex, THEN THE Matcher_Translator SHALL fail with a message naming the hook and the offending pattern.

### Requirement 4: Convert Manual Hooks to Slash-Command Steering Files

**User Story:** As a bootcamper, I want the former manual-trigger hooks available as named commands, so that I can still run backups, commit reminders, and Markdown validation on demand under 1.0.

#### Acceptance Criteria

1. THE Power SHALL provide a Slash_Command_File for each of the three Manual_Hooks: `backup-project-on-request`, `git-commit-reminder`, and `commonmark-validation`.
2. THE Power SHALL preserve the instruction text of each Manual_Hook prompt in its corresponding Slash_Command_File.
3. THE Power SHALL configure each Slash_Command_File for manual invocation so that a bootcamper triggers it by name.
4. THE Power SHALL remove the three Manual_Hooks from the shipped hook definition set so that no `userTriggered` hook remains.
5. THE Power SHALL remove the three Manual_Hook identifiers from Hook_Categories, the hook registry files, the Hook_Installer metadata, and `hooks/hooks.lock.yaml`.
6. WHERE a Slash_Command_File is added under `senzing-bootcamp/steering/`, THE Power SHALL record its token count and size category in `steering/steering-index.yaml`.

### Requirement 5: Preserve Write-Gate Enforcement Behavior

**User Story:** As a Power maintainer, I want the write-time policy gates to keep intercepting writes under 1.0, so that SQL blocking, single-question enforcement, path policies, and mandatory gates are not silently lost.

#### Acceptance Criteria

1. THE Power SHALL migrate `write-policy-gate`, `enforce-mandatory-gate`, and `gate-module3-visualization` to V1_Hooks with Trigger `PreToolUse`.
2. THE Power SHALL set the Matcher of each migrated `PreToolUse` write gate to the tool-name regex `fs_write|str_replace|fs_append`.
3. THE Power SHALL preserve the full policy prompt text of each migrated write gate verbatim.
4. IF a migration change would remove or disable a `PreToolUse` write gate, THEN THE Power SHALL block that change pending explicit maintainer approval.
5. WHEN a maintainer explicitly approves removing or disabling a `PreToolUse` write gate, THE Power SHALL allow that change to proceed.

### Requirement 6: Update Hook Validation to the v1 Schema

**User Story:** As a Power maintainer, I want the validators to enforce the 1.0 schema, so that CI verifies migrated hooks and rejects stale legacy definitions.

#### Acceptance Criteria

1. THE Hook_Validator SHALL validate that each shipped V1_Hook file has a top-level `version` of `v1` and a `hooks` array.
2. THE Hook_Validator SHALL validate that each V1_Hook entry contains `name`, `trigger`, `matcher` (where required by the trigger), and `action`.
3. THE Hook_Validator SHALL accept only the 1.0 Trigger names and reject any legacy trigger name.
4. THE Hook_Validator SHALL accept only the 1.0 Action types `agent` and `command` and reject `askAgent` and `runCommand`.
5. WHEN a V1_Hook Matcher is present, THE Hook_Validator SHALL confirm the Matcher compiles as a valid regular expression.
6. IF any shipped hook file uses the legacy `*.kiro.hook` schema, THEN THE Hook_Validator SHALL report a validation error identifying the file.
7. THE Hook_Validator SHALL verify that the shipped hook definitions and the hook registry files reference the same set of hook identifiers.

### Requirement 7: Regenerate the Hook Registry and Lockfile in v1 Terms

**User Story:** As a Power maintainer, I want the registry and lockfile generated from v1 definitions, so that the `--verify` gate stays green and the registry reflects 1.0 triggers.

#### Acceptance Criteria

1. THE Registry_Generator SHALL read V1_Hook definitions as its source of truth.
2. THE Registry_Generator SHALL emit 1.0 Trigger names and Action types in the generated event-flow descriptions.
3. THE Registry_Generator SHALL emit the full V1_Hook prompt text and 1.0 creation parameters in `hook-registry-critical.md` and the per-module `hook-registry-module-*.md` slices.
4. THE `hooks/hooks.lock.yaml` file SHALL record each hook identifier with its 1.0 Trigger name.
5. WHEN the Registry_Generator runs in `--verify` mode against the committed registry and lockfile, THE Registry_Generator SHALL exit with a success code.
6. THE Registry_Generator SHALL list exactly the migrated hook set, excluding the three Manual_Hooks.

### Requirement 8: Update the Prompt Composer for v1 Output

**User Story:** As a Power maintainer, I want the Module 3 gate-hook composer to emit v1 hooks, so that shared gate logic remains single-sourced and CI drift checks still pass.

#### Acceptance Criteria

1. THE Prompt_Composer SHALL compose the Module 3 gate hooks (`gate-module3-visualization`, `enforce-mandatory-gate`, `enforce-gate-on-stop`) as V1_Hooks.
2. THE Prompt_Composer SHALL preserve the shared fragment text defined in `scripts/hook_prompt_fragments.py` verbatim within the composed V1_Hook prompts.
3. WHEN the Prompt_Composer runs in `--write` mode, THE Prompt_Composer SHALL produce output byte-identical to the committed V1_Hook files.
4. WHEN the Prompt_Composer runs in `--verify` mode against the committed V1_Hook files, THE Prompt_Composer SHALL exit with a success code.
5. THE Prompt_Composer SHALL run before the Registry_Generator in the CI_Pipeline so fragment drift is reported before registry drift.

### Requirement 9: Update the Hook Installer for v1

**User Story:** As a bootcamper cloning the repository, I want the file-copy installer to install 1.0 hooks, so that copied hooks actually run under 1.0.

#### Acceptance Criteria

1. THE Hook_Installer SHALL discover and install all shipped V1_Hook definition files.
2. THE Hook_Installer SHALL install V1_Hook files into the bootcamper's `.kiro/hooks/` directory.
3. THE Hook_Installer SHALL derive each installable hook set from the shipped V1_Hook files rather than a hardcoded legacy filename list.
4. THE Hook_Installer SHALL exclude every Manual_Hook identifier from all install sets so no `userTriggered` hook is installed.
5. THE Hook_Installer SHALL define its critical and essential hook sets consistently with the migrated Hook_Categories, excluding `commonmark-validation` from the critical set.
6. WHEN the Hook_Installer completes, THE Hook_Installer SHALL report the actual number of installed V1_Hook files.

### Requirement 10: Update the Onboarding Hook-Creation Path for 1.0

**User Story:** As a bootcamper starting the bootcamp, I want onboarding to create 1.0-valid hooks, so that the guided experience is fully hooked up from the first session.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL create hooks that are schema-valid V1_Hooks in `.kiro/hooks/`.
2. THE Onboarding_Flow SHALL express hook-creation instructions using 1.0 Trigger, Matcher, and Action terminology sourced from the hook registry.
3. THE Onboarding_Flow SHALL create the capture-critical hooks `ask-bootcamper`, `module-recap-append`, and `session-log-events` as V1_Hooks during onboarding or session resume.
4. THE Onboarding_Flow SHALL remove `commonmark-validation` from the critical-hook creation list and the associated failure-impact messages.
5. WHERE the bootcamper needs the former manual hooks, THE Onboarding_Flow SHALL direct them to the corresponding Slash_Command_File instead of a `userTriggered` hook.
6. WHEN the Onboarding_Flow verifies hook presence at session start, THE Onboarding_Flow SHALL check for the V1_Hook definitions in `.kiro/hooks/`.

### Requirement 11: Update Documentation and Steering to v1

**User Story:** As a bootcamper reading the docs, I want the hook documentation to describe the 1.0 model, so that the instructions match what the IDE actually does.

#### Acceptance Criteria

1. THE `hooks/README.md` file SHALL describe the migrated hook set using 1.0 Trigger names and the migrated hook count.
2. THE `hooks/README.md` file SHALL describe installation using `.json` V1_Hook files rather than `*.kiro.hook` files.
3. THE `docs/guides/HOOKS_INSTALLATION_GUIDE.md` file SHALL describe the 1.0 hook-creation path with accurate hook counts and 1.0 Trigger names.
4. THE `steering/hook-architecture.md` file SHALL describe the `Stop`-trigger precedence and guard rules using 1.0 Trigger names.
5. THE Power SHALL update all steering references to hook triggers and actions to use 1.0 terminology.
6. IF a document or steering file references a removed Manual_Hook as an automatic hook, THEN THE Power SHALL update that reference to point to the corresponding Slash_Command_File.

### Requirement 12: Document Permissions and MCP Auto-Approve

**User Story:** As a bootcamper on 1.0, I want to know which permissions to approve, so that the capability prompts do not stall the guided bootcamp.

#### Acceptance Criteria

1. THE Permissions_Doc SHALL describe the write, shell, and MCP capabilities the bootcamp requests under the 1.0 permissions model.
2. THE Permissions_Doc SHALL describe the recommended approval scope for the file writes, Python script executions, and Senzing MCP tool calls the bootcamp performs.
3. THE MCP_Config SHALL list the read-only Senzing MCP tools used by the bootcamp in its `autoApprove` array so that read-only MCP calls do not stall.
4. THE MCP_Config SHALL keep `submit_feedback` in its `disabledTools` list.
5. THE MCP_Config SHALL remain the sole source of the Senzing MCP server URL.

### Requirement 13: Record the Back-Compatibility Decision and Version Bump

**User Story:** As a Power maintainer, I want the legacy back-compatibility decision recorded with a version bump, so that consumers know the minimum Kiro version and what changed.

#### Acceptance Criteria

1. THE Power SHALL remove the legacy `*.kiro.hook` files from `senzing-bootcamp/hooks/` so that only V1_Hook definitions ship.
2. THE `POWER.md` file SHALL state that the Power requires Kiro 1.0 or later.
3. THE `CHANGELOG.md` file SHALL record the 1.0 hook migration under a new released version section following the Keep a Changelog format.
4. THE `senzing-bootcamp/VERSION` file SHALL contain a new semantic version greater than `0.1.3`.
5. THE `POWER.md` frontmatter version SHALL equal the value in `senzing-bootcamp/VERSION`.

### Requirement 14: Keep CI Green Under Project Constraints

**User Story:** As a Power maintainer, I want the full CI pipeline to pass after migration, so that the migrated Power ships in a verified state.

#### Acceptance Criteria

1. WHEN the CI_Pipeline runs after migration, THE CI_Pipeline SHALL complete all validation and test gates with a success code.
2. THE Power SHALL implement all migration tooling changes using only the Python standard library, except where an existing documented exception already applies.
3. THE Power SHALL provide tests that verify V1_Hook schema validity, glob-to-regex Matcher equivalence, and registry generation round-trip.
4. THE Power SHALL keep the shipped hook definitions, Hook_Categories, registry files, and lockfile mutually consistent so the `--verify` gates pass.
5. IF any migrated hook file, config, steering file, or document still references the legacy schema after migration, THEN a CI_Pipeline gate SHALL fail and identify the stale reference.
