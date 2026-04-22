# Requirements Document

## Introduction

This spec retroactively documents the module completion workflow — the guided sequence that runs after every module to capture journal entries, prompt reflection, present next-step options, and detect/celebrate path completion. The workflow lives in `senzing-bootcamp/steering/module-completion.md`.

## Glossary

- **Module_Completion_Workflow**: The post-module sequence (journal entry → reflection → next-step options → path completion check) loaded after any module finishes.
- **Bootcamp_Journal**: The file `docs/bootcamp_journal.md` that accumulates structured entries for each completed module.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Path_Completion_Map**: The mapping of learning paths to their final module (A→1, B→8, C→8, D→12).
- **Lessons_Learned**: The steering file `lessons-learned.md` loaded to offer a retrospective when a path is completed.

## Requirements

### Requirement 1: Bootcamp Journal Entry and Reflection

**User Story:** As a Bootcamper, I want a structured journal entry recorded after each module with a chance to reflect, so that I have a running log of what I built and learned.

#### Acceptance Criteria

1. WHEN a module is completed, THE Agent SHALL append a structured entry to `docs/bootcamp_journal.md` containing: module name, completion date, what was done, what was produced, why it matters, and the Bootcamper's takeaway.
2. WHEN the factual journal entry is written, THE Agent SHALL ask a reflection question prefixed with 👉 asking the Bootcamper for their main takeaway.
3. WHEN the Bootcamper provides a reflection response, THE Agent SHALL append the response under "Bootcamper's takeaway" in the journal entry.
4. IF the Bootcamper declines to reflect, THEN THE Agent SHALL write "No additional notes" under "Bootcamper's takeaway" and proceed without pushing further.

### Requirement 2: Next-Step Options with Iterate-vs-Proceed Gate

**User Story:** As a Bootcamper, I want concrete next-step choices after each module, so that I can decide whether to proceed, iterate, explore, or share before moving on.

#### Acceptance Criteria

1. WHEN the journal entry and reflection are complete, THE Agent SHALL present four options: Proceed (next module), Iterate (improve current work), Explore (dig deeper into artifacts), and Share (prepare a team summary).
2. THE Agent SHALL present the options as a single list followed by "👉 What would you like to do?" and wait for the Bootcamper's response.
3. WHILE Module 1 has just been completed, THE Agent SHALL treat the Explore option as a second chance for the visualization offer that should have been presented before reaching the Module_Completion_Workflow.

### Requirement 3: Path Completion Detection and Celebration

**User Story:** As a Bootcamper, I want to be recognized when I finish my learning path with a summary of everything I built, so that I know what I accomplished and what to do next.

#### Acceptance Criteria

1. WHEN a module is completed, THE Agent SHALL check the Path_Completion_Map to determine if the Bootcamper has finished their path's final module.
2. WHEN path completion is detected, THE Agent SHALL display a 🎉 celebration message including: path name, summary of all artifacts built, file locations (src/, data/transformed/, docs/, config/, database/), and a reference to `docs/bootcamp_journal.md`.
3. WHEN path completion is detected, THE Agent SHALL present next options: switch to a longer path (modules carry forward), harden for production, or start using the code.
4. WHEN path completion is detected, THE Agent SHALL load `lessons-learned.md` and offer a retrospective.
5. WHEN path completion is detected, THE Agent SHALL remind the Bootcamper to say "bootcamp feedback" to share their experience.
