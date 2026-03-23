---
inclusion: manual
---

# Disaster Recovery and Backup Procedures

## Overview

Disaster recovery (DR) ensures you can recover from data loss, corruption, or system failures. This guide covers backup strategies, rollback procedures, and disaster recovery planning for Senzing deployments.

## Why Disaster Recovery Matters

- **Data Protection**: Prevent permanent data loss
- **Business Continuity**: Minimize downtime
- **Compliance**: Meet regulatory requirements (GDPR, SOX, HIPAA)
- **Risk Mitigation**: Reduce impact of failures
- **Peace of Mind**: Sleep better knowing you can recover

## Recovery Objectives

### RTO (Recovery Time Objective)

How long can you afford to be down?

- **Critical Systems**: < 1 hour
- **Production Systems**: < 4 hours
- **Development Systems**: < 24 hours

### RPO (Recovery Point Objective)

How much data can you afford to lose?

- **Critical Data**: < 5 minutes (near real-time)
- **Production Data**: < 1 hour
- **Development Data**: < 24 hours

**Example**:
- RTO = 2 hours: System must be back online within 2 hours
- RPO = 15 minutes: Can lose up to 15 minutes of data

## Backup Strategy

### What to Back Up

**1. Database** (CRITICAL)
```
Priority: HIGHEST
Frequency: Continuous or hourly
Retention: 30 days minimum
```

The Senzing database contains:
- All loaded records
- Resolved entities
- Configuration
- Relationships

**2. Configuration Files** (CRITICAL)
```
Priority: HIGH
Frequency: On change
Retention: All versions
```

Files to back up:
- Engine configuration JSON
- Data source definitions
- Feature configurations
- Custom rules (if any)

**3. Source Data** (HIGH)
```
Priority: HIGH
Frequency: On receipt
Retention: 90 days minimum
```

Files to back up:
- `data/raw/` - Original source files
- `data/transformed/` - Transformed Senzing JSON

**4. Application Code** (MEDIUM)
```
Priority: MEDIUM
Frequency: On commit
Retention: All versions (Git)
```

Files to back up:
- `src/` - All application code
- Configuration files
- Scripts and utilities

**5. Logs and Metadata** (LOW)
```
Priority: LOW
Frequency: Daily
Retention: 30 days
```

Files to back up:
- `logs/` - Application logs
- `docs/` - Documentation
- Statistics and reports

### Backup Frequency

| Data Type | Frequency | Method |
|-----------|-----------|--------|
| Database | Continuous | WAL archiving + snapshots |
| Database | Hourly | Incremental backup |
| Database | Daily | Full backup |
| Database | Weekly | Full backup + offsite |
| Source Data | On receipt | Copy to backup location |
| Config Files | On change | Version control (Git) |
| Application Code | On commit | Version control (Git) |
| Logs | Daily | Archive to object storage |

## Database Backup

### PostgreSQL Backup

**Continuous Archiving (WAL)**:
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'

# Or use pg_receivewal for streaming
pg_receivewal -D /backup/wal -h localhost -U postgres
```

**Full Backup**:
```bash
#!/bin/bash
# Full database backup script

BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="senzing"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup with pg_dump
pg_dump -h localhost -U postgres -Fc "$DB_NAME" > "$BACKUP_DIR/senzing_$DATE.dump"

# Compress
gzip "$BACKUP_DIR/senzing_$DATE.dump"

# Verify backup
if [ $? -eq 0 ]; then
    echo "✅ Backup successful: senzing_$DATE.dump.gz"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Clean up old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +30 -delete
```

**Incremental Backup**:
```bash
#!/bin/bash
# Incremental backup using pg_basebackup

BACKUP_DIR="/backup/postgres/incremental"
DATE=$(date +%Y%m%d_%H%M%S)

pg_basebackup -h localhost -U postgres -D "$BACKUP_DIR/$DATE" -Ft -z -P

echo "✅ Incremental backup complete: $DATE"
```

**Automated Backup Schedule**:
```bash
# Add to crontab
# Full backup daily at 2 AM
0 2 * * * /usr/local/bin/backup_postgres_full.sh

# Incremental backup every hour
0 * * * * /usr/local/bin/backup_postgres_incremental.sh

# WAL archiving (continuous)
# Configured in postgresql.conf
```

### SQLite Backup

**Simple Backup**:
```bash
#!/bin/bash
# SQLite backup script

BACKUP_DIR="data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="database/G2C.db"

mkdir -p "$BACKUP_DIR"

# Copy database file
cp "$DB_FILE" "$BACKUP_DIR/G2C_$DATE.db"

# Compress
gzip "$BACKUP_DIR/G2C_$DATE.db"

echo "✅ SQLite backup complete: G2C_$DATE.db.gz"

