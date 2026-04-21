# Design Document: Complete Module 0 License Configuration

## Overview

Expand Step 5 of the Module 0 steering file (`senzing-bootcamp/steering/module-00-sdk-setup.md`) to include full license configuration guidance that matches the module documentation. This is a content-only change to a single markdown file — no code, no new files.

## Current State

Step 5 in the steering file already contains:
- CONFIGPATH license discovery
- Project-local `licenses/g2.lic` check
- BASE64 key handling with security warning
- License file placement instructions
- `LICENSEFILE` in PIPELINE engine config
- Evaluation fallback with `bootcamp_preferences.yaml` recording

## Gaps Identified

Comparing with `docs/modules/MODULE_0_SDK_SETUP.md`, the steering file is missing:
1. **License priority order** — The module doc states: `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → `/etc/opt/senzing/g2.lic`. The steering file doesn't document this sequence.
2. **`SENZING_LICENSE_PATH` environment variable** — Not mentioned in the discovery flow.
3. **License acquisition guidance** — No contact info for obtaining evaluation or production licenses.
4. **`licenses/README.md` reference** — Not mentioned.

## Changes

### Change 1: Add License Priority Order Block

**Location:** At the top of Step 5, immediately after the section heading and before the discovery logic.

**Content:** A clearly formatted block explaining the Senzing license resolution order:
1. Project-local `licenses/g2.lic` (highest priority)
2. `SENZING_LICENSE_PATH` environment variable
3. System CONFIGPATH `g2.lic` (e.g., `/etc/opt/senzing/g2.lic`)
4. Built-in evaluation mode (500-record limit, no file needed)

This gives the agent context before it starts the discovery flow.

### Change 2: Add SENZING_LICENSE_PATH Check to Discovery Sequence

**Location:** Insert a new check between the existing CONFIGPATH check and the "no license found" prompt.

**Content:** After checking CONFIGPATH and before asking the user, check if `SENZING_LICENSE_PATH` is set:
- If set and points to a valid file, inform the user and offer to use it
- If set but file doesn't exist, warn the user

The discovery sequence becomes:
1. Check project-local `licenses/g2.lic`
2. Check system CONFIGPATH
3. Check `SENZING_LICENSE_PATH` environment variable
4. If none found, ask the user

### Change 3: Add License Acquisition Guidance

**Location:** Within the "If they don't have a license" section, after the evaluation limits note.

**Content:** Add contact information:
- Evaluation license: support@senzing.com (1-2 business days, 30-90 day validity)
- Production license: sales@senzing.com

### Change 4: Add licenses/README.md Reference

**Location:** At the end of Step 5, as a note.

**Content:** A reference directing the agent to mention `licenses/README.md` for complete licensing details.

## Approach

All changes are additive insertions into the existing Step 5 markdown content. No existing text is modified or removed. The insertions are placed at logical points in the existing flow.

## Correctness Properties

### Property 1: License priority order is documented
- **Criteria:** 1.1, 1.2
- **Validation:** The steering file contains text describing the four-level priority order in the correct sequence

### Property 2: SENZING_LICENSE_PATH discovery is included
- **Criteria:** 2.1, 2.2, 2.3
- **Validation:** The steering file contains instructions to check `SENZING_LICENSE_PATH` and handle both valid and invalid cases

### Property 3: License acquisition contacts are present
- **Criteria:** 3.1, 3.2, 3.3
- **Validation:** The steering file contains support@senzing.com, sales@senzing.com, and the 30-90 day note

### Property 4: README reference is included
- **Criteria:** 4.1, 4.2
- **Validation:** The steering file references `licenses/README.md`

### Property 5: Existing content is preserved
- **Criteria:** 5.1, 5.2
- **Validation:** All key existing phrases remain in the file: "CONFIGPATH", "BASE64", "LICENSEFILE", "PIPELINE", "bootcamp_preferences.yaml", "500 records"
