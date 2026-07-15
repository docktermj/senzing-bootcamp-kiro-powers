# Requirements Document

## Introduction

This feature enriches the Senzing Bootcamp graduation / track-completion experience so it produces navigable, shareable project documentation instead of ending at a chat celebration. A Medium-priority UX/Workflow feedback item reported that graduation celebrated Core-track completion but left the project's artifacts undocumented and hard to navigate: there was no source-code index, no data index, no top-level pointer to the per-directory indexes, and no closing announcement telling the bootcamper where the recap, recap PDF, and indexes live.

The graduation workflow is defined in `senzing-bootcamp/steering/graduation.md` (it runs after Module 7 for the Core track and after Module 11 for the Advanced track), and the track-completion celebration and shareable deliverables are defined in `senzing-bootcamp/steering/module-completion-track.md`.

Several pieces of the original feedback are **already specified elsewhere**, and this feature deliberately **extends and reuses** them rather than redefining them:

- **`docs/README.md`** generation is already specified by the `graduation-docs-index` feature (a graduation step that generates `docs/README.md` via a generator, `senzing-bootcamp/scripts/generate_docs_index.py`). This feature reuses that step and mirrors its generator pattern for the new indexes.
- **The full-bootcamp recap PDF** (per-module Information Shared / Questions & Responses / Actions Taken) is already guaranteed by the `guaranteed-graduation-artifacts` feature (enforced recap plus a rendered recap PDF, with an HTML fallback when `fpdf2` is absent) and made resilient by the `graduation-recap-pdf-resilience` feature (bundled-helper-first with a self-contained inline fallback). This feature relies on those for generation and resilience and adds only the presentation-polish and announce-location expectations.
- **The journal/recap pointer** ties into the `journal-recap-consolidation` feature, which merges `docs/bootcamp_journal.md` and `docs/bootcamp_recap.md` into a single consolidated `docs/bootcamp_recap.md` carrying a `### Journal` subsection. This feature references that consolidated file and does not reintroduce a separate journal.

The **genuinely new scope** of this feature is therefore:

- **A** — a source-code index step that generates `src/README.md`: an annotated, depth-1 index of every top-level file and immediate subdirectory under `src/`, each with a one-line synopsis, generated at graduation from actual disk contents, deterministic and idempotent, and valid Markdown.
- **B** — a data index step that generates `data/README.md` with the same properties, for the `data/` directory.
- **C** — a top-level `README.md` update step that points to `docs/README.md`, `src/README.md`, and `data/README.md`, each with a synopsis, applied idempotently to a managed section without clobbering existing top-level README content.
- **D** — a graduation artifact-announcement step that tells the bootcamper the locations of the consolidated recap, the full-bootcamp recap PDF, and the three per-directory indexes plus the updated top-level README.
- **E** — a presentation-polish expectation for the recap PDF so it reads as a finished artifact representing the bootcamp experience.

New supporting scripts are Python 3.11+ standard-library only, live under `senzing-bootcamp/scripts/`, and mirror the deterministic, `--check`-capable, atomic-write, skip-is-success behavior of `generate_docs_index.py`. Everything under `senzing-bootcamp/` ships to users, so no PII, credentials, or internal-only URLs are introduced.

## Glossary

