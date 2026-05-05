# Requirements Document

## Introduction

This spec is the canonical description of the senzing-bootcamp Kiro Power — a guided 11-module bootcamp for learning Senzing entity resolution. It supersedes all older per-feature specs that reference stale module numbering (0–12) or outdated track definitions.

The power is installed into Kiro IDE and connects to the Senzing MCP server (`mcp.senzing.com`) for interactive, tool-assisted workflows. It produces working code artifacts in the bootcamper's chosen language (Python, Java, C#, Rust, or TypeScript).

## Glossary

- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Module**: One of 11 sequential learning units (Modules 1–11).
- **Track**: A predefined subset of modules matching a learning goal (A, B, C, or D).
- **Phase**: A subdivision of a large module into smaller context-efficient chunks.
- **Steering_File**: A markdown file with YAML frontmatter providing runtime instructions to the Agent.
- **Hook**: A JSON-defined automation that fires on IDE events (file edits, agent stops, tool use).
- **MCP_Server**: The Senzing Model Context Protocol server providing SDK code generation, documentation, and data mapping tools.
- **Gate**: A validation checkpoint between modules that blocks progression until criteria are met.
- **Progress_File**: `config/bootcamp_progress.json` — tracks current module, completed modules, step history, and skipped steps.
- **Preferences_File**: `config/bootcamp_preferences.yaml` — stores language, verbosity, cloud provider, hooks installed, and other user choices.

## Requirements

### Requirement 1: 11-Module Curriculum

**User Story:** As a Bootcamper, I want a structured curriculum that takes me from defining a business problem through production deployment, so that I learn Senzing entity resolution end-to-end.

#### Acceptance Criteria

1. THE Power SHALL provide exactly 11 modules numbered 1–11:
   - Module 1: Business Problem
   - Module 2: SDK Setup
   - Module 3: Quick Demo
   - Module 4: Data Collection
   - Module 5: Data Quality & Mapping
   - Module 6: Load Data
   - Module 7: Query & Visualize
   - Module 8: Performance Testing
   - Module 9: Security Hardening
   - Module 10: Monitoring & Observability
   - Module 11: Package & Deploy
2. EACH module SHALL have a root steering file (`module-NN-*.md`) with `inclusion: manual`.
3. MODULES with more than ~120 lines SHALL be split into phases with separate phase files referenced from the root.
4. THE following modules SHALL be phase-split:
   - Module 1: 2 phases (discovery, document-confirm)
   - Module 5: 3 phases (quality-assessment, data-mapping, test-load-validate)
   - Module 6: 4 phases (build-loading, load-first-source, multi-source, validation)
   - Module 8: 3 phases (requirements, benchmarking, optimization)
   - Module 9: 2 phases (assessment, hardening)
   - Module 10: 2 phases (setup, operations)
   - Module 11: 2 phases (packaging, deploy)

### Requirement 2: Four Learning Tracks

**User Story:** As a Bootcamper, I want to choose a track matching my experience level, so that I can skip modules I don't need.

#### Acceptance Criteria

1. THE Power SHALL offer four tracks:
   - A (Quick Demo): Modules 1 → 2 → 3
   - B (Fast Track): Modules 5 → 6 → 7 (Module 2 auto-inserted)
   - C (Complete Beginner): Modules 1 → 4 → 5 → 6 → 7
   - D (Full Production): All modules 1–11
2. Module 2 (SDK Setup) SHALL be auto-inserted before any module requiring the SDK.
3. ALL completed modules SHALL carry forward when switching tracks.
4. THE module dependency graph SHALL be defined in `config/module-dependencies.yaml`.

### Requirement 3: Language-Agnostic Code Generation

**User Story:** As a Bootcamper, I want to work in my preferred programming language, so that the bootcamp produces code I can use in production.

#### Acceptance Criteria

