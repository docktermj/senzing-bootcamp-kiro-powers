# Requirements Document

## Introduction

This feature improves the module completion workflow in the Senzing Bootcamp Power to ensure that two key cumulative artifacts — the bootcamp journal (`docs/bootcamp_journal.md`) and the bootcamp recap (`docs/bootcamp_recap.md`) — are reliably created and maintained from the very first module completion onward. Currently, the journal was not created until Module 3 (requiring backfilling of Modules 1 and 2), and the recap document may not exist at graduation time, causing the graduation workflow to silently skip PDF generation. This feature makes both artifacts mandatory outputs of every module completion and treats their absence at graduation as an error condition requiring recovery.

## Glossary

- **Module_Completion_Workflow**: The agent-driven process that executes after a bootcamper finishes all steps in a module, governed by the `module-completion.md` steering file
- **Journal**: The file at `docs/bootcamp_journal.md` that records a brief structured entry for each completed module
- **Recap_Document**: The file at `docs/bootcamp_recap.md` that accumulates detailed session content (information shared, questions asked, answers given, actions taken) for each completed module
- **Graduation_Workflow**: The agent-driven process that transitions a completed bootcamp project into a production-ready codebase, governed by the `graduation.md` steering file
- **Progress_File**: The file at `config/bootcamp_progress.json` that tracks which modules have been completed
- **Preferences_File**: The file at `config/bootcamp_preferences.yaml` that stores the bootcamper's name, language, and other settings
- **Module_Artifacts**: Files and code produced during a module that serve as source material for journal and recap entries

## Requirements

### Requirement 1: Journal File Creation on First Module Completion

**User Story:** As a bootcamper, I want the bootcamp journal to be created when I complete my first module, so that I have a complete and accurate record from the start without any backfilling.

#### Acceptance Criteria

1. WHEN the first module is completed AND `docs/bootcamp_journal.md` does not exist, THE Module_Completion_Workflow SHALL create the `docs/` directory if absent, then create `docs/bootcamp_journal.md` with a markdown header consisting of a level-1 heading "Bootcamp Journal", the bootcamper name from `config/bootcamp_preferences.yaml`, and the start date in ISO 8601 format (YYYY-MM-DD), before appending the first entry
2. WHEN any module is completed AND `docs/bootcamp_journal.md` already exists, THE Module_Completion_Workflow SHALL append a new entry to the end of the file without modifying existing content, preserving all prior entries byte-for-byte
3. THE Module_Completion_Workflow SHALL create the journal entry as a mandatory step in the completion checklist, positioned after the progress file update and before the next-step options, and SHALL NOT skip this step regardless of module number or completion method (normal completion or skip)
4. IF journal file creation or entry append fails due to a file-system error, THEN THE Module_Completion_Workflow SHALL log a warning indicating the failure reason, continue the remaining completion steps without blocking, and retry the journal write on the next module completion

### Requirement 2: Journal Entry Structure

**User Story:** As a bootcamper, I want each journal entry to follow a consistent structure, so that I can easily review my progress across all modules.

#### Acceptance Criteria

1. WHEN a module is completed, THE Module_Completion_Workflow SHALL append a journal entry containing the module number, module name, completion date, a summary of what was done, a list of artifacts produced, a statement of why the module matters, and a bootcamper takeaway field
2. THE Module_Completion_Workflow SHALL derive the module name from `config/module-dependencies.yaml`
3. THE Module_Completion_Workflow SHALL use ISO 8601 format with timezone offset for all dates in journal entries
4. THE Module_Completion_Workflow SHALL derive the artifacts list from files created or modified during the module session

### Requirement 3: Recap Document Creation on First Module Completion

**User Story:** As a bootcamper, I want the recap document to be created when I complete my first module, so that it exists as a cumulative artifact from the beginning and is guaranteed to be available at graduation.

#### Acceptance Criteria

