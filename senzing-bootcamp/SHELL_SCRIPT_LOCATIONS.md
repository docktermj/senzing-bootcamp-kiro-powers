# Shell Script Location Policy

## Policy

**All shell scripts (*.sh) must be stored in the `scripts/` directory.**

This policy ensures:
- Consistent project organization
- Easy discovery of automation scripts
- Clear separation between source code and scripts
- Standard deployment practices

## Directory Structure

```
project-root/
├── scripts/              # All shell scripts go here
│   ├── deploy.sh
│   ├── backup.sh
│   ├── migrate_db.sh
│   ├── run_pipeline.sh
│   ├── health_check.sh
│   └── ...
├── src/                  # Python/Java/C# source code
│   ├── transform/
│   ├── load/
│   ├── query/
│   └── utils/
├── config/               # Configuration files
├── docs/                 # Documentation
└── tests/                # Test files
```

## Examples from Workflows

### Module 7: Multi-Source Orchestration
- ❌ Wrong: `src/load/orchestrate_loading.sh`
- ✅ Correct: `scripts/orchestrate_loading.sh`

### Module 10: Security Hardening
- ❌ Wrong: `src/security/backup.sh`
- ✅ Correct: `scripts/backup.sh`

### Module 11: Monitoring and Observability
- ❌ Wrong: `monitoring/health_check.sh`
- ✅ Correct: `scripts/health_check.sh`

### Module 12: Package and Deploy
- ❌ Wrong: `deploy/deploy.sh`
- ✅ Correct: `scripts/deploy.sh`
- ❌ Wrong: `deploy/migrate_db.sh`
- ✅ Correct: `scripts/migrate_db.sh`

## Common Shell Scripts

### Deployment Scripts
- `scripts/deploy.sh` - Main deployment script
- `scripts/pre_deploy_check.sh` - Pre-deployment validation
- `scripts/post_deploy_check.sh` - Post-deployment validation
- `scripts/rollback.sh` - Rollback to previous version

### Database Scripts
- `scripts/migrate_db.sh` - Database migration
- `scripts/backup.sh` - Database backup
- `scripts/restore.sh` - Database restore
- `scripts/init_db.sh` - Database initialization

### Pipeline Scripts
- `scripts/run_pipeline.sh` - Run complete pipeline
- `scripts/run_transform.sh` - Run transformation only
- `scripts/run_load.sh` - Run loading only
- `scripts/run_query.sh` - Run queries

### Monitoring Scripts
- `scripts/health_check.sh` - Health check
- `scripts/check_metrics.sh` - Check metrics
- `scripts/alert_test.sh` - Test alerting

### Utility Scripts
- `scripts/setup_env.sh` - Environment setup
- `scripts/cleanup.sh` - Cleanup temporary files
- `scripts/generate_config.sh` - Generate configuration

## Python vs Shell Scripts

### Use Shell Scripts (*.sh) for:
- Deployment automation
- Environment setup
- System-level operations
- CI/CD pipelines
- Database operations
- Service management

**Location**: `scripts/`

### Use Python Scripts (*.py) for:
- Data transformation
- Data loading
- Query operations
- Business logic
- Data processing
- Application code

**Location**: `src/`

## Examples

### Shell Script (scripts/deploy.sh)
```bash
#!/bin/bash
# Deployment script
set -e

ENVIRONMENT=$1

echo "Deploying to $ENVIRONMENT..."

# Load configuration
source config/env.$ENVIRONMENT.sh

# Run pre-deployment checks
python src/utils/pre_deploy_check.py

# Deploy application
kubectl apply -f k8s/

echo "Deployment complete!"
```

### Python Script (src/load/loader.py)
```python
#!/usr/bin/env python3
"""
Data loading module
"""

from senzing import SzEngine

class Loader:
    def load_records(self, input_file):
        # Loading logic here
        pass
```

## Workflow Updates Needed

The following workflows in `NEW_WORKFLOWS_PHASE5.md` reference shell scripts and should follow this policy:

### Module 7: Multi-Source Orchestration
- Orchestration script should be Python: `src/load/orchestrate_loading.py` ✅
- No shell scripts needed

### Module 10: Security Hardening
- Backup script: `scripts/backup.sh` ✅

### Module 11: Monitoring and Observability
- Health check script: `scripts/health_check.sh` ✅

### Module 12: Package and Deploy
- Deployment script: `scripts/deploy.sh` ✅
- Database migration: `scripts/migrate_db.sh` ✅
- Pipeline runner: `scripts/run_pipeline.sh` ✅

## Agent Instructions

When generating code for users:

1. **Always place shell scripts in `scripts/`**
2. **Always place Python/Java/C# code in `src/`**
3. **Use descriptive names**: `deploy.sh`, not `d.sh`
4. **Include shebang**: `#!/bin/bash` at the top
5. **Set executable**: Mention `chmod +x scripts/deploy.sh`
6. **Add comments**: Explain what the script does

## Verification

To verify compliance:

```bash
# Find all shell scripts
find . -name "*.sh" -type f

# Expected output: All in scripts/
./scripts/deploy.sh
./scripts/backup.sh
./scripts/migrate_db.sh
...

# No shell scripts should be in src/
find src/ -name "*.sh" -type f
# Expected: (empty)
```

## Related Policies

- **Python Requirements Policy**: See `PYTHON_REQUIREMENTS_POLICY.md`
- **Code Organization**: See `NEW_MODULE_STRUCTURE.md`
- **Module 0 Code Location**: See `MODULE_0_CODE_LOCATION.md`

## Version History

- **v1.0.0** (2026-03-17): Initial policy document created

## References

- Module 7 workflow: Multi-Source Orchestration
- Module 10 workflow: Security Hardening
- Module 11 workflow: Monitoring and Observability
- Module 12 workflow: Package and Deploy
- `NEW_WORKFLOWS_PHASE5.md`: All workflow documentation
