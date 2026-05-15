# Requirements: Module 3 System Verification Default-On

## Overview

Change Module 3 (System Verification) from opt-in/optional to default-on (opt-out) in the bootcamp flow, since it validates the entire SDK setup end-to-end before bootcampers invest time with their own data.

## Requirements

1. Update `onboarding-flow.md` to include Module 3 in the default Core Bootcamp path (Modules 1, 2, 3, 4, 5, 6, 7) rather than marking it optional
2. Update POWER.md module table to remove "(Optional)" from Module 3's description
3. Update POWER.md Quick Start section to reflect Module 3 as part of the default flow
4. Add an explicit opt-out mechanism: if the bootcamper says "skip verification" or "I've already verified", allow skipping with a note that issues may surface later
5. Update `module-transitions.md` to reflect Module 3 as a standard transition point (2→3→4) rather than an optional branch
6. Update `module-prerequisites.md` if Module 3 completion becomes a soft prerequisite for Module 4
7. Update `steering-index.yaml` if any keyword routing changes are needed
8. Ensure existing tests that reference Module 3 as optional are updated to reflect the new default-on status
9. Update `config/module-dependencies.yaml` to reflect the new dependency chain
