# Requirements Document

## Introduction

CORD (Collections Of Relatable Data) datasets are downloaded during Module 4 via the `get_sample_data` MCP tool. In many runs these datasets already arrive in a Senzing-loadable form, so sending them through the full Module 5 mapping workflow adds steps and time for data that needs no transformation. This feature lets the bootcamp recognize CORD-sourced data and, when that data is confirmed to already be in a Senzing-loadable form, offer the bootcamper the option to skip the mapping phase and proceed straight to loading in Module 6.

The fast-path is deliberately a conditional *offer*, not an automatic skip. CORD data is not always in the final Senzing-loadable schema — in a real bootcamp run, three CORD sources were profiled as a legacy flat / sub-list structure (not the Senzing FEATURES-array form) and therefore still required structural mapping in Module 5. So the feature couples two independent signals: (1) CORD provenance, recorded when a source is obtained via `get_sample_data`, and (2) a lightweight readiness check confirming the data is already in a Senzing-loadable form. The fast-path is offered only when both hold. A CORD source that is not Senzing-ready — and every non-CORD source — continues through the normal quality assessment and mapping workflow unchanged.

All Senzing schema facts (what constitutes a Senzing-loadable record) come from the Senzing MCP server, never from training data. The feature is delivered primarily through steering Markdown changes, optionally supported by a small standard-library-only readiness helper, and the fast-path decision is recorded in the data source registry so later modules and reconciliation stay consistent.

This feature complements, and must not contradict, the existing `cord-data-priority`, `cord-data-freshness`, `data-source-registry`, and `data-collection-template` specs.

## Glossary

- **Agent**: The AI assistant executing the bootcamp steering files within the Kiro IDE.
- **Bootcamper**: A user working through the Senzing Bootcamp.
- **CORD**: Collections Of Relatable Data — curated sample datasets provided by Senzing, obtained via the `get_sample_data` MCP tool.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides tools including `get_sample_data`, `analyze_record`, and `download_resource`, and is the single authoritative source of Senzing schema and SDK facts.
- **Entity_Specification**: The Senzing Generic Entity Specification retrieved from the MCP_Server (via `download_resource(filename="senzing_entity_specification.md")`), which defines Senzing attribute names and structures.
- **Senzing_Loadable_Form**: A record structure that conforms to the Senzing-acceptable schema (for example, a FEATURES-array structure with `DATA_SOURCE` and `RECORD_ID` present or derivable) as defined by the Entity_Specification obtained from the MCP_Server.
- **Legacy_Structure**: A CORD record structured as a flat or sub-list layout that does not conform to the Senzing_Loadable_Form and therefore requires structural mapping.
- **Provenance**: The recorded origin of a data source, stored in the source's Registry_Entry. A value of `cord` indicates the source was obtained via `get_sample_data`.
- **Registry**: The YAML file at `config/data_sources.yaml` in the bootcamper's project directory, defined by the `data-source-registry` spec.
- **Registry_Entry**: A single data source record within the Registry, keyed by the DATA_SOURCE name.
- **Readiness_Check**: A lightweight determination of whether a CORD source is already in Senzing_Loadable_Form versus a Legacy_Structure that still needs mapping.
- **Readiness_Check_Helper**: An optional Python standard-library-only script under `senzing-bootcamp/scripts/` that performs the lightweight structural pre-screen for the Readiness_Check.
- **Senzing_Ready**: The Readiness_Check outcome indicating a CORD source is already in Senzing_Loadable_Form.
- **Fast_Path**: The workflow branch in which the Module 5 data mapping phase is bypassed for a source and the source proceeds directly to loading in Module 6.
- **Mapping_Phase**: Module 5 Phase 2 (Data Mapping) — the transformation workflow that the Fast_Path bypasses.
- **Module_4_Steering**: The steering file `senzing-bootcamp/steering/module-04-data-collection.md`.
- **Module_5_Steering**: The Module 5 steering files, including `module-05-data-quality-mapping.md`, `module-05-phase1-quality-assessment.md`, and `module-05-phase2-data-mapping.md`.
- **Module_6_Loading**: The loading workflow (Module 6) that a fast-pathed source proceeds to.
- **Steering_Index**: The token-budget index file at `senzing-bootcamp/steering/steering-index.yaml`.

## Requirements

### Requirement 1: Record CORD Provenance

**User Story:** As a Bootcamper, I want the bootcamp to remember that a data source came from CORD, so that later steps can recognize its origin without re-deriving it.

