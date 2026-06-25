# Requirements Document

## Introduction

This feature enhances the Senzing Bootcamp graduation report so it serves as a complete, annotated takeaway summary for the bootcamper. A Medium-priority Documentation feedback item reported that the generated `GRADUATION_REPORT.md` listed only the files placed in the `production/` directory. It did not enumerate the full set of artifacts created across all modules — business problem, data source registry, mappers, transformed data, SDK config, verification scripts, query programs, web app, recap/journal, and so on — and it did not explain why each file matters to the bootcamper.

The graduation report is the bootcamper's takeaway summary. Without a complete, annotated inventory of everything produced, it is harder for the bootcamper to understand what they now own, what each artifact is for, and which files to carry forward versus leave behind. As a workaround, the agent manually expanded `GRADUATION_REPORT.md` with a "Complete Artifact Inventory" section; this feature makes that a standard, repeatable part of the graduation workflow.

The graduation workflow is defined in `senzing-bootcamp/steering/graduation.md`. Today its report includes a timestamp, track completed, modules finished, language, database type, a files-generated table and a files-excluded table (both scoped to the `production/` copy step), and next steps. This feature adds a complete artifact inventory grouped by module/phase, covering every artifact created for the bootcamper throughout the bootcamp — not just the production subset — each annotated with a short why-it-matters note. Inventory contents are derived from the bootcamper's actual progress and the files present in their project, so the report reflects what was really produced.

## Glossary

- **Graduation report**: `production/GRADUATION_REPORT.md`, always generated at the end of the graduation workflow.
- **Artifact**: Any file created for the bootcamper during the bootcamp (docs, config, code, data, registries, journals, web app, etc.).
- **Complete artifact inventory**: A new report section listing every artifact created across all modules/phases, grouped by module/phase, each with a why-it-matters note.
- **Why-it-matters note**: A short description of an artifact's purpose and how the bootcamper uses it going forward.
- **Production subset**: The artifacts copied into `production/` during graduation Step 1 (the only files the report enumerates today).
- **Carry-forward vs leave-behind**: Whether an artifact belongs in the production codebase or is bootcamp-only scaffolding (e.g., progress/journal files).

## Requirements

### Requirement 1: Complete artifact inventory in the graduation report

**User Story:** As a graduating bootcamper, I want the graduation report to list every file created for me across all modules, so that I understand the full set of artifacts I now own — not just the production subset.

#### Acceptance Criteria

1. WHEN the graduation report is generated THEN the system SHALL include a "Complete Artifact Inventory" section enumerating the artifacts created for the bootcamper across all completed modules/phases, not limited to files copied into `production/`.
2. WHEN the inventory is produced THEN the system SHALL derive its entries from the bootcamper's actual progress (`config/bootcamp_progress.json`) and the artifacts present in the project, rather than from a fixed hardcoded list that ignores what was actually produced.
3. WHEN an expected artifact for a completed module is absent from the project THEN the system SHALL omit it from the inventory (or mark it as not produced) rather than listing a file that does not exist.
4. WHEN the inventory is generated THEN the system SHALL include the existing report content (timestamp, track, modules finished, language, database type, files-generated/excluded tables, next steps) in addition to the new inventory section.

### Requirement 2: Group the inventory by module/phase

**User Story:** As a bootcamper, I want the inventory organized by module/phase, so that I can see what each stage of the bootcamp produced and find artifacts in context.

#### Acceptance Criteria

1. WHEN the inventory is rendered THEN the system SHALL group artifacts by the module or phase that produced them (e.g., business problem and data source registry under discovery/data collection, mappers and transformed data under mapping/processing, query programs and web app under querying, recap/journal under completion).
2. WHEN a module in `modules_completed` produced artifacts THEN the system SHALL include a group for that module/phase containing its artifacts.
3. WHEN a module was not completed THEN the system SHALL NOT fabricate artifacts for it, and SHALL only inventory artifacts that were actually produced.

### Requirement 3: Annotate each artifact with why it matters

**User Story:** As a bootcamper, I want each listed file to explain why it matters, so that I know its purpose and how to use it going forward.

#### Acceptance Criteria

1. WHEN an artifact is listed in the inventory THEN the system SHALL include its path (or location) and a short why-it-matters note describing its purpose and how it is used going forward.
2. WHEN an artifact is part of the production codebase THEN the why-it-matters note SHALL indicate it is a carry-forward artifact.
3. WHEN an artifact is bootcamp-only scaffolding (e.g., `config/bootcamp_progress.json`, `docs/bootcamp_journal.md`) THEN the why-it-matters note SHALL indicate it is a learning/record artifact rather than production code.
4. WHEN why-it-matters notes are written THEN they SHALL be concise (a brief phrase or sentence per artifact), consistent with the report's existing tone.

### Requirement 4: Reliable, non-blocking generation

**User Story:** As a bootcamper, I want the inventory to generate reliably as part of graduation, so that my report is complete even if some steps had problems.

#### Acceptance Criteria

1. WHEN the graduation workflow reaches report generation THEN the system SHALL always generate `production/GRADUATION_REPORT.md` with the inventory section, consistent with the existing "always generate the report" guarantee.
2. IF progress data is missing or incomplete THEN the system SHALL inventory whatever artifacts can be determined from the project and SHALL note that the inventory may be incomplete, rather than failing report generation.
3. IF inventory generation encounters an error for a specific module/phase THEN the system SHALL record the issue (consistent with the existing "⚠️ Issues Encountered" section) and SHALL still produce the rest of the report.
4. WHEN the inventory references the bootcamp feedback or completion artifacts THEN the system SHALL remain consistent with the existing graduation report structure and SHALL NOT duplicate or contradict the files-generated/excluded tables.
