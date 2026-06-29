# Requirements Document

## Introduction

This feature surfaces the Senzing MCP server's built-in, in-flow license-request capability
as an explicit licensing option within the Senzing Bootcamp's Module 2 (SDK Setup, Step 5 —
Configure License) guidance, and documents it in the Module 2 companion documentation.

Today, when a bootcamper reaches Module 2 Step 5 and indicates they have no Senzing license
(the Step 5c "no license" branch in `senzing-bootcamp/steering/module-02-sdk-setup.md`), the
guidance offers only external paths: contact `support@senzing.com` for an evaluation license,
contact `sales@senzing.com` for production, and consult the MCP server documentation. It does
not present that the Senzing MCP server can itself request an evaluation license in-flow by
invoking the `submit_feedback` tool with the `license_request` category. This omits the same
faster, self-contained path that Module 1 Step 6d already surfaces, forcing the bootcamper to
discover the capability on their own.

The `submit_feedback` tool ships disabled by default (it is listed in `disabledTools` in
`senzing-bootcamp/mcp.json`), so the guidance must account for the tool being unavailable,
verify availability at runtime before offering the option, and instruct the bootcamper on
re-enabling the tool when needed. This feature mirrors the established, tested behavior from
the Module 1 licensing branch so the two modules present a consistent in-flow path. Consistent
with the bootcamp's core constraint, all Senzing-specific facts (including the evaluation
license's validity period and record capacity) must be retrieved from MCP tools at runtime
rather than hardcoded from training data.

## Glossary

- **Bootcamp**: The senzing-bootcamp Kiro Power that guides developers through Senzing entity resolution across 11 modules.
- **Agent**: The Kiro agent executing the bootcamp by following its steering files.
- **License_Configuration**: The Module 2 Step 5 (Configure License) workflow defined in `senzing-bootcamp/steering/module-02-sdk-setup.md`, specifically the Step 5c no-license branch and the Step 5d configuration steps.
- **Module2_Documentation**: The Module 2 companion documentation, `senzing-bootcamp/docs/modules/MODULE_2_SDK_SETUP.md`, specifically its Senzing License Requirements section.
- **MCP_Server**: The Senzing MCP server configured in `senzing-bootcamp/mcp.json`.
- **License_Request_Option**: The in-flow path for obtaining an evaluation license by invoking the `submit_feedback` MCP tool with the `license_request` category.
- **submit_feedback**: The MCP tool that supports a `license_request` category for generating an evaluation license.
- **get_capabilities**: The MCP tool that reports the currently available MCP tools and workflows.
- **disabledTools**: The array in `senzing-bootcamp/mcp.json` listing MCP tools that are disabled by default; `submit_feedback` is currently a member.
- **Evaluation_License**: The built-in evaluation license, limited to 500 records, that applies when no custom Senzing license is configured.

## Requirements

### Requirement 1: Offer the MCP license-request option in the Step 5 no-license branch

**User Story:** As a bootcamper configuring a license in Module 2 who has no Senzing license, I want to be told that the Senzing MCP server can request an evaluation license for me, so that I can obtain a license through a faster in-flow path instead of only external channels.

#### Acceptance Criteria

1. WHEN the bootcamper indicates in Step 5c that they have no Senzing license, THE License_Configuration SHALL present exactly three licensing paths as distinct, individually selectable options, displayed in this order: the License_Request_Option first, the existing external request path second, and the apply-an-existing-license path third.
2. WHERE the License_Request_Option is presented, THE License_Configuration SHALL identify it as the in-flow path that uses the MCP_Server, and SHALL state all three of the following about it: that it generates an evaluation license, that the license is delivered by email, and that the email includes a download link.
3. WHEN the bootcamper indicates in Step 5b that they have a Senzing license file or a Base64-encoded license key, THE License_Configuration SHALL omit the License_Request_Option and direct the bootcamper to the apply-an-existing-license path as the sole presented path.
4. WHEN the bootcamper selects one of the three presented licensing paths in Step 5c, THE License_Configuration SHALL proceed with only the selected path and SHALL NOT initiate the actions of the two unselected paths.
5. IF the bootcamper's Step 5c response does not match any of the three presented options, THEN THE License_Configuration SHALL re-present the same three options unchanged, SHALL indicate that the prior response was not recognized, and SHALL NOT advance past Step 5c.

