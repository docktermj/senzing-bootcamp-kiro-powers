# Requirements Document

## Introduction

The Module 5 (Data Quality & Mapping) `mapping_workflow` MCP tool downloads its
workflow resources into a single workspace directory (for example
`data/temp/mapping/`). That bundle mixes reusable Python scripts
(`sz_schema_generator.py`, `sz_json_analyzer.py`, `sz_verbatim_check.py`,
`sz_routing_report.py`) and reference files (`senzing_entity_specification.md`,
`senzing_mapping_examples.md`, `identifier_crosswalk.json`) together inside a
scratch directory under `data/temp/`.

This conflicts with the project file-placement policy taught by the bootcamp
(`.py` → `src/` subdirectories, non-README `.md` → `docs/`, data → `data/`,
config JSON → `config/`) and enforced by the `write-policy-gate` hook. Because
the bootcamp's organize step currently runs only after transformation output is
generated, the downloaded scripts and reference documents sit in `data/temp/`
for the duration of the run, where they are easy to clean up or `.gitignore`,
and where a returning developer will not find them at the locations the
structure guide promises.

This feature consolidates the same improvement reported three times in the
feedback file into one change: run the existing organizer
(`senzing-bootcamp/scripts/organize_mapping_files.py`) immediately after the
`mapping_workflow` download so reusable resources are relocated to
policy-correct locations before further work, keep only transient run artifacts
in the workspace, and document the canonical home of the entity specification.
The change is limited to the bootcamp's own steering and documentation around
the MCP tool; it does not modify the MCP tool itself, the organizer's existing
routing rules, or the `write-policy-gate` policy.

## Glossary

- **Mapping_Workflow_Tool**: The `mapping_workflow` MCP tool used in Module 5
  Phase 2. It downloads workflow resources into and reads/writes run artifacts
  from a caller-supplied `workspace_dir`. Its download and workspace behavior
  is owned by the MCP server and cannot be changed by the bootcamp.
- **Module_5_Guidance**: The bootcamp's own instructions that wrap the
  Mapping_Workflow_Tool — the Module 5 companion doc
  (`senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`) and the
  Module 5 steering files under `senzing-bootcamp/steering/`
  (notably `module-05-phase2-data-mapping.md`). This is the system whose
  behavior this feature changes.
- **Organizer**: The existing script
  `senzing-bootcamp/scripts/organize_mapping_files.py`, which routes files from
  a `--source` directory into project subdirectories first-match-wins by
  filename/extension, supports `--project-root` and `--dry-run`, and
  deduplicates canonical single-copy artifacts.
- **Organize_Step**: The action, defined by Module_5_Guidance, of invoking the
  Organizer with `--source <workspace_dir>` and
  `--project-root <bootcamper_project_root>`.
- **Workspace_Dir**: The directory passed to the Mapping_Workflow_Tool as
  `workspace_dir` (for example `data/temp/mapping/`), into which resources are
  downloaded and run artifacts are written.
- **Reusable_Resource**: A downloaded file intended to persist beyond a single
  run — the workflow `.py` scripts and the reference `.md`/`.json` files
  (including `senzing_entity_specification.md`).
- **Transient_Run_Artifact**: A file produced for the workflow's own use during
  a run and not intended for long-term project placement — for example
  `profile_report.md`, `schema_hints.md`, `JOURNAL.md`, and generated JSONL
  output.
- **File_Placement_Policy**: The project's placement rules from `structure.md`:
  `.py` → `src/` subdirectories, non-README `.md` → `docs/`, data → `data/`,
  config JSON → `config/`.
- **Write_Policy_Gate**: The `write-policy-gate` hook that blocks file writes to
  locations that violate the File_Placement_Policy.
- **Entity_Specification**: The reference document
  `senzing_entity_specification.md`, whose canonical project home is
  `docs/reference/`.

## Requirements

### Requirement 1: Run the organize step immediately after download

**User Story:** As a bootcamper, I want reusable mapping resources relocated to
their policy-correct locations as soon as they are downloaded, so that scripts
and reference docs are never left buried in a scratch directory while I continue
working.

#### Acceptance Criteria

1. WHEN the Mapping_Workflow_Tool completes downloading resources into the
   Workspace_Dir, THE Module_5_Guidance SHALL instruct the agent to run the
   Organize_Step before any further mapping work proceeds.
