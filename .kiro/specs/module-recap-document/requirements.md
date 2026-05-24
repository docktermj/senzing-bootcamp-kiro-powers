# Requirements Document

## Introduction

This feature adds a running recap document (`docs/bootcamp_recap.md`) that accumulates a module-by-module account of the entire bootcamp experience. At the end of each module, before transitioning to the next, the system appends a structured recap section capturing what was shared, what was asked, what was answered, and what actions were taken. At bootcamp graduation, the system auto-generates a PDF of the recap file for sharing.

## Glossary

- **Recap_Document**: The markdown file at `docs/bootcamp_recap.md` that accumulates per-module recap sections throughout the bootcamp
- **Recap_Section**: A structured block appended to the Recap_Document at module completion, containing information shared, questions asked, answers given, and actions taken for one module
- **Recap_Generator**: The Python script (`scripts/generate_recap_pdf.py`) responsible for converting the Recap_Document markdown into a PDF file
- **Module_Completion_Hook**: The hook that fires at module completion boundaries and triggers recap section generation
- **Bootcamper**: The user progressing through the Senzing bootcamp
- **Progress_File**: The JSON file at `config/bootcamp_progress.json` tracking module completion state

## Requirements

### Requirement 1: Recap Document Initialization

**User Story:** As a bootcamper, I want the recap document to be created automatically when I complete my first module, so that I do not need to set up any files manually.

#### Acceptance Criteria

1. WHEN the first module is completed and `docs/bootcamp_recap.md` does not exist, THE Module_Completion_Hook SHALL create the file with a title header, bootcamp start date, and the first Recap_Section
2. WHEN the first module is completed and `docs/bootcamp_recap.md` already exists, THE Module_Completion_Hook SHALL append the Recap_Section without overwriting existing content
3. THE Recap_Document SHALL include a top-level header containing the bootcamper's name (from `config/bootcamp_preferences.yaml` if available) and the bootcamp start date in ISO 8601 format

### Requirement 2: Recap Section Structure

**User Story:** As a bootcamper, I want each module recap to follow a consistent structure, so that I can easily review what happened in any module.

#### Acceptance Criteria

1. THE Recap_Section SHALL contain a level-2 heading with the module number, module name, and completion timestamp in ISO 8601 format
2. THE Recap_Section SHALL contain an "Information Shared" subsection listing key concepts, explanations, and reference material presented to the Bootcamper during the module
3. THE Recap_Section SHALL contain a "Questions Asked" subsection listing all questions the agent posed to the Bootcamper during the module
4. THE Recap_Section SHALL contain an "Answers Given" subsection listing the Bootcamper's responses to each question, paired with the corresponding question
5. THE Recap_Section SHALL contain an "Actions Taken" subsection listing all file creation, code generation, configuration changes, and commands executed during the module
6. THE Recap_Section SHALL contain a "Duration" field recording the elapsed time for the module (from module start to completion)

### Requirement 3: Recap Append at Module Completion

**User Story:** As a bootcamper, I want the recap to be appended automatically at the end of each module, so that I have a complete record without manual effort.

#### Acceptance Criteria

1. WHEN a module is marked complete in the Progress_File, THE Module_Completion_Hook SHALL append a Recap_Section to the Recap_Document before the module transition question is presented
2. WHILE the Recap_Document is being appended, THE Module_Completion_Hook SHALL preserve all existing content in the file
3. IF the Recap_Document cannot be written (file system error), THEN THE Module_Completion_Hook SHALL log a warning and continue the module completion flow without blocking the Bootcamper

### Requirement 4: Recap Content Derivation

**User Story:** As a bootcamper, I want the recap to accurately reflect what happened during the module, so that it serves as a reliable reference.

#### Acceptance Criteria

