# Design: Mapping Workflow Checkpoint Resume

## Overview

Enhance the session resume workflow to detect in-progress `mapping_workflow` checkpoints (`config/mapping_state_*.json`), present clear resume options to the bootcamper, validate checkpoint state via the MCP `mapping_workflow` tool, and handle corrupted or invalid checkpoints gracefully. Also update `agent-instructions.md` to cross-reference this behavior and add tests verifying the steering file content.

## Architecture

### Data Flow

```text
Session Start
    │
    ▼
Step 1: Read State Files
    │
    ├─ config/bootcamp_progress.json
    ├─ config/bootcamp_preferences.yaml
    ├─ config/mapping_state_*.json  ◄── checkpoint detection
    └─ config/session_log.jsonl
    │
    ▼
Step 3: Summarize and Confirm
    │
    ├─ Display mapping checkpoint info per data source
    └─ Present 3 options: resume / restart / skip
    │
    ▼
Step 4: Load Module Steering
    │
    ├─ If resume: mapping_workflow(action='status', state=<checkpoint>)
    │   ├─ Valid → fast-track through completed steps
    │   └─ Invalid → inform user, offer restart
    ├─ If restart: delete checkpoint, start mapping fresh
    └─ If skip: continue with other work
```

### Checkpoint File Format

Each `config/mapping_state_[datasource].json` file contains:

```json
{
  "data_source": "CUSTOMERS",
  "source_file": "data/raw/customers.csv",
  "current_step": 3,
  "completed_steps": ["profile", "plan", "map"],
  "decisions": {
    "entity_type": "PERSON",
    "field_mappings": {"full_name": "NAME_FULL"}
  },
  "last_updated": "2026-04-14T10:30:00Z"
}
```

Required fields for a valid checkpoint: `data_source`, `current_step`, `completed_steps`.

## Changes Required

### 1. `session-resume.md` — Step 1 Enhancement

Step 1 already lists `config/mapping_state_*.json` as item 4 in the state files to read. The current instruction says: "If found, the user was mid-mapping when the session ended." This is sufficient for detection.

**No change needed to Step 1** — it already covers checkpoint detection.

### 2. `session-resume.md` — Step 3 Enhancement

Step 3 already includes mapping checkpoint display logic:

> **If mapping checkpoints exist** (`config/mapping_state_*.json`), include the data source name and completed mapping steps in the summary.

**Enhancement needed:** Add explicit three-option resume offer after the mapping checkpoint summary. Currently the file mentions "I can pick up where we left off" but does not present the three distinct options (resume/restart/skip) as required.

Add after the existing mapping checkpoint paragraph in Step 3:

```markdown
**Mapping resume options:** For each detected mapping checkpoint, after describing the in-progress state, present these options:

- **(a) Resume** — Pick up the mapping from where it left off
- **(b) Restart** — Delete the checkpoint and start the mapping from scratch
- **(c) Skip** — Continue with other bootcamp work; the checkpoint stays for later

If only one mapping checkpoint exists, present the options inline. If multiple checkpoints exist, list each data source with its state first, then ask which one(s) to resume.
```

### 3. `session-resume.md` — Step 4 Enhancement

Step 4 already has mapping checkpoint resume logic. **Enhancement needed:** Add explicit state validation via `mapping_workflow(action='status')` before fast-tracking, and add error handling for invalid/corrupted checkpoints.

Add to the mapping checkpoint handling in Step 4:

```markdown
**Checkpoint validation:** Before fast-tracking through completed steps, validate the checkpoint:

1. Read the checkpoint file. If JSON is invalid or required fields (`data_source`, `current_step`, `completed_steps`) are missing, the checkpoint is corrupted.
2. Call `mapping_workflow` with `action='status'` and pass the full checkpoint contents as the `state` parameter.
3. If the MCP response confirms the state is valid, proceed with fast-tracking through `completed_steps`.
4. If the MCP response indicates the state is invalid (e.g., data source no longer exists, schema changed), inform the bootcamper: "The mapping checkpoint for [data source] appears to be outdated or invalid. Would you like to restart the mapping from scratch?"
5. If the checkpoint file has invalid JSON, inform the bootcamper: "The mapping checkpoint for [data source] is corrupted and cannot be read. The mapping will need to restart from the beginning."

In cases 4 and 5, delete the corrupted/invalid checkpoint file and offer to restart.
```

### 4. `agent-instructions.md` — State & Progress Note

Add a cross-reference note to the existing `mapping_workflow` bullet in the State & Progress section:

```markdown
- `mapping_workflow`: pass exact `state`, never modify. Checkpoint to `config/mapping_state_[datasource].json` after **each** step. Delete checkpoint when workflow completes for a source. On session resume, `session-resume.md` detects these checkpoints and offers resume/restart/skip options with state validation via `mapping_workflow(action='status')`.
```

### 5. Tests

Create `senzing-bootcamp/tests/test_mapping_checkpoint_resume.py` with tests that read `session-resume.md` and `agent-instructions.md` to verify:

1. Step 1 mentions `mapping_state_*.json` detection
2. Step 3 contains mapping checkpoint display instructions
3. Step 3 contains the three resume options (resume/restart/skip)
4. Step 4 contains `mapping_workflow` with `action='status'` validation instruction
5. Step 4 contains corrupted checkpoint handling instructions
6. Multiple data source handling is documented
7. `agent-instructions.md` State & Progress section references checkpoint resume behavior

## Integration Points

### Existing References (No Changes Needed)

These files already reference the checkpoint behavior correctly:

- `module-05-phase3-test-load.md` — Documents checkpoint format and Phase 3 resume
- `docs/guides/AFTER_BOOTCAMP.md` — Mentions checkpoint resume for new data sources
- `docs/guides/ARCHITECTURE.md` — Lists mapping state files in session resume flow

### Files to Modify

| File | Change |
|------|--------|
| `senzing-bootcamp/steering/session-resume.md` | Add three-option resume offer (Step 3) and checkpoint validation logic (Step 4) |
| `senzing-bootcamp/steering/agent-instructions.md` | Add cross-reference note to State & Progress section |

### Files to Create

| File | Purpose |
|------|---------|
| `senzing-bootcamp/tests/test_mapping_checkpoint_resume.py` | Unit tests verifying steering file content |

## Correctness Properties

1. **Detection is non-destructive**: Reading checkpoint files during Step 1 never modifies them.
2. **Three options always presented**: When a checkpoint is found, the bootcamper always gets resume/restart/skip choices.
3. **Validation before action**: The agent always validates checkpoint state via MCP before attempting to fast-track.
4. **Graceful degradation**: Invalid or corrupted checkpoints result in a clear message and restart offer, never a crash or silent failure.
5. **Multi-source support**: Each data source checkpoint is handled independently — one corrupted checkpoint does not affect others.
6. **Idempotent resume**: Resuming from a valid checkpoint produces the same result regardless of how many times the session was interrupted.

## Constraints

- No new Python scripts needed — this is purely steering file content
- Tests use the existing pattern of reading and parsing steering markdown files
- No third-party test dependencies beyond pytest (no Hypothesis needed for these content-verification tests)
- Changes must not break existing session resume flow for bootcampers without mapping checkpoints