# Clean up old backups
find "$BACKUP_DIR" -name "*.db.gz" -mtime +30 -delete
```

**Online Backup** (no downtime):
```bash
# Use SQLite backup API
sqlite3 database/G2C.db ".backup data/backups/G2C_backup.db"
```

## Source Data Backup

### Backup Raw Data

```bash
#!/bin/bash
# Backup raw data files

SOURCE_DIR="data/raw"
BACKUP_DIR="/backup/data/raw"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup with timestamp
rsync -av "$SOURCE_DIR/" "$BACKUP_DIR/$DATE/"

# Create latest symlink
ln -sfn "$BACKUP_DIR/$DATE" "$BACKUP_DIR/latest"

echo "✅ Raw data backed up: $DATE"
```

### Backup Transformed Data

```bash
#!/bin/bash
# Backup transformed data files

SOURCE_DIR="data/transformed"
BACKUP_DIR="/backup/data/transformed"
DATE=$(date +%Y%m%d_%H%M%S)

rsync -av "$SOURCE_DIR/" "$BACKUP_DIR/$DATE/"

ln -sfn "$BACKUP_DIR/$DATE" "$BACKUP_DIR/latest"

echo "✅ Transformed data backed up: $DATE"
```

## Configuration Backup

### Version Control (Git)

**Best Practice**: Use Git for all configuration and code:

```bash
# Initialize Git repository
git init

# Add .gitignore
cat > .gitignore << EOF
# Exclude data files
data/
logs/

