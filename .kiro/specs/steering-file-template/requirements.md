# Requirements Document

## Introduction

Every module steering file (`module-NN-*.md`) follows roughly the same structural pattern — YAML frontmatter, a first-read instruction, before/after framing, prerequisites, numbered workflow steps with checkpoints, and a success criteria line — but with slight variations that have accumulated over time. This feature creates a canonical template file (`templates/module-steering-template.md`) that defines the required structure, and a linter rule (integrated into `scripts/lint_steering.py`) that validates all module steering files conform to the template structure. This catches structural drift before it ships.

## Glossary

- **Module_Steering_File**: A markdown file in `senzing-bootcamp/steering/` named `module-NN-*.md` that contains the numbered workflow steps for a specific bootcamp module
- **Template**: The `senzing-bootcamp/templates/module-steering-template.md` file that defines the required structural sections and their ordering for all Module_Steering_Files
- **Template_Section**: A named structural block in the Template (e.g., frontmatter, first-read instruction, before/after, prerequisites, workflow steps, success criteria)
- **Linter**: The `scripts/lint_steering.py` script that validates steering files; this feature adds a template-conformance rule to the existing linter
- **Frontmatter_Block**: The YAML block delimited by `---` at the top of a Module_Steering_File, containing at minimum an `inclusion` field
- **First_Read_Instruction**: The bold-formatted line beginning with `**🚀 First:**` that tells the agent to read progress and display the module start banner
- **Before_After_Block**: A section (bold label `**Before/After:**` or heading) that describes what the bootcamper's state is before and after completing the module
- **Prerequisites_Block**: A section (bold label `**Prerequisites**:` or similar) listing what must be completed before starting the module
- **Workflow_Steps**: The numbered list items (`1.`, `2.`, etc.) that form the core instructional content of the module
- **Checkpoint_Instruction**: A line matching `**Checkpoint:** Write step N to \`config/bootcamp_progress.json\`.` that persists step-level progress
- **Success_Indicator**: The final line of the module matching the pattern `**Success indicator:** ✅ ...` that summarizes completion criteria
- **Lint_Violation**: A single issue found by the Linter, classified as error or warning
- **Section_Order**: The required sequence of Template_Sections: frontmatter → first-read instruction → user reference → before/after → prerequisites → workflow steps → success indicator

## Requirements

### Requirement 1: Template File Creation

**User Story:** As a power maintainer, I want a canonical template file that documents the required structure of module steering files, so that contributors know the expected format when creating new modules.

#### Acceptance Criteria

1. THE Template SHALL be located at `senzing-bootcamp/templates/module-steering-template.md`
2. THE Template SHALL contain placeholder sections in the required Section_Order: Frontmatter_Block, First_Read_Instruction, user reference line, Before_After_Block, Prerequisites_Block, Workflow_Steps (with at least one example step containing a Checkpoint_Instruction), and Success_Indicator
3. THE Template SHALL include inline comments (HTML comments `<!-- ... -->`) explaining what each section is for and what content is expected
4. THE Template SHALL use placeholder values (e.g., `NN`, `[Module Title]`, `[description]`) that make it clear which parts must be customized

### Requirement 2: Frontmatter Validation

**User Story:** As a power maintainer, I want the linter to verify that every module steering file has valid YAML frontmatter with the correct inclusion mode, so that the agent framework loads module files correctly.

#### Acceptance Criteria

1. THE Linter SHALL verify that every Module_Steering_File begins with a Frontmatter_Block delimited by `---` on the first line and a closing `---`
2. THE Linter SHALL verify that the Frontmatter_Block contains an `inclusion` field with the value `manual`
3. WHEN a Module_Steering_File lacks a Frontmatter_Block, THE Linter SHALL report an error Lint_Violation identifying the file
4. WHEN a Module_Steering_File has a Frontmatter_Block with an `inclusion` value other than `manual`, THE Linter SHALL report a warning Lint_Violation identifying the file and the unexpected value

### Requirement 3: First-Read Instruction Validation

**User Story:** As a power maintainer, I want the linter to verify that every module steering file has the standard first-read instruction, so that agents always display the module start banner before proceeding.

#### Acceptance Criteria

