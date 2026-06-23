# Requirements Document

## Introduction

This feature improves how the Senzing Bootcamp Power presents the built-in 500-record evaluation license. A Medium-priority UX feedback item (Module 4, Data Collection) reported that the agent presented the 500-record limit as a constraint that effectively forced the bootcamper toward a small substitute dataset — for example, using CORD records to stand in for their accounts "within the 500-record limit." This reads as the limit being *imposed* on the bootcamper rather than *informing* them of their licensing options, leaving them feeling boxed in when they actually have choices for handling larger volumes.

The bootcamp already establishes the correct framing and the expansion paths during the Module 1 discovery licensing flow (`module-01-phase1-discovery.md`, Steps 6a–6e): a built-in evaluation license, plus three expansion paths — request an evaluation license in-flow via the Senzing MCP server (`submit_feedback` with the `license_request` category, when available), request one through the external support channel, or apply an existing license. The gap is that Module 4 (Data Collection) and other dataset-sizing touchpoints do not consistently carry that framing forward; instead they can present 500 records as a hard cap and steer the bootcamper to shrink their dataset.

This feature ensures that **everywhere** the bootcamp surfaces the 500-record limit it is framed as a *default* evaluation license the bootcamper already has, accompanied by the expansion paths, and that downsizing the dataset is presented as one option among several rather than the only path. All Senzing-specific facts (record capacity, validity period, license-request mechanics) are sourced from the Senzing MCP server at request time, never from training data or hardcoded figures.

## Glossary

- **Built-in evaluation license**: The default Senzing SDK license that allows processing up to a documented record count (currently surfaced as 500) with no license file present.
- **Expansion path**: A documented option for processing more records than the built-in evaluation license allows — in-flow MCP request, external support request, or applying an existing license.
- **In-flow MCP request**: Requesting an evaluation license without leaving the bootcamp, by invoking the Senzing MCP server `submit_feedback` tool with the `license_request` category (available only when the tool is enabled).
- **Dataset-sizing touchpoint**: Any module step or guidance where the bootcamper's data volume is discussed relative to the evaluation limit (notably Module 1 discovery, Module 4 data collection, and Module 6 data processing).
- **Downsizing**: Reducing the working dataset (sampling, choosing a smaller substitute, or using a subset of CORD data) so it fits within the built-in evaluation license.

## Requirements

### Requirement 1: Frame the limit as a default license, not a hard cap

**User Story:** As a bootcamper collecting my data, I want the 500-record limit presented as an evaluation license I already have, so that I understand it is a starting default rather than a wall I cannot move past.

#### Acceptance Criteria

1. WHEN the bootcamp surfaces the 500-record limit at any dataset-sizing touchpoint THEN the system SHALL describe it as a built-in evaluation license the bootcamper already has by default, not as a fixed maximum or a hard cap.
2. WHEN the limit is presented THEN the system SHALL state that the bootcamper has options to process more records, before or alongside any suggestion to reduce the dataset.
3. WHEN the system describes the record capacity or validity period of the evaluation license THEN it SHALL retrieve those values from a Senzing MCP server tool during the session and present exactly what the tool returns.
4. IF a Senzing MCP server tool does not return a capacity or validity value, or the MCP server cannot be reached THEN the system SHALL omit the specific figure and tell the bootcamper the current value is unavailable from the MCP server, and SHALL NOT substitute a hardcoded or remembered figure.

### Requirement 2: Always present the expansion paths

**User Story:** As a bootcamper whose data exceeds 500 records, I want to be told my expansion options, so that I can choose how to handle larger volumes instead of assuming I must shrink my data.

#### Acceptance Criteria

1. WHEN the bootcamper's data exceeds (or may exceed) the built-in evaluation limit THEN the system SHALL present the expansion paths: apply an existing license, request an evaluation license through the external support channel, and — when available — request an evaluation license in-flow via the Senzing MCP server.
2. WHEN determining whether to present the in-flow MCP request path THEN the system SHALL check that the `submit_feedback` tool is available (consistent with the Module 1 licensing flow) and SHALL present the in-flow path only when it is available.
3. WHEN the in-flow MCP request path is unavailable, returns an error, or does not respond THEN the system SHALL present the remaining paths (external request and apply-an-existing-license) without blocking the bootcamper.
4. WHEN the bootcamper already has a Senzing license THEN the system SHALL route them to the apply-an-existing-license path and SHALL omit the in-flow MCP request option.
5. WHERE the Module 1 discovery licensing flow (Steps 6a–6e) already establishes these paths THEN the system SHALL remain consistent with that flow and SHALL NOT contradict its branching or its tool-availability checks.

### Requirement 3: Present downsizing as one option, not the only path

**User Story:** As a bootcamper with a real dataset larger than 500 records, I want downsizing to be offered as a choice rather than assumed, so that I do not feel forced to abandon my own data.

#### Acceptance Criteria

1. WHEN the bootcamper's dataset is larger than the built-in evaluation limit THEN the system SHALL NOT automatically steer the bootcamper to a smaller substitute dataset as the only path forward.
2. WHEN downsizing (sampling, a smaller substitute, or a CORD subset) is mentioned THEN the system SHALL present it as one option alongside the expansion paths in Requirement 2.
3. WHEN the bootcamper chooses to keep their full dataset and pursue an expansion path THEN the system SHALL support that choice and continue the data collection workflow without requiring a reduced dataset.
4. WHEN the bootcamper chooses to downsize THEN the system SHALL continue to support sampling and CORD-subset workflows as it does today.

### Requirement 4: Consistent framing across touchpoints

**User Story:** As a bootcamper, I want the licensing message to be consistent wherever data volume comes up, so that I am not confused by conflicting descriptions of the limit.

#### Acceptance Criteria

1. WHEN the 500-record limit is referenced in Module 4 (Data Collection) THEN the system SHALL use the default-license-with-expansion-paths framing defined in Requirements 1–3.
2. WHEN the limit is referenced in other dataset-sizing touchpoints (e.g., Module 1 discovery and Module 6 data processing) THEN the system SHALL use the same framing, consistent with the existing Module 1 flow.
3. WHEN user-facing reference material describes licensing (e.g., quick-start and module companion docs) THEN it SHALL present the limit as a default with expansion options rather than as a hard cap.
4. WHEN any framing references Senzing license facts THEN the system SHALL source those facts from the Senzing MCP server per Requirement 1, and SHALL NOT introduce hardcoded MCP URLs or external URLs into steering files.
