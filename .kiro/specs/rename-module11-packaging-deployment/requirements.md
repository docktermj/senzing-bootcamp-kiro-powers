# Requirements Document

## Introduction

Module 11 is currently named "Deployment and Packaging" in the steering file heading, but its internal structure covers Packaging first (Steps 2–11) and Deployment second (Steps 12–15). The module name should be "Packaging and Deployment" to reflect the actual content order. Other display variants ("Package & Deploy", "Package and Deploy") already use the correct order and should be left as-is. All references to the old name — in headings, filenames, file listings, templates, tests, and diagrams — must be updated consistently.

## Glossary

- **Steering_File**: A Markdown file in `senzing-bootcamp/steering/` that provides step-by-step agent workflow instructions for a module.
- **Module_Doc**: A Markdown file in `senzing-bootcamp/docs/modules/` that provides user-facing background documentation for a module.
- **Steering_Index**: The YAML file `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to their steering file names and metadata.
- **POWER_MD**: The main power definition file `senzing-bootcamp/POWER.md` that describes the bootcamp to Kiro.
- **Rename_System**: The collection of files, references, and cross-links that together define Module 11's name across the codebase.

## Requirements

### Requirement 1: Rename the Steering File Heading

**User Story:** As a bootcamp maintainer, I want the Module 11 steering file heading to say "Packaging and Deployment" instead of "Deployment and Packaging", so that the name matches the module's internal structure (Packaging first, Deployment second).

#### Acceptance Criteria

1. WHEN the Steering_File `senzing-bootcamp/steering/module-11-deployment.md` is read, THE Rename_System SHALL contain the heading `# Module 11: Packaging and Deployment` instead of `# Module 11: Deployment and Packaging`.
2. WHEN the Steering_File `senzing-bootcamp/steering/module-11-deployment.md` is read, THE Rename_System SHALL contain the user message text `"Module 11 has two phases. First we'll package your code."` unchanged, preserving the packaging-first framing.

### Requirement 2: Rename the Module Documentation File

**User Story:** As a bootcamp maintainer, I want the Module 11 documentation filename to reflect the new name order, so that the filename is consistent with the heading inside it.

#### Acceptance Criteria

1. THE Rename_System SHALL rename the file `senzing-bootcamp/docs/modules/MODULE_11_DEPLOYMENT_PACKAGING.md` to `senzing-bootcamp/docs/modules/MODULE_11_PACKAGING_DEPLOYMENT.md`.
2. WHEN the renamed Module_Doc is read, THE Rename_System SHALL contain the heading `# Module 11: Package and Deploy` unchanged (this heading already uses the correct order).
3. WHEN the Steering_File references the Module_Doc, THE Rename_System SHALL use the new filename `MODULE_11_PACKAGING_DEPLOYMENT.md` in the reference path.

### Requirement 3: Update the Module Documentation Index

**User Story:** As a bootcamp user, I want the module listing in `senzing-bootcamp/docs/modules/README.md` to link to the renamed file, so that navigation links remain valid.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/docs/modules/README.md` references Module 11, THE Rename_System SHALL link to `MODULE_11_PACKAGING_DEPLOYMENT.md` instead of `MODULE_11_DEPLOYMENT_PACKAGING.md`.

### Requirement 4: Update the Docs README File Listing

**User Story:** As a bootcamp maintainer, I want the file listing in `senzing-bootcamp/docs/README.md` to reference the renamed file, so that the documentation index is accurate.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/docs/README.md` lists Module 11, THE Rename_System SHALL reference `MODULE_11_PACKAGING_DEPLOYMENT.md` instead of `MODULE_11_DEPLOYMENT_PACKAGING.md`.
2. WHEN the file `senzing-bootcamp/docs/README.md` describes Module 11, THE Rename_System SHALL use the description "Packaging and deployment" instead of "Deployment packaging".

### Requirement 5: Update the Stakeholder Summary Template

**User Story:** As a bootcamp maintainer, I want the stakeholder summary template to use the new module name, so that generated summaries reflect the correct name.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/templates/stakeholder_summary.md` references Module 11 by name, THE Rename_System SHALL use "Packaging and Deployment" instead of "Deployment and Packaging" in the section header and `[module_name]` placeholder value.

### Requirement 6: Update the Graduation Reference

**User Story:** As a bootcamp maintainer, I want graduation reference text to use consistent terminology, so that the packaging-before-deployment order is reflected in checklist items.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/steering/graduation-reference.md` references Module 11 packaging, THE Rename_System SHALL use "packaging and deployment" instead of "deployment packaging" in checklist item text.

### Requirement 7: Update the Module Prerequisites Diagram

**User Story:** As a bootcamp user, I want the Mermaid prerequisites diagram to show the correct Module 11 name, so that the visual diagram is consistent with the rest of the documentation.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/docs/diagrams/module-prerequisites.md` renders Module 11 in the Mermaid graph, THE Rename_System SHALL display `Module 11: Package & Deploy` instead of `Module 11: Monitoring, Package & Deploy` (Module 11 does not cover Monitoring — that is Module 10).

### Requirement 8: Update the Test File Heading Constants

**User Story:** As a bootcamp developer, I want the test constants that reference Module 11 headings to match the actual steering file headings, so that heading-ownership tests pass.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/tests/test_module_closing_question_ownership.py` defines `_HEADINGS_MODULE_11`, THE Rename_System SHALL use `"# Module 11: Packaging and Deployment"` as the first heading instead of `"# Module 11: Deployment and Packaging"`.

### Requirement 9: Update the Stakeholder Summary Monitoring Section

**User Story:** As a bootcamp maintainer, I want the Module 10 (Monitoring) stakeholder summary section to reference Module 11 with the correct name, so that next-steps guidance is accurate.

#### Acceptance Criteria

1. WHEN the file `senzing-bootcamp/templates/stakeholder_summary.md` lists next steps for the Monitoring module, THE Rename_System SHALL reference "packaging and deployment (Module 11)" instead of "deployment packaging (Module 11)".

### Requirement 10: Preserve Unchanged References

**User Story:** As a bootcamp maintainer, I want references that already use the correct order ("Package & Deploy", "Package and Deploy") to remain unchanged, so that the rename does not introduce unnecessary churn.

#### Acceptance Criteria

1. WHEN POWER_MD contains the table entry `11 — Package & Deploy`, THE Rename_System SHALL leave that text unchanged.
2. WHEN POWER_MD contains the bootcamp modules table entry `Package and Deploy`, THE Rename_System SHALL leave that text unchanged.
3. WHEN the Module_Doc contains the heading `# Module 11: Package and Deploy`, THE Rename_System SHALL leave that text unchanged.
4. WHEN the Module_Doc contains the banner `MODULE 11: PACKAGE AND DEPLOY`, THE Rename_System SHALL leave that text unchanged.
5. THE Rename_System SHALL leave the steering filename `module-11-deployment.md` unchanged (it is an internal agent reference and does not surface to users).
6. THE Rename_System SHALL leave the Steering_Index file `senzing-bootcamp/steering/steering-index.yaml` unchanged (it references the steering filename, not the display name).

### Requirement 11: All Tests Pass After Rename

**User Story:** As a bootcamp developer, I want all existing tests to pass after the rename, so that the change does not introduce regressions.

#### Acceptance Criteria

1. WHEN the full test suite is run with `pytest senzing-bootcamp/tests/`, THE Rename_System SHALL produce zero test failures related to Module 11 heading or filename references.
