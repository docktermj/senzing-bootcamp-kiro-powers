# Requirements Document

## Introduction

When the Senzing Bootcamp power is installed via Kiro's power system, only `steering/`, `mcp.json`, and `POWER.md` are distributed to `~/.kiro/powers/installed/senzing-bootcamp/`. The `hooks/` directory is not included. This means the onboarding step that copies `senzing-bootcamp/hooks/*.kiro.hook` to `.kiro/hooks/` silently fails — no hook files exist to copy. All 18 hooks (feedback capture, enforcement, quality checks, visualization offers, etc.) are unavailable to bootcampers.

The fix: embed hook definitions directly in the distributed steering files and have the agent create hooks programmatically using Kiro's `createHook` tool during onboarding, instead of copying files that may not exist in the installed power.

## Glossary

- **Agent**: The Kiro AI agent that runs the bootcamp, loads steering files, and executes tool calls
- **Onboarding_Flow**: The steering file (`onboarding-flow.md`) that defines the setup sequence when a bootcamper starts fresh
- **Agent_Instructions**: The always-loaded steering file (`agent-instructions.md`) that defines core agent rules
- **Hook**: A Kiro automation that fires on IDE events (file edits, prompt submissions, agent stops, etc.) and triggers agent actions
- **createHook_Tool**: Kiro's built-in tool for programmatically creating hooks — accepts name, description, event type, action type, prompt, file patterns, and tool types as parameters
- **Critical_Hook**: A hook that must be created during onboarding for core bootcamp functionality (feedback capture, path enforcement, working directory enforcement)
- **Module_Hook**: A hook that supports a specific bootcamp module and can be created when that module starts
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that is distributed with the power and loaded by the agent at runtime
- **Hook_Registry**: The embedded section within a steering file that contains all hook definitions with their createHook parameters
- **Hooks_Installation_Guide**: The user-facing document (`docs/guides/HOOKS_INSTALLATION_GUIDE.md`) that explains hook installation to bootcampers
- **Power_Distribution**: The set of files included when a power is installed via Kiro's power system (currently: `steering/`, `mcp.json`, `POWER.md`)

## Requirements

### Requirement 1: Embed Hook Definitions in Steering Files

**User Story:** As a bootcamp agent, I want hook definitions embedded in the steering files I can access, so that I can create hooks programmatically without depending on source files that may not exist in the power distribution.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL contain a Hook_Registry section that defines each hook using createHook_Tool parameters: id, name, description, eventType, hookAction, outputPrompt, filePatterns, toolTypes, and timeout
2. WHEN the Agent loads the Onboarding_Flow, THE Hook_Registry SHALL provide all 18 hook definitions with complete parameter values ready for createHook_Tool invocation
3. THE Hook_Registry SHALL organize hooks into two groups: Critical_Hooks (created during onboarding) and Module_Hooks (created when the relevant module starts)
4. THE Hook_Registry SHALL specify each hook's createHook_Tool parameters in a structured format that the Agent can read and pass directly to the createHook_Tool

### Requirement 2: Create Critical Hooks During Onboarding

**User Story:** As a bootcamper, I want essential hooks installed automatically during onboarding, so that feedback capture, path enforcement, and working directory enforcement work from the start.

#### Acceptance Criteria

1. WHEN the Agent executes onboarding setup (Step 1 of Onboarding_Flow), THE Agent SHALL create Critical_Hooks using the createHook_Tool instead of copying hook files
2. THE Onboarding_Flow SHALL classify the following hooks as Critical_Hooks: capture-feedback, enforce-feedback-path, enforce-working-directory, verify-senzing-facts, code-style-check, summarize-on-stop, and commonmark-validation
3. WHEN the Agent creates a Critical_Hook, THE Agent SHALL use the createHook_Tool with the exact parameters defined in the Hook_Registry
4. THE Onboarding_Flow SHALL instruct the Agent to create all Critical_Hooks before displaying the welcome banner (Step 4)

### Requirement 3: Create Module-Specific Hooks on Module Start

**User Story:** As a bootcamper, I want module-specific hooks activated when I start the relevant module, so that hooks with module-specific file patterns only fire when those files exist.

#### Acceptance Criteria

1. THE Hook_Registry SHALL classify the following hooks as Module_Hooks with their associated modules: data-quality-check (Module 5), validate-senzing-json (Module 5), analyze-after-mapping (Module 5), backup-before-load (Module 6), run-tests-after-change (Module 6), verify-generated-code (Module 6), offer-visualization (Module 8), enforce-visualization-offers (Module 8), module12-phase-gate (Module 12), backup-project-on-request (any module), and git-commit-reminder (any module)
2. WHEN the Agent starts a module that has associated Module_Hooks, THE Agent SHALL create those Module_Hooks using the createHook_Tool if the hooks do not already exist in `.kiro/hooks/`
3. THE Agent_Instructions SHALL include a directive for the Agent to check the Hook_Registry and create Module_Hooks at each module start

### Requirement 4: Fallback Behavior for createHook Failures

**User Story:** As a bootcamper, I want the onboarding to continue even if a hook fails to create, so that a single hook failure does not block the entire bootcamp setup.

