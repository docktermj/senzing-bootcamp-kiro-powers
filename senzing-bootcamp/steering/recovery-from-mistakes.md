---
inclusion: manual
---

# Recovery from Mistakes

When a bootcamper makes a mistake mid-step (wrong field mapping, bad transformation, incorrect config):

1. **Identify what went wrong** — explain the issue clearly before attempting to fix it.
2. **MCP workflow state** — if a `mapping_workflow` is in progress, the state can be reset by calling `mapping_workflow(action='start')` again with the same source file. This restarts the workflow from scratch for that source.
3. **File artifacts** — if incorrect files were created (bad transformation output, wrong config), delete or overwrite them. Tell the bootcamper which files are being replaced.
4. **Progress state** — do NOT roll back `config/bootcamp_progress.json` step numbers. The step counter tracks where the bootcamper is in the workflow, not whether the step succeeded. Re-doing a step at the same step number is fine.
5. **Database state** — if bad records were loaded into `database/G2C.db`, the simplest recovery is to delete the database file and re-run loading from scratch. Warn the bootcamper before doing this: "This will delete all loaded data. You'll need to re-run the loading step."