1. THE Module_Completion_Hook SHALL derive the "Information Shared" content from the steering file topics covered and explanations provided during the module session
2. THE Module_Completion_Hook SHALL derive the "Questions Asked" content from all agent-initiated questions posed to the Bootcamper during the module (excluding rhetorical or transitional prompts)
3. THE Module_Completion_Hook SHALL derive the "Answers Given" content from the Bootcamper's responses captured in the conversation history
4. THE Module_Completion_Hook SHALL derive the "Actions Taken" content from file writes, code generation events, and commands executed during the module
5. WHEN a module contains sub-steps, THE Module_Completion_Hook SHALL include content from all sub-steps in the Recap_Section

### Requirement 5: PDF Generation at Graduation

**User Story:** As a bootcamper, I want a PDF version of my recap document generated at graduation, so that I can share my bootcamp experience with colleagues and stakeholders.

#### Acceptance Criteria

1. WHEN the graduation workflow is initiated, THE Recap_Generator SHALL convert `docs/bootcamp_recap.md` into a PDF file at `docs/bootcamp_recap.pdf`
2. THE Recap_Generator SHALL render markdown headings, lists, bold text, and code blocks in the PDF with appropriate formatting
3. THE Recap_Generator SHALL include a cover page with the bootcamp title, bootcamper name, completion date, and total duration
4. IF `docs/bootcamp_recap.md` does not exist at graduation time, THEN THE Recap_Generator SHALL skip PDF generation and log a warning message
5. IF PDF generation fails (missing library or rendering error), THEN THE Recap_Generator SHALL inform the Bootcamper of the failure reason and suggest manual conversion alternatives

### Requirement 6: PDF Generation Script

**User Story:** As a developer, I want the PDF generation to be a standalone script, so that it can be run independently or integrated into the graduation workflow.

#### Acceptance Criteria

1. THE Recap_Generator SHALL be implemented as a Python script at `scripts/generate_recap_pdf.py` with a `main()` entry point and argparse CLI
2. THE Recap_Generator SHALL accept `--input` and `--output` arguments for specifying source markdown and destination PDF paths
3. THE Recap_Generator SHALL default to `docs/bootcamp_recap.md` as input and `docs/bootcamp_recap.pdf` as output when arguments are omitted
4. THE Recap_Generator SHALL use only Python 3.11+ standard library for markdown parsing, with an optional dependency on `fpdf2` for PDF rendering
5. WHEN `fpdf2` is not installed, THE Recap_Generator SHALL exit with a clear error message explaining how to install the dependency (`pip install fpdf2`)
6. THE Recap_Generator SHALL produce valid PDF output that opens correctly in standard PDF viewers
7. FOR ALL valid Recap_Document markdown content, parsing then rendering then re-reading the PDF text content SHALL preserve the semantic structure (headings, lists, section order)

### Requirement 7: Timestamp and Date Recording

**User Story:** As a bootcamper, I want dates and times recorded in my recap, so that I can track when each module was completed and how long the bootcamp took.

#### Acceptance Criteria

1. THE Recap_Document SHALL record the bootcamp start date and time in the document header using ISO 8601 format with timezone
2. WHEN a Recap_Section is appended, THE Module_Completion_Hook SHALL include the module completion date and time in ISO 8601 format with timezone
3. THE Recap_Generator SHALL include the graduation date and time on the PDF cover page in ISO 8601 format with timezone
4. THE Recap_Document SHALL record the total elapsed bootcamp duration (from first module start to final module completion) in the document footer, updated with each new Recap_Section

### Requirement 8: Integration with Existing Module Completion Workflow

**User Story:** As a bootcamper, I want the recap generation to fit seamlessly into the existing module completion flow, so that it does not disrupt my experience.

#### Acceptance Criteria

1. THE Module_Completion_Hook SHALL execute the recap append after the module is marked complete in the Progress_File and before the journal entry in `module-completion.md` workflow
2. THE Module_Completion_Hook SHALL complete the recap append within the existing module completion flow without requiring additional Bootcamper confirmation
3. WHEN the recap append completes, THE Module_Completion_Hook SHALL display a brief confirmation message (one line) indicating the recap was updated
4. THE Module_Completion_Hook SHALL not alter the behavior of the existing module-completion-celebration hook or the journal entry process