1. THE Power SHALL support Python, Java, C#, Rust, and TypeScript/Node.js.
2. ALL code SHALL be generated dynamically by the Senzing MCP server via `generate_scaffold` — no static code templates shipped.
3. THE Agent SHALL query the MCP server for supported languages on the bootcamper's platform during onboarding and relay any platform-specific warnings.
4. FIVE language steering files SHALL load conditionally via `fileMatch` on the corresponding file extension.
5. THE Bootcamper SHALL be able to change languages mid-bootcamp with a warning that existing code must be regenerated.

### Requirement 4: Cross-Platform Support

**User Story:** As a Bootcamper, I want the power to work on Linux, macOS, and Windows, so that I can use my preferred operating system.

#### Acceptance Criteria

1. ALL scripts SHALL use stdlib-only Python and `pathlib` for cross-platform path handling.
2. THE `preflight.py` script SHALL detect the OS and perform platform-appropriate checks (Windows: VS Build Tools, `npm.cmd`; macOS: `brew` suggestions; Linux: `apt` suggestions).
3. THE `common-pitfalls.md` steering file SHALL include a Windows-Specific Pitfalls section.
4. HOOK prompts SHALL include both Linux/macOS and Windows command variants where applicable.

### Requirement 5: MCP-First Information Policy

**User Story:** As a Bootcamper, I want all Senzing information to come from the authoritative MCP server, so that I get accurate, current information.

#### Acceptance Criteria

1. THE Agent SHALL source ALL Senzing facts from MCP tools — never from training data.
2. THE Agent SHALL call `get_capabilities` at the start of each session.
3. THE Agent SHALL use the correct MCP tool for each purpose: `mapping_workflow` for attribute names, `generate_scaffold`/`sdk_guide` for SDK code, `get_sdk_reference` for signatures, `explain_error_code` for errors, `search_docs` for docs, `find_examples` for examples.
4. IF the MCP server is unavailable, THE Agent SHALL retry once, then load `mcp-offline-fallback.md` for guidance on what's blocked vs. continuable.
5. THE Agent SHALL never fabricate Senzing information.

### Requirement 6: Context Budget Management

**User Story:** As a Bootcamper, I want the agent to manage its context window efficiently, so that it remains effective throughout long sessions.

#### Acceptance Criteria

1. THE `steering-index.yaml` SHALL track `token_count` and `size_category` for every steering file.
2. ALWAYS-on steering files SHALL total no more than 3 files, each under 80 lines.
3. AUTO-included files SHALL be under 120 lines each.
4. THE Agent SHALL warn at 60% context usage (120k tokens) and enter critical mode at 80% (160k tokens).
5. RETENTION priority SHALL be: agent-instructions > current module > language file > troubleshooting > everything else.
6. PHASE-split modules SHALL allow loading only the current phase rather than the entire module.

### Requirement 7: Hook-Based Automation

**User Story:** As a Bootcamper, I want automated checks and reminders that fire without relying on the agent's memory, so that quality standards are enforced consistently.

#### Acceptance Criteria

1. THE Power SHALL provide 25 hooks organized into critical (created during onboarding) and module-specific (created when the module starts) categories.
2. CRITICAL hooks SHALL include: ask-bootcamper, capture-feedback, feedback-submission-reminder, review-bootcamper-input, code-style-check, commonmark-validation, enforce-feedback-path, enforce-working-directory, verify-senzing-facts.
3. MODULE hooks SHALL cover: Module 2 (verify-sdk-setup), Module 4 (validate-data-files), Module 5 (analyze-after-mapping, data-quality-check, enforce-mapping-spec), Module 6 (backup-before-load, run-tests-after-change, verify-generated-code), Module 7 (enforce-visualization-offers, offer-visualization), Module 8 (validate-benchmark-results), Module 9 (security-scan-on-save), Module 10 (validate-alert-config), Module 11 (deployment-phase-gate).
4. ANY-TIME hooks SHALL include: backup-project-on-request, git-commit-reminder.
5. THE hook registry (`hook-categories.yaml` and `hook-registry.md`) SHALL stay in sync with `.kiro.hook` files — verified by `sync_hook_registry.py --verify`.

