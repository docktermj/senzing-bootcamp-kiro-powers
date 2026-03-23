---
inclusion: manual
---

# Rollback and Recovery Procedures

Prepare for failures and enable quick recovery.

## Database Backup Strategy

### Before Major Operations

Create `src/utils/backup_database.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="data/backups"
mkdir -p $BACKUP_DIR

# SQLite backup
if [ -f "database/G2C.db" ]; then
    cp database/G2C.db "$BACKUP_DIR/G2C_$DATE.db"
    echo "SQLite backup created: $BACKUP_DIR/G2C_$DATE.db"
fi

# PostgreSQL backup
if [ ! -z "$POSTGRES_DB" ]; then
    pg_dump -h localhost -U senzing -d senzing > "$BACKUP_DIR/senzing_$DATE.sql"
    echo "PostgreSQL backup created: $BACKUP_DIR/senzing_$DATE.sql"
fi

# Keep only last 7 backups
ls -t $BACKUP_DIR/*.db 2>/dev/null | tail -n +8 | xargs rm -f
ls -t $BACKUP_DIR/*.sql 2>/dev/null | tail -n +8 | xargs rm -f
```

### Rollback Procedure

Create `src/utils/rollback.sh`:

```bash
#!/bin/bash
# src/utils/rollback.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./src/utils/rollback.sh <backup_file>"
    echo "Available backups:"
    ls -lh data/backups/
    exit 1
fi

echo "WARNING: This will restore database to $BACKUP_FILE"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    if [[ $BACKUP_FILE == *.db ]]; then
        # SQLite restore
        mkdir -p database
        cp "$BACKUP_FILE" database/G2C.db
        echo "SQLite database restored"
    elif [[ $BACKUP_FILE == *.sql ]]; then
        # PostgreSQL restore
        psql -h localhost -U senzing -d senzing < "$BACKUP_FILE"
        echo "PostgreSQL database restored"
    fi
fi
```

## Recovery Procedures

Create `docs/recovery_procedures.md`:

```markdown
# Recovery Procedures

## Failed Transformation
**Symptom**: Transformation program crashes or produces invalid output

**Recovery**:
1. Check logs/transform.log for errors
2. Fix transformation logic in `src/transform/`
3. Delete invalid output: `rm data/transformed/[source]_senzing.jsonl`
4. Re-run transformation on sample data first
5. Validate with lint_record before full run

## Failed Loading
**Symptom**: Loading program fails partway through

**Recovery**:
1. Check logs/load.log for error codes
2. Use explain_error_code to diagnose
3. Restore database from backup:
   ```bash
   ./src/utils/rollback.sh data/backups/G2C_YYYYMMDD_HHMMSS.db
   ```
4. Fix data quality issues
5. Resume loading from last successful record

## Data Quality Issues
**Symptom**: Poor match rates or unexpected results

**Recovery**:
1. Don't load more data - stop and analyze
2. Review data quality reports from Module 3
3. Check mapping specifications from Module 4
4. Test with small sample (100 records)
5. Reload corrected data
5. Adjust confidence scores or mappings
6. Rollback and reload with improved mappings

## Database Corruption
**Symptom**: Database errors, crashes, or inconsistent results

**Recovery**:
1. Stop all loading/query operations
2. Restore from most recent backup
3. Verify backup integrity
4. Resume operations
5. If backups are corrupted, rebuild from scratch

## Version Control Recovery
**Symptom**: Accidentally deleted or modified critical files

**Recovery**:
```bash
# Restore specific file from git
git checkout HEAD -- src/transform/transform_customer.py

# Restore entire src directory to previous commit
git log  # Find commit hash
git checkout <commit-hash> -- src/

# Undo last commit (keep changes)
git reset --soft HEAD~1
```
```

## Backup Best Practices

1. **Backup before Module 6**: Always backup before loading data
2. **Backup before major changes**: Before modifying configurations or schemas
3. **Test backups regularly**: Verify backups can be restored
4. **Keep multiple versions**: Retain at least 7 days of backups
5. **Document backup locations**: Ensure team knows where backups are stored

## When to Load This Guide

Load this steering file when:
- Starting Module 6 (before loading data)
- User encounters errors during loading
- User asks about backup or recovery
- Setting up production systems
- After a failure or data corruption incident
