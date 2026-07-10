# Requirements Document

## Introduction

Module 3 (System Verification) is designed to run a deterministic verification pass against a Senzing TruthSet — a curated dataset with published expected-result counts and known matches — so that Step 7 can compare resolved outcomes against known-good values. The current design acquires the TruthSet by calling the MCP server's `get_sample_data` tool.

On some MCP server versions, `get_sample_data` exposes only the CORD collections (Las Vegas, London, Moscow) and no named TruthSet. When that happens, deterministic verification cannot run as designed, and the agent is forced onto a substitute dataset with no published expected results.

This feature ADDS a fallback acquisition path to Module 3. It does not replace the primary path. When the MCP server provides a usable TruthSet, that TruthSet is used exactly as today. Only when no MCP-provided TruthSet is available does the module fetch the demo TruthSet published in the official Senzing `truth-sets` repository, so the deterministic verification (expected entity counts, known matches) is preserved.

The Senzing `truth-sets` repository is a new external source. The workspace security posture allows only the MCP server (`mcp.senzing.com`) as an external endpoint and flags steering that references external URLs. This feature therefore treats the `truth-sets` repository as an explicitly sanctioned, reviewed fallback source, declared once in a documented location, used only for TruthSet DATA, while every Senzing SDK fact continues to come from the MCP server.

## Glossary

- **System_Verification_Module**: Module 3 of the Senzing Bootcamp, responsible for confirming the bootcamper's environment is fully functional before proceeding to subsequent modules.
- **TruthSet_Acquisition**: The component of the System_Verification_Module responsible for obtaining TruthSet data and its paired expected results before data loading (Step 2 of the Module 3 pipeline).
- **TruthSet**: A curated, deterministic dataset with known entities, known matches, and predictable resolution outcomes, used by the System_Verification_Module for deterministic verification.
- **Primary_TruthSet**: A TruthSet provided by the MCP_Server through the `get_sample_data` tool with a named TruthSet reference.
- **Fallback_TruthSet**: The demo TruthSet fetched from the Sanctioned_Fallback_Source when no Primary_TruthSet is available.
- **CORD_Collection**: A sample data collection exposed by `get_sample_data` (Las Vegas, London, or Moscow) that has no published expected-result counts or known matches.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that generates SDK code, provides documentation, and supplies authoritative Senzing facts via tool calls.
- **Sanctioned_Fallback_Source**: The official Senzing `truth-sets` repository (`https://github.com/Senzing/truth-sets`), specifically the demo set under `truthsets/demo`, explicitly approved as the single external source for Fallback_TruthSet data.
- **Sanctioned_Source_Registry**: A single reviewed, documented power-level configuration entry (`senzing-bootcamp/config/fallback_sources.yaml`) that declares the Sanctioned_Fallback_Source location, its purpose, and its approval rationale, and is the only place the raw fallback URL is defined.
- **Expected_Results**: The predetermined entity resolution outcomes for a TruthSet — expected entity count, known matched record pairs, and known relationship patterns — that Step 7 validates against.
- **Fallback_Expected_Results**: Expected_Results derived from the Sanctioned_Fallback_Source demo set's published truth definitions and paired with the Fallback_TruthSet.
- **TruthSet_Data_File**: The saved TruthSet record file at `src/system_verification/truthset_data.jsonl` consumed by the downstream data-loading and validation steps, regardless of which source produced it.
- **TruthSet_Source_Provenance**: A recorded label identifying which source produced the TruthSet used for a verification run (`mcp_primary`, `github_fallback`, or `cord_substitute`).
- **Verification_Report**: The structured summary produced at the end of Module 3 listing each verification check, its status, and any remediation instructions.
- **Deterministic_Verification**: The Step 7 validation that compares resolved entity outcomes against Expected_Results (entity count tolerance, known matches, and cross-record resolution).

## Requirements

### Requirement 1: Primary TruthSet Availability Detection

**User Story:** As a bootcamper, I want the module to detect whether the MCP server actually provides a usable TruthSet, so that verification chooses the correct data source without guessing.

#### Acceptance Criteria

1. WHEN TruthSet_Acquisition begins, THE TruthSet_Acquisition SHALL call the MCP_Server `get_sample_data` tool and inspect the response for a named TruthSet reference.
2. WHEN the `get_sample_data` response contains a named TruthSet reference with retrievable records, THE TruthSet_Acquisition SHALL classify the Primary_TruthSet as available.
3. IF the `get_sample_data` response contains only CORD_Collection entries and no named TruthSet reference, THEN THE TruthSet_Acquisition SHALL classify the Primary_TruthSet as unavailable.
4. WHEN classification of Primary_TruthSet availability completes, THE TruthSet_Acquisition SHALL record the classification result in `config/bootcamp_progress.json` before selecting an acquisition path.

