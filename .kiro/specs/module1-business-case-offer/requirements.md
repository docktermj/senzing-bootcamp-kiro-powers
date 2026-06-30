# Requirements Document

## Introduction

This feature adds an explicit "I can generate a business case for you" offer to the
Senzing Bootcamp's Module 1 (Business Problem) discovery flow. It serves bootcampers who
either have no specific business case yet or have a real case but do not want to expose
sensitive details.

Today, the Module 1 discovery prompt (Step 5 in
`senzing-bootcamp/steering/module-01-phase1-discovery.md`) asks the bootcamper to describe
the problem they are solving, their data, and what success looks like. It assumes the
bootcamper has a case to share. The design-pattern gallery (Step 4) offers ready-made
patterns to adapt, but neither step tells the bootcamper that the bootcamp can generate a
complete scenario — including realistic, multi-source, mapping-complexity-rich data — so
they can experience the full bootcamp without supplying or inventing a case. Bootcampers
who lack a case, or who do not want to disclose one, may stall at the first substantive
question or feel forced to fabricate or expose details. The only known way to reach this
outcome today is for the bootcamper to ask the agent directly (as one did to produce the
"Meridian Bank" scenario), which the bootcamp never advertises.

This feature surfaces a third path in the discovery flow, defines the characteristics of
the generated scenario (realistic, multi-source, mapping-complexity-rich), records the
generated scenario into the same Module 1 artifacts a real case would produce
(`docs/business_problem.md` and `config/data_sources.yaml`), and ensures downstream modules
operate on the generated scenario and its data so the rest of the bootcamp flows without
real data. Consistent with the bootcamp's core constraint, all Senzing-specific facts
(including CORD dataset details) are retrieved from the Senzing MCP server at runtime rather
than from training data.

## Glossary

- **Bootcamp**: The senzing-bootcamp Kiro Power that guides developers through Senzing entity resolution across 11 modules.
- **Agent**: The Kiro agent executing the Bootcamp by following its steering files.
- **Bootcamper**: The developer working through the Bootcamp.
- **Discovery_Flow**: The Module 1 Phase 1 discovery steps defined in `senzing-bootcamp/steering/module-01-phase1-discovery.md`, specifically the design-pattern gallery (Step 4) and the open-ended discovery prompt (Step 5).
- **Discovery_Prompt**: The open-ended Step 5 question that asks the Bootcamper to describe their problem, data, and definition of success.
- **Design_Pattern_Gallery**: The Step 4 presentation of entity resolution design patterns the Bootcamper may adopt as a starting point.
- **Business_Case_Offer**: The explicit third path, presented within the Discovery_Flow, in which the Bootcamp generates a complete scenario for the Bootcamper.
- **Generated_Scenario**: A complete business case produced by the Bootcamp on the Bootcamper's behalf, including a problem description, use-case category, and a definition of success.
- **Scenario_Data**: The multi-source dataset associated with a Generated_Scenario, drawn from CORD datasets or synthetically generated.
- **CORD**: Collections Of Relatable Data — curated Senzing data collections (Las Vegas, London, Moscow) designed for entity resolution evaluation, whose details are retrieved from the MCP_Server at runtime.
- **Generated_Data**: Synthetic multi-source test data produced when CORD data does not fit the Generated_Scenario.
- **Business_Problem_Document**: The Module 1 problem statement artifact at `docs/business_problem.md`.
- **Data_Sources_Config**: The Module 1 data source configuration artifact at `config/data_sources.yaml`.
- **MCP_Server**: The Senzing MCP server configured in `senzing-bootcamp/mcp.json`, the source of all Senzing-specific facts.
- **Downstream_Modules**: The Bootcamp modules after Module 1 that consume the Module 1 artifacts (data sources, problem statement, and dataset).

## Requirements

### Requirement 1: Present the business-case offer as a third path in discovery

**User Story:** As a bootcamper who has no business case or does not want to share one, I want the discovery prompt to tell me the bootcamp can generate a complete scenario for me, so that I can proceed without inventing or exposing a case.

#### Acceptance Criteria

1. WHEN the Discovery_Prompt is presented in Step 5, THE Discovery_Flow SHALL present three separately selectable paths: describing a real business case, selecting a Design_Pattern_Gallery entry, and the Business_Case_Offer.
2. WHERE the Business_Case_Offer is presented, THE Discovery_Flow SHALL state that it applies both when the Bootcamper has no business case and when the Bootcamper has a business case but does not want to share it.
3. WHERE the Business_Case_Offer is presented, THE Discovery_Flow SHALL state that the Bootcamp will generate a Generated_Scenario with realistic multi-source Scenario_Data that enables the Bootcamper to complete the full Bootcamp without supplying or inventing a case.
4. WHEN the Design_Pattern_Gallery is presented in Step 4, THE Discovery_Flow SHALL reference the Business_Case_Offer as an available path the Bootcamper may select.
5. WHEN the Discovery_Prompt is presented, THE Discovery_Flow SHALL present the Business_Case_Offer as a selectable option.
6. IF the Bootcamper has not explicitly accepted the Business_Case_Offer, THEN THE Discovery_Flow SHALL NOT produce a Generated_Scenario.

### Requirement 2: Generate a scenario when the bootcamper accepts the offer

**User Story:** As a bootcamper who accepts the offer, I want the bootcamp to create a complete scenario for me, so that I have a documented business case without supplying my own.

#### Acceptance Criteria