- **Graduation_Workflow**: The post-track-completion workflow defined in `senzing-bootcamp/steering/graduation.md` that transitions a completed bootcamp project into a production-ready codebase; it runs after Module 7 (Core track) or Module 11 (Advanced track).
- **Graduation_Report**: `production/GRADUATION_REPORT.md`, always generated at the end of the Graduation_Workflow, including an "⚠️ Issues Encountered" section for any step that failed.
- **Src_Index_Step**: The new graduation step that generates the source-code index file `src/README.md`.
- **Data_Index_Step**: The new graduation step that generates the data index file `data/README.md`.
- **Directory_Index_Step**: Either the Src_Index_Step or the Data_Index_Step; used to state behavior that both steps share.
- **Directory index**: The generated index file produced by a Directory_Index_Step — `src/README.md` for the Src_Index_Step and `data/README.md` for the Data_Index_Step.
- **Target directory**: The directory a Directory_Index_Step indexes — `src/` for the Src_Index_Step and `data/` for the Data_Index_Step.
- **Directory entry**: A single regular file or immediate subdirectory located at the top level (depth 1) of a Target directory that a Directory index describes.
- **Synopsis**: A one-line text description of a Directory entry's purpose, shown alongside that entry in an index.
- **Docs_Index_Step**: The existing graduation step, defined by the `graduation-docs-index` feature, that generates `docs/README.md` via `senzing-bootcamp/scripts/generate_docs_index.py`. This feature reuses it unchanged.
- **Readme_Index_Step**: The new graduation step that updates the top-level `README.md` to point to the docs, source, and data indexes.
- **Managed_Section**: A delimited block within the top-level `README.md`, bounded by stable begin and end markers, that the Readme_Index_Step owns and regenerates; content outside this block is never modified.
- **Consolidated_Recap**: The single per-module recap file `docs/bootcamp_recap.md` defined by the `journal-recap-consolidation` feature, which carries the structured recap content and the narrative journal content (as a `### Journal` subsection) for every completed module.
- **Recap_PDF**: The shareable rendered recap — `docs/bootcamp_recap.pdf` when `fpdf2` is available, otherwise the HTML fallback `docs/bootcamp_recap.html` — produced and guaranteed by the `guaranteed-graduation-artifacts` and `graduation-recap-pdf-resilience` features.
- **Artifact_Announcement_Step**: The closing graduation step that names the locations of the enriched artifacts; it extends the mandatory closing announcement defined by the `guaranteed-graduation-artifacts` feature.
- **fpdf2**: The optional, lazily-imported Python PDF library (`import fpdf`) used only by the PDF-rendering scripts, which degrade gracefully when it is absent.

## Requirements

### Requirement 1: Generate the source and data indexes during graduation

**User Story:** As a graduating bootcamper, I want the graduation workflow to generate an index of the `src/` directory and an index of the `data/` directory, so that my code and data artifacts are self-describing for handoff.

#### Acceptance Criteria

1. WHEN the Src_Index_Step runs during the Graduation_Workflow, THE Src_Index_Step SHALL generate the file `src/README.md` located directly at the root of the `src/` directory.
2. WHEN the Data_Index_Step runs during the Graduation_Workflow, THE Data_Index_Step SHALL generate the file `data/README.md` located directly at the root of the `data/` directory.
3. WHERE a Directory index already exists when its Directory_Index_Step runs, THE Directory_Index_Step SHALL replace the entire contents of that Directory index with the regenerated index, retaining no content from the prior file.
4. THE Directory_Index_Step SHALL write its Directory index as a Markdown table of contents that lists the Directory entries contained in its Target directory.
5. WHEN a Directory_Index_Step regenerates its Directory index from identical Target directory contents, THE Directory_Index_Step SHALL produce byte-identical index output.
6. IF a Directory_Index_Step cannot write its Directory index as valid Markdown parseable as a table of contents, THEN THE Directory_Index_Step SHALL fail the step, SHALL NOT leave a partially written or malformed Directory index, and SHALL record the failure reason in the Graduation_Report.

### Requirement 2: Enumerate the actual contents of the source and data directories

**User Story:** As a bootcamper, I want each index to reflect the files and folders that actually exist in that directory, so that it stays accurate regardless of which modules I completed.

#### Acceptance Criteria