#### Acceptance Criteria

1. IF the createHook_Tool fails to create a Critical_Hook, THEN THE Agent SHALL log the failure, continue creating the remaining hooks, and report all failures to the bootcamper after the hook creation step completes
2. IF the createHook_Tool fails to create a Critical_Hook, THEN THE Agent SHALL inform the bootcamper which hooks failed and what functionality is affected (e.g., "The capture-feedback hook could not be created — feedback trigger phrases will not be automatically detected")
3. IF the createHook_Tool fails to create a Module_Hook, THEN THE Agent SHALL log the failure and continue with the module without blocking progress
4. IF all Critical_Hook creation attempts fail, THEN THE Agent SHALL warn the bootcamper that hooks are unavailable and suggest restarting the onboarding or manually creating hooks later

### Requirement 5: Verify Hook Creation Success

**User Story:** As a bootcamp agent, I want to verify that hooks were created successfully, so that I can confirm the bootcamper's environment is properly configured.

#### Acceptance Criteria

1. WHEN the Agent finishes creating Critical_Hooks during onboarding, THE Agent SHALL verify that each hook exists in `.kiro/hooks/` by checking for the expected hook files
2. IF a hook file is missing after creation, THEN THE Agent SHALL retry creation once using the createHook_Tool before reporting failure
3. WHEN all Critical_Hooks are verified, THE Agent SHALL record the hook installation status in `config/bootcamp_preferences.yaml` with a list of installed hook names and a timestamp
4. WHEN the Agent resumes a session (via session-resume.md), THE Agent SHALL check `config/bootcamp_preferences.yaml` for hook installation status and skip hook creation if hooks are already recorded as installed

### Requirement 6: Update Onboarding Flow to Replace File Copying

**User Story:** As a bootcamp maintainer, I want the onboarding flow to use createHook instead of file copying, so that hooks work regardless of how the power is distributed.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL replace the instruction "Install hooks: copy `senzing-bootcamp/hooks/*.kiro.hook` to `.kiro/hooks/`" with an instruction to create hooks using the createHook_Tool and the embedded Hook_Registry
2. THE Onboarding_Flow SHALL instruct the Agent to create the `.kiro/hooks/` directory if it does not exist before creating hooks
3. THE Onboarding_Flow SHALL retain the existing setup step ordering: directory creation, hook creation, glossary copy, steering file generation

### Requirement 7: Update Agent Instructions for Hook Management

**User Story:** As a bootcamp maintainer, I want agent-instructions.md to reference the new hook creation approach, so that the agent knows to use createHook instead of file copying in all contexts.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL replace the directive "Install to `.kiro/hooks/` from `senzing-bootcamp/hooks/`" with a directive to create hooks using the createHook_Tool and the Hook_Registry embedded in the Onboarding_Flow
2. THE Agent_Instructions SHALL instruct the Agent to create Module_Hooks at module start by referencing the Hook_Registry in the Onboarding_Flow
3. THE Agent_Instructions SHALL retain the directive that the capture-feedback hook is critical and must be verified as installed

### Requirement 8: Update Hooks Installation Guide

**User Story:** As a bootcamper, I want the hooks installation guide to reflect the current installation method, so that manual reinstallation instructions are accurate.

#### Acceptance Criteria

1. THE Hooks_Installation_Guide SHALL state that hooks are created automatically during onboarding using the createHook_Tool
2. THE Hooks_Installation_Guide SHALL provide a manual reinstallation method: "Ask the agent: Please recreate the bootcamp hooks"
3. THE Hooks_Installation_Guide SHALL remove references to copying files from `senzing-bootcamp/hooks/` since that directory may not exist in the installed power
4. THE Hooks_Installation_Guide SHALL remove references to `scripts/install_hooks.py` since that script may not exist in the installed power
5. THE Hooks_Installation_Guide SHALL update the hook count from 11 to 18 to reflect all available hooks

### Requirement 9: Update Hooks README for Consistency

**User Story:** As a bootcamp maintainer, I want the hooks README to document the createHook-based installation as the primary method, so that all documentation is consistent.

#### Acceptance Criteria

1. THE hooks README (`senzing-bootcamp/hooks/README.md`) SHALL document the createHook_Tool-based installation as the primary installation method
2. THE hooks README SHALL retain file-copying instructions as a secondary method for development environments where the hooks directory is available
3. THE hooks README SHALL remove the `scripts/install_hooks.py` reference from the recommended installation method since the script may not be distributed

### Requirement 10: Preserve Hook Definitions in Source Repository

**User Story:** As a bootcamp maintainer, I want the `.kiro.hook` JSON files retained in the source repository, so that they serve as the canonical definitions and can be used in development environments.

#### Acceptance Criteria

1. THE source repository SHALL retain all 18 `.kiro.hook` files in `senzing-bootcamp/hooks/` as canonical hook definitions
2. WHEN a hook definition is updated in a `.kiro.hook` file, THE corresponding entry in the Hook_Registry in the Onboarding_Flow SHALL be updated to match
3. THE hooks README SHALL note that the `.kiro.hook` files are the canonical source and the Hook_Registry in the Onboarding_Flow must be kept in sync