1. THE Linter SHALL verify that every Module_Steering_File contains a line matching the pattern `**🚀 First:**` within the first 10 non-blank lines after the frontmatter
2. WHEN the First_Read_Instruction references `config/bootcamp_progress.json` and `module-transitions.md`, THE Linter SHALL treat the instruction as valid
3. WHEN a Module_Steering_File lacks a First_Read_Instruction, THE Linter SHALL report an error Lint_Violation identifying the file
4. WHEN the First_Read_Instruction is present but does not reference both `config/bootcamp_progress.json` and `module-transitions.md`, THE Linter SHALL report a warning Lint_Violation identifying the file and the missing reference

### Requirement 4: Before/After Block Validation

**User Story:** As a power maintainer, I want the linter to verify that every module steering file includes before/after framing, so that agents always set context for the bootcamper.

#### Acceptance Criteria

1. THE Linter SHALL verify that every Module_Steering_File contains a Before_After_Block identified by a line containing `**Before/After**` (case-insensitive match on the label text)
2. WHEN a Module_Steering_File lacks a Before_After_Block, THE Linter SHALL report a warning Lint_Violation identifying the file
3. THE Linter SHALL verify that the Before_After_Block appears before the first Workflow_Step in the document

### Requirement 5: Checkpoint Completeness Validation

**User Story:** As a power maintainer, I want the linter to verify that every numbered workflow step has a checkpoint instruction, so that step-level progress tracking is never silently skipped.

#### Acceptance Criteria

1. THE Linter SHALL parse each Module_Steering_File to identify all top-level Workflow_Steps by scanning for lines matching the pattern of a numbered list item (e.g., `1. `, `2. `) at the top indentation level
2. WHEN a Workflow_Step does not have a corresponding Checkpoint_Instruction before the next Workflow_Step or end of file, THE Linter SHALL report an error Lint_Violation identifying the module file and step number
3. WHEN a Checkpoint_Instruction references a step number that does not match the Workflow_Step it belongs to, THE Linter SHALL report an error Lint_Violation identifying the mismatched step numbers
4. WHEN a Module_Steering_File contains zero Workflow_Steps, THE Linter SHALL skip checkpoint validation for that file without reporting a violation

### Requirement 6: Success Indicator Validation

**User Story:** As a power maintainer, I want the linter to verify that every module steering file ends with a success indicator, so that agents know when the module is complete.

#### Acceptance Criteria

1. THE Linter SHALL verify that every Module_Steering_File contains a Success_Indicator line matching the pattern `**Success indicator:**` (case-insensitive on the label)
2. WHEN a Module_Steering_File lacks a Success_Indicator, THE Linter SHALL report a warning Lint_Violation identifying the file
3. THE Linter SHALL verify that the Success_Indicator appears after all Workflow_Steps in the document
4. WHEN the Success_Indicator appears before a Workflow_Step, THE Linter SHALL report an error Lint_Violation identifying the file and the out-of-order section

### Requirement 7: Section Order Validation

**User Story:** As a power maintainer, I want the linter to verify that the structural sections of each module steering file appear in the correct order, so that agents process modules consistently.

#### Acceptance Criteria

1. THE Linter SHALL verify that the detected Template_Sections in each Module_Steering_File appear in the required Section_Order: Frontmatter_Block before First_Read_Instruction, First_Read_Instruction before Before_After_Block, Before_After_Block before Workflow_Steps, Workflow_Steps before Success_Indicator
2. WHEN a detected section appears out of the required order, THE Linter SHALL report a warning Lint_Violation identifying the file and the two sections that are out of order
3. THE Linter SHALL only validate ordering for sections that are present; missing sections are reported by their individual validation rules and do not trigger an ordering violation

### Requirement 8: Linter CLI Integration

**User Story:** As a CI pipeline maintainer, I want the template-conformance checks to integrate into the existing linter CLI, so that a single command validates all steering file rules including template conformance.

#### Acceptance Criteria

1. THE Linter SHALL include the template-conformance checks as part of the standard `python scripts/lint_steering.py` execution without requiring additional flags
2. THE Linter SHALL report template-conformance violations in the same format as other lint violations: `{level}: {file}:{line}: {message}`
3. WHEN the `--skip-template` flag is passed, THE Linter SHALL skip all template-conformance checks for Module_Steering_Files
4. THE Linter SHALL depend only on the Python standard library for template-conformance checks