### Requirement 2: Primary-Path Precedence

**User Story:** As a bootcamper, I want the MCP-provided TruthSet used whenever it is available, so that the fallback source is a last resort and the primary design is unchanged.

#### Acceptance Criteria

1. WHILE the Primary_TruthSet is classified as available, THE TruthSet_Acquisition SHALL acquire TruthSet data exclusively from the MCP_Server.
2. WHEN the Primary_TruthSet is used, THE TruthSet_Acquisition SHALL save the Primary_TruthSet records to the TruthSet_Data_File and set TruthSet_Source_Provenance to `mcp_primary`.
3. WHILE the Primary_TruthSet is classified as available, THE System_Verification_Module SHALL execute Deterministic_Verification using the Expected_Results retrieved from the MCP_Server, unchanged from the existing Module 3 design.

### Requirement 3: Fallback TruthSet Acquisition

**User Story:** As a bootcamper, I want the module to fetch the official demo TruthSet when the MCP server has none, so that deterministic verification can still run.

#### Acceptance Criteria

1. WHEN the Primary_TruthSet is classified as unavailable, THE TruthSet_Acquisition SHALL fetch the demo TruthSet from the Sanctioned_Fallback_Source over HTTPS within a timeout of 30 seconds.
2. WHEN the fallback fetch returns an HTTP 200 response with demo TruthSet content, THE TruthSet_Acquisition SHALL save the Fallback_TruthSet records to the TruthSet_Data_File, overwriting any previously existing file at that path, so that downstream data-loading and validation steps operate unchanged.
3. WHEN the Fallback_TruthSet is saved, THE TruthSet_Acquisition SHALL set TruthSet_Source_Provenance to `github_fallback`.
4. IF the fallback fetch returns a non-200 HTTP status, THEN THE TruthSet_Acquisition SHALL classify the Sanctioned_Fallback_Source as unreachable and record the HTTP status.
5. IF the fallback fetch does not complete within 30 seconds or fails with a network error, THEN THE TruthSet_Acquisition SHALL terminate the request, classify the Sanctioned_Fallback_Source as unreachable, and record the failure reason (timeout or network error).

### Requirement 4: Fallback Data Validation and Normalization

**User Story:** As a bootcamper, I want the fetched fallback data validated and normalized to the loader's format, so that a malformed or unexpected file does not silently corrupt verification.

#### Acceptance Criteria

1. WHEN the Fallback_TruthSet content is fetched, THE TruthSet_Acquisition SHALL normalize the content into the TruthSet_Data_File as one valid JSON object per line (JSONL).
2. WHEN normalization completes, THE TruthSet_Acquisition SHALL validate that the TruthSet_Data_File contains one valid JSON object per line and that the line count equals the number of records obtained from the Sanctioned_Fallback_Source.
3. FOR ALL records fetched from the Sanctioned_Fallback_Source, parsing the source representation, serializing to the TruthSet_Data_File, and parsing the TruthSet_Data_File again SHALL yield an equivalent record set (round-trip property).
4. IF the TruthSet_Data_File fails validation because a line is not valid JSON or the line count does not match the fetched record count, THEN THE TruthSet_Acquisition SHALL report a fail status identifying which validation failed and SHALL NOT proceed to data loading.

### Requirement 5: Preservation of Deterministic Verification

**User Story:** As a bootcamper, I want the fallback TruthSet to carry expected-result counts and known matches, so that the Step 7 known-good comparison still runs when the fallback path is used.

#### Acceptance Criteria

1. WHEN the Fallback_TruthSet is acquired, THE TruthSet_Acquisition SHALL obtain Fallback_Expected_Results derived from the Sanctioned_Fallback_Source demo set's published truth definitions.
2. THE Fallback_Expected_Results SHALL include an expected entity count and at least three known entity matches, so that the entity-count-tolerance, known-matches, and cross-record-resolution checks of Deterministic_Verification can execute unchanged.
3. WHEN TruthSet_Source_Provenance is `github_fallback`, THE System_Verification_Module SHALL execute Deterministic_Verification using the Fallback_Expected_Results in place of the MCP-provided Expected_Results.
4. IF the Fallback_Expected_Results cannot be derived (missing or incomplete truth definitions), THEN THE TruthSet_Acquisition SHALL treat the Sanctioned_Fallback_Source as unusable for deterministic verification and report a fail status for the TruthSet acquisition check identifying the missing expected-result data.