# Exclude database files
database/*.db
database/*.db-journal

# Exclude secrets
.env
*.key
*.pem

# Exclude temporary files
__pycache__/
*.pyc
.DS_Store
EOF

# Commit configuration
git add config/ src/ docs/
git commit -m "Backup configuration"

# Push to remote (GitHub, GitLab, Bitbucket)
git remote add origin https://github.com/company/senzing-project.git
git push -u origin main
```

### Configuration Export

```python
#!/usr/bin/env python3
"""
Export Senzing configuration
"""

import json
from senzing import SzEngine

def backup_configuration(output_file='backup/config/senzing_config.json'):
    """Export current Senzing configuration"""
    
    engine = SzEngine()
    engine.initialize(instance_name='backup', settings=ENGINE_CONFIG)
    
    # Get active config ID
    config_id = engine.getActiveConfigID()
    
    # Export configuration
    config_json = engine.exportConfig(config_id)
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(config_json)
    
    engine.destroy()
    
    print(f"✅ Configuration backed up: {output_file}")

if __name__ == '__main__':
    backup_configuration()
```

## Restore Procedures

### Restore Database (PostgreSQL)

**Full Restore**:
```bash
#!/bin/bash
# Restore PostgreSQL database from backup

BACKUP_FILE="/backup/postgres/senzing_20260317_020000.dump.gz"
DB_NAME="senzing"

# Stop application
systemctl stop senzing-app

# Drop existing database (CAREFUL!)
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# Create new database
psql -h localhost -U postgres -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
gunzip -c "$BACKUP_FILE" | pg_restore -h localhost -U postgres -d "$DB_NAME"

# Verify restore
psql -h localhost -U postgres -d "$DB_NAME" -c "SELECT COUNT(*) FROM dsrc_record;"

# Start application
systemctl start senzing-app

echo "✅ Database restored from $BACKUP_FILE"
```

**Point-in-Time Recovery (PITR)**:
```bash
#!/bin/bash
# Restore to specific point in time

BACKUP_DIR="/backup/postgres"
WAL_DIR="/backup/wal"
TARGET_TIME="2026-03-17 14:30:00"

# Stop PostgreSQL
systemctl stop postgresql

# Restore base backup
rm -rf /var/lib/postgresql/data/*
tar -xzf "$BACKUP_DIR/base.tar.gz" -C /var/lib/postgresql/data/

# Create recovery.conf
cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'cp $WAL_DIR/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL (will replay WAL to target time)
systemctl start postgresql

echo "✅ Database restored to $TARGET_TIME"
```

### Restore Database (SQLite)

```bash
#!/bin/bash
# Restore SQLite database

BACKUP_FILE="data/backups/G2C_20260317_020000.db.gz"
DB_FILE="database/G2C.db"

# Stop application
systemctl stop senzing-app

# Backup current database (just in case)
mkdir -p database
cp "$DB_FILE" "$DB_FILE.before_restore"

# Restore from backup
gunzip -c "$BACKUP_FILE" > "$DB_FILE"

# Verify restore
sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM dsrc_record;"

# Start application
systemctl start senzing-app

echo "✅ Database restored from $BACKUP_FILE"
```

### Restore Source Data

```bash
#!/bin/bash
# Restore source data from backup

BACKUP_DATE="20260317_020000"
BACKUP_DIR="/backup/data/raw/$BACKUP_DATE"
TARGET_DIR="data/raw"

# Backup current data
mv "$TARGET_DIR" "${TARGET_DIR}.before_restore"

# Restore from backup
rsync -av "$BACKUP_DIR/" "$TARGET_DIR/"

echo "✅ Source data restored from $BACKUP_DATE"
```

### Restore Configuration

```bash
#!/bin/bash
# Restore configuration from Git

# Checkout specific version
git checkout v1.2.3

# Or restore from backup
cp backup/config/senzing_config.json config/

echo "✅ Configuration restored"
```

## Rollback Procedures

### Rollback Data Load

If a data load goes wrong, rollback to previous state:

```python
#!/usr/bin/env python3
"""
Rollback data load by deleting records from a data source
"""

import json
from senzing import SzEngine

def rollback_data_source(data_source):
    """Delete all records from a data source"""
    
    engine = SzEngine()
    engine.initialize(instance_name='rollback', settings=ENGINE_CONFIG)
    
    # Get all records for data source
    # Note: This is a simplified example
    # In production, you'd need to track loaded record IDs
    
    print(f"Rolling back data source: {data_source}")
    
    # Read record IDs from loading log
    with open(f'logs/loaded_records_{data_source}.txt') as f:
        for line in f:
            record_id = line.strip()
            try:
                engine.deleteRecord(data_source, record_id)
                print(f"  Deleted: {record_id}")
            except Exception as e:
                print(f"  Error deleting {record_id}: {e}")
    
    engine.destroy()
    
    print(f"✅ Rollback complete for {data_source}")

if __name__ == '__main__':
    rollback_data_source('CUSTOMERS_CRM')
```

**Better Approach**: Use database backup/restore instead of deleting records.

### Rollback Configuration Change

```python
#!/usr/bin/env python3
"""
Rollback to previous configuration
"""

import json
from senzing import SzConfig, SzEngine

def rollback_configuration(backup_file='backup/config/senzing_config_previous.json'):
    """Restore previous configuration"""
    
    # Load backup configuration
    with open(backup_file) as f:
        config_json = f.read()
    
    # Import configuration
    config = SzConfig()
    config.initialize(instance_name='rollback', settings=ENGINE_CONFIG)
    
    config_handle = config.importConfig(config_json)
    config_id = config.addConfig(config_handle, "Rollback to previous version")
    
    # Set as default
    engine = SzEngine()
    engine.initialize(instance_name='rollback', settings=ENGINE_CONFIG)
    engine.setDefaultConfigID(config_id)
    
    config.destroy()
    engine.destroy()
    
    print(f"✅ Configuration rolled back from {backup_file}")

if __name__ == '__main__':
    rollback_configuration()
```

## Disaster Recovery Scenarios

### Scenario 1: Database Corruption

**Symptoms**: Database errors, crashes, data inconsistencies

**Recovery Steps**:
1. Stop application
2. Assess damage (can database be opened?)
3. If repairable: Run database repair tools
4. If not repairable: Restore from latest backup
5. Replay WAL logs (PostgreSQL) to recover recent data
6. Verify data integrity
7. Restart application

**Time**: 1-4 hours (depending on database size)

### Scenario 2: Accidental Data Deletion

**Symptoms**: Records or entities missing

**Recovery Steps**:
1. Identify what was deleted and when
2. Stop further operations
3. Restore database to point before deletion (PITR)
4. Or reload deleted records from source data
5. Verify restoration
6. Resume operations

**Time**: 30 minutes - 2 hours

### Scenario 3: Bad Data Load

**Symptoms**: Incorrect matches, data quality issues

**Recovery Steps**:
1. Stop loading process
2. Identify problematic data source
3. Restore database to point before load
4. Fix transformation logic
5. Retest with sample data
6. Reload corrected data

**Time**: 2-8 hours (depending on data volume)

### Scenario 4: Server Failure

**Symptoms**: Server crash, hardware failure

**Recovery Steps**:
1. Provision new server
2. Install Senzing SDK
3. Restore database from backup
4. Restore application code from Git
5. Restore configuration
6. Verify functionality
7. Update DNS/load balancer

**Time**: 2-6 hours

### Scenario 5: Data Center Outage

**Symptoms**: Complete site unavailable

**Recovery Steps**:
1. Activate DR site
2. Restore database from offsite backup
3. Deploy application from Git
4. Update DNS to point to DR site
5. Verify functionality
6. Communicate with stakeholders

**Time**: 4-12 hours

## Disaster Recovery Testing

### Test Schedule

- **Monthly**: Restore from backup to test environment
- **Quarterly**: Full DR drill with failover
- **Annually**: Complete disaster simulation

### Test Checklist

- [ ] Backup files are accessible
- [ ] Backup files are not corrupted
- [ ] Restore procedure works
- [ ] Restored data is complete
- [ ] Application works with restored data
- [ ] Recovery time meets RTO
- [ ] Data loss meets RPO
- [ ] Documentation is up to date
- [ ] Team knows their roles

### Test Documentation

```markdown
# DR Test Report

**Date**: 2026-03-17
**Test Type**: Full Database Restore
**Tester**: John Smith

## Test Scenario
Simulate database corruption and restore from backup

## Steps Executed
1. Stopped application
2. Backed up current database
3. Deleted database
4. Restored from backup (dated 2026-03-16 02:00)
5. Verified data integrity
6. Restarted application

## Results
- ✅ Backup file accessible
- ✅ Restore completed successfully
- ✅ Data integrity verified
- ✅ Application functional
- ⚠️ Recovery time: 45 minutes (RTO: 2 hours) - PASS
- ⚠️ Data loss: 22 hours (RPO: 24 hours) - PASS

## Issues Found
- Restore script had incorrect path (fixed)
- Documentation was outdated (updated)

## Recommendations
- Increase backup frequency to hourly
- Automate restore testing
- Update runbook with new paths

**Status**: PASS
```

## Backup Storage

### Local Storage

**Pros**: Fast, simple
**Cons**: Not protected from site disasters

```bash
# Local backup directory
/backup/
├── postgres/
│   ├── full/
│   └── incremental/
├── sqlite/
├── data/
└── config/
```

### Network Storage (NAS/SAN)

**Pros**: Centralized, accessible
**Cons**: Single point of failure

```bash
# Mount network storage
mount -t nfs backup-server:/backups /backup
```

### Cloud Storage (S3, Azure Blob, GCS)

**Pros**: Offsite, durable, scalable
**Cons**: Cost, network dependency

```bash
#!/bin/bash
# Upload backup to S3

BACKUP_FILE="/backup/postgres/senzing_20260317.dump.gz"
S3_BUCKET="s3://company-backups/senzing/"

aws s3 cp "$BACKUP_FILE" "$S3_BUCKET"

echo "✅ Backup uploaded to S3"
```

### 3-2-1 Backup Rule

**3** copies of data
**2** different media types
**1** offsite copy

Example:
- Copy 1: Production database (local SSD)
- Copy 2: Local backup (local HDD)
- Copy 3: Cloud backup (S3)

## Monitoring and Alerts

### Backup Monitoring

```python
#!/usr/bin/env python3
"""
Monitor backup health
"""

import os
from datetime import datetime, timedelta

def check_backup_health():
    """Check if backups are current"""
    
    backup_dir = '/backup/postgres'
    max_age_hours = 24
    
    # Find latest backup
    backups = sorted(os.listdir(backup_dir))
    if not backups:
        print("❌ No backups found!")
        return False
    
    latest_backup = backups[-1]
    backup_path = os.path.join(backup_dir, latest_backup)
    backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
    age_hours = (datetime.now() - backup_time).total_seconds() / 3600
    
    if age_hours > max_age_hours:
        print(f"❌ Latest backup is {age_hours:.1f} hours old (max: {max_age_hours})")
        return False
    
    print(f"✅ Latest backup is {age_hours:.1f} hours old")
    return True

if __name__ == '__main__':
    check_backup_health()
```

### Alert on Backup Failure

```bash
#!/bin/bash
# Backup with alerting

BACKUP_SCRIPT="/usr/local/bin/backup_postgres.sh"
ALERT_EMAIL="ops@company.com"

if ! $BACKUP_SCRIPT; then
    echo "Backup failed at $(date)" | mail -s "ALERT: Senzing Backup Failed" $ALERT_EMAIL
    exit 1
fi
```

## Agent Behavior

When helping with disaster recovery in Module 12:

1. **Assess current backup status**: What backups exist?
2. **Define RTO/RPO**: What are recovery objectives?
3. **Create backup scripts**: Generate backup scripts for database and data
4. **Set up automation**: Configure cron jobs or schedulers
5. **Document procedures**: Create restore runbooks
6. **Test backups**: Help user test restore procedures
7. **Set up monitoring**: Create backup health checks
8. **Create DR plan**: Document disaster recovery procedures

## When to Load This Guide

Load this guide when:
- Starting Module 12 (deployment)
- User asks about backups or disaster recovery
- Planning production deployment
- After a data loss incident
- Setting up new environment

## Related Documentation

- `POWER.md` - Module 12 overview
- `steering/steering.md` - Module 12 workflow
- `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` - Deployment guide
- `steering/multi-environment-strategy.md` - Environment management

## Version History

- **v3.0.0** (2026-03-17): Disaster recovery guide created for Module 12 enhancement