1. WHEN a Directory_Index_Step generates its Directory index, THE Directory_Index_Step SHALL enumerate the Directory entries by reading the actual contents of its Target directory at graduation time, rather than from a hardcoded list of names.
2. THE Directory_Index_Step SHALL include in its Directory index each regular file located at the top level (depth 1) of its Target directory, and SHALL NOT enumerate files nested inside subdirectories as separate entries.
3. THE Directory_Index_Step SHALL include in its Directory index each subdirectory located at the top level (depth 1) of its Target directory as a single entry, without recursing into that subdirectory's contents.
4. WHEN a Directory entry is present at the top level of the Target directory at graduation time, THE Directory_Index_Step SHALL include that Directory entry in its Directory index.
5. IF a Directory entry is absent from the top level of the Target directory at graduation time, THEN THE Directory_Index_Step SHALL omit that Directory entry from its Directory index.
6. WHEN a Directory_Index_Step generates its Directory index file, THE Directory_Index_Step SHALL exclude the Directory index file itself from the enumerated Directory entries.
7. WHEN the Directory entries are enumerated, THE Directory_Index_Step SHALL order them in a deterministic, case-insensitive alphabetical order by entry name, so that regenerating the index from identical Target directory contents produces an identical entry order.
8. IF a top-level Directory entry name begins with a dot (`.`), THEN THE Directory_Index_Step SHALL exclude that Directory entry from its Directory index.

### Requirement 3: Describe the purpose of each entry with a synopsis

**User Story:** As a bootcamper or teammate, I want a one-line synopsis for each file and subdirectory in the source and data indexes, so that I can understand the code and data set without opening every file.

#### Acceptance Criteria

1. WHEN a Directory entry is listed in a Directory index, THE Directory_Index_Step SHALL include the entry's name and exactly one Synopsis for that entry rendered on a single line containing 1 to 120 characters.
2. THE Directory_Index_Step SHALL apply a consistent visual indicator to every subdirectory entry in its Directory index that is applied to no file entry, so that each Directory entry is unambiguously identifiable as either a file or a subdirectory.
3. IF no predefined Synopsis is available for a Directory entry's name, THEN THE Directory_Index_Step SHALL include a non-empty generic Synopsis of 1 to 120 characters for that Directory entry rather than omitting the Synopsis.

### Requirement 4: Reliable, non-blocking generation of the source and data indexes

**User Story:** As a bootcamper, I want index generation to follow the same non-blocking behavior as other graduation steps, so that a problem generating an index does not stop graduation.

#### Acceptance Criteria

1. IF a Directory_Index_Step fails for any reason, THEN THE Graduation_Workflow SHALL record the failure reason in the Graduation_Report and proceed to the next graduation step without halting the Graduation_Workflow.
2. IF the Target directory of a Directory_Index_Step does not exist at graduation time, THEN THE Directory_Index_Step SHALL skip index generation, record in its one-line summary that the index was not generated, and complete the step with a non-error success status.
3. WHILE the Target directory exists at graduation time, THE Directory_Index_Step SHALL proceed with index generation without requesting confirmation that the directory was found.
4. WHEN a Directory_Index_Step generates its Directory index successfully, THE Directory_Index_Step SHALL report a success message identifying the location of the generated Directory index before reporting the one-line summary.
5. WHEN a Directory_Index_Step completes, THE Directory_Index_Step SHALL report a one-line summary that states whether the Directory index was generated and, when generated, the location of the Directory index file.

### Requirement 5: Update the top-level README with an artifact index

**User Story:** As a bootcamper or teammate, I want the top-level `README.md` to point to the docs, source, and data indexes with a synopsis of each, so that I can navigate the whole project from the front page without losing my existing README content.

#### Acceptance Criteria

