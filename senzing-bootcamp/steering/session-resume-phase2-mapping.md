# Mapping Checkpoint Recovery

## Guard Condition

If this file was loaded but none of the following conditions are true, skip all content below and return to the Phase-1 flow:

- One or more `config/mapping_state_*.json` files exist

## Checkpoint Validation

Before fast-tracking through completed steps, validate each checkpoint:

1. Read the checkpoint file. If JSON is invalid or required fields (`data_source`, `current_step`, `completed_steps`) are missing, the checkpoint is corrupted.
2. Call `mapping_workflow` with `action='status'` and pass the full checkpoint contents as the `state` parameter.
3. If the MCP response confirms the state is valid, proceed with fast-tracking through `completed_steps`.
4. If the MCP response indicates the state is invalid (e.g., data source no longer exists, schema changed), inform the bootcamper: "The mapping checkpoint for [data source] appears to be outdated or invalid. Would you like to restart the mapping from scratch?"
5. If the checkpoint file has invalid JSON, inform the bootcamper: "The mapping checkpoint for [data source] is corrupted and cannot be read. The mapping will need to restart from the beginning."

In cases 4 and 5, delete the corrupted/invalid checkpoint file and offer to restart.

## Resume Options

For each detected mapping checkpoint, after describing the in-progress state, present these options:

- **(a) Resume** — Pick up the mapping from where it left off
- **(b) Restart** — Delete the checkpoint and start the mapping from scratch
- **(c) Skip** — Continue with other bootcamp work; the checkpoint stays for later

If only one mapping checkpoint exists, present the options inline. If multiple checkpoints exist, list each data source with its state first, then ask which one(s) to resume.

When the bootcamper chooses **(b) Restart**, delete the corresponding `config/mapping_state_[datasource].json` file before beginning the mapping workflow from scratch.

## Fast-Track Through Completed Steps

After validation succeeds, restart `mapping_workflow` for each data source with a valid checkpoint and fast-track through the completed mapping steps (listed in `completed_steps`) before resuming from the first incomplete mapping step.

## Summary Integration

When mapping checkpoints exist, include in the welcome-back summary: the data source name and completed mapping steps. For each checkpoint, mention: "You were in the middle of mapping [data source name] — we completed steps [list of completed_steps] last time. I can pick up where we left off." If multiple mapping checkpoints exist, list each one.