1. WHEN the first module is completed AND `docs/bootcamp_recap.md` does not exist, THE Module_Completion_Workflow SHALL read the bootcamper name from `config/bootcamp_preferences.yaml` and create `docs/bootcamp_recap.md` with a header containing the bootcamper name, start timestamp in ISO 8601 format with timezone offset, and total duration initialized to the first module's session duration, before appending the first recap section
2. IF `config/bootcamp_preferences.yaml` does not exist or the name field is missing, THEN THE Module_Completion_Workflow SHALL use "Bootcamper" as the default name in the recap document header
3. WHEN any module is completed AND `docs/bootcamp_recap.md` already exists, THE Module_Completion_Workflow SHALL append a new recap section at the end of the file without modifying existing bytes in the file
4. THE Module_Completion_Workflow SHALL execute the recap append after the progress file update and before the journal entry

### Requirement 4: Recap Section Content

**User Story:** As a bootcamper, I want each recap section to capture the full context of what happened during a module, so that I have a detailed record for future reference and graduation.

#### Acceptance Criteria

1. WHEN a module is completed, THE Module_Completion_Workflow SHALL append a recap section containing: information shared, questions asked, answers given, actions taken, and duration
2. THE Module_Completion_Workflow SHALL maintain one-to-one correspondence between questions asked and answers given in each recap section
3. THE Module_Completion_Workflow SHALL use ISO 8601 format with timezone offset for the recap section timestamp
4. THE Module_Completion_Workflow SHALL update the total duration in the file header to reflect cumulative time across all completed modules
5. THE Module_Completion_Workflow SHALL order recap sections chronologically by completion timestamp

### Requirement 5: Recap Document Validation at Graduation

**User Story:** As a bootcamper, I want the graduation workflow to treat a missing recap document as an error that gets resolved, so that I receive the recap PDF I was promised rather than having it silently skipped.

#### Acceptance Criteria

1. WHEN the Graduation_Workflow begins Step 0 AND `docs/bootcamp_recap.md` does not exist, THE Graduation_Workflow SHALL halt the normal graduation flow and attempt to regenerate the recap document before proceeding to PDF generation
2. WHEN the recap document is missing, THE Graduation_Workflow SHALL generate it from available progress data in the Progress_File and module artifacts produced during the bootcamp before proceeding to PDF generation
3. WHEN the recap document is missing, THE Graduation_Workflow SHALL display a message to the bootcamper stating that the recap document was not found and has been reconstructed from available progress data
4. THE Graduation_Workflow SHALL proceed to PDF generation only after confirming that `docs/bootcamp_recap.md` exists and contains at least one markdown heading matching the pattern `## Module N:` where N is a module number present in the Progress_File `modules_completed` array
5. IF the recap document is missing AND the Progress_File does not exist or contains an empty `modules_completed` array, THEN THE Graduation_Workflow SHALL display a message to the bootcamper indicating that the recap cannot be generated due to insufficient progress data and SHALL skip PDF generation

### Requirement 6: Non-Blocking Error Handling for Artifact Creation

**User Story:** As a bootcamper, I want the module completion flow to continue even if journal or recap creation encounters an error, so that a file system issue does not block my progress.

#### Acceptance Criteria

1. IF the journal file cannot be written due to a file system error, THEN THE Module_Completion_Workflow SHALL log a warning message and continue to the next step in the completion flow
2. IF the recap file cannot be written due to a file system error, THEN THE Module_Completion_Workflow SHALL log a warning message and continue to the next step in the completion flow
3. IF both the journal and recap writes fail, THEN THE Module_Completion_Workflow SHALL still present the next-step options to the bootcamper

### Requirement 7: Completion Checklist Ordering

**User Story:** As a power author, I want the module completion steps to execute in a defined order, so that each artifact has access to the data it needs and the bootcamper experiences a consistent flow.

#### Acceptance Criteria

1. THE Module_Completion_Workflow SHALL execute completion steps in this fixed order: progress file update, recap append, journal entry, completion certificate, next-step options
2. THE Module_Completion_Workflow SHALL complete the recap append before starting the journal entry
3. THE Module_Completion_Workflow SHALL complete the journal entry before generating the completion certificate
4. IF any step produces a file system error, a timeout exceeding 30 seconds, or an unhandled exception, THEN THE Module_Completion_Workflow SHALL skip that step, log a warning message visible to the bootcamper identifying which step was skipped, and proceed to the next step in the defined order
5. IF a predecessor step is skipped due to failure, THEN THE Module_Completion_Workflow SHALL still attempt subsequent steps using only the data available from previously successful steps