1. WHEN the Readme_Index_Step runs, THE Readme_Index_Step SHALL ensure the top-level `README.md` contains a Managed_Section that links to `docs/README.md`, `src/README.md`, and `data/README.md`, each accompanied by a Synopsis of 1 to 120 characters, whether the step is invoked as part of the Graduation_Workflow or on its own.
2. THE Readme_Index_Step SHALL delimit the Managed_Section with a stable begin marker and a stable end marker so that the Managed_Section can be located and replaced on subsequent runs.
3. THE Readme_Index_Step SHALL preserve all top-level `README.md` content located outside the Managed_Section without modification.
4. WHEN the Readme_Index_Step runs on a top-level `README.md` that already contains a Managed_Section, THE Readme_Index_Step SHALL replace only the content between the begin and end markers and SHALL leave all content outside those markers unchanged.
5. WHEN the Readme_Index_Step runs on an existing top-level `README.md` that contains no Managed_Section, THE Readme_Index_Step SHALL append the Managed_Section to the file and SHALL leave the pre-existing content unchanged.
6. IF the top-level `README.md` does not exist at graduation time, THEN THE Readme_Index_Step SHALL create `README.md` containing the Managed_Section.
7. WHEN the Readme_Index_Step runs on a top-level `README.md` whose Managed_Section and referenced indexes are unchanged, THE Readme_Index_Step SHALL produce a byte-identical `README.md`.
8. IF a per-directory index (`docs/README.md`, `src/README.md`, or `data/README.md`) does not exist when the Readme_Index_Step runs, THEN THE Readme_Index_Step SHALL omit that index's entry from the Managed_Section.
9. IF the Readme_Index_Step cannot write a valid-Markdown Managed_Section, THEN THE Readme_Index_Step SHALL fail the step, SHALL NOT leave a partially written or malformed `README.md`, and SHALL record the failure reason in the Graduation_Report.
10. IF the Readme_Index_Step fails for any reason, THEN THE Graduation_Workflow SHALL record the failure reason in the Graduation_Report and proceed to the next graduation step without halting the Graduation_Workflow.

### Requirement 6: Announce the enriched artifacts at graduation

**User Story:** As a graduating bootcamper, I want the closing graduation announcement to tell me where my recap, recap PDF, and per-directory and top-level indexes live, so that none of my navigable deliverables go unnoticed.

#### Acceptance Criteria

1. WHEN graduation completes, THE Artifact_Announcement_Step SHALL, as part of the mandatory closing announcement defined by the `guaranteed-graduation-artifacts` feature, state the location of the Consolidated_Recap at `docs/bootcamp_recap.md`.
2. WHEN the Artifact_Announcement_Step announces the Consolidated_Recap, THE Artifact_Announcement_Step SHALL identify `docs/bootcamp_recap.md` as the single per-module recap that also carries the narrative journal content, rather than referencing a separate `docs/bootcamp_journal.md` file.
3. WHERE the Recap_PDF has been produced by the `guaranteed-graduation-artifacts` feature, WHEN graduation completes, THE Artifact_Announcement_Step SHALL state the location of the Recap_PDF (`docs/bootcamp_recap.pdf`, or the HTML fallback `docs/bootcamp_recap.html` when `fpdf2` is unavailable).
4. WHEN graduation completes, THE Artifact_Announcement_Step SHALL state the locations of `docs/README.md`, `src/README.md`, `data/README.md`, and the top-level `README.md`.
5. THE Artifact_Announcement_Step SHALL report only those artifacts confirmed to exist at their stated paths at announcement time, and SHALL omit from the announcement any artifact that is not confirmed to exist.
6. WHEN graduation completes, THE Artifact_Announcement_Step SHALL emit the announcement exactly once.

### Requirement 7: Polished full-bootcamp recap PDF presentation

**User Story:** As a graduating bootcamper, I want the full-bootcamp recap PDF presented as nicely as possible, so that it is a polished artifact representing my bootcamp experience that I can share.

#### Acceptance Criteria

1. WHEN the Recap_PDF is rendered at graduation, THE Recap_PDF SHALL present, for every completed module, the three labeled sections Information Shared, Questions & Responses, and Actions Taken.
2. THE Recap_PDF SHALL apply consistent presentation formatting across all module sections, including a title element identifying the bootcamp and its completion, a distinct heading for each module, and readable list and code-block formatting.
3. THE feature SHALL rely on the recap PDF generation, `fpdf2` graceful-degradation, and HTML-fallback behavior defined by the `guaranteed-graduation-artifacts` and `graduation-recap-pdf-resilience` features, and SHALL NOT redefine that generation, degradation, or fallback behavior.
4. IF `fpdf2` is unavailable when the Recap_PDF is rendered at graduation, THEN THE feature SHALL rely on the stdlib-only HTML fallback (`docs/bootcamp_recap.html`) guaranteed by the `guaranteed-graduation-artifacts` feature, and graduation SHALL remain non-blocking rather than halting until `fpdf2` is installed.

### Requirement 8: Consistency with existing graduation specs