### Requirement 8: Onboarding Flow

**User Story:** As a new Bootcamper, I want a guided setup that configures my environment and introduces the bootcamp before I choose a track.

#### Acceptance Criteria

1. THE onboarding sequence SHALL be: setup preamble → directory creation + hook installation → team detection → language selection (⛔ gate) → prerequisite check → welcome banner + introduction → verbosity preference → comprehension check → track selection (⛔ gate).
2. THE Agent SHALL generate foundational steering files (`product.md`, `tech.md`, `structure.md`) in `.kiro/steering/` during onboarding.
3. THE Agent SHALL run `preflight.py` for environment verification.
4. THE Agent SHALL present a welcome banner with 🎓 emojis signaling the bootcamp has officially started.

### Requirement 9: State Management and Progress Tracking

**User Story:** As a Bootcamper, I want my progress saved between sessions, so that I can resume where I left off.

#### Acceptance Criteria

1. THE Agent SHALL maintain `config/bootcamp_progress.json` with: current_module, modules_completed, current_step, step_history, and skipped_steps.
2. THE Agent SHALL checkpoint after each numbered step or sub-step.
3. ON session start with existing progress, THE Agent SHALL load `session-resume.md` instead of `onboarding-flow.md`.
4. THE `validate_module.py` script SHALL validate completion criteria for all 11 modules.
5. THE `repair_progress.py` script SHALL reconstruct progress from project artifacts when state is corrupted.

### Requirement 10: Communication Protocol

**User Story:** As a Bootcamper, I want clear, one-question-at-a-time interaction with the agent, so that I'm never overwhelmed.

#### Acceptance Criteria

1. THE Agent SHALL ask one question at a time, prefixed with 👉, and STOP.
2. THE Agent SHALL never fabricate user input or assume choices at ⛔ gates.
3. THE Agent SHALL write `config/.question_pending` when asking a 👉 question and delete it when processing the next message.
4. THE Agent SHALL never end a turn with only an acknowledgment — every turn must advance the conversation.
5. AT module transitions, THE Agent SHALL immediately begin the next module when the bootcamper responds affirmatively.

### Requirement 11: Validation and CI

**User Story:** As a power maintainer, I want automated validation that catches regressions before they ship.

#### Acceptance Criteria

1. THE CI pipeline SHALL run: `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest.
2. THE test suite SHALL include property-based tests (Hypothesis) for scripts and unit tests for steering structure.
3. THE `validate_module.py` script SHALL check meaningful artifacts for all 11 modules (not just file existence for later modules).

### Requirement 12: Skip Step Protocol

**User Story:** As a Bootcamper, I want to skip steps that don't apply to me without breaking the bootcamp flow.

#### Acceptance Criteria

1. THE Agent SHALL recognize skip trigger phrases ("skip this step", "I'm stuck", "not relevant", etc.).
2. THE Agent SHALL record skipped steps in `config/bootcamp_progress.json` with reason and timestamp.
3. THE Agent SHALL assess downstream consequences before allowing a skip.
4. MANDATORY gates (⛔) SHALL NOT be skippable.
5. THE Bootcamper SHALL be able to revisit skipped steps later.

### Requirement 13: Deployment Platform Support

**User Story:** As a Bootcamper deploying to production, I want platform-specific guidance for my target environment.

#### Acceptance Criteria

1. THE Power SHALL provide deployment steering files for: AWS, Azure, GCP, Kubernetes, and on-premises.
2. THE Agent SHALL load the appropriate deployment file based on `deployment_target` in preferences during Module 11.
3. THE AWS deployment file SHALL cover ECS/Fargate, RDS, Secrets Manager, CloudWatch, IAM, and cost optimization.