### Requirement 6: Sanctioned Fallback Source Governance

**User Story:** As a power maintainer, I want the external fallback source declared once and clearly justified, so that introducing a second external endpoint is a deliberate, reviewable security decision rather than an ad-hoc URL.

#### Acceptance Criteria

1. THE Sanctioned_Fallback_Source location SHALL be declared in exactly one place, the Sanctioned_Source_Registry, and every other file that needs the fallback source SHALL reference it by its registry identifier rather than embedding the raw URL.
2. THE Sanctioned_Source_Registry SHALL record the Sanctioned_Fallback_Source purpose (TruthSet data fallback for Module 3), the approval rationale (official Senzing-published deterministic data), and the demo-set path within the repository.
3. WHILE the fallback path is active, THE TruthSet_Acquisition SHALL fetch only TruthSet DATA from the Sanctioned_Fallback_Source and SHALL obtain every Senzing SDK fact, method signature, and expected-behavior definition from the MCP_Server.
4. THE System_Verification_Module SHALL restrict external network contact to the MCP_Server and the Sanctioned_Fallback_Source.

### Requirement 7: Graceful Degradation When No TruthSet Source Is Reachable

**User Story:** As a bootcamper, I want a clear outcome when neither the MCP TruthSet nor the fallback source is available, so that I am never misled into thinking a non-deterministic run was a deterministic pass.

#### Acceptance Criteria

1. IF the Primary_TruthSet is unavailable AND the Sanctioned_Fallback_Source is unreachable, THEN THE System_Verification_Module SHALL display a message identifying that both the MCP TruthSet and the fallback source are unavailable and SHALL provide remediation steps (verify MCP connectivity, verify reachability of the Sanctioned_Fallback_Source, retry).
2. WHEN both TruthSet sources are unavailable, THE System_Verification_Module SHALL offer the bootcamper a clearly labeled non-deterministic substitute using a CORD_Collection and SHALL wait for the bootcamper's decision before proceeding.
3. WHEN the bootcamper accepts the CORD_Collection substitute, THE System_Verification_Module SHALL set TruthSet_Source_Provenance to `cord_substitute` and SHALL mark the Deterministic_Verification check as `non_deterministic` in the Verification_Report rather than `passed`.
4. WHEN the bootcamper declines the CORD_Collection substitute, THE System_Verification_Module SHALL mark the Deterministic_Verification check as `blocked` in the Verification_Report and record the remediation steps.
5. WHEN the Deterministic_Verification check is recorded as `non_deterministic` or `blocked`, THE System_Verification_Module SHALL record the overall Module 3 verification status as `incomplete`.

### Requirement 8: TruthSet Source Provenance Transparency

**User Story:** As a bootcamper, I want the verification output to state which TruthSet source was used, so that I can trust or investigate the deterministic guarantee for that run.

#### Acceptance Criteria

1. WHEN the Verification_Report is generated, THE System_Verification_Module SHALL include the TruthSet_Source_Provenance value for the run (`mcp_primary`, `github_fallback`, or `cord_substitute`).
2. WHEN TruthSet_Source_Provenance is `github_fallback`, THE System_Verification_Module SHALL state in the Verification_Report that deterministic verification used the sanctioned fallback source rather than an MCP-provided TruthSet.
3. THE System_Verification_Module SHALL persist the TruthSet_Source_Provenance value to `config/bootcamp_progress.json` alongside the TruthSet acquisition check result.

### Requirement 9: Fallback Path Documentation in Module 3 Steering

**User Story:** As a power maintainer, I want the Module 3 steering to document the fallback path and its sanctioned source, so that the agent applies it consistently and the security exception is discoverable.

#### Acceptance Criteria

1. THE Module 3 steering (`module-03-system-verification.md` and the TruthSet acquisition step in `module-03-phase1-verification.md`) SHALL document the fallback path, describing detection of an unavailable Primary_TruthSet and acquisition from the Sanctioned_Fallback_Source.
2. THE Module 3 steering SHALL reference the Sanctioned_Fallback_Source by its Sanctioned_Source_Registry identifier and SHALL state the approval rationale for the external-source exception.
3. THE Module 3 steering SHALL state that the primary MCP path takes precedence and that the fallback path fetches TruthSet DATA only, with all Senzing SDK facts continuing to come from the MCP_Server.
