---
inclusion: manual
---

# Multi-Environment Strategy

## Overview

This guide covers strategies for managing multiple environments (development, testing, staging, production) for Senzing deployments, including configuration management, promotion processes, and environment-specific settings.

## Why Multiple Environments?

Multiple environments provide:

- **Isolation**: Changes don't affect production
- **Testing**: Validate changes before production
- **Stability**: Production remains stable
- **Rollback**: Easy to revert changes
- **Compliance**: Meet audit requirements
- **Confidence**: Test thoroughly before deployment

## Standard Environments

### Development (Dev)

**Purpose**: Active development and experimentation

**Characteristics**:
- Frequent changes
- Sample data (small datasets)
- SQLite or small PostgreSQL
- Minimal monitoring
- No SLA requirements
- Single instance

**Data**:
- Sample data (1K-10K records)
- Synthetic or anonymized data
- Refreshed as needed

**Access**:
- Developers have full access
- No authentication required
- Local or shared dev server

### Testing (Test/QA)

**Purpose**: Automated and manual testing

**Characteristics**:
- Stable for testing cycles
- Representative data
- PostgreSQL database
- Basic monitoring
- Matches production configuration
- May have multiple instances

**Data**:
- Representative sample (10K-100K records)
- Anonymized production data
- Refreshed weekly/monthly

**Access**:
- Developers and QA have access
- Basic authentication
- Shared test environment

### Staging (Stage/Pre-Prod)

**Purpose**: Final validation before production

**Characteristics**:
- Production-like environment
- Full-scale data
- PostgreSQL (production-sized)
- Full monitoring
- Matches production exactly
- Load balanced

**Data**:
- Full production data copy
- Or large representative sample (100K-1M records)
- Refreshed regularly from production

**Access**:
- Limited access (ops, senior devs)
- Production-like authentication
- Requires approval for changes

### Production (Prod)

**Purpose**: Live system serving real users

**Characteristics**:
- Highly stable
- Full data
- PostgreSQL (optimized)
- Comprehensive monitoring
- High availability
- Load balanced
- Disaster recovery

**Data**:
- Real production data
- Backed up continuously
- Strict access controls

**Access**:
- Minimal access (ops only)
- Full authentication/authorization
- All changes require approval
- Audit logging enabled

## Environment Comparison

| Aspect | Dev | Test | Staging | Production |
|--------|-----|------|---------|------------|
| Data Size | 1K-10K | 10K-100K | 100K-1M | Full |
| Database | SQLite | PostgreSQL | PostgreSQL | PostgreSQL |
| Instances | 1 | 1-2 | 2-4 | 4+ |
| Monitoring | Minimal | Basic | Full | Comprehensive |
| Backups | None | Daily | Hourly | Continuous |
| SLA | None | None | 99% | 99.9% |
| Changes | Frequent | Weekly | Monthly | Controlled |
| Access | Open | Developers | Limited | Restricted |

## Configuration Management

### Environment-Specific Configuration

Use environment variables for configuration:

```bash
# .env.dev
ENVIRONMENT=development
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=senzing_dev
DATABASE_USER=dev_user
DATABASE_PASSWORD=dev_password
LOG_LEVEL=DEBUG
SENZING_DATA_DIR=/data/dev
BACKUP_ENABLED=false

# .env.test
ENVIRONMENT=test
DATABASE_HOST=test-db.company.com
DATABASE_PORT=5432
DATABASE_NAME=senzing_test
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
LOG_LEVEL=INFO
SENZING_DATA_DIR=/data/test
BACKUP_ENABLED=true

# .env.staging
ENVIRONMENT=staging
DATABASE_HOST=staging-db.company.com
DATABASE_PORT=5432
DATABASE_NAME=senzing_staging
DATABASE_USER=staging_user
DATABASE_PASSWORD=staging_password
LOG_LEVEL=INFO
SENZING_DATA_DIR=/data/staging
BACKUP_ENABLED=true

# .env.prod
ENVIRONMENT=production
DATABASE_HOST=prod-db.company.com
DATABASE_PORT=5432
DATABASE_NAME=senzing_prod
DATABASE_USER=prod_user
DATABASE_PASSWORD=prod_password
LOG_LEVEL=WARNING
SENZING_DATA_DIR=/data/prod
BACKUP_ENABLED=true
```

