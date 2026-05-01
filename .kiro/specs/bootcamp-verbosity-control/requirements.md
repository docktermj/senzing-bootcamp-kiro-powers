# Requirements Document

## Introduction

The senzing-bootcamp power currently delivers output at a single, fixed verbosity level. Every bootcamper receives the same depth of explanation, code walkthrough, recap, and technical detail regardless of their experience level or learning preferences. There is no mechanism for a bootcamper to say "give me more detail here" or "skip the recap, I got it."

This feature introduces a verbosity control system that lets the bootcamper choose how much output they see across categorized output types. The initial preference is captured during onboarding, but the bootcamper can adjust it at any time — either by selecting a named preset or by using natural language to fine-tune specific categories (e.g., "I want more code walkthroughs" or "less recap"). Because the bootcamp is a learning exercise, the system is biased toward helping the bootcamper build a mental model of what is happening and why, with structured framing around every code execution step.

## Glossary

- **Verbosity_Preferences**: The section within `config/bootcamp_preferences.yaml` (or `config/preferences_{member_id}.yaml` in co-located team mode) that stores the bootcamper's current verbosity settings, including the active preset and per-category level overrides.
- **Output_Category**: A named classification of bootcamp output content. The defined categories are: `explanations` (conceptual "what and why" context), `code_walkthroughs` (line-by-line or block-by-block code explanations), `step_recaps` (summaries of what a step accomplished and what changed), `technical_details` (SDK internals, configuration specifics, performance notes), and `code_execution_framing` (before/during/after framing around code runs).
- **Verbosity_Preset**: A named collection of per-category verbosity levels. The defined presets are: `concise` (minimal output, experienced users), `standard` (balanced output, default), and `detailed` (maximum output, deep learners).
- **Category_Level**: An integer from 1 to 3 representing the verbosity for a single Output_Category, where 1 is minimal, 2 is moderate, and 3 is full detail.
- **Verbosity_Steering**: The steering file at `senzing-bootcamp/steering/verbosity-control.md` that instructs the agent how to apply verbosity settings when generating output.
- **Onboarding_Flow**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that guides the initial bootcamp setup, including the verbosity preference question.
- **Bootcamper**: The user participating in the Senzing bootcamp learning exercise.
- **Agent**: The Kiro-powered assistant that delivers the bootcamp content, reads steering files, and generates output for the Bootcamper.

## Requirements

### Requirement 1: Output Category Definitions

**User Story:** As a bootcamper, I want the types of output I receive to be organized into clear categories, so that I can control the verbosity of each type independently.

#### Acceptance Criteria

1. THE Verbosity_Steering SHALL define the following Output_Categories: `explanations`, `code_walkthroughs`, `step_recaps`, `technical_details`, and `code_execution_framing`.
2. THE Verbosity_Steering SHALL describe each Output_Category with a definition and examples of what content falls under that category.
3. WHEN the Agent generates output, THE Agent SHALL classify each section of output into exactly one Output_Category before applying verbosity rules.
4. THE Verbosity_Steering SHALL specify, for each Output_Category at each Category_Level (1, 2, 3), what content to include and what content to omit.

### Requirement 2: Verbosity Presets

**User Story:** As a bootcamper, I want to choose from named verbosity presets so that I can quickly set an overall verbosity level without configuring each category individually.

#### Acceptance Criteria

1. THE Verbosity_Steering SHALL define three Verbosity_Presets: `concise`, `standard`, and `detailed`.
2. THE `concise` preset SHALL set `explanations` to 1, `code_walkthroughs` to 1, `step_recaps` to 2, `technical_details` to 1, and `code_execution_framing` to 1.
3. THE `standard` preset SHALL set `explanations` to 2, `code_walkthroughs` to 2, `step_recaps` to 2, `technical_details` to 2, and `code_execution_framing` to 2.
4. THE `detailed` preset SHALL set `explanations` to 3, `code_walkthroughs` to 3, `step_recaps` to 3, `technical_details` to 3, and `code_execution_framing` to 3.
5. WHEN a Bootcamper selects a Verbosity_Preset, THE Agent SHALL update the Verbosity_Preferences in the preferences file with the preset name and the corresponding per-category levels.

### Requirement 3: Onboarding Verbosity Question

**User Story:** As a bootcamper starting the bootcamp, I want to be asked my preferred verbosity level during onboarding, so that the bootcamp output matches my learning style from the beginning.

