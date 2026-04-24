# Requirements: Module 12 Phase Gate

## Overview

Module 12 (Deployment and Packaging) has two distinct phases: Packaging (Steps 2–11) and Deployment (Steps 12–15). The steering file instructs the agent to pause after packaging and ask the bootcamper whether to proceed to deployment, but the agent blends the phases together without a clear decision gate. This feature adds a deterministic `postTaskExecution` hook that enforces the phase gate externally, along with steering file improvements to make the boundary more prominent.

## Deliverables

1. A hook file: `senzing-bootcamp/hooks/module12-phase-gate.kiro.hook`
2. Updates to `senzing-bootcamp/steering/module-12-deployment.md` to make the phase gate more prominent
3. Updates to `senzing-bootcamp/hooks/README.md` to document the new hook

## Requirements

### 1. Phase Gate Hook

1.1 The system SHALL provide a `postTaskExecution` hook at `senzing-bootcamp/hooks/module12-phase-gate.kiro.hook` that fires after Module 12 packaging tasks complete.

1.2 WHEN the hook fires THEN the agent SHALL display a clear packaging-complete summary listing what was accomplished (containerization, multi-environment config, CI/CD pipeline, pre-deployment checklist, documentation).

1.3 WHEN the hook fires THEN the agent SHALL reassure the bootcamper that the packaging phase did not deploy anything or make any changes to the target environment — everything so far was local preparation work, and it is safe to stop here.

1.4 WHEN the hook fires THEN the agent SHALL explicitly ask the bootcamper: "Would you like to actually deploy this now, or would you prefer to stop here and deploy later on your own?"

1.5 WHEN the hook fires THEN the agent SHALL wait for the bootcamper's response before proceeding to any deployment steps (Steps 12–15).

1.6 The hook SHALL instruct the agent to read `config/bootcamp_progress.json` to confirm the current module is Module 12 before displaying the phase gate prompt; if the module is not 12, the hook SHALL do nothing.

1.7 The hook SHALL follow the existing hook JSON format and conventions used by other hooks in `senzing-bootcamp/hooks/`.

### 2. Steering File Improvements

2.1 The steering file `senzing-bootcamp/steering/module-12-deployment.md` SHALL be updated to make the packaging-to-deployment phase gate more visually prominent.

2.2 The steering file SHALL include a clearly marked PHASE GATE section between Step 11 and Step 12 that is distinct from surrounding content.

2.3 The steering file SHALL reinforce the WAIT instruction with explicit formatting (e.g., bold, block quotes, or banner-style markers) so the agent is less likely to skip it.

2.4 The steering file updates SHALL NOT change the functional content of any packaging steps (Steps 2–11) or deployment steps (Steps 12–15).

### 3. Hooks README Update

3.1 The hooks README at `senzing-bootcamp/hooks/README.md` SHALL be updated to include documentation for the new `module12-phase-gate.kiro.hook`.

3.2 The README entry SHALL follow the same format as existing hook entries (numbered, with trigger type, action, and use case).

3.3 The README entry SHALL be added in the correct sequential position in the numbered list.
