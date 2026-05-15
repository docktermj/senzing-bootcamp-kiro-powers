# Requirements: Split onboarding-flow.md Below Token Threshold

## Overview

Split `onboarding-flow.md` (currently 6,451 tokens) to comply with the 5,000-token split threshold defined in `steering-index.yaml`, since onboarding is a sequential multi-phase process that naturally decomposes.

## Requirements

1. Split `onboarding-flow.md` into phases following the existing step structure: Phase 1 (welcome, version display, language selection) and Phase 2 (track selection, hook installation, project setup)
2. The root file (`onboarding-flow.md`) must remain as the entry point with phase routing logic, target under 3,500 tokens
3. The second phase file must contain track selection, hook installation, and project scaffolding steps, target under 3,500 tokens
4. Update `steering-index.yaml` to add a `phases` map for onboarding (similar to module phase maps)
5. Both files must remain under the 5,000-token split threshold
6. Update `agent-instructions.md` references to onboarding-flow.md if needed
7. Update `session-resume.md` references to onboarding-flow.md if needed
8. Ensure keyword routing (`onboard`, `start`) still works correctly
9. Run `measure_steering.py` to update token counts
10. Run `validate_commonmark.py` on both new files
11. Update tests that validate onboarding-flow.md structure to account for the split
