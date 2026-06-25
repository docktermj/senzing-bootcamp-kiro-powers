# Requirements Document

## Introduction

Add MCP server license guidance to Module 2 Step 5 of the Senzing Bootcamp steering file. Bootcampers should learn that they can request a larger evaluation license directly through the Senzing MCP server, in addition to the existing email-based contact paths. This information is integrated into sub-step 5a (initial license explanation) and the "no license" response path in sub-step 5c.

## Glossary

- **Steering_File**: The markdown file with YAML frontmatter at `senzing-bootcamp/steering/module-02-sdk-setup.md` that guides agent behavior during Module 2.
- **Step_5**: The "Configure License" section of the Steering_File, containing sub-steps 5a through 5d.
- **Sub_Step_5a**: The sub-step that explains the built-in evaluation license to the bootcamper before any questions are asked.
- **Sub_Step_5c**: The sub-step that handles the bootcamper's response about their license situation, including the "no license" path.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides interactive tool-assisted workflows and can supply license guidance.
- **Existing_Test_Suite**: The pytest + Hypothesis property-based tests in `senzing-bootcamp/tests/test_steering_structure_properties.py` that validate structural invariants of steering files.

## Requirements

### Requirement 1: Add MCP license guidance to sub-step 5a

**User Story:** As a bootcamp developer, I want the steering file to mention MCP server license availability in the initial license explanation, so that bootcampers are aware of this option from the start.

#### Acceptance Criteria

1.1 THE Steering_File SHALL contain text in Sub_Step_5a that informs the bootcamper they can request a larger evaluation license through the Senzing MCP server.

1.2 WHEN the agent presents Sub_Step_5a content, THE Steering_File SHALL position the MCP license guidance after the existing explanation of the 500-record evaluation limit and SENZ9000 error.

1.3 THE Steering_File SHALL preserve all existing Sub_Step_5a content including the explanation of the built-in 500-record evaluation license, the SENZ9000 error description, and the `licenses/g2.lic` placement instruction.

### Requirement 2: Add MCP license guidance to sub-step 5c "no license" path

**User Story:** As a bootcamp developer, I want the "no license" response path in sub-step 5c to mention the MCP server as a way to get license guidance, so that bootcampers who need more than 500 records have an actionable next step.

#### Acceptance Criteria

2.1 THE Steering_File SHALL contain text in the "no license" branch of Sub_Step_5c that mentions the MCP server as a resource for requesting a larger evaluation license.

2.2 WHEN the bootcamper indicates they have no license, THE Steering_File SHALL present the MCP server license guidance alongside the existing email contact information for `support@senzing.com` and `sales@senzing.com`.

2.3 THE Steering_File SHALL preserve all existing Sub_Step_5c "no license" path content including the confirmation message, the email contacts, the `licenses/README.md` reference, and the `config/bootcamp_preferences.yaml` recording instruction.

### Requirement 3: Preserve structural test compliance

**User Story:** As a bootcamp developer, I want the modified steering file to continue passing all existing property-based tests, so that the change does not break CI.

#### Acceptance Criteria

3.1 THE Steering_File SHALL retain the YAML frontmatter with `inclusion: manual` at the start of the file.

3.2 THE Steering_File SHALL retain the pointing question (👉) in sub-step 5b followed by a STOP instruction within 5 non-blank lines.

3.3 THE Steering_File SHALL retain exactly one pointing question per sub-step boundary (5a, 5b, 5c, 5d).

3.4 THE Steering_File SHALL retain the checkpoint instruction at the end of Step 5.

3.5 THE Steering_File SHALL retain the `**Before/After**` framing section elsewhere in the file.

3.6 THE Steering_File SHALL retain the `Prerequisites` section elsewhere in the file.

### Requirement 4: Content accuracy and scope

**User Story:** As a bootcamp developer, I want the added content to be factually accurate and scoped only to Step 5, so that no other module content is affected.

#### Acceptance Criteria

4.1 THE Steering_File SHALL limit all modifications to the Step 5 section only, leaving Steps 1 through 4 and Steps 6 through 9 unchanged.

4.2 THE Steering_File SHALL reference the MCP server capability without hardcoding specific MCP tool names or URLs outside of what already exists in the file.

4.3 THE Steering_File SHALL not introduce any new pointing questions (👉) or STOP instructions beyond those already present in Step 5.
