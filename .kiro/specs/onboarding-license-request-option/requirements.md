# Requirements Document

## Introduction

The bootcamp's onboarding overview (Module 0, Step 5 "Bootcamp Introduction" in
`senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`) presents a one-line summary
of Senzing licensing as part of the points it covers before track selection:

> Built-in 500-record eval license; bring your own for more

This line presents only two options: use the built-in evaluation license, or bring your own.
It omits a third option that is actually available in-flow: the bootcamper can request a
temporary Senzing evaluation license directly through the bootcamp by asking the Senzing MCP
server (the `submit_feedback` tool's `license_request` category issues a time-limited
evaluation license). Bootcampers who need more capacity than the built-in license provides
have no way of knowing this path exists at the point where licensing is first introduced.

This feature updates the onboarding overview licensing line to add the in-flow MCP
license-request path as a third option, consistent with the framing already established in
Module 1 discovery (`module1-license-request-option`) and the canonical default-plus-expansion
framing (`license-capacity-framing`). The onboarding overview is an early, high-level mention,
so the addition is a brief pointer — it names the in-flow option without duplicating the full
Module 1 availability-check and branching logic, which remains the authoritative place for the
detailed flow.

All Senzing-specific facts (record capacity, validity period, license-request mechanics) are
sourced from the Senzing MCP server at request time, never from training data or hardcoded
figures, and the line must not introduce any MCP server URL or external URL into the steering
file.

## Glossary

- **Bootcamp**: The senzing-bootcamp Kiro Power that guides developers through Senzing entity resolution across 11 modules.
- **Agent**: The Kiro agent executing the bootcamp by following its steering files.
- **Onboarding_Overview**: The Step 5 "Bootcamp Introduction" overview in `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`, presented before track selection, that covers high-level orientation points including licensing.
- **Licensing_Line**: The single overview bullet currently reading "Built-in 500-record eval license; bring your own for more".
- **In_Flow_MCP_Request**: The path for obtaining an evaluation license without leaving the bootcamp, by invoking the Senzing MCP server `submit_feedback` tool with the `license_request` category.
- **Module_1_Licensing_Flow**: The authoritative licensing flow in `senzing-bootcamp/steering/module-01-phase1-discovery.md` (Steps 6a–6e) that performs the `get_capabilities` availability check and branching for the in-flow path.

## Requirements

### Requirement 1: Present the in-flow MCP request as a third licensing option

**User Story:** As a bootcamper reviewing the onboarding overview, I want to learn that I can request a temporary evaluation license through the bootcamp, so that I know all my licensing options before choosing a track.

#### Acceptance Criteria

1. THE Licensing_Line SHALL present three options rather than two: the built-in evaluation license (the default the bootcamper already has), bringing/applying an existing license, and the In_Flow_MCP_Request path.
2. WHERE the In_Flow_MCP_Request is presented, THE Licensing_Line SHALL identify it as a path that asks the Senzing MCP server to issue a temporary evaluation license, without restating the full Module 1 availability-check and branching logic.
3. THE Licensing_Line SHALL frame the built-in license as a default the bootcamper already has and the other two paths as ways to get more capacity, consistent with the `license-capacity-framing` default-plus-expansion framing.
4. THE Onboarding_Overview SHALL reference Module 1 (or the licensing flow it loads) as the place where the In_Flow_MCP_Request option is actually offered and gated, so the overview remains a pointer rather than a duplicate of the Module 1 flow.

### Requirement 2: Do not hardcode Senzing license facts

**User Story:** As a maintainer, I want the onboarding licensing line to stay accurate as Senzing's terms change, so that the overview never presents stale figures.

#### Acceptance Criteria

1. THE Licensing_Line MAY refer to the built-in evaluation limit by the figure already used elsewhere in onboarding (500 records) for orientation, but SHALL NOT introduce any new hardcoded validity period or capacity figure for the In_Flow_MCP_Request evaluation license.
2. WHEN the bootcamper asks for the specific capacity or validity of a requested evaluation license during onboarding, THE Agent SHALL defer to the Module_1_Licensing_Flow, which sources those values from the Senzing MCP server at request time.

### Requirement 3: No new URLs and consistency with existing flow

**User Story:** As a maintainer, I want the change to obey the power's security and consistency rules, so that it passes CI and does not contradict the Module 1 flow.

#### Acceptance Criteria

1. THE Licensing_Line SHALL NOT contain any MCP server URL or any external URL; it SHALL refer to the Senzing MCP server by name only.
2. THE Licensing_Line SHALL NOT contradict the Module_1_Licensing_Flow's availability gating — it SHALL NOT claim the In_Flow_MCP_Request always succeeds or is always available.
3. THE updated `onboarding-phase1b-intro-language.md` SHALL remain valid CommonMark and stay within its steering token budget recorded in `steering-index.yaml`.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want a test asserting the onboarding overview mentions the in-flow MCP license-request option, so that the third option is not silently dropped in a future edit.

#### Acceptance Criteria

1. THE Test_Suite SHALL include a test that reads `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md` and asserts the onboarding overview licensing content references the in-flow MCP license-request path (e.g., mentions requesting an evaluation license through the Senzing MCP server).
2. THE Test_Suite SHALL include a test asserting the licensing content contains no MCP server URL and no external URL.
3. THE Test_Suite SHALL be located under `senzing-bootcamp/tests/`.