1. WHEN the Bootcamper accepts the Business_Case_Offer, THE Agent SHALL produce, within the active session and before continuing the Discovery_Flow, a Generated_Scenario containing a non-empty problem description, exactly one use-case category, and a non-empty definition of success.
2. WHEN the Bootcamper accepts the Business_Case_Offer, THE Agent SHALL produce a Generated_Scenario whose use-case category exactly matches one entry from the categories recognized by Module 1 (Customer 360, Fraud Detection, Data Migration, Compliance, Marketing, Healthcare, Supply Chain, KYC, Insurance, or Vendor MDM).
3. IF the Bootcamper selected a Design_Pattern_Gallery entry before accepting the Business_Case_Offer, THEN THE Agent SHALL produce a Generated_Scenario whose use-case category matches the selected Design_Pattern_Gallery entry's use-case category.
4. WHEN the Bootcamper declines the Business_Case_Offer, THE Discovery_Flow SHALL continue with the Bootcamper's own description without producing a Generated_Scenario and without writing a Business_Problem_Document from one.
5. IF scenario generation cannot complete after the Bootcamper accepts the Business_Case_Offer, THEN THE Agent SHALL inform the Bootcamper and SHALL fall back to the Bootcamper's own description without writing a Business_Problem_Document.

### Requirement 3: Generated scenario data is multi-source and mapping-complexity-rich

**User Story:** As a bootcamper using a generated scenario, I want its data to be realistic, multi-source, and rich in mapping complexity, so that I exercise the same data-mapping work a real case would require.

#### Acceptance Criteria

1. WHEN the Agent produces Scenario_Data, THE Agent SHALL include records drawn from two or more distinct data sources, where each such data source is separately identified and contributes at least one record.
2. WHEN the Agent produces Scenario_Data, THE Agent SHALL include attributes that require at least one of the following transformations when mapped to the Senzing Entity Specification: differing field names across sources, fields that must be combined or split, or inconsistent value formatting across sources.
3. WHEN the Agent produces Scenario_Data, THE Agent SHALL source it from a CORD dataset or from Generated_Data.
4. WHEN the Agent produces Scenario_Data for a Generated_Scenario, THE Agent SHALL determine whether to use a CORD dataset and SHALL retrieve CORD dataset details from the MCP_Server during the active session rather than from training data.
5. IF no CORD dataset fits the Generated_Scenario, THEN THE Agent SHALL produce Generated_Data that satisfies the criteria in acceptance criteria 1 and 2 rather than using a CORD dataset.

### Requirement 4: Record the generated scenario into Module 1 artifacts

**User Story:** As a bootcamper using a generated scenario, I want it documented in the same artifacts a real case would produce, so that the rest of the bootcamp treats it as my business problem.

#### Acceptance Criteria

1. WHEN a Generated_Scenario is produced, THE Agent SHALL write the Generated_Scenario into the Business_Problem_Document using the same problem-statement structure produced for a Bootcamper-supplied real case.
2. WHEN a Generated_Scenario is produced, THE Agent SHALL record each Scenario_Data source in the Data_Sources_Config such that the number of recorded entries equals the number of distinct Scenario_Data sources.
3. WHEN the Agent writes the Business_Problem_Document for a Generated_Scenario, THE Agent SHALL include an observable marker within the document identifying the business case as bootcamp-generated.
4. WHEN a Generated_Scenario is produced, THE Business_Problem_Document SHALL contain the problem description, the use-case category, the data sources, and the definition of success of the Generated_Scenario, independent of whether the data sources are recorded in the Data_Sources_Config.
5. IF writing the Business_Problem_Document or the Data_Sources_Config fails, THEN THE Agent SHALL indicate the error and inform the Bootcamper.

### Requirement 5: Downstream modules operate on the generated scenario

**User Story:** As a bootcamper who chose a generated scenario, I want the later modules to use that scenario and its data, so that I can complete the full bootcamp without supplying real data.

#### Acceptance Criteria

1. WHEN Module 1 completes with a Generated_Scenario, THE Bootcamp SHALL persist the Generated_Scenario in the Business_Problem_Document and each Scenario_Data source in the Data_Sources_Config such that both artifacts are present and readable by the Downstream_Modules.
2. WHEN a Downstream_Module reads the data sources for the project, THE Downstream_Module SHALL obtain every Scenario_Data source recorded in the Data_Sources_Config.
3. WHILE a Generated_Scenario is in effect, THE Bootcamp SHALL allow the Bootcamper to complete every Downstream_Module using only the Scenario_Data, without requiring the Bootcamper to supply real data.
4. IF the Business_Problem_Document or the Data_Sources_Config is missing or unreadable when a Downstream_Module requests it after Module 1 completes, THEN THE Bootcamp SHALL inform the Bootcamper that the Generated_Scenario data is unavailable and SHALL allow the Bootcamper to supply real data to proceed.

### Requirement 6: Source Senzing and CORD facts from the MCP server

**User Story:** As a maintainer, I want the scenario's Senzing-specific facts to come from the MCP server rather than static text, so that the guidance stays accurate as Senzing's data offerings change.

#### Acceptance Criteria

1. WHEN the Agent presents CORD dataset names, contents, or availability to the Bootcamper, THE Agent SHALL retrieve those facts from the MCP_Server during the active session rather than from training data.
2. WHERE CORD details are returned by the MCP_Server, THE Agent SHALL present those returned values and SHALL NOT substitute static figures.
3. IF the MCP_Server does not return CORD details within 30 seconds of a request, OR the MCP_Server cannot be reached after 1 retry attempt when CORD details are requested, THEN THE Agent SHALL omit the unavailable CORD facts and SHALL produce Generated_Data that satisfies the multi-source and mapping-complexity criteria instead of using CORD data.
4. WHEN the Agent omits CORD facts because the MCP_Server did not return CORD details within the timeout or could not be reached, THE Agent SHALL inform the Bootcamper with a message indicating that CORD details are unavailable from the MCP_Server.
