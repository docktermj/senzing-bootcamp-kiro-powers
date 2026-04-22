# Requirements Document

## Introduction

This spec retroactively documents the bootcamp onboarding experience — the guided sequence that takes a new user from zero to a configured, path-selected bootcamp session. The onboarding flow lives in `senzing-bootcamp/steering/onboarding-flow.md` with supporting communication rules in `senzing-bootcamp/steering/agent-instructions.md`.

## Glossary

- **Onboarding_Flow**: The sequential process (directory creation → language selection → prerequisite checks → welcome banner → introduction → path selection) that initializes a new bootcamp session.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Validation_Gate**: A prerequisite check that must pass before the Bootcamper can proceed to the next module.
- **Steering_File**: A markdown file with YAML frontmatter that provides runtime instructions to the Agent.
- **Goldilocks_Check**: A periodic detail-level calibration question asked every 3 modules.
- **WAIT_Marker**: An instruction in the steering file that forces the Agent to stop and wait for Bootcamper input before continuing.

## Requirements

### Requirement 1: Guided Onboarding Sequence

**User Story:** As a Bootcamper, I want a structured onboarding sequence that sets up my environment and introduces the bootcamp, so that I can start learning without manual configuration.

#### Acceptance Criteria

1. WHEN a new bootcamp session starts, THE Onboarding_Flow SHALL execute steps in this order: setup preamble, directory creation, language selection, prerequisite checks, welcome banner, bootcamp introduction, path selection.
2. WHEN the setup preamble is displayed, THE Agent SHALL inform the Bootcamper that administrative setup is happening and that a WELCOME banner will signal when the bootcamp officially starts.
3. WHEN directory creation runs, THE Onboarding_Flow SHALL create the project directory structure, install hooks, copy the glossary, and generate foundational Steering_Files (product.md, tech.md, structure.md) at `.kiro/steering/`.
4. WHEN the welcome banner is displayed, THE Agent SHALL render a banner containing 🎓 emojis and the text "WELCOME TO THE SENZING BOOTCAMP" using a visually prominent format.

### Requirement 2: One-Question-at-a-Time Interaction

**User Story:** As a Bootcamper, I want the agent to ask me one question at a time and wait for my response, so that I am not overwhelmed by multiple prompts.

#### Acceptance Criteria

1. THE Agent SHALL present only one question per message during the Onboarding_Flow and mark each question with a WAIT_Marker in the steering file.
2. WHEN a question requires Bootcamper input, THE Agent SHALL prefix the question with a 👉 input-required marker so the Bootcamper can distinguish questions from informational statements.
3. THE Agent SHALL NOT combine language selection, introduction, and path selection into a single message.

### Requirement 3: MCP-Driven Language Selection and Prerequisite Checks

**User Story:** As a Bootcamper, I want language options sourced from the Senzing MCP server and validated against my platform, so that I only see supported choices.

#### Acceptance Criteria

1. WHEN language selection begins, THE Agent SHALL detect the Bootcamper's platform and query the Senzing MCP server for supported languages on that platform.
2. IF the MCP server flags a language as discouraged or unsupported on the detected platform, THEN THE Agent SHALL relay the warning and suggest alternatives.
3. WHEN prerequisite checks run, THE Onboarding_Flow SHALL verify the language runtime and Senzing SDK availability and present results only when something is missing.
4. WHEN the Senzing SDK is already installed at version 4.0 or higher, THE Agent SHALL inform the Bootcamper that the SDK is already installed and skip re-installation at Module 0.

### Requirement 4: Path Selection with Validation Gates

**User Story:** As a Bootcamper, I want to choose a learning path (A/B/C/D) that matches my experience level, so that I can skip modules I do not need.

#### Acceptance Criteria

1. WHEN the introduction is acknowledged, THE Agent SHALL present four paths: A (Quick Demo: 0→1), B (Fast Track: 5→6→8), C (Complete Beginner: 2→3→4→5→6→8), D (Full Production: 0–12).
2. WHEN a Bootcamper selects a path, THE Onboarding_Flow SHALL persist the selection to `config/bootcamp_preferences.yaml` and automatically insert Module 0 before any module requiring the SDK.
3. WHEN a module boundary is reached, THE Validation_Gate SHALL run `validate_module.py --module N` and block progression until the gate criteria pass.

### Requirement 5: Adaptive Detail and First-Term Explanations

**User Story:** As a Bootcamper, I want the agent to calibrate its detail level to my preference and explain unfamiliar terms on first use, so that the experience matches my learning style.

#### Acceptance Criteria

1. WHEN Modules 3, 6, or 9 are completed, THE Agent SHALL ask a Goldilocks_Check: "is the level of detail too much, too little, or just right?" and persist the response to `config/bootcamp_preferences.yaml` as `detail_level`.
2. WHEN a Senzing-specific term appears for the first time in conversation, THE Agent SHALL define the term inline in one sentence and reference `docs/guides/GLOSSARY.md`.
3. THE Agent SHALL NOT re-explain a Senzing-specific term after its first inline definition.
