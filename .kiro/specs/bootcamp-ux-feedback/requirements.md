# Requirements Document

## Introduction

This feature addresses two UX improvements to the Senzing Bootcamp Power, based on user feedback collected during a live bootcamp session. The first improvement reorders the onboarding overview sections in Step 4 of `onboarding-flow.md` so that the Tracks section immediately follows the modules table (tying structure to content), with Licensing and test-data notes moved to secondary positions. The second improvement adds a clear delivery-mode choice (static HTML vs. web service) at every visualization checkpoint, so bootcampers understand whether they are getting a point-in-time snapshot or a live-data service.

## Glossary

- **Onboarding_Flow**: The steering file (`senzing-bootcamp/steering/onboarding-flow.md`) that defines the sequence of steps from directory creation through track selection when starting a fresh bootcamp.
- **Visualization_Protocol**: The steering file (`senzing-bootcamp/steering/visualization-protocol.md`) that defines the single authoritative visualization offer flow used across Modules 3, 5, 7, and 8.
- **Checkpoint**: A defined point in a module where the agent offers a visualization to the bootcamper, as specified in the Visualization_Protocol checkpoint map.
- **Delivery_Mode**: The mechanism by which a visualization is served to the bootcamper — either as a static HTML file with baked-in data, or as a web service with live SDK queries.
- **Offer_Template**: The text template in the Visualization_Protocol that the agent uses to present visualization options at a checkpoint.
- **Visualization_Tracker**: The JSON file at `config/visualization_tracker.json` that records visualization offer state, chosen types, and delivery modes.
- **Overview_Sections**: The bullet-point content presented in Step 4 of the Onboarding_Flow after the modules table and before the comprehension check.
- **Web_Service_Guidance**: The steering file (`senzing-bootcamp/steering/visualization-web-service.md`) that provides endpoint specs, framework selection, code generation, and lifecycle management for the web service delivery mode.

## Requirements

### Requirement 1: Reorder Onboarding Overview Sections

**User Story:** As a bootcamper, I want the Tracks section to appear immediately after the modules table in the onboarding overview, so that I can see how modules are grouped into tracks without secondary context interrupting the flow.

#### Acceptance Criteria

1. WHEN the agent presents the Step 4 overview in the Onboarding_Flow, THE Onboarding_Flow SHALL list the overview bullet points in this order after the modules table: (a) Tracks let you skip to what matters, (b) Built-in 500-record eval license, (c) Test data available anytime with three sample datasets.
2. THE Onboarding_Flow SHALL preserve all existing overview content without removing or altering the text of any bullet point.
3. THE Onboarding_Flow SHALL maintain the guided-discovery preamble and glossary reference bullet points in their current positions (before and after the reordered group, respectively).

### Requirement 2: Add Delivery-Mode Choice to Visualization Checkpoints

**User Story:** As a bootcamper, I want to be offered a clear choice between a static HTML snapshot and a live web service at every visualization checkpoint, so that I can make an informed decision about whether my visualization will update with new data.

#### Acceptance Criteria

1. WHEN a visualization checkpoint is reached and the bootcamper selects a visualization type, THE Visualization_Protocol SHALL present a delivery-mode question offering two options: Static HTML (self-contained file, data baked in, no server needed, does not update) and Web service + HTML (small HTTP service with live SDK queries, refreshes on reload, requires running a local process).
2. THE Visualization_Protocol SHALL present the delivery-mode question after the type selection and before dispatching to the generation workflow.
3. IF the bootcamper selects the Web service delivery mode, THEN THE Visualization_Protocol SHALL dispatch to the Web_Service_Guidance steering file for scaffolding and lifecycle management.
4. IF the bootcamper selects the Static HTML delivery mode, THEN THE Visualization_Protocol SHALL follow the existing static generation path without loading the Web_Service_Guidance.
5. THE Visualization_Tracker SHALL record the chosen delivery mode in a `delivery_mode` field (value: `static` or `web_service`) alongside the existing `chosen_type` field when the status transitions from `offered` to `accepted`.
6. WHILE the checkpoint map lists only `Static_HTML_Report` as the available type (Module 5), THE Visualization_Protocol SHALL skip the delivery-mode question and default to static delivery.
7. THE Visualization_Protocol SHALL end the delivery-mode offer with a STOP directive, waiting for the bootcamper's input before proceeding.

### Requirement 3: Update Visualization Tracker Schema for Delivery Mode

**User Story:** As a bootcamp agent, I want the visualization tracker to record which delivery mode was chosen, so that subsequent checkpoints and session resumption can reference the bootcamper's preference.

#### Acceptance Criteria

1. THE Visualization_Tracker SHALL include a `delivery_mode` field in each offer entry, with valid values of `static`, `web_service`, or `null`.
2. WHEN an offer entry is first created with status `offered`, THE Visualization_Tracker SHALL set `delivery_mode` to `null`.
3. WHEN the bootcamper accepts a visualization and selects a delivery mode, THE Visualization_Tracker SHALL update `delivery_mode` to the selected value (`static` or `web_service`).
4. THE Visualization_Tracker SHALL increment the schema version from `1.0.0` to `1.1.0` to reflect the addition of the `delivery_mode` field.
