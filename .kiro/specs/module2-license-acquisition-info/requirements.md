# Requirements Document

## Introduction

This feature surfaces, in the **upfront** Module 2 Step 5a license explanation, the option that
the bootcamp can help request a temporary evaluation license in-flow through the Senzing MCP
server's `submit_feedback` `license_request` path — so bootcampers with datasets larger than the
built-in evaluation license's record limit understand this path exists *before* they reach the
Step 5c no-license branch where it is currently the only place it appears.

Today, the Step 5a explanation in `senzing-bootcamp/steering/module-02-sdk-setup.md` tells the
bootcamper about the built-in evaluation license (limited to roughly 500 records) and that larger
datasets need a custom license file at `licenses/g2.lic`. The only acquisition direction it gives
is to consult the MCP server for "a larger or temporary evaluation license." It does not state
that the bootcamp itself can initiate an in-flow temporary-license request via the MCP server's
`submit_feedback` tool. As a result, a bootcamper reading the upfront explanation may assume their
only options are "stay under the limit" or "go find a license elsewhere," and may not realize the
in-flow path exists until Step 5c.

This feature adds the in-flow MCP license-request option to the Step 5a explanation (and to the
agent's spoken/summarized version of that explanation), alongside the existing options of applying
an already-held license and requesting one through Senzing support. Because the in-flow path
depends on the `submit_feedback` MCP tool — which ships disabled by default and may be unavailable
in a given session — the upfront mention must carry an availability caveat rather than promising
the path unconditionally. The option already exists in Step 5c; this feature is about advertising
it earlier in Step 5a and keeping the two locations consistent. Consistent with the bootcamp's core
constraint, all Senzing-specific license facts (record capacity, validity period) presented in the
explanation must be retrieved from MCP tools at runtime rather than hardcoded from training data.

This feature changes only the upfront explanatory content of Step 5a (and its summarized
presentation). It does not change the Step 5c branch's interactive option-selection, capability
verification, invocation, or enablement behavior, which are owned by the existing
`surface-mcp-license-request` spec.

## Glossary

- **Bootcamp**: The senzing-bootcamp Kiro Power that guides developers through Senzing entity resolution across its modules.
- **Agent**: The Kiro agent executing the bootcamp by following its steering files.
- **License_Explanation**: The upfront Module 2 Step 5a built-in-evaluation-license explanation defined in `senzing-bootcamp/steering/module-02-sdk-setup.md` (subsection "5a. Explain the built-in evaluation license").
- **Summarized_Explanation**: The Agent's spoken or condensed presentation of the License_Explanation delivered to the bootcamper at Step 5a, as opposed to the verbatim steering text.
- **Step_5c_Branch**: The Module 2 Step 5c "no license" branch in `senzing-bootcamp/steering/module-02-sdk-setup.md` where the in-flow license-request option is presented as a selectable path.
- **MCP_Server**: The Senzing MCP server configured in `senzing-bootcamp/mcp.json`.
- **submit_feedback**: The MCP tool that supports a `license_request` category for generating an evaluation license; it is listed in the `disabledTools` array in `senzing-bootcamp/mcp.json` and is disabled by default.
- **License_Request_Option**: The in-flow path for obtaining a temporary evaluation license by the Bootcamp invoking the `submit_feedback` MCP tool with the `license_request` category.
- **Existing_License_Option**: The path of applying a Senzing license the bootcamper already holds by placing it at `licenses/g2.lic`.
- **Support_Request_Option**: The path of requesting an evaluation license through Senzing support's external channel.
- **Availability_Caveat**: The qualification that the License_Request_Option depends on the `submit_feedback` tool being available (enabled and reported by the MCP_Server) and may therefore be unavailable in a given session.
- **Evaluation_License**: The built-in evaluation license that applies when no custom Senzing license is configured, limited to a record capacity reported by the MCP_Server.
- **Record_Limit**: The maximum number of records the Evaluation_License supports, a value sourced from the MCP_Server.

## Requirements

### Requirement 1: Surface the in-flow license-request option in the upfront Step 5a explanation

**User Story:** As a bootcamper reading the upfront license explanation in Module 2, I want to learn that the bootcamp can request a temporary evaluation license for me in-flow, so that I understand this path exists before I reach the Step 5c no-license branch.

#### Acceptance Criteria

1. THE License_Explanation SHALL explicitly present the License_Request_Option as a path for obtaining a temporary Evaluation_License in-flow through the MCP_Server when the bootcamper needs more than the Evaluation_License's Record_Limit.
2. THE License_Explanation SHALL name, within the same explanation, all three acquisition paths available when more than the Record_Limit is needed: the License_Request_Option, the Existing_License_Option, and the Support_Request_Option.
3. WHERE the License_Explanation presents the License_Request_Option, THE License_Explanation SHALL state that the License_Request_Option is initiated by the Bootcamp invoking the `submit_feedback` MCP tool with the `license_request` category.
4. THE License_Explanation SHALL present the Step 5a mention of the License_Request_Option as informational only and SHALL NOT initiate an option-selection or execution prompt at Step 5a.
5. WHEN the Agent delivers the Summarized_Explanation at Step 5a, THE Summarized_Explanation SHALL state that, when more than the Record_Limit is needed, the Bootcamp can help request a temporary Evaluation_License in-flow through the MCP_Server, in addition to the Existing_License_Option and the Support_Request_Option.

### Requirement 2: State the availability caveat for the in-flow option

**User Story:** As a bootcamper, I want the upfront explanation to make clear that the in-flow license-request path depends on a tool that may be off or unavailable, so that I do not treat it as guaranteed.

#### Acceptance Criteria

1. WHERE the License_Explanation presents the License_Request_Option, THE License_Explanation SHALL state the Availability_Caveat that the License_Request_Option depends on the `submit_feedback` tool being both enabled and reported as available by the MCP_Server.
2. WHERE the License_Explanation presents the License_Request_Option, THE License_Explanation SHALL state that the `submit_feedback` tool is disabled by default and that the License_Request_Option may therefore be unavailable in a given session and is not guaranteed.
3. WHERE the Summarized_Explanation mentions the License_Request_Option, THE Summarized_Explanation SHALL state both that the in-flow path depends on the `submit_feedback` tool being available and that it may be unavailable in a given session.
4. WHERE the License_Explanation presents the three acquisition paths, THE License_Explanation SHALL qualify only the License_Request_Option with the Availability_Caveat and SHALL present the Existing_License_Option and the Support_Request_Option without the Availability_Caveat.

### Requirement 3: Keep Step 5a consistent with the Step 5c branch

**User Story:** As a bootcamper, I want the upfront mention of the in-flow option to match how it actually works in Step 5c, so that the bootcamp feels consistent and I am not surprised later.

#### Acceptance Criteria

1. THE License_Explanation SHALL describe the License_Request_Option using the same mechanism described in the Step_5c_Branch — a `submit_feedback` invocation with the `license_request` category through the MCP_Server — and SHALL NOT describe a mechanism absent from the Step_5c_Branch.
2. THE License_Explanation SHALL describe the License_Request_Option's availability dependency consistently with the Step_5c_Branch, namely that the option depends on `submit_feedback` being available and that `submit_feedback` is disabled by default, and SHALL NOT state an availability condition that contradicts the Step_5c_Branch.
3. THE License_Explanation SHALL NOT present an interactive option-selection prompt at Step 5a and SHALL NOT request the bootcamper to choose, confirm, or initiate an acquisition path at Step 5a.
4. THE License_Explanation SHALL direct the selection and execution of the License_Request_Option to the Step_5c_Branch.
5. WHERE the License_Explanation names the acquisition paths, THE License_Explanation SHALL name the same three paths the Step_5c_Branch offers — the License_Request_Option, the Support_Request_Option, and the Existing_License_Option — and SHALL NOT add a path absent from the Step_5c_Branch.

### Requirement 4: Source license facts from the MCP server

**User Story:** As a maintainer, I want the record and license figures in the upfront explanation to come from the MCP server, so that the guidance stays accurate as Senzing's terms change.

#### Acceptance Criteria

1. WHEN the License_Explanation is about to present the Evaluation_License's Record_Limit or validity period, THE Agent SHALL retrieve that value from an MCP_Server tool during the current session rather than from training data, hardcoded values, or values cached from a prior session.
2. WHERE an MCP_Server tool returns the Evaluation_License's Record_Limit or validity period within the retrieval timeout, THE License_Explanation SHALL present the returned value exactly as returned, without rounding, reformatting, or substituting a static figure.
3. WHEN the Agent requests the Record_Limit or validity period from an MCP_Server tool, THE Agent SHALL treat the MCP_Server as unreachable if no response is returned within 30 seconds.
4. IF an MCP_Server tool does not return the Record_Limit or validity period, OR the MCP_Server is unreachable when that value is requested, THEN THE License_Explanation SHALL omit the specific figure and SHALL indicate to the bootcamper that the current value is unavailable from the MCP_Server.