#### Acceptance Criteria

1. WHEN a data source is obtained via the `get_sample_data` MCP tool during Module 4, THE Agent SHALL set the `provenance` field of that source's Registry_Entry to `cord`.
2. WHEN a data source is obtained from an origin other than the `get_sample_data` MCP tool, THE Agent SHALL set the `provenance` field of that source's Registry_Entry to a non-CORD value of `own`, `free_data`, or `synthesized`.
3. THE `provenance` field SHALL be an additive optional field of the Registry_Entry that leaves the required fields and the `mapping_status` and `load_status` value sets defined by the `data-source-registry` spec unchanged.
4. WHEN the Agent needs to determine whether a source is CORD, THE Agent SHALL read the recorded `provenance` field from the Registry_Entry.
5. IF a source's origin cannot be determined, THEN THE Agent SHALL set the `provenance` field to `unknown` and treat the source as non-CORD for Fast_Path eligibility.
6. WHEN the Agent creates or updates the `provenance` field, THE Agent SHALL set the Registry_Entry `updated_at` field to the current ISO 8601 timestamp.

### Requirement 2: Assess CORD Readiness for Loading

**User Story:** As a Bootcamper, I want the bootcamp to check whether my CORD data is already in a Senzing-loadable form, so that mapping is only skipped when the data genuinely does not need it.

#### Acceptance Criteria

1. WHERE a source's `provenance` is `cord`, THE Agent SHALL perform a Readiness_Check for that source before recommending a mapping approach.
2. WHEN determining what constitutes a Senzing_Loadable_Form, THE Agent SHALL obtain the definition from the MCP_Server, using the Entity_Specification or `analyze_record`, and SHALL NOT assert Senzing schema facts from training data.
3. THE Readiness_Check SHALL classify a CORD source as Senzing_Ready only when the source's sampled records conform to the Senzing_Loadable_Form defined by the Entity_Specification obtained from the MCP_Server.
4. WHEN a CORD source is structured as a Legacy_Structure, THE Readiness_Check SHALL classify the source as not Senzing_Ready.
5. THE Readiness_Check SHALL evaluate a bounded sample of at most 100 records from the source so that the check remains lightweight.
6. WHEN the Readiness_Check completes, THE Agent SHALL record the boolean outcome in the source's Registry_Entry `senzing_ready` field and set `updated_at` to the current ISO 8601 timestamp.
7. IF the Readiness_Check cannot reach the MCP_Server or cannot conclusively determine readiness, THEN THE Agent SHALL classify the source as not Senzing_Ready.
8. WHERE the Readiness_Check_Helper is used, THE Readiness_Check_Helper SHALL rely only on the Python standard library and SHALL limit itself to lightweight structural detection without asserting Senzing schema facts independently of the MCP_Server.
9. WHERE a source has already been classified as Senzing_Ready by conforming to the Senzing_Loadable_Form, THE Agent SHALL treat the source as Senzing_Ready regardless of the retrieval path used to obtain the Senzing_Loadable_Form definition.

### Requirement 3: Offer the Fast-Path for Ready CORD Sources

**User Story:** As a Bootcamper, I want to be offered the option to skip mapping when my CORD data is already loadable, so that I avoid redundant steps and reach loading faster.

#### Acceptance Criteria

1. WHERE a source's `provenance` is `cord` AND the source is Senzing_Ready, WHEN the Agent reaches the mapping decision point for that source, THE Agent SHALL offer to skip the Mapping_Phase and proceed directly to Module_6_Loading.
2. WHEN the Agent presents the Fast_Path offer, THE Agent SHALL present it as a single leading question formatted in bold with the 👉 marker and SHALL stop and wait for the Bootcamper's answer.
3. WHERE a source is Fast_Path eligible, THE Agent SHALL present the Fast_Path offer so that the offer step is never omitted while its conditions hold.
4. THE Agent SHALL NOT bypass the Mapping_Phase for any source without an explicit confirming answer from the Bootcamper.
5. WHEN the Bootcamper confirms the Fast_Path offer, THE Agent SHALL bypass the Mapping_Phase for that source and route the source to Module_6_Loading.
6. IF the Bootcamper declines the Fast_Path offer, THEN THE Agent SHALL route the source through the normal Mapping_Phase workflow.

### Requirement 4: Route Non-Ready CORD Sources Through Mapping

**User Story:** As a Bootcamper, I want CORD data that is not yet loadable to still go through mapping, so that structurally different CORD sources are transformed correctly.

