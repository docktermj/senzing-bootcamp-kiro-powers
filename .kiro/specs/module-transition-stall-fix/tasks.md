# Implementation Plan: Module Transition Stall Fix

## Overview

Add explicit "act on confirmation" rules to ensure the agent immediately begins the next module when the bootcamper confirms readiness, rather than producing a dead-end response.

## Tasks

- [x] 1. Add Module Transition Protocol to agent-instructions.md
  - [x] 1.1 Add a new rule to the Communication section in `senzing-bootcamp/steering/agent-instructions.md`
    - Rule text: "When you ask 'Ready for Module X?' and the bootcamper responds affirmatively (yes, sure, let's go, ready, etc.), immediately begin that module in the same turn. Display the module banner, journey map, and start Step 1. Never acknowledge without acting at a module transition."
    - Place after the "No Dead-End Responses" rule (or after the question-stop protocol if that spec hasn't been implemented yet)
    - Do NOT modify existing rules
    - _Requirements: 1, 3_

- [x] 2. Strengthen module completion workflow steering
  - [x] 2.1 Locate the module completion/transition steering file (likely `senzing-bootcamp/steering/module-completion-workflow.md` or equivalent)
  - [x] 2.2 At the point where the "Ready for Module X?" question is defined, add post-confirmation instructions:
    - "Upon receiving an affirmative response, immediately execute the next module's startup sequence: (1) Display module banner, (2) Show journey map, (3) Begin Step 1. Do not produce any intermediate acknowledgment."
    - _Requirements: 2, 3_

- [x] 3. Verify the fix
  - Confirm `agent-instructions.md` contains the Module Transition Protocol rule
  - Confirm the rule explicitly ties affirmative responses to immediate module startup
  - Confirm the module completion steering contains post-confirmation instructions
  - Confirm negative responses and questions at transition points are not affected
  - Run any existing steering validation scripts

## Notes

- This fix is closely related to the dead-end-response-fix spec but targets the specific case of module transitions
- The module startup sequence (banner + journey map + Step 1) is already defined in module steering files — this fix just ensures it's triggered immediately on confirmation
- No Python code changes — only steering markdown edits