**User Story:** As a power maintainer, I want this feature to extend rather than contradict or duplicate the existing graduation specs, so that the graduation workflow stays coherent.

#### Acceptance Criteria

1. THE feature SHALL reuse the existing Docs_Index_Step defined by the `graduation-docs-index` feature to generate `docs/README.md`, and SHALL NOT redefine or duplicate docs index generation.
2. THE feature SHALL rely on the `guaranteed-graduation-artifacts` feature to guarantee that the recap, transcript, and rendered recap exist and are non-empty at every stopping point, and SHALL NOT weaken those guarantees.
3. THE feature SHALL rely on the `graduation-recap-pdf-resilience` feature for resilient recap PDF generation, and SHALL NOT redefine its bundled-helper-versus-inline fallback behavior.
4. WHEN the feature references per-module completion history, THE feature SHALL reference the Consolidated_Recap at `docs/bootcamp_recap.md` defined by the `journal-recap-consolidation` feature, and SHALL NOT reintroduce a separately written `docs/bootcamp_journal.md`.
5. THE Artifact_Announcement_Step SHALL extend the existing mandatory closing announcement rather than introduce a second competing closing announcement.

### Requirement 9: Graduation step ordering and integration

**User Story:** As a bootcamper, I want the new index steps to run in a predictable order within graduation, so that the top-level README and the closing announcement reference indexes that already exist.

#### Acceptance Criteria

1. THE Graduation_Workflow SHALL run the Src_Index_Step and the Data_Index_Step during graduation alongside the existing Docs_Index_Step and before the Artifact_Announcement_Step.
2. WHEN the Readme_Index_Step runs, THE Graduation_Workflow SHALL have already completed the Docs_Index_Step, the Src_Index_Step, and the Data_Index_Step, so that the Managed_Section references indexes that have already been generated.
3. WHEN the Artifact_Announcement_Step runs, THE Graduation_Workflow SHALL have already completed the Src_Index_Step, the Data_Index_Step, and the Readme_Index_Step.
4. THE Graduation_Workflow SHALL execute the Src_Index_Step, the Data_Index_Step, and the Readme_Index_Step as non-blocking steps consistent with the existing Docs_Index_Step, such that a failure of any one step — whether it fails to start or fails during execution, and regardless of how many of these steps fail — records its reason in the Graduation_Report and does not prevent the remaining steps from running.

### Requirement 10: Script, steering, and distribution constraints

**User Story:** As a power maintainer, I want the new generators and steering changes to follow the workspace rules, so that the feature is safe to ship and keeps CI green.

#### Acceptance Criteria

1. WHERE new generator scripts are added for the source index, data index, and top-level README update, THE feature SHALL place them under `senzing-bootcamp/scripts/` using `snake_case.py` naming, each with a `main()` entry point and an argparse command-line interface.
2. THE new generator scripts SHALL use only the Python 3.11+ standard library.
3. THE new generator scripts SHALL each provide a `--check` mode that reports drift without writing any file and exits with a non-zero status when the on-disk output differs from a freshly generated output, consistent with `generate_docs_index.py`.
4. WHEN a new generator writes its output file, THE generator SHALL write the file atomically so that a failure never leaves a partial or malformed output file.
5. THE generated `src/README.md`, the generated `data/README.md`, and the updated top-level `README.md` SHALL be valid CommonMark so that `validate_commonmark.py` passes.
6. WHEN steering files are added or changed for the new graduation steps, THE `steering/steering-index.yaml` token counts SHALL be updated so that `measure_steering.py --check` passes.
7. THE feature SHALL keep the CI gates green, including `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, and the pytest suite.
8. THE files added or changed under `senzing-bootcamp/` SHALL contain no PII, credentials, or internal-only URLs, and SHALL NOT introduce any external endpoint other than the Senzing MCP server URL (`mcp.senzing.com`).
9. THE feature SHALL include tests following the project pattern (pytest plus Hypothesis where useful, class-based, `sys.path` import) located in `senzing-bootcamp/tests/`, covering the deterministic and idempotent generation of `src/README.md` and `data/README.md` and the non-destructive, idempotent top-level README Managed_Section update.