#### Acceptance Criteria

1. WHEN the Onboarding_Flow reaches the introduction step (Step 4), THE Agent SHALL present the verbosity preset options (`concise`, `standard`, `detailed`) with a one-line description of each.
2. THE Agent SHALL present the `standard` preset as the recommended default.
3. WHEN the Bootcamper selects a preset, THE Agent SHALL persist the selection to the Verbosity_Preferences section of the preferences file.
4. WHEN the Bootcamper selects a preset, THE Agent SHALL inform the Bootcamper how to change the verbosity level later by stating: "You can change your verbosity level at any time by saying 'change verbosity' or by fine-tuning specific categories like 'I want more code walkthroughs'."
5. IF the Bootcamper does not select a preset and proceeds without answering, THEN THE Agent SHALL apply the `standard` preset as the default and inform the Bootcamper of this choice.

### Requirement 4: Runtime Verbosity Adjustment

**User Story:** As a bootcamper, I want to change my verbosity level at any point during the bootcamp, so that I can adapt the output to my evolving needs as I learn.

#### Acceptance Criteria

1. WHEN the Bootcamper requests a verbosity change (e.g., "change verbosity", "adjust verbosity", "set verbosity to detailed"), THE Agent SHALL present the available Verbosity_Presets and allow the Bootcamper to select one.
2. WHEN the Bootcamper selects a new Verbosity_Preset, THE Agent SHALL update the Verbosity_Preferences in the preferences file and confirm the change.
3. WHEN the Bootcamper changes verbosity, THE Agent SHALL apply the new settings starting from the next output the Agent generates.
4. THE Agent SHALL inform the Bootcamper of the change by summarizing the new per-category levels.

### Requirement 5: Natural Language Category Adjustment

**User Story:** As a bootcamper, I want to fine-tune specific output categories using natural language (e.g., "I want more code walkthroughs" or "less technical detail"), so that I can customize the output without memorizing category names or numeric levels.

#### Acceptance Criteria

1. WHEN the Bootcamper uses a phrase matching the pattern "more [category-related term]" or "I want more of [description]", THE Agent SHALL identify the matching Output_Category and increase its Category_Level by 1, up to a maximum of 3.
2. WHEN the Bootcamper uses a phrase matching the pattern "less [category-related term]" or "I want less of [description]", THE Agent SHALL identify the matching Output_Category and decrease its Category_Level by 1, down to a minimum of 1.
3. THE Verbosity_Steering SHALL define a mapping of common natural language terms to Output_Categories (e.g., "explanations" and "context" map to `explanations`; "code detail" and "code walkthrough" map to `code_walkthroughs`; "recaps" and "summaries" map to `step_recaps`; "technical" and "internals" map to `technical_details`; "before and after" and "execution framing" map to `code_execution_framing`).
4. WHEN a natural language adjustment changes a Category_Level, THE Agent SHALL update the Verbosity_Preferences in the preferences file and confirm the change by stating the category name and its new level.
5. WHEN a natural language adjustment is made, THE Agent SHALL change the active preset name to `custom` in the Verbosity_Preferences to indicate the settings no longer match a named preset.
6. IF the Bootcamper's natural language request does not match any Output_Category, THEN THE Agent SHALL list the available Output_Categories with brief descriptions and ask the Bootcamper to clarify.

### Requirement 6: Verbosity Preferences Persistence

**User Story:** As a bootcamper, I want my verbosity preferences saved to my configuration file, so that my settings persist across sessions and are restored when I resume the bootcamp.

#### Acceptance Criteria

1. THE Verbosity_Preferences SHALL be stored under a `verbosity` key in the bootcamper's preferences file (`config/bootcamp_preferences.yaml`, or `config/preferences_{member_id}.yaml` in co-located team mode).
2. THE `verbosity` key SHALL contain a `preset` field (string: `concise`, `standard`, `detailed`, or `custom`) and a `categories` map with each Output_Category name as a key and its Category_Level (integer 1–3) as the value.
3. WHEN the Agent starts a session, THE Agent SHALL read the Verbosity_Preferences from the preferences file and apply the stored settings.
4. IF the preferences file does not contain a `verbosity` key, THEN THE Agent SHALL apply the `standard` preset as the default.
5. WHEN any verbosity setting changes (preset selection or natural language adjustment), THE Agent SHALL write the updated Verbosity_Preferences to the preferences file within the same turn.

