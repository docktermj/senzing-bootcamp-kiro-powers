# Requirements Document

## Introduction

Three related UX improvements to the Senzing Bootcamp Power's steering files enhance the bootcamp experience. After Module 1 completes, the agent should offer a visualization/exploration prompt before entering the journal workflow. Module starts should display bold, prominent banners matching the onboarding welcome banner style. The journey map shown at module start should use a consistent tabular format for scannability.

## Glossary

- **Module_Steering_File**: A per-module steering file that defines the workflow for a specific bootcamp module
- **Module_Transitions_Steering**: The `module-transitions.md` steering file containing the module start banner template, journey map format, and before/after framing instructions
- **Module_Completion_Steering**: The `module-completion.md` steering file for post-module journal entries, reflection, and next-step options
- **Module_Start_Banner**: A formatted ASCII banner displayed at the beginning of each module to orient the user
- **Journey_Map**: A table showing completed, current, and upcoming modules displayed at module start
- **Before_After_Framing**: A summary presented at module start showing what the user has now and what they will have when the module is complete

## Requirements

### Requirement 1: Post-Module 1 Visualization Offer

**User Story:** As a bootcamper completing Module 1, I want to be offered a visualization of the demo results before the module closes, so that I can explore the entity resolution output interactively.

#### Acceptance Criteria

1. WHEN Module 1 completes, THE agent SHALL offer visualization ("Would you like me to create a web page showing these results?") with interactive feature options before entering the Module_Completion_Steering workflow.
2. THE visualization offer SHALL be a distinct numbered step in the Module 1 steering file, sequenced after the results explanation and before the module close step.
3. THE visualization step SHALL include an instruction that it must complete before closing the module.

### Requirement 2: Enhanced Explore Option for Module 1

**User Story:** As a bootcamper who completed Module 1, I want the post-module "Explore" option to explicitly mention visualization and interactive exploration, so that I know these options are available.

#### Acceptance Criteria

1. WHEN Module 1 completes and the agent presents next-step options, THE "Explore" option SHALL explicitly mention visualization, entity examination, and attribute search.
2. THE Module_Completion_Steering SHALL include a Module 1 special-case note indicating that the visualization offer should have been presented before reaching the completion workflow.

### Requirement 3: Bold Module Start Banners

**User Story:** As a bootcamper starting any module, I want to see a prominent visual banner matching the onboarding welcome banner style, so that module transitions feel polished and I can immediately identify which module I'm entering.

#### Acceptance Criteria

1. WHEN any module begins, THE agent SHALL display a Module_Start_Banner using bordered text with 🚀 emojis in the format: `━━━ 🚀🚀🚀 MODULE N: [NAME IN CAPS] 🚀🚀🚀 ━━━`.
2. THE Module_Start_Banner SHALL appear before the Journey_Map and Before_After_Framing.
3. THE Module_Transitions_Steering SHALL contain an explicit banner template with instructions to display it at every module start.

### Requirement 4: Tabular Journey Map Format

**User Story:** As a bootcamper, I want the journey map at module start to be displayed as a structured table, so that I can quickly scan my progress across modules.

#### Acceptance Criteria

1. WHEN any module begins and the journey map is displayed, THE agent SHALL render it as a markdown table with Module, Name, and Status columns.
2. THE Journey_Map SHALL use ✅ for completed modules, 🔄 (with → prefix on the module number) for the current module, and ⬜ for upcoming modules.
3. THE Journey_Map SHALL only show modules in the user's selected path.

### Requirement 5: Preserve Existing UX Behaviors

**User Story:** As a bootcamp maintainer, I want the UX improvements to leave all other steering file behaviors intact, so that no existing workflows are disrupted.

#### Acceptance Criteria

1. THE onboarding welcome banner in `onboarding-flow.md` SHALL continue to use 🎓 emojis and "WELCOME TO THE SENZING BOOTCAMP!" text exactly as-is.
2. THE Module_Completion_Steering journal entry, reflection question, and next-step options workflow SHALL continue to execute in its current order.
3. THE step-level Before/During/After progress updates in Module_Transitions_Steering SHALL remain unchanged.
4. THE Module 1 explicit close statement, purpose summary, and Module 2 transition with use-case discovery questions SHALL remain intact.
5. Modules other than Module 1 SHALL NOT receive Module-1-specific visualization prompts in their next-step options.
