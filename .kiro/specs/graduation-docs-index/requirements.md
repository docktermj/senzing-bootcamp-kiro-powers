# Requirements Document

## Introduction

This feature adds a step to the Senzing Bootcamp graduation workflow that generates `docs/README.md` — an index (table of contents) describing the contents of the `docs/` directory. A Medium-priority Workflow/UX feedback item reported that, while graduation produces a clean `production/` tree with its own README, it produces no guide for the `docs/` directory. By track completion, `docs/` has accumulated many artifacts (for example `bootcamp_recap.md`, `bootcamp_journal.md`, `completion_summary.md`, `business_problem.md`, `data_source_evaluation.md`, `stakeholder_summary_module1.md`) plus subdirectories (for example `mapping/`, `progress/`, `visualizations/`, `reference/`, `feedback/`), with no single document explaining what each item is.

Without an index, anyone returning to the project later — or a teammate the bootcamper shares it with — must open files one by one to understand the documentation set. A short index makes the deliverables self-describing and improves handoff.

The graduation workflow is defined in `senzing-bootcamp/steering/graduation.md` and runs after Module 7. This feature adds a graduation step that generates `docs/README.md` from the actual contents of `docs/` at graduation time — enumerating each file and immediate subdirectory that actually exists, each with a one-line purpose description — so the index stays accurate regardless of which modules were completed. The set of artifacts under `docs/` varies by which modules were completed; the index must reflect what is actually present rather than a hardcoded list. Generation is consistent with the existing non-blocking graduation steps: a failure logs a warning and graduation continues. Supporting scripts are Python 3.11+ standard-library only and live under `senzing-bootcamp/scripts/`.

## Glossary

- **Docs index**: `docs/README.md`, a table of contents generated at graduation time that describes every file and immediate subdirectory under `docs/`.
- **Docs directory**: The `docs/` directory in the bootcamper's project, where bootcamp documentation artifacts and subdirectories accumulate.
- **Docs entry**: A single file or immediate subdirectory directly under `docs/` that the index describes.
- **Purpose description**: A one-line text description of a docs entry's purpose, shown alongside that entry in the index.
- **Graduation workflow**: The post-Module-7 workflow defined in `senzing-bootcamp/steering/graduation.md` that transitions a completed bootcamp project into a production-ready codebase.
- **Docs index step**: The graduation step added by this feature that generates the docs index.
- **Graduation report**: `production/GRADUATION_REPORT.md`, always generated at the end of the graduation workflow.

## Requirements

### Requirement 1: Generate the docs index during graduation

**User Story:** As a graduating bootcamper, I want the graduation workflow to generate an index of the `docs/` directory, so that the documentation set is self-describing for handoff.

#### Acceptance Criteria

1. WHEN the Docs_Index_Step runs during the Graduation_Workflow, THE Docs_Index_Step SHALL generate the file `docs/README.md` located directly at the root of the `docs/` directory.
2. WHERE a `docs/README.md` file already exists when the Docs_Index_Step runs, THE Docs_Index_Step SHALL replace its entire contents with the regenerated index, leaving no content from the prior file.
3. THE Docs_Index_Step SHALL write the docs index as a Markdown table of contents that lists the docs entries contained in the `docs/` directory.
4. IF the docs index cannot be written as valid Markdown (parseable as a Markdown table of contents), THEN THE Docs_Index_Step SHALL fail the step, SHALL NOT leave a partially written or malformed `docs/README.md`, and SHALL record the failure reason in the Graduation_Report.

### Requirement 2: Enumerate the actual contents of the docs directory

**User Story:** As a bootcamper, I want the index to reflect the files and folders that actually exist in `docs/`, so that it stays accurate regardless of which modules I completed.

#### Acceptance Criteria

1. WHEN the docs index is generated, THE Docs_Index_Step SHALL enumerate the docs entries by reading the actual contents of the `docs/` directory at graduation time, rather than from a hardcoded list of file names.
2. THE Docs_Index_Step SHALL include in the index each regular file located at the top level of `docs/` (depth 1), and SHALL NOT enumerate files nested inside subdirectories as separate entries.
3. THE Docs_Index_Step SHALL include in the index each subdirectory located at the top level of `docs/` (depth 1) as a single entry, without recursing into its contents.
4. WHEN a docs entry is present at the top level of the `docs/` directory at graduation time, THE Docs_Index_Step SHALL include that entry in the index.
5. IF a docs entry is absent from the top level of the `docs/` directory at graduation time, THEN THE Docs_Index_Step SHALL omit that entry from the index.
6. WHEN the docs index file `docs/README.md` is generated, THE Docs_Index_Step SHALL exclude the index file itself from the enumerated entries.
7. WHEN the docs entries are enumerated, THE Docs_Index_Step SHALL list them in a deterministic, case-insensitive alphabetical order by entry name, so that regenerating the index from identical `docs/` contents produces an identical entry order.
8. IF a top-level docs entry name begins with a dot (`.`), THEN THE Docs_Index_Step SHALL exclude that entry from the index.

### Requirement 3: Describe the purpose of each entry

**User Story:** As a bootcamper or teammate, I want a one-line purpose for each file and subdirectory, so that I can understand the documentation set without opening every file.

#### Acceptance Criteria

1. WHEN a docs entry is listed in the index, THE Docs_Index_Step SHALL include the entry's name and exactly one purpose description for that entry rendered on a single line containing 1 to 120 characters.
2. THE Docs_Index_Step SHALL apply a consistent visual indicator to every subdirectory entry in the index that is applied to no file entry, so that each entry is unambiguously identifiable as either a file or a subdirectory.
3. IF no predefined purpose description is available for a docs entry's name, THEN THE Docs_Index_Step SHALL include a non-empty generic purpose description of 1 to 120 characters for that entry rather than omitting the description.

### Requirement 4: Reliable, non-blocking generation

**User Story:** As a bootcamper, I want index generation to follow the same non-blocking behavior as other graduation steps, so that a problem generating the index does not stop graduation.

#### Acceptance Criteria

1. IF the Docs_Index_Step fails for any reason, THEN THE Graduation_Workflow SHALL record the failure reason in the Graduation_Report and proceed to the next graduation step without halting the Graduation_Workflow.
2. IF the `docs/` directory does not exist at graduation time, THEN THE Docs_Index_Step SHALL skip index generation, record in its one-line summary that the index was not generated, and complete the step with a non-error (success) status.
3. WHILE the `docs/` directory exists at graduation time, THE Docs_Index_Step SHALL proceed with index generation without requesting confirmation that the directory was found.
4. WHEN the docs index is generated successfully, THE Docs_Index_Step SHALL report a success message identifying that the index was generated at `docs/README.md` before reporting the one-line summary.
5. WHEN the Docs_Index_Step completes, THE Docs_Index_Step SHALL report a one-line summary that states whether the index was generated and, when generated, the location `docs/README.md`.
6. IF the docs index is generated but the one-line summary cannot be reported, THEN THE Docs_Index_Step SHALL treat the step as failed and record the failure reason in the Graduation_Report.