### Requirement 7: Learning-First Explanations (What and Why)

**User Story:** As a bootcamper, I want the bootcamp to explain what it is doing and why it is doing it, so that I can build a mental model of Senzing entity resolution rather than just following instructions blindly.

#### Acceptance Criteria

1. WHEN the `explanations` Category_Level is 2 or 3, THE Agent SHALL precede each substantive action with a "what" statement describing the action and a "why" statement explaining the purpose.
2. WHEN the `explanations` Category_Level is 1, THE Agent SHALL provide only the "what" statement without the "why" statement.
3. WHEN the `explanations` Category_Level is 3, THE Agent SHALL additionally include how the current action connects to the broader entity resolution workflow (e.g., "This mapping step feeds into the loading step in Module 6, which is where Senzing actually resolves entities").
4. THE Verbosity_Steering SHALL provide examples of "what and why" framing for each Category_Level so the Agent applies the pattern consistently.

### Requirement 8: Step Recaps

**User Story:** As a bootcamper, I want a recap after each step completes, so that I can confirm what happened and what changed before moving on.

#### Acceptance Criteria

1. WHEN a numbered step in a module completes and the `step_recaps` Category_Level is 2 or 3, THE Agent SHALL provide a recap that includes: what was accomplished, which files were created or modified (with paths), and what the Bootcamper should understand before proceeding.
2. WHEN the `step_recaps` Category_Level is 1, THE Agent SHALL provide a one-line summary of what was accomplished and list any file paths created or modified.
3. WHEN the `step_recaps` Category_Level is 3, THE Agent SHALL additionally explain how the step's output connects to the next step and to the module's overall goal.
4. THE step recap SHALL appear after the step's checkpoint is written to the progress file and before the `ask-bootcamper` hook fires.

### Requirement 9: Code Execution Framing

**User Story:** As a bootcamper, I want structured framing around every code execution — what exists before, what the code does, and what changed after — so that I can understand the effect of each code run.

#### Acceptance Criteria

1. WHEN the Agent runs code and the `code_execution_framing` Category_Level is 2 or 3, THE Agent SHALL present three sections before and after execution: (a) "Before" — describing the current state of relevant files, databases, or configurations, (b) "What this code does" — a plain-language summary of the code's purpose, and (c) "After" — describing what changed as a result of the execution.
2. WHEN the `code_execution_framing` Category_Level is 1, THE Agent SHALL present only the "What this code does" summary before execution and a one-line "Result" after execution.
3. WHEN the `code_execution_framing` Category_Level is 3, THE Agent SHALL additionally include specific before/after values for key metrics or state (e.g., "Records in database: 0 → 500", "New file created: src/load_data.py (45 lines)").
4. THE "Before" section SHALL appear before the code is executed, and the "After" section SHALL appear after the code execution completes.

### Requirement 10: Verbosity Steering File

**User Story:** As the bootcamp power author, I want a dedicated steering file that defines all verbosity rules, so that the agent applies verbosity settings consistently across all modules.

#### Acceptance Criteria

1. THE Verbosity_Steering SHALL be a markdown file with YAML frontmatter located at `senzing-bootcamp/steering/verbosity-control.md`.
2. THE Verbosity_Steering SHALL use `inclusion: always` in its YAML frontmatter so that verbosity rules are available to the Agent at all times.
3. THE Verbosity_Steering SHALL define the complete Output_Category taxonomy with definitions and examples.
4. THE Verbosity_Steering SHALL define the content rules for each Output_Category at each Category_Level (1, 2, 3).
5. THE Verbosity_Steering SHALL define the three Verbosity_Presets with their per-category level mappings.
6. THE Verbosity_Steering SHALL define the natural language term-to-category mapping for natural language adjustments.
7. THE Verbosity_Steering SHALL define the "what and why" framing pattern with examples for each Category_Level.
8. THE Verbosity_Steering SHALL define the code execution framing pattern (before / what this code does / after) with examples for each Category_Level.
9. THE Verbosity_Steering SHALL define the step recap pattern with examples for each Category_Level.
10. THE Verbosity_Steering SHALL be registered in `senzing-bootcamp/steering/steering-index.yaml` under the `keywords` section with the keywords `verbosity`, `verbose`, and `output level`.
