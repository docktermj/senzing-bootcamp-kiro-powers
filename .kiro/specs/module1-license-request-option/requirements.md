# Requirements Document

## Introduction

This feature adds the Senzing MCP server's built-in license-request capability as an
explicit licensing option within the Senzing Bootcamp's Module 1 (Business Problem)
guidance and the bootcamp's licensing reference documentation.

Today, when a bootcamper's dataset exceeds the built-in 500-record evaluation limit, the
Module 1 licensing branch (steering steps 6b–6e in
`senzing-bootcamp/steering/module-01-business-problem.md`) offers only two paths: apply an
existing license, or request one through an external/email channel. It does not mention that
the Senzing MCP server can itself request an evaluation license through the `submit_feedback`
tool using the `license_request` category. This omits a faster, in-flow path to obtaining an
evaluation license.

The `submit_feedback` tool ships disabled by default (it is listed in `disabledTools` in
`senzing-bootcamp/mcp.json`), so the guidance must account for the tool being unavailable,
verify availability at runtime before offering the option, and instruct the bootcamper on
re-enabling the tool when needed. Consistent with the bootcamp's core constraint, all
Senzing-specific facts (including the evaluation license's validity period and record
capacity) must be retrieved from MCP tools at runtime rather than hardcoded from training
data.

## Glossary

- **Bootcamp**: The senzing-bootcamp Kiro Power that guides developers through Senzing entity resolution across 11 modules.
- **Agent**: The Kiro agent executing the bootcamp by following its steering files.
- **Licensing_Guidance**: The Module 1 licensing branch defined in `senzing-bootcamp/steering/module-01-business-problem.md`, specifically Steps 6b through 6e.
- **Licensing_Reference**: The bootcamp's user-facing licensing documentation, `senzing-bootcamp/licenses/README.md`.
- **MCP_Server**: The Senzing MCP server configured in `senzing-bootcamp/mcp.json`.
- **License_Request_Option**: The in-flow path for obtaining an evaluation license by invoking the `submit_feedback` MCP tool with the `license_request` category.
- **submit_feedback**: The MCP tool that supports a `license_request` category for generating an evaluation license.
- **get_capabilities**: The MCP tool that reports the currently available MCP tools and workflows.
- **disabledTools**: The array in `senzing-bootcamp/mcp.json` listing MCP tools that are disabled by default; `submit_feedback` is currently a member.
- **Evaluation_Limit**: The built-in 500-record limit that applies when no full Senzing license is configured.

## Requirements

### Requirement 1: Offer the MCP license-request option when a license is needed

**User Story:** As a bootcamper whose dataset exceeds the evaluation limit, I want to be told that the Senzing MCP server can request an evaluation license for me, so that I can obtain a license through a faster in-flow path instead of only an external channel.

#### Acceptance Criteria

1. WHEN the bootcamper indicates in Step 6d that they do not have a Senzing license, THE Licensing_Guidance SHALL present exactly three licensing paths as distinct, individually selectable options: the License_Request_Option, the existing external request path, and the existing apply-an-existing-license path.
2. WHERE the License_Request_Option is presented, THE Licensing_Guidance SHALL identify it as the in-flow path that uses the MCP_Server, and SHALL state all three of the following about it: that it generates an evaluation license, that the license is delivered by email, and that the email includes a download link.
3. THE Licensing_Guidance SHALL include, in the Step 6b license-guidance trigger, a reference to the License_Request_Option that names it as one of the available licensing paths.
4. IF the bootcamper indicates in Step 6d that they already have a Senzing license, THEN THE Licensing_Guidance SHALL omit the License_Request_Option and direct the bootcamper to the apply-an-existing-license path.

### Requirement 2: Verify capability availability before offering the option

**User Story:** As a bootcamper, I want the bootcamp to only offer the MCP license-request option when it actually works, so that I am not directed to a capability that is unavailable in my session.

#### Acceptance Criteria

1. WHEN the Agent is about to present the License_Request_Option, THE Agent SHALL call `get_capabilities` on the MCP_Server within the same Module 1 licensing interaction, before presenting the option, to determine whether `submit_feedback` is reported as available.
2. WHEN the `get_capabilities` response reports `submit_feedback` as available, THE Licensing_Guidance SHALL present the License_Request_Option alongside the apply-an-existing-license path and the external request path.
3. IF the `get_capabilities` response reports `submit_feedback` as unavailable, THEN THE Licensing_Guidance SHALL omit the License_Request_Option and present only the apply-an-existing-license path and the external request path.
4. IF the MCP_Server returns no `get_capabilities` response within 30 seconds or returns an error response, THEN THE Licensing_Guidance SHALL omit the License_Request_Option and present only the apply-an-existing-license path and the external request path.

