# Requirements: Mapping Workflow Checkpoint Resume

## Overview

Ensure that when a session is interrupted during an in-progress `mapping_workflow`, the agent detects and offers to resume from the checkpoint on session resume, preventing loss of multi-step mapping progress.

## Requirements

1. `session-resume.md` must check for `config/mapping_state_*.json` files during Step 1 (Read All State Files)
2. When mapping checkpoint files are found, the session resume summary (Step 3) must inform the bootcamper which data source has an in-progress mapping and at which step it was interrupted
3. The resume offer must present three options: (a) resume the mapping from the checkpoint, (b) restart the mapping from scratch, (c) skip and continue with other work
4. When resuming, the agent must read the checkpoint file and pass its contents as the `state` parameter to `mapping_workflow` with `action='status'` to verify the state is still valid
5. If the checkpoint state is invalid or corrupted, inform the bootcamper and offer to restart the mapping
6. The checkpoint detection must work for multiple data sources (multiple `mapping_state_*.json` files) and present each one
7. Add a note to `agent-instructions.md` State & Progress section referencing the checkpoint resume behavior
8. Write tests verifying session-resume.md contains mapping checkpoint detection instructions