2. THE Module_5_Guidance SHALL invoke the Organize_Step with
   `--source <workspace_dir>` and `--project-root <bootcamper_project_root>`.
3. THE Module_5_Guidance SHALL retain an Organize_Step after transformation
   output is generated, so that output files produced later in the workflow are
   also relocated.
4. WHEN the Organize_Step completes, THE Module_5_Guidance SHALL instruct the
   agent to review the Organizer summary output to confirm files landed at the
   expected locations.

### Requirement 2: Route reusable resources to policy-correct locations

**User Story:** As a developer returning to the project, I want downloaded
scripts and reference documents at the locations the structure guide promises,
so that I can find the analyzer/profiler tools and the entity specification
where they belong.

#### Acceptance Criteria

1. WHEN the Organize_Step processes a downloaded `.py` Reusable_Resource, THE
   Organizer SHALL route the file to a `src/` subdirectory per its existing
   routing rules.
2. WHEN the Organize_Step processes the Entity_Specification, THE Organizer
   SHALL route the file to `docs/reference/` per its existing routing rules.
3. WHEN the Organize_Step processes a reference `.md` or `.json`
   Reusable_Resource, THE Organizer SHALL route the file to its policy-correct
   destination per its existing routing rules.
4. THE Module_5_Guidance SHALL rely on the existing Organizer routing rules and
   SHALL NOT introduce alternative placement destinations for Reusable_Resource
   files that conflict with the File_Placement_Policy.

### Requirement 3: Keep transient run artifacts in the workspace

**User Story:** As a bootcamper, I want the workflow's transient run artifacts
to remain in the workspace, so that the mapping workflow keeps functioning
during the run while only reusable resources are relocated.

#### Acceptance Criteria

1. WHEN the Organize_Step runs, THE Module_5_Guidance SHALL leave
   Transient_Run_Artifact files in the Workspace_Dir for the workflow's
   continued use during the run.
2. THE Module_5_Guidance SHALL identify `profile_report.md`, `schema_hints.md`,
   `JOURNAL.md`, and generated JSONL output as Transient_Run_Artifact files that
   remain in the Workspace_Dir during the run.

### Requirement 4: Document the canonical home of the entity specification

**User Story:** As a bootcamper, I want the Module 5 documentation to state
where the entity specification lives, so that I know its canonical location
without guessing.

#### Acceptance Criteria

1. THE Module_5_Guidance SHALL document the Entity_Specification by its file
   name (`senzing_entity_specification.md`) and SHALL state that its canonical
   home after the Organize_Step completes is `docs/reference/`.
2. THE Module_5_Guidance SHALL document that the Organize_Step runs after the
   Mapping_Workflow_Tool download completes and before any further mapping work
   proceeds, to place Reusable_Resource files in policy-correct locations.
3. THE Module_5_Guidance SHALL state the Entity_Specification's canonical home
   (`docs/reference/`) in the Module 5 companion doc, so that a bootcamper can
   locate the file at that path without inspecting the Workspace_Dir.

### Requirement 5: Preserve the write-policy-gate and MCP tool behavior

**User Story:** As a power maintainer, I want this change to respect the
existing write policy and the MCP tool's required workspace behavior, so that
the bootcamp stays consistent with the rules it teaches and does not break the
mapping workflow.

#### Acceptance Criteria

1. WHEN the Organize_Step relocates a Reusable_Resource, THE Module_5_Guidance SHALL place the file only at a destination permitted by the File_Placement_Policy (`.py` → `src/` subdirectories, non-README `.md` → `docs/`, data → `data/`, config JSON → `config/`), such that the Write_Policy_Gate blocks none of the writes performed during the Organize_Step.
2. WHILE the Mapping_Workflow_Tool run is in progress, THE Module_5_Guidance SHALL NOT relocate, delete, or redirect Transient_Run_Artifact files out of the Workspace_Dir, so that the tool's downloads and run artifacts remain in the Workspace_Dir until the run completes.
3. THE Module_5_Guidance SHALL NOT modify the Mapping_Workflow_Tool, the Organizer's existing routing rules, or the Write_Policy_Gate policy.
4. IF a downloaded file matches no Organizer routing rule, THEN THE Organizer SHALL leave the file in the Workspace_Dir and report the file as unrouted in its summary output.
5. IF the Write_Policy_Gate blocks a write attempted during the Organize_Step, THEN THE Organizer SHALL leave the affected file in the Workspace_Dir and report the blocked destination as an error in its summary output.