### Requirement 2: Verify capability availability before offering the option

**User Story:** As a bootcamper, I want the bootcamp to only offer the MCP license-request option when it actually works, so that I am not directed to a capability that is unavailable in my session.

#### Acceptance Criteria

1. WHEN the Agent is about to present the licensing paths in the Step 5c no-license branch, THE Agent SHALL call `get_capabilities` on the MCP_Server within the same Step 5 licensing interaction and SHALL wait for the capability determination — a response received, an error response, or the 30-second window elapsing — before presenting any licensing path.
2. WHEN the `get_capabilities` response explicitly reports `submit_feedback` as available, THE License_Configuration SHALL present exactly three paths: the License_Request_Option, the apply-an-existing-license path, and the external request path.
3. IF the `get_capabilities` response explicitly reports `submit_feedback` as unavailable, THEN THE License_Configuration SHALL omit the License_Request_Option and present exactly two paths: the apply-an-existing-license path and the external request path.
4. IF the MCP_Server returns no `get_capabilities` response within 30 seconds, returns an error response, or returns a response that does not explicitly report `submit_feedback` as available (including a missing, empty, or unrecognized `submit_feedback` value), THEN THE License_Configuration SHALL omit the License_Request_Option and present exactly two paths: the apply-an-existing-license path and the external request path.
5. WHEN the License_Configuration omits the License_Request_Option per criterion 3 or criterion 4, THE Agent SHALL present a message to the bootcamper indicating that the in-session license-request capability is unavailable for the current session.

### Requirement 3: Inform the bootcamper that the tool is disabled by default

**User Story:** As a bootcamper, I want to know that the license-request tool is off by default and how to turn it on, so that I can enable it when I choose the in-flow path.

#### Acceptance Criteria

1. WHEN the License_Configuration presents the License_Request_Option while `submit_feedback` is listed in `disabledTools` in `senzing-bootcamp/mcp.json`, THE License_Configuration SHALL state that the License_Request_Option requires the `submit_feedback` tool and that `submit_feedback` is disabled by default.
2. WHEN the bootcamper expresses intent to use the License_Request_Option while `submit_feedback` is listed in `disabledTools`, THE License_Configuration SHALL provide instructions that identify `senzing-bootcamp/mcp.json`, direct the bootcamper to remove `submit_feedback` from the `disabledTools` array, and direct the bootcamper to save the file.
3. WHEN the bootcamper indicates they have re-enabled `submit_feedback`, THE Agent SHALL re-verify `submit_feedback` availability by calling `get_capabilities` on the MCP_Server and waiting for the capability determination (a response received, an error response, or the 30-second window elapsing) before invoking the License_Request_Option.
4. IF the re-verification `get_capabilities` call reports `submit_feedback` as unavailable, returns an error response, or does not return a response within 30 seconds, THEN THE License_Configuration SHALL NOT invoke the License_Request_Option and SHALL present the apply-an-existing-license path and the external request path.
5. IF the bootcamper declines to re-enable `submit_feedback`, THEN THE License_Configuration SHALL present the apply-an-existing-license path and the external request path.

### Requirement 4: Invoke the license request when the bootcamper chooses it

**User Story:** As a bootcamper, I want the agent to submit the license request for me when I choose the in-flow path, so that I receive an evaluation license without leaving the bootcamp.

#### Acceptance Criteria

