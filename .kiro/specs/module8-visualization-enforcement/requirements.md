# Requirements: Module 8 Visualization Enforcement

## Overview

Module 8 (Query, Visualize & Validate Results) requires the agent to offer two visualizations before closing the module: an interactive entity graph (after exploratory queries, step 3) and a results dashboard (after documenting findings, step 7). The agent sometimes skips these offers and moves directly from validation results to the completion summary. The existing `offer-visualization.kiro.hook` only triggers on `fileCreated` in `src/query/`, which does not cover the case where the agent skips the offer entirely.

This feature strengthens enforcement by: (1) updating the Module 8 steering file to make both visualization offers mandatory WAIT steps with prominent formatting, and (2) adding an `agentStop` hook that checks whether Module 8 visualization offers were made before the module closes.

## Deliverables

1. Updates to `senzing-bootcamp/steering/module-08-query-validation.md` to make visualization offers mandatory WAIT steps
2. A new hook or update to the existing `offer-visualization.kiro.hook` to enforce the visualization offer on `agentStop`
3. Updates to `senzing-bootcamp/hooks/README.md` to document the changes

## Requirements

### 1. Steering File — Mandatory Visualization WAIT Steps

1.1 The steering file `senzing-bootcamp/steering/module-08-query-validation.md` SHALL be updated to make the entity graph visualization offer in step 3 a mandatory WAIT step that the agent cannot skip.

1.2 The entity graph WAIT step SHALL use prominent formatting (bold, block quotes, or banner-style markers) to clearly distinguish it from surrounding content and signal that the agent must pause for user input.

1.3 The steering file SHALL be updated to make the results dashboard visualization offer in step 7 a mandatory WAIT step that the agent cannot skip.

1.4 The results dashboard WAIT step SHALL use the same prominent formatting as the entity graph WAIT step for consistency.

1.5 Each mandatory WAIT step SHALL explicitly instruct the agent to wait for the user's response before proceeding to the next step — the agent may continue only after the user accepts or declines.

1.6 The steering file updates SHALL NOT change the functional content of any other steps in the module workflow.

1.7 The steering file updates SHALL NOT change the user's ability to decline a visualization — declining is a valid response that allows the agent to proceed.

### 2. Visualization Enforcement Hook

2.1 The system SHALL provide an `agentStop` hook that checks whether Module 8 visualization offers were made before the module closes.

2.2 WHEN the hook fires THEN the agent SHALL read `config/bootcamp_progress.json` to determine if the current module is Module 8; if the module is not 8, the hook SHALL do nothing.

2.3 WHEN the current module is Module 8 and the agent has not offered the entity graph visualization THEN the hook SHALL prompt the agent to offer it before closing.

2.4 WHEN the current module is Module 8 and the agent has not offered the results dashboard visualization THEN the hook SHALL prompt the agent to offer it before closing.

2.5 The hook SHALL follow the existing hook JSON format and conventions used by other hooks in `senzing-bootcamp/hooks/`.

2.6 The hook SHALL NOT block or interfere with the existing `offer-visualization.kiro.hook` fileCreated trigger — both hooks may coexist.

2.7 The hook SHALL NOT block or interfere with the existing `summarize-on-stop.kiro.hook` — both hooks may fire independently on `agentStop`.

### 3. Hooks README Update

3.1 The hooks README at `senzing-bootcamp/hooks/README.md` SHALL be updated to document the new visualization enforcement hook.

3.2 The README entry SHALL follow the same format as existing hook entries (numbered, with trigger type, action, and use case).

3.3 The README entry SHALL be added in the correct sequential position in the numbered list.

3.4 The existing entry for `offer-visualization.kiro.hook` (entry 14) SHALL be updated to note that it works in conjunction with the new enforcement hook — the fileCreated trigger catches query program creation, while the agentStop trigger catches the case where the agent skips the offer entirely.