### Configuration Loading

```python
#!/usr/bin/env python3
"""
Environment-aware configuration
"""

import os
from dotenv import load_dotenv

class Config:
    """Base configuration"""
    
    def __init__(self):
        # Load environment-specific .env file
        env = os.getenv('ENVIRONMENT', 'development')
        load_dotenv(f'.env.{env}')
        
        self.environment = env
        self.database_host = os.getenv('DATABASE_HOST')
        self.database_port = int(os.getenv('DATABASE_PORT', 5432))
        self.database_name = os.getenv('DATABASE_NAME')
        self.database_user = os.getenv('DATABASE_USER')
        self.database_password = os.getenv('DATABASE_PASSWORD')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.senzing_data_dir = os.getenv('SENZING_DATA_DIR')
        self.backup_enabled = os.getenv('BACKUP_ENABLED', 'false').lower() == 'true'
    
    def get_database_url(self):
        """Get database connection URL"""
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
    
    def is_production(self):
        """Check if running in production"""
        return self.environment == 'production'
    
    def is_development(self):
        """Check if running in development"""
        return self.environment == 'development'

# Usage
config = Config()
print(f"Running in {config.environment} environment")
print(f"Database: {config.database_host}/{config.database_name}")
```

### Secrets Management

**Development**: Plain text in .env files (not committed to Git)

**Production**: Use secrets manager

```python
# AWS Secrets Manager
import boto3
import json

def get_secret(secret_name):
    """Get secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
if config.is_production():
    secrets = get_secret('senzing/prod/database')
    config.database_password = secrets['password']
```

```python
# Azure Key Vault
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret_azure(vault_url, secret_name):
    """Get secret from Azure Key Vault"""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# Usage
if config.is_production():
    vault_url = "https://company-keyvault.vault.azure.net/"
    config.database_password = get_secret_azure(vault_url, "database-password")
```

## Promotion Process

### Code Promotion

```
Dev → Test → Staging → Production
```

**Step 1: Development**
```bash
# Develop feature
git checkout -b feature/customer-search
# ... make changes ...
git commit -m "Add customer search feature"
git push origin feature/customer-search
```

**Step 2: Code Review**
```bash
# Create pull request
# Review by peers
# Automated tests run
# Merge to main branch
```

**Step 3: Deploy to Test**
```bash
# Automated deployment to test environment
git checkout main
git pull
./deploy.sh test
```

**Step 4: QA Testing**
```bash
# QA team tests in test environment
# Run automated test suite
# Manual testing
# Sign off
```

**Step 5: Deploy to Staging**
```bash
# Deploy to staging for final validation
./deploy.sh staging

# Run smoke tests
./run_smoke_tests.sh staging
```

**Step 6: Deploy to Production**
```bash
# Create release tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# Deploy to production (requires approval)
./deploy.sh production

# Monitor deployment
./monitor_deployment.sh production
```

### Configuration Promotion

**DO NOT** promote configuration files directly. Instead:

1. **Export configuration** from lower environment
2. **Review changes** carefully
3. **Test in staging** first
4. **Import to production** with approval