1. WHEN the bootcamper selects the License_Request_Option and a `get_capabilities` check performed within the same Step 5 licensing interaction confirms `submit_feedback` is available, THE Agent SHALL invoke `submit_feedback` exactly once with the `license_request` category.
2. WHEN the `submit_feedback` invocation returns a response with no error, THE License_Configuration SHALL instruct the bootcamper to check the email associated with their request for the evaluation license and its download link.
3. WHEN the bootcamper confirms they have received the requested license AND the License_Request_Option's `submit_feedback` invocation previously returned a response with no error, THE License_Configuration SHALL direct the bootcamper to the Step 5d configuration steps for saving and wiring the license file.
4. IF the `submit_feedback` invocation returns an error or does not return a response within 30 seconds, THEN THE License_Configuration SHALL inform the bootcamper that the license request did not complete and present the remaining licensing paths (the apply-an-existing-license path and the external request path) without automatically re-invoking `submit_feedback`.
5. IF the bootcamper selects the License_Request_Option and no `get_capabilities` check within the same Step 5 licensing interaction confirms `submit_feedback` is available, THEN THE Agent SHALL re-verify availability with `get_capabilities` before invoking `submit_feedback` and SHALL NOT invoke `submit_feedback` unless that check confirms availability.
6. WHILE a `submit_feedback` invocation initiated for the License_Request_Option is awaiting its response, THE Agent SHALL NOT initiate an additional `submit_feedback` invocation for the License_Request_Option.

### Requirement 5: Document the option in the Module 2 documentation

**User Story:** As a bootcamper reading the Module 2 documentation, I want the MCP license-request option described there, so that I can learn about the in-flow path outside the Step 5 conversational flow.

#### Acceptance Criteria

1. THE Module2_Documentation SHALL contain a written description of the License_Request_Option that identifies it as a path to obtain an evaluation license in-flow through the MCP_Server, and that description SHALL state it is available outside the Step 5 conversational flow.
2. THE Module2_Documentation SHALL state that the evaluation license obtained through the License_Request_Option is delivered by email and that the email contains a download link for the license.
3. THE Module2_Documentation SHALL state that the License_Request_Option invokes the `submit_feedback` MCP tool with the `license_request` category.
4. THE Module2_Documentation SHALL state that the `submit_feedback` tool is disabled by default and is therefore non-functional until explicitly enabled.
5. THE Module2_Documentation SHALL state that enabling the License_Request_Option requires removing the `submit_feedback` entry from the `disabledTools` array in `senzing-bootcamp/mcp.json`.

### Requirement 6: Source Senzing license facts from MCP tools

**User Story:** As a maintainer, I want license terms presented to the bootcamper to come from the MCP server rather than static text, so that the guidance stays accurate as Senzing's terms change.

#### Acceptance Criteria

1. WHEN the License_Configuration is about to present the Evaluation_License's validity period or record capacity, THE Agent SHALL retrieve those values from an MCP_Server tool during the active session rather than from training data or hardcoded values.
2. WHERE the MCP_Server tool returns a validity period value, a record-capacity value, or both, THE License_Configuration SHALL present the returned value or values exactly as returned and SHALL NOT substitute or override them with static figures; this rule constrains only the value or values that the MCP_Server tool actually returns.
3. IF the MCP_Server tool does not return a validity period or record-capacity value, OR the MCP_Server cannot be reached when those values are requested, THEN THE License_Configuration SHALL omit the specific figure, SHALL NOT present a hardcoded or training-data value in its place, and SHALL indicate to the bootcamper that the current value is unavailable from the MCP_Server.

### Requirement 7: Preserve consistency with the Module 1 licensing branch

**User Story:** As a bootcamper, I want the in-flow license-request option to behave the same way in Module 2 as it does in Module 1, so that the bootcamp feels consistent and predictable.

#### Acceptance Criteria

1. THE License_Configuration SHALL describe the License_Request_Option's availability gate as the `get_capabilities` check with the 30-second window, identical to the gate used in the Module 1 Step 6d licensing branch.
2. THE License_Configuration SHALL describe the License_Request_Option's invocation as a single `submit_feedback` call with the `license_request` category, identical to the invocation used in the Module 1 Step 6d licensing branch.
3. THE License_Configuration SHALL describe enabling the License_Request_Option as removing `submit_feedback` from the `disabledTools` array in `senzing-bootcamp/mcp.json`, identical to the enable instruction used in the Module 1 Step 6d licensing branch.
4. IF the availability gate reports `submit_feedback` as unavailable, returns an error response, or does not return a response within 30 seconds, THEN THE License_Configuration SHALL omit the License_Request_Option, consistent with the Module 1 Step 6d licensing branch.
5. WHEN the bootcamper enters the Step 5c no-license branch and a license was already configured and applied earlier in the current bootcamp session, THE License_Configuration SHALL omit the License_Request_Option and route the bootcamper to the apply-an-existing-license path.
