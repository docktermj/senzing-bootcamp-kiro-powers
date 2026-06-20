---
inclusion: manual
---

## Non-Blocking Error Handling

Every artifact-creation step (recap append, journal entry, completion certificate) MUST handle errors gracefully so that a single failure never blocks the bootcamper's flow.

### Per-Step Error Handling

For each of the following steps — **recap_append**, **journal_entry**, and **completion_certificate** — apply these rules:

1. **Catch file-system errors** (permission denied, disk full, path not found, or any OS-level I/O failure).
2. **Log a warning** visible to the bootcamper using this exact format:

   > ⚠️ [Step name] skipped: [reason]. This will be retried on next module completion.

   Examples:
   - `⚠️ recap_append skipped: Permission denied writing to docs/bootcamp_recap.md. This will be retried on next module completion.`
   - `⚠️ journal_entry skipped: Disk full. This will be retried on next module completion.`
   - `⚠️ completion_certificate skipped: Path not found for docs/progress/. This will be retried on next module completion.`

3. **Continue** to the next step in the defined order. Do NOT halt, raise an error, or prompt the bootcamper for intervention.
4. **Do NOT retry immediately** — the failed step will be retried on the next module completion.

### 30-Second Timeout

If any single step exceeds **30 seconds** of execution time (e.g., due to a hung file system or unresponsive disk), skip that step and log a warning:

> ⚠️ [Step name] skipped: Timed out after 30 seconds. This will be retried on next module completion.

### Predecessor Failure Does Not Block Subsequent Steps

If a predecessor step fails or is skipped:

- Subsequent steps **still execute** using only data available from previously successful steps.
- The journal entry does NOT depend on the recap append's output — it can proceed independently.
- The completion certificate does NOT depend on the journal entry — it can proceed independently.
- Even if **both** the recap append and journal entry fail, the **next_step_options** step MUST still execute and present the bootcamper with their choices.

### Retry on Next Module Completion

Failed steps are not retried within the same completion flow. Instead:

- The next time any module is completed, each step runs again from scratch.
- If the file-system issue has been resolved by then, the step will succeed normally.
- If the issue persists, the same skip-and-warn behavior applies again.
