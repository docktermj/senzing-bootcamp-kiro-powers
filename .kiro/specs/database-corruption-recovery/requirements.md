# Requirements: Database Corruption Recovery

## Overview

Document and provide tooling for recovering from database corruption during Module 6 data loading (disk full, process killed, SQLite lock issues), since the current recovery-from-mistakes.md doesn't cover database-level failures.

## Requirements

1. Add a "Database Recovery" section to `steering/recovery-from-mistakes.md` covering common corruption scenarios: disk full during load, process killed mid-transaction, SQLite WAL file corruption, lock file stale
2. Document detection signals: "database is locked" errors, "database disk image is malformed", unexpected zero entity counts after a load that reported success
3. Provide recovery steps for SQLite: check integrity (`PRAGMA integrity_check`), recover from WAL (`PRAGMA wal_checkpoint(TRUNCATE)`), rebuild from scratch using the loading program
4. Provide recovery steps for PostgreSQL: check for orphaned transactions, vacuum, re-run failed loads with idempotent RECORD_ID behavior
5. Add a `scripts/check_database.py` script that runs basic health checks: file exists, can connect, integrity check passes, entity count > 0 (for SQLite)
6. The script must accept `--repair` flag that attempts automatic recovery (WAL checkpoint, vacuum) before reporting
7. Integrate the database check into `preflight.py` as an optional check when a database file already exists
8. Add database recovery to `common-pitfalls.md` under a new "Database Issues" section
9. Update `troubleshooting-decision-tree.md` to include a database corruption branch
10. Write tests for `check_database.py` covering: missing database, healthy database, simulated corruption detection
