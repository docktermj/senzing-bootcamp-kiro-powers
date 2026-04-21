# Requirements Document

## Introduction

Complete the Module 0 steering file's Step 5 (license configuration) to match the full license guidance found in the module documentation (`docs/modules/MODULE_0_SDK_SETUP.md`). The steering file currently lacks license priority order documentation, `SENZING_LICENSE_PATH` environment variable discovery, license acquisition guidance, and a reference to `licenses/README.md`. All existing content must be preserved — only additions and expansions are permitted.

## Glossary

- **Steering_File**: The agent workflow file at `senzing-bootcamp/steering/module-00-sdk-setup.md` that guides the AI agent through Module 0 steps
- **Module_Documentation**: The user-facing reference at `senzing-bootcamp/docs/modules/MODULE_0_SDK_SETUP.md` describing Module 0 in detail
- **CONFIGPATH**: The system-level directory where Senzing stores configuration and license files (e.g., `/etc/opt/senzing/` on Linux)
- **License_Priority_Order**: The sequence in which Senzing checks for license files: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` environment variable → system CONFIGPATH `g2.lic`
- **Evaluation_Mode**: The built-in SDK mode with a 500-record limit that requires no license file
- **SENZING_LICENSE_PATH**: An environment variable that can point to a custom license file location

## Requirements

### Requirement 1: Document License Priority Order

**User Story:** As an AI agent following the steering file, I want clear documentation of the license resolution priority order, so that I can explain to the bootcamper how Senzing discovers licenses.

#### Acceptance Criteria

1. THE Steering_File SHALL document the License_Priority_Order as: project-local `licenses/g2.lic` first, `SENZING_LICENSE_PATH` environment variable second, system CONFIGPATH `g2.lic` third, and Evaluation_Mode as the built-in fallback
2. WHEN the agent explains license configuration to the bootcamper, THE Steering_File SHALL provide the priority order so the agent can communicate which license will take effect

### Requirement 2: Add SENZING_LICENSE_PATH Discovery

**User Story:** As an AI agent, I want the steering file to include checking the `SENZING_LICENSE_PATH` environment variable during license discovery, so that I can detect licenses configured via environment variable.

#### Acceptance Criteria

1. THE Steering_File SHALL instruct the agent to check the `SENZING_LICENSE_PATH` environment variable as part of the license discovery sequence
2. WHEN `SENZING_LICENSE_PATH` is set and points to a valid license file, THE Steering_File SHALL instruct the agent to inform the bootcamper and offer to use that license
3. THE Steering_File SHALL place the `SENZING_LICENSE_PATH` check after the project-local check and before the system CONFIGPATH check in the discovery sequence

### Requirement 3: Add License Acquisition Guidance

**User Story:** As an AI agent, I want the steering file to include information on how bootcampers can obtain a license, so that I can guide them if they want to remove evaluation limits.

#### Acceptance Criteria

1. WHEN the bootcamper does not have a license and wants one, THE Steering_File SHALL provide contact information for obtaining an evaluation license (support@senzing.com)
2. WHEN the bootcamper needs a production license, THE Steering_File SHALL provide contact information for sales (sales@senzing.com)
3. THE Steering_File SHALL note that evaluation licenses are valid for 30-90 days and are recommended for the bootcamp

### Requirement 4: Add licenses/README.md Reference

**User Story:** As an AI agent, I want the steering file to reference `licenses/README.md` for complete licensing details, so that I can direct bootcampers to additional information.

#### Acceptance Criteria

1. THE Steering_File SHALL reference `licenses/README.md` as the location for complete licensing information
2. THE Steering_File SHALL instruct the agent to mention this reference when discussing license configuration with the bootcamper

### Requirement 5: Preserve Existing Content

**User Story:** As a power developer, I want all existing Step 5 content preserved intact, so that no current functionality is lost.

#### Acceptance Criteria

1. THE Steering_File SHALL retain all existing Step 5 content including CONFIGPATH discovery, project-local license check, BASE64 key handling, license file placement, LICENSEFILE pipeline configuration, and evaluation fallback guidance
2. THE Steering_File SHALL only add new content or expand existing sections without removing or altering current instructions