```python
#!/usr/bin/env python3
"""
Promote Senzing configuration between environments
"""

import json
from senzing import SzConfig, SzEngine

def export_config(env_name, output_file):
    """Export configuration from environment"""
    
    # Load environment config
    config = Config()
    os.environ['ENVIRONMENT'] = env_name
    
    engine = SzEngine()
    engine.initialize(instance_name='export', settings=ENGINE_CONFIG)
    
    # Get active config
    config_id = engine.getActiveConfigID()
    config_json = engine.exportConfig(config_id)
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(config_json)
    
    engine.destroy()
    
    print(f"✅ Configuration exported from {env_name} to {output_file}")

def import_config(env_name, input_file):
    """Import configuration to environment"""
    
    # Load environment config
    config = Config()
    os.environ['ENVIRONMENT'] = env_name
    
    # Read configuration
    with open(input_file) as f:
        config_json = f.read()
    
    # Import configuration
    sz_config = SzConfig()
    sz_config.initialize(instance_name='import', settings=ENGINE_CONFIG)
    
    config_handle = sz_config.importConfig(config_json)
    config_id = sz_config.addConfig(config_handle, f"Promoted from {input_file}")
    
    # Set as default
    engine = SzEngine()
    engine.initialize(instance_name='import', settings=ENGINE_CONFIG)
    engine.setDefaultConfigID(config_id)
    
    sz_config.destroy()
    engine.destroy()
    
    print(f"✅ Configuration imported to {env_name} from {input_file}")

# Usage
if __name__ == '__main__':
    # Export from staging
    export_config('staging', 'config_staging.json')
    
    # Review changes
    print("Review config_staging.json before importing to production")
    input("Press Enter to continue...")
    
    # Import to production
    import_config('production', 'config_staging.json')
```

### Data Promotion

**DO NOT** promote data from lower to higher environments.

**Instead**:
- **Test/Staging**: Copy data from production (anonymized)
- **Production**: Load from source systems only

```bash
#!/bin/bash
# Refresh test environment with production data (anonymized)

# Export from production
pg_dump -h prod-db -U postgres senzing_prod | \
    # Anonymize sensitive data
    sed 's/[0-9]\{3\}-[0-9]\{2\}-[0-9]\{4\}/XXX-XX-XXXX/g' | \
    # Import to test
    psql -h test-db -U postgres senzing_test

echo "✅ Test environment refreshed with anonymized production data"
```

## Deployment Strategies

### Blue-Green Deployment

Maintain two identical production environments:

```
Blue (Current Production) ← Users
Green (New Version) ← Testing

After validation:
Blue (Old Version) ← Standby
Green (New Production) ← Users
```

**Advantages**:
- Zero downtime
- Instant rollback
- Full testing in production-like environment

**Implementation**:
```bash
#!/bin/bash
# Blue-green deployment

CURRENT_ENV=$(cat /etc/senzing/current_env)
NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

echo "Current environment: $CURRENT_ENV"
echo "Deploying to: $NEW_ENV"

# Deploy to new environment
./deploy.sh $NEW_ENV

# Run smoke tests
if ./smoke_tests.sh $NEW_ENV; then
    echo "✅ Smoke tests passed"
    
    # Switch traffic to new environment
    ./switch_traffic.sh $NEW_ENV
    
    # Update current environment marker
    echo $NEW_ENV > /etc/senzing/current_env
    
    echo "✅ Deployment complete. Now serving from $NEW_ENV"
else
    echo "❌ Smoke tests failed. Keeping $CURRENT_ENV active"
    exit 1
fi
```

### Canary Deployment

Gradually roll out to subset of users:

```
Production (v1.0) ← 90% of users
Canary (v1.1) ← 10% of users

Monitor metrics, then:
Production (v1.1) ← 100% of users
```

**Advantages**:
- Reduced risk
- Real user feedback
- Gradual rollout

**Implementation** (Nginx):
```nginx
upstream senzing_stable {
    server senzing-v1:8080;
}

upstream senzing_canary {
    server senzing-v2:8080;
}

split_clients "${remote_addr}" $backend {
    10% "canary";  # 10% to canary
    *   "stable";  # 90% to stable
}

server {
    location /api/ {
        proxy_pass http://senzing_$backend;
    }
}
```

### Rolling Deployment

Update instances one at a time:

```
Instance 1 (v1.0) ← Update to v1.1
Instance 2 (v1.0) ← Wait
Instance 3 (v1.0) ← Wait

Then:
Instance 1 (v1.1) ← Running
Instance 2 (v1.0) ← Update to v1.1
Instance 3 (v1.0) ← Wait

Finally:
Instance 1 (v1.1) ← Running
Instance 2 (v1.1) ← Running
Instance 3 (v1.1) ← Running
```