#### Acceptance Criteria

1. IF a source's `provenance` is `cord` AND the source is not Senzing_Ready, THEN THE Agent SHALL route the source through the normal Module 5 quality assessment and Mapping_Phase workflow.
2. WHEN a CORD source is not Senzing_Ready, THE Agent SHALL withhold the Fast_Path offer for that source.
3. WHEN a not-Senzing_Ready CORD source is routed through mapping, THE Agent SHALL treat the source identically to any source that requires structural mapping.

### Requirement 5: Leave Non-CORD Sources Unchanged

**User Story:** As a Bootcamper, I want my own data and other non-CORD sources to follow the existing workflow, so that the fast-path does not alter behavior for data that always needs mapping.

#### Acceptance Criteria

1. WHERE a source's `provenance` is not `cord`, THE Agent SHALL route the source through the existing Module 5 quality assessment and Mapping_Phase workflow.
2. WHERE a source's `provenance` is not `cord`, THE Agent SHALL withhold the Fast_Path offer for that source.
3. IF Module 5 or the Mapping_Phase is temporarily unavailable when a non-CORD source is ready to be processed, THEN THE Agent SHALL queue the source until Module 5 and the Mapping_Phase are available again rather than failing the source.

### Requirement 6: Record the Fast-Path Decision and Preserve Lineage

**User Story:** As a Bootcamper, I want the fast-path decision recorded, so that later modules and reconciliation reflect that a source loaded without transformation.

#### Acceptance Criteria

1. WHEN the Bootcamper confirms the Fast_Path for a source, THE Agent SHALL set that source's Registry_Entry `mapping_status` to `complete`, using the value set already defined by the `data-source-registry` spec.
2. WHEN the Bootcamper confirms the Fast_Path for a source, THE Agent SHALL set a `fast_pathed` boolean field to true in that source's Registry_Entry.
3. WHEN a source is fast-pathed, THE Agent SHALL keep the Registry_Entry `file_path` pointing at the original CORD file in `data/raw/`, because no transformed output is produced.
4. WHEN a source is fast-pathed, THE Agent SHALL record a data-lineage entry indicating that no transformation occurred, with the input and output referring to the same file and equal before-and-after record counts.
5. WHEN the Agent updates a Registry_Entry for a Fast_Path decision, THE Agent SHALL set the `updated_at` field to the current ISO 8601 timestamp.
6. THE `fast_pathed` field SHALL be an additive optional field of the Registry_Entry that leaves the required fields and the existing `mapping_status` and `load_status` value sets unchanged.
7. THE Agent SHALL record a data-lineage entry only for sources that are explicitly fast-pathed.
8. IF recording the data-lineage entry for a fast-pathed source fails, THEN THE Agent SHALL allow the Fast_Path to proceed and SHALL log the lineage recording failure for later retry.

### Requirement 7: Preserve Existing Loading Safeguards for Fast-Pathed Sources

**User Story:** As a Bootcamper, I want a fast-pathed CORD source to still pass the existing load-time checks, so that skipping mapping does not skip safety checks.

#### Acceptance Criteria

1. WHEN a fast-pathed source proceeds to Module_6_Loading, THE Agent SHALL apply the existing pre-load CORD freshness verification defined by the `cord-data-freshness` spec to that source.
2. THE Fast_Path behavior SHALL retain the Module_6_Loading safeguards that apply to CORD data.

### Requirement 8: Honor Power Delivery Constraints

**User Story:** As a power developer, I want the fast-path feature to follow the power's delivery and MCP-first constraints, so that the change ships safely to users.

#### Acceptance Criteria

1. THE Fast_Path feature SHALL be delivered primarily through steering Markdown changes under `senzing-bootcamp/steering/`.
2. THE Fast_Path feature SHALL obtain all Senzing schema and loadability facts from the MCP_Server and SHALL NOT hardcode Senzing schema facts in steering files or scripts.
3. WHERE the Readiness_Check_Helper script is added, THE Readiness_Check_Helper SHALL reside under `senzing-bootcamp/scripts/`, use only the Python standard library, and follow the `snake_case` naming convention with a `main()` entry point and an argparse CLI.
4. WHEN steering files are modified for the Fast_Path feature, THE Agent SHALL update the token budgets recorded in the Steering_Index so that they remain accurate.
5. IF the MCP_Server is unavailable, THEN THE Agent SHALL not proceed with schema-dependent Fast_Path steps until the MCP_Server is available.