### Requirement 3: Inform the bootcamper that the tool is disabled by default

**User Story:** As a bootcamper, I want to know that the license-request tool is off by default and how to turn it on, so that I can enable it when I choose the in-flow path.

#### Acceptance Criteria

1. WHEN the Licensing_Guidance presents the License_Request_Option while `submit_feedback` is listed in `disabledTools` in `senzing-bootcamp/mcp.json`, THE Licensing_Guidance SHALL state that the License_Request_Option requires the `submit_feedback` tool and that `submit_feedback` is disabled by default.
2. WHEN the bootcamper expresses intent to use the License_Request_Option while `submit_feedback` is listed in `disabledTools`, THE Licensing_Guidance SHALL provide instructions that identify `senzing-bootcamp/mcp.json`, direct the bootcamper to remove `submit_feedback` from the `disabledTools` array, and direct the bootcamper to save the file.
3. WHEN the bootcamper indicates they have re-enabled `submit_feedback`, THE Agent SHALL re-verify `submit_feedback` availability by calling `get_capabilities` on the MCP_Server before invoking the License_Request_Option.
4. IF the bootcamper declines to re-enable `submit_feedback`, THEN THE Licensing_Guidance SHALL present only the remaining licensing paths.

### Requirement 4: Invoke the license request when the bootcamper chooses it

**User Story:** As a bootcamper, I want the agent to submit the license request for me when I choose the in-flow path, so that I receive an evaluation license without leaving the bootcamp.

#### Acceptance Criteria

1. WHEN the bootcamper selects the License_Request_Option and the most recent `get_capabilities` check confirms `submit_feedback` is available, THE Agent SHALL invoke `submit_feedback` exactly once with the `license_request` category.
2. WHEN the `submit_feedback` invocation returns a response with no error, THE Licensing_Guidance SHALL instruct the bootcamper to check the email associated with their request for the evaluation license and its download link.
3. WHEN the bootcamper confirms they have received the requested license, THE Licensing_Guidance SHALL direct the bootcamper to the existing Step 6c configuration steps for saving and wiring the license file.
4. IF the `submit_feedback` invocation returns an error or does not return a response within 30 seconds, THEN THE Licensing_Guidance SHALL inform the bootcamper that the license request did not complete and present the remaining licensing paths (the apply-an-existing-license path and the external request path) without automatically re-invoking `submit_feedback`.

### Requirement 5: Document the option in the licensing reference

**User Story:** As a bootcamper consulting the licensing reference, I want the MCP license-request option documented there, so that I can learn about it outside the Module 1 conversational flow.

#### Acceptance Criteria

1. THE Licensing_Reference SHALL contain a written description of the License_Request_Option that identifies it as a path to obtain an evaluation license through the MCP_Server.
2. THE Licensing_Reference SHALL state that the evaluation license obtained through the License_Request_Option is delivered by email with a download link.
3. THE Licensing_Reference SHALL state that the License_Request_Option invokes the `submit_feedback` MCP tool with the `license_request` category.
4. THE Licensing_Reference SHALL state that the `submit_feedback` tool is disabled by default.
5. THE Licensing_Reference SHALL state that enabling the License_Request_Option requires removing `submit_feedback` from the `disabledTools` array in `senzing-bootcamp/mcp.json`.

### Requirement 6: Source Senzing license facts from MCP tools

**User Story:** As a maintainer, I want license terms presented to the bootcamper to come from the MCP server rather than static text, so that the guidance stays accurate as Senzing's terms change.

#### Acceptance Criteria

1. WHEN the Licensing_Guidance is about to present the evaluation license's validity period or record capacity, THE Agent SHALL retrieve those values from an MCP_Server tool during the active session rather than from training data or hardcoded values.
2. WHERE the validity period or record-capacity values are returned by the MCP_Server tool, THE Licensing_Guidance SHALL present those returned values and SHALL NOT substitute or override them with static figures.
3. IF the MCP_Server tool does not return a validity period or record-capacity value, OR the MCP_Server cannot be reached when those values are requested, THEN THE Licensing_Guidance SHALL omit the specific figure, SHALL NOT present a hardcoded or training-data value in its place, and SHALL indicate to the bootcamper that the current value is unavailable from the MCP_Server.