**Advantages**:
- No additional infrastructure
- Gradual rollout
- Can pause/rollback

**Implementation**:
```bash
#!/bin/bash
# Rolling deployment

INSTANCES=("senzing-1" "senzing-2" "senzing-3")

for instance in "${INSTANCES[@]}"; do
    echo "Deploying to $instance..."
    
    # Remove from load balancer
    ./lb_remove.sh $instance
    
    # Deploy new version
    ssh $instance "./deploy_local.sh"
    
    # Health check
    if ./health_check.sh $instance; then
        echo "✅ $instance healthy"
        
        # Add back to load balancer
        ./lb_add.sh $instance
        
        # Wait before next instance
        sleep 60
    else
        echo "❌ $instance unhealthy. Rolling back."
        ssh $instance "./rollback.sh"
        ./lb_add.sh $instance
        exit 1
    fi
done

echo "✅ Rolling deployment complete"
```

## Environment Parity

### Keep Environments Similar

**Configuration Parity**:
- Same Senzing version
- Same database schema
- Same data sources defined
- Same feature configuration

**Infrastructure Parity**:
- Similar hardware specs (scaled down for lower envs)
- Same OS and dependencies
- Same network topology
- Same monitoring tools

**Code Parity**:
- Same codebase (different branches/tags)
- Same deployment process
- Same directory structure

### Differences to Maintain

**Data Volume**:
- Dev: 1K-10K records
- Test: 10K-100K records
- Staging: 100K-1M records
- Production: Full dataset

**Monitoring**:
- Dev: Minimal
- Test: Basic
- Staging: Full
- Production: Comprehensive + alerting

**Backups**:
- Dev: None
- Test: Daily
- Staging: Hourly
- Production: Continuous

## Environment Checklist

### Development Environment
- [ ] SQLite or small PostgreSQL database
- [ ] Sample data loaded (1K-10K records)
- [ ] Local or shared dev server
- [ ] No authentication required
- [ ] Minimal logging
- [ ] No backups needed

### Test Environment
- [ ] PostgreSQL database
- [ ] Representative data (10K-100K records)
- [ ] Matches production configuration
- [ ] Basic authentication
- [ ] Standard logging
- [ ] Daily backups
- [ ] Automated tests configured

### Staging Environment
- [ ] Production-sized PostgreSQL
- [ ] Large dataset (100K-1M records)
- [ ] Exact production configuration
- [ ] Production-like authentication
- [ ] Full logging and monitoring
- [ ] Hourly backups
- [ ] Load testing configured
- [ ] Smoke tests automated

### Production Environment
- [ ] Optimized PostgreSQL cluster
- [ ] Full production data
- [ ] High availability setup
- [ ] Full authentication/authorization
- [ ] Comprehensive monitoring
- [ ] Continuous backups
- [ ] Disaster recovery tested
- [ ] Alerting configured
- [ ] Runbooks documented
- [ ] Change control process

## Agent Behavior

When implementing multi-environment strategy in Module 12:

1. **Assess current state**: What environments exist?
2. **Define environments**: What environments are needed?
3. **Create configuration**: Generate .env files for each environment
4. **Set up secrets**: Configure secrets management for production
5. **Document promotion**: Create promotion process documentation
6. **Create deployment scripts**: Generate deployment scripts
7. **Set up monitoring**: Configure environment-specific monitoring
8. **Test promotion**: Walk through promotion process
9. **Document runbooks**: Create environment-specific runbooks

## When to Load This Guide

Load this guide when:
- Starting Module 12 (deployment)
- User asks about environments or deployment
- Planning production deployment
- Setting up CI/CD pipeline
- Need to manage multiple environments

## Related Documentation

- `POWER.md` - Module 12 overview
- `steering/steering.md` - Module 12 workflow
- `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` - Deployment guide
- `steering/disaster-recovery.md` - Backup and recovery
- `steering/api-gateway-patterns.md` - API integration

## Version History

- **v3.0.0** (2026-03-17): Multi-environment strategy guide created for Module 12 enhancement

