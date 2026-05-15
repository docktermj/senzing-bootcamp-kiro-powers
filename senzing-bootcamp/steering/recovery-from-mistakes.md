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

## Database Recovery

When the database itself becomes corrupted or inaccessible (beyond just bad records), use the following guidance.

### Common Corruption Scenarios

6. **Disk full during load** — the loading process ran out of disk space mid-write. SQLite may leave a partial transaction or corrupted WAL file. The database file may exist but be in an inconsistent state.
7. **Process killed mid-transaction** — the loading program was interrupted (Ctrl+C, OOM kill, container restart) while a transaction was open. The WAL or journal file may contain uncommitted changes.
8. **WAL file corruption** — the `-wal` or `-shm` companion files alongside `G2C.db` are damaged or out of sync with the main database file. This can happen after an unclean shutdown or disk error.
9. **Lock file stale** — a previous process crashed without releasing the database lock. Subsequent connections fail with "database is locked" even though no process is actively using the file.

### Detection Signals

Watch for these indicators that the database needs recovery:

- **"database is locked"** — another process holds the lock, or a stale lock file remains from a crashed process.
- **"database disk image is malformed"** — SQLite cannot read the file structure. The database is corrupted and needs repair or rebuild.
- **Unexpected zero entity counts** — a load reported success but querying `RES_ENT_OKEY` returns zero rows. The transaction may not have committed.

Run `scripts/check_database.py` for automated detection of all these conditions:

```bash
python scripts/check_database.py --db-path database/G2C.db
```

### SQLite Recovery Steps

10. **Check integrity** — run the integrity check to confirm corruption:

    ```sql
    PRAGMA integrity_check;
    ```

    If the result is anything other than "ok", the database has structural damage.

11. **Recover from WAL** — if the WAL file exists but the database won't open cleanly, force a checkpoint:

    ```sql
    PRAGMA wal_checkpoint(TRUNCATE);
    ```

    This flushes pending WAL changes into the main database file and truncates the WAL. Use `scripts/check_database.py --repair` to attempt this automatically.

12. **Rebuild from scratch** — if integrity check fails after WAL recovery, delete the database and reload:

    ```bash
    rm database/G2C.db database/G2C.db-wal database/G2C.db-shm
    # Re-run the loading program to recreate the database
    ```

    Warn the bootcamper: "The database is unrecoverable. Deleting and re-running the load from scratch."

### PostgreSQL Recovery Steps

13. **Check for orphaned transactions** — long-running or abandoned transactions can block other operations:

    ```sql
    SELECT pid, state, query_start, query
    FROM pg_stat_activity
    WHERE state = 'idle in transaction';
    ```

    Terminate orphaned backends with `SELECT pg_terminate_backend(pid);`.

14. **Vacuum** — reclaim space and update statistics after recovering from failed loads:

    ```sql
    VACUUM;
    ANALYZE;
    ```

15. **Re-run with idempotent RECORD_ID** — Senzing uses `DATA_SOURCE` + `RECORD_ID` as a unique key. Re-loading the same records with the same RECORD_IDs is safe and idempotent — existing records are updated rather than duplicated. Simply re-run the failed load without deleting the database.

### Automated Recovery

Use `scripts/check_database.py` for one-command detection and repair:

```bash
# Check database health
python scripts/check_database.py

# Attempt automatic repair (WAL checkpoint + vacuum)
python scripts/check_database.py --repair

# JSON output for programmatic use
python scripts/check_database.py --json
```

The script checks: file exists, can connect, integrity check passes, and entity count is greater than zero.
