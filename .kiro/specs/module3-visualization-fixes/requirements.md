# Requirements Document

## Introduction

Three targeted fixes to the Module 3 Phase 2 visualization steering file (`senzing-bootcamp/steering/module-03-phase2-visualization.md`). The fixes address: (1) the agent skipping Phase 2 entirely despite the steering file specifying it, (2) the Entity Graph tab using a fixed 600px height instead of filling the viewport, and (3) the agent offering no guided tour after the visualization launches.

## Glossary

- **Steering_File**: The markdown file `senzing-bootcamp/steering/module-03-phase2-visualization.md` that instructs the agent on Phase 2 visualization generation and delivery
- **Agent**: The Kiro AI agent executing the Module 3 bootcamp workflow
- **Entity_Graph**: The D3.js force-directed graph tab in the visualization web page showing resolved entities and relationships
- **Graph_Container**: The HTML element wrapping the Entity Graph SVG, controlling its visible height
- **Guided_Tour**: A structured text-based walkthrough delivered in chat after the visualization launches, describing what the bootcamper should observe
- **Enforcement_Block**: A prominently formatted section in the steering file that explicitly prohibits skipping Phase 2

## Requirements

### Requirement 1: Phase 2 Execution Enforcement

**User Story:** As a bootcamp maintainer, I want the Phase 2 steering file to contain explicit "do not skip" reinforcement language, so that the agent cannot bypass the visualization step.

#### Acceptance Criteria

1.1 THE Steering_File SHALL contain an enforcement block at the top of the document (before Step 9) with the exact phrase "DO NOT SKIP" in uppercase.

1.2 THE Steering_File SHALL contain an enforcement block that states Phase 2 execution is mandatory and not optional.

1.3 THE Steering_File SHALL contain an enforcement block that explicitly prohibits transitioning to Module 4 before Phase 2 completes.

1.4 THE Steering_File SHALL contain an enforcement block that uses a visual marker (emoji or bold formatting) to draw attention to the non-skippable nature of Phase 2.

1.5 THE Steering_File SHALL contain the phrase "This phase is MANDATORY" or equivalent mandatory declaration within the enforcement block.

### Requirement 2: Entity Graph Viewport Height

**User Story:** As a bootcamper, I want the Entity Graph to fill the remaining viewport height below the header, so that the graph is large and immersive rather than constrained to a small fixed box.

#### Acceptance Criteria

2.1 THE Steering_File SHALL specify that the Graph_Container uses `calc(100vh - 120px)` as its height value instead of a fixed pixel height.

2.2 THE Steering_File SHALL specify that the 120px offset accounts for the fixed header, banner, and tab navigation combined height.

2.3 THE Steering_File SHALL NOT specify a fixed pixel height (such as 600px) for the Graph_Container.

### Requirement 3: Post-Launch Guided Tour

**User Story:** As a bootcamper, I want the agent to offer a text-based guided tour after the visualization launches, so that I understand what to look for in the entity resolution results.

#### Acceptance Criteria

3.1 WHEN the visualization web service is verified and running, THE Steering_File SHALL instruct the Agent to present a guided tour message in chat.

3.2 THE Steering_File SHALL specify that the guided tour describes cross-source matches visible in the Entity Graph.

3.3 THE Steering_File SHALL specify that the guided tour describes name variations resolved by Senzing (e.g., Robert Smith / Bob Smith).

3.4 THE Steering_File SHALL specify that the guided tour describes relationship edges and their match key labels.

3.5 THE Steering_File SHALL specify that the guided tour describes the records-per-entity histogram in the Merge Statistics tab.

3.6 THE Steering_File SHALL specify that the guided tour is delivered as a single structured chat message with no interactive pauses.

3.7 THE Steering_File SHALL specify that the guided tour is offered after the URL is presented and before the STOP block that waits for the bootcamper.
