---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
description: "Guided discovery of Senzing entity resolution. Walk through data mapping, SDK setup, record loading, and result exploration using the Senzing MCP server."
keywords: ["Entity Resolution", "Senzing", "Data Mapping", "SDK", "Identity Resolution", "Data Matching", "ER"]
author: "Senzing"
---

# Power: Senzing Boot Camp

## Overview

This power provides a guided boot camp experience for learning Senzing entity resolution. It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

## Hooks

### Auto Architecture Diagram Generator

Please create a Kiro agent hook that will automatically generate and update architecture diagrams in the architecture/diagrams folder whenever I make changes to my chatbot application. The hook should:

1. Trigger when I save files in the src folder
2. Analyze the current application structure
3. Generate an updated architecture diagram using the AWS Diagram MCP server
4. Save the diagram in the architecture/diagrams folder
5. Update any related documentation

Make sure the hook is well-documented and easy to modify. Make sure the hook is enabled.

## Available MCP Servers

### senzing-mcp-server

- **URL**: `https://mcp.senzing.com/mcp`
- **Purpose**: AI-assisted entity resolution tools — data mapping, SDK code generation, documentation search, troubleshooting, and sample data access.
- **Key tools**:
  - `get_capabilities` — Discover all available tools and workflows (call this first)
  - `mapping_workflow` — 7-step interactive data mapping from source files to Senzing JSON format
  - `lint_record` / `analyze_record` — Validate and analyze mapped data quality
  - `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust) for common workflows
  - `sdk_guide` — Platform-specific SDK installation and pipeline setup
  - `get_sample_data` — Sample datasets (Las Vegas, London, Moscow) for testing
  - `find_examples` — Working code examples from 27 Senzing GitHub repositories
  - `search_docs` — Search indexed Senzing documentation
  - `explain_error_code` — Diagnose Senzing errors (456 error codes)
  - `get_sdk_reference` — SDK method signatures, flags, and V3-to-V4 migration

## Boot Camp Learning Path

The boot camp follows a progressive learning path. Each module builds on the previous one.

**Modules**:
- **Module 0**: Quick Demo (Optional) - Experience entity resolution with sample data
- **Module 1**: Understand Business Problem - Define your problem and identify data sources
- **Module 2**: Verify Data Sources - Evaluate if data needs mapping or is SGES-compliant
- **Module 3**: Map Your Data - Create transformation programs for non-compliant sources
- **Module 4**: Set Up SDK - Install and configure Senzing
- **Module 5**: Load Records - Create loading programs and observe entity resolution
- **Module 6**: Query Results - Create query programs that answer your business problem

**Note**: While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.

### Project Directory Structure

Before starting, set up a project directory to organize all your boot camp artifacts:

```
my-senzing-project/
├── .git/                          # Version control (initialize with git init)
├── .gitignore                     # Exclude sensitive data and large files
├── .env.example                   # Template for environment variables
├── .env                           # Actual environment variables (not in git)
├── data/                          # User's data files
│   ├── raw/                       # Original source data
│   │   ├── customer_crm.csv
│   │   └── vendor_api.json
│   ├── transformed/               # Senzing-formatted JSON output
│   │   ├── customer_crm_senzing.jsonl
## Boot Camp Learning Path

The boot camp follows a progressive learning path. Each module builds on the previous one.

**Modules**:

- **Module 0: Quick Demo (Optional)**
  - Experience entity resolution with sample data
  - See how Senzing resolves duplicate records automatically
  - 10-15 minutes

- **Module 1: Understand Business Problem**
  - Define your problem and identify data sources
  - View design pattern gallery (optional)
  - Create problem statement document
  - 15-30 minutes

- **Module 2: Verify Data Sources**
  - Evaluate if data needs mapping or is SGES-compliant
  - Create data source evaluation report
  - 10 minutes per data source

- **Module 3: Map Your Data**
  - Create transformation programs for non-compliant sources
  - Validate data quality
  - Generate test files
  - 1-2 hours per data source

- **Module 4: Set Up SDK**
  - Install and configure Senzing
  - Set up database (SQLite or PostgreSQL)
  - Verify installation
  - 30 minutes - 1 hour

- **Module 5: Load Records**
  - Create loading programs for each data source
  - Observe entity resolution in real time
  - Generate loading statistics dashboard
  - 30 minutes per data source

- **Module 6: Query Results**
  - Create query programs that answer your business problem
  - Validate results
  - Complete lessons learned
  - 1-2 hours

**Total Time**: 3-6 hours for a typical single data source project

**Note**: While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.
│   │   └── search_person.py
│   └── utils/                     # Shared utilities
│       ├── senzing_client.py
│       └── data_quality.py
├── tests/                         # Test files for the project
│   ├── test_transform_customer.py
│   ├── test_load_customer.py
│   ├── test_query_duplicates.py
│   └── test_data_quality.py
├── docs/                          # Design documents
│   ├── business_problem.md        # Module 1 output
│   ├── data_source_evaluation.md  # Module 2 output
│   ├── mapping_specifications.md  # Module 3 mappings
│   ├── query_specifications.md    # Module 6 queries
│   ├── lessons_learned.md         # Post-project retrospective
│   ├── security_compliance.md     # Privacy and security notes
│   └── performance_benchmarks.md  # Performance metrics
├── config/                        # Configuration files
│   ├── senzing_config.json
│   ├── data_sources.json
│   └── monitoring_config.yaml
├── logs/                          # Log files
│   ├── transform.log
│   ├── load.log
│   └── monitoring.log
├── monitoring/                    # Monitoring and dashboards
│   ├── dashboard.html
│   └── metrics.json
├── scripts/                       # Utility scripts
│   ├── setup_environment.sh
│   ├── backup_database.sh
│   └── rollback.sh
├── docker-compose.yml             # Docker environment (optional)
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies (if applicable)
└── README.md                      # Project description and instructions
```

**Agent behavior**: At the start of Module 1, help the user create this directory structure. As you generate programs throughout the boot camp, save them in the appropriate folders. Keep the project organized so users can easily find and maintain their artifacts.

### Progress Tracking

As you work through the boot camp, track your progress:
- ✅ Module 0: Quick Demo (Optional)
- ⬜ Module 1: Understand Business Problem
- ⬜ Module 2: Verify Data Sources
- ⬜ Module 3: Map Your Data
- ⬜ Module 4: Set Up SDK
- ⬜ Module 5: Load Records
- ⬜ Module 6: Query Results

**Agent behavior**: Maintain a mental model of which modules are complete and which are in progress. Remind users of their progress periodically.

### Estimated Time Commitment

- **Module 0**: 10-15 minutes (optional quick demo)
- **Module 1**: 15-30 minutes (problem discovery)
- **Module 2**: 10 minutes per data source (evaluation)
- **Module 3**: 1-2 hours per data source (mapping and transformation)
- **Module 4**: 30 minutes - 1 hour (SDK installation)
- **Module 5**: 30 minutes per data source (loading)
- **Module 6**: 1-2 hours (query development)

**Total**: 3-6 hours for a typical single data source project

### Skip Ahead Options

Experienced users can skip modules:
- **Have SGES-compliant data?** → Skip Module 3, go to Module 4
- **Senzing already installed?** → Skip Module 4, go to Module 5
- **Just want to explore?** → Start with Module 0 (Quick Demo)
- **Already loaded data?** → Jump to Module 6

### Environment Setup

Before starting the boot camp, set up your development environment:

**Version Control**:
```bash
cd my-senzing-project
git init
git add .
git commit -m "Initial project setup"
```

**Create .gitignore**:
```gitignore
# Sensitive data
.env
*.key
*.pem
config/*_credentials.json

# Data files (too large for git)
data/raw/*
data/transformed/*
!data/raw/.gitkeep
!data/transformed/.gitkeep

# Logs
logs/*.log
*.log

# Database files
*.db
*.sqlite
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/

# Node
node_modules/
npm-debug.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backups
data/backups/*.sql
```

**Python Environment** (if using Python):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install senzing
pip freeze > requirements.txt
```

**Environment Variables** (create .env.example):
```bash
# Senzing Configuration
SENZING_ENGINE_CONFIG_JSON={"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing"}}
SENZING_DATABASE_URL=sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db

# Data Source Credentials (examples - replace with actual)
CRM_API_KEY=your_api_key_here
DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost:5432/dbname

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
```

**Docker Environment** (optional, create docker-compose.yml):
```yaml
version: '3.8'
services:
  senzing:
    image: senzing/senzing-tools:latest
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - SENZING_ENGINE_CONFIGURATION_JSON=${SENZING_ENGINE_CONFIG_JSON}
  
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=senzing
      - POSTGRES_USER=senzing
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Agent behavior**: Help users set up their environment at the start of Module 1. Ensure version control is initialized and sensitive data is excluded from git.

### Data Privacy and Security

**CRITICAL**: Handle data responsibly throughout the boot camp.

**Data Privacy Considerations**:
- **PII Protection**: Customer data contains Personally Identifiable Information (names, addresses, SSNs, etc.)
- **Sample Data**: Use anonymized or synthetic data for testing when possible
- **Access Control**: Limit who can access raw data files
- **Compliance**: Consider GDPR, CCPA, HIPAA, or other regulations applicable to your data

**Security Best Practices**:
1. **Never commit sensitive data to git**:
   - Use .gitignore for data files
   - Store credentials in .env (not in git)
   - Use .env.example as a template

2. **Anonymize test data**:
   - Replace real names with fake names
   - Use fake addresses and phone numbers
   - Mask or remove SSNs and other identifiers
   - Keep data structure but change values

3. **Secure credentials**:
   - Use environment variables for API keys
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate credentials regularly
   - Never hardcode passwords in source code

4. **Database security**:
   - Use strong passwords
   - Enable encryption at rest
   - Use SSL/TLS for connections
   - Regular backups with encryption

5. **Access logging**:
   - Log who accesses data and when
   - Monitor for unusual access patterns
   - Audit trail for compliance

**Create docs/security_compliance.md**:
```markdown
# Security and Compliance Notes

## Data Classification
- **Data Source 1**: Contains PII (names, addresses, SSNs)
- **Data Source 2**: Contains business data (no PII)

## Compliance Requirements
- GDPR: Right to be forgotten, data portability
- CCPA: Consumer privacy rights
- [Add your specific requirements]

## Data Handling Procedures
1. All PII must be encrypted at rest
2. Access requires authentication
3. Audit logs retained for 90 days
4. Data retention: [specify period]

## Anonymization Strategy
- Test data: Use faker library to generate synthetic data
- Sample data: Mask last 4 digits of SSN, use fake addresses

## Incident Response
- Contact: [security team email]
- Procedure: [link to incident response plan]
```

**Agent behavior**: Remind users about data privacy at the start of Module 2 when requesting sample data. Suggest anonymization techniques for sensitive data.

### Testing Strategy

Implement testing at each module to ensure quality and reliability.

**Test Types**:

1. **Unit Tests** (Module 3 - Transformation):
```python
# tests/test_transform_customer.py
import unittest
from src.transform.transform_customer_crm import transform_record

class TestCustomerTransform(unittest.TestCase):
    def test_name_mapping(self):
        source_record = {"customer_name": "John Doe"}
        result = transform_record(source_record)
        self.assertEqual(result["NAME_FULL"], "John Doe")
    
    def test_missing_fields(self):
        source_record = {"customer_id": "123"}
        result = transform_record(source_record)
        self.assertIn("RECORD_ID", result)
        self.assertEqual(result["RECORD_ID"], "123")
    
    def test_data_cleansing(self):
        source_record = {"phone": "  (555) 123-4567  "}
        result = transform_record(source_record)
        self.assertEqual(result["PHONE_NUMBER"], "555-123-4567")
```

2. **Integration Tests** (Module 5 - Loading):
```python
# tests/test_load_customer.py
import unittest
from src.load.load_customer_crm import load_records
from senzing import G2Engine

class TestCustomerLoad(unittest.TestCase):
    def setUp(self):
        self.engine = G2Engine()
        # Initialize with test database
    
    def test_load_sample_records(self):
        result = load_records("data/samples/customer_sample.jsonl", "TEST_CRM")
        self.assertEqual(result["success_count"], 10)
        self.assertEqual(result["error_count"], 0)
    
    def test_duplicate_record_handling(self):
        # Load same record twice
        load_records("data/samples/duplicate_test.jsonl", "TEST_CRM")
        # Verify only one entity created
```

3. **Data Quality Tests** (Module 3):
```python
# tests/test_data_quality.py
import unittest
from src.utils.data_quality import analyze_quality

class TestDataQuality(unittest.TestCase):
    def test_attribute_coverage(self):
        records = load_transformed_records("data/transformed/customer_crm_senzing.jsonl")
        quality = analyze_quality(records)
        self.assertGreater(quality["name_coverage"], 0.95)
        self.assertGreater(quality["address_coverage"], 0.80)
    
    def test_data_completeness(self):
        records = load_transformed_records("data/transformed/customer_crm_senzing.jsonl")
        quality = analyze_quality(records)
        self.assertGreater(quality["overall_score"], 70)
```

4. **Query Validation Tests** (Module 6):
```python
# tests/test_query_duplicates.py
import unittest
from src.query.find_duplicates import find_duplicates_for_datasource

class TestDuplicateQuery(unittest.TestCase):
    def test_finds_known_duplicates(self):
        # Load test data with known duplicates
        duplicates = find_duplicates_for_datasource("TEST_CRM")
        self.assertGreater(len(duplicates), 0)
    
    def test_no_false_positives(self):
        # Load test data with no duplicates
        duplicates = find_duplicates_for_datasource("TEST_UNIQUE")
        self.assertEqual(len(duplicates), 0)
```

**Running Tests**:
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_transform_customer.py

# Run with coverage
python -m pytest --cov=src tests/
```

**Agent behavior**: Generate test files alongside transformation, loading, and query programs. Encourage users to run tests before proceeding to the next module.

### Performance Benchmarking

Track performance metrics to optimize and scale your entity resolution system.

**Key Metrics to Track**:

1. **Transformation Performance**:
   - Records processed per second
   - Memory usage
   - Error rate
   - Data quality score

2. **Loading Performance**:
   - Records loaded per second
   - Entity resolution time
   - Database write throughput
   - Match rate (entities created vs records loaded)

3. **Query Performance**:
   - Query response time
   - Result accuracy
   - Cache hit rate

**Create docs/performance_benchmarks.md**:
```markdown
# Performance Benchmarks

## Baseline Metrics (Date: YYYY-MM-DD)

### Transformation Performance
- **Data Source**: Customer CRM
- **Record Count**: 50,000
- **Processing Time**: 5 minutes
- **Throughput**: 166 records/second
- **Memory Usage**: 512 MB
- **Error Rate**: 0.1%
- **Quality Score**: 85%

### Loading Performance
- **Data Source**: Customer CRM
- **Record Count**: 50,000
- **Loading Time**: 15 minutes
- **Throughput**: 55 records/second
- **Entities Created**: 42,000
- **Match Rate**: 16% (8,000 duplicates found)
- **Database Size**: 2.5 GB

### Query Performance
- **Query Type**: Find duplicates
- **Response Time**: 2.3 seconds
- **Results**: 4,200 duplicate entities
- **Accuracy**: 98% (manual validation of sample)

## Optimization Notes
- Batch size of 1000 records optimal for loading
- Index on DATA_SOURCE improves query performance by 40%
- PostgreSQL performs 3x faster than SQLite for >100K records

## Scaling Projections
- 1M records: ~2 hours transformation, ~6 hours loading
- 10M records: ~20 hours transformation, ~60 hours loading
- Recommend: Parallel processing for >1M records
```

**Monitoring Script** (create src/utils/performance_monitor.py):
```python
import time
import psutil
import json

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self, operation_name):
        self.start_time = time.time()
        self.metrics[operation_name] = {
            "start_time": self.start_time,
            "start_memory": psutil.Process().memory_info().rss / 1024 / 1024  # MB
        }
    
    def end(self, operation_name, record_count=0):
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        duration = end_time - self.metrics[operation_name]["start_time"]
        throughput = record_count / duration if duration > 0 else 0
        
        self.metrics[operation_name].update({
            "end_time": end_time,
            "duration_seconds": duration,
            "record_count": record_count,
            "throughput_per_second": throughput,
            "memory_used_mb": end_memory - self.metrics[operation_name]["start_memory"]
        })
        
        return self.metrics[operation_name]
    
    def save_metrics(self, filepath="monitoring/metrics.json"):
        with open(filepath, "w") as f:
            json.dump(self.metrics, f, indent=2)
```

**Agent behavior**: Add performance monitoring to generated programs. Track metrics and save to monitoring/metrics.json. Compare against baselines to identify performance issues.

### Rollback and Recovery Procedures

Prepare for failures and enable quick recovery.

**Database Backup Strategy**:

1. **Before major operations**:
```bash
# scripts/backup_database.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="data/backups"
mkdir -p $BACKUP_DIR

# SQLite backup
if [ -f "/var/opt/senzing/sqlite/G2C.db" ]; then
    cp /var/opt/senzing/sqlite/G2C.db "$BACKUP_DIR/G2C_$DATE.db"
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

2. **Rollback procedure** (create scripts/rollback.sh):
```bash
#!/bin/bash
# scripts/rollback.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./rollback.sh <backup_file>"
    echo "Available backups:"
    ls -lh data/backups/
    exit 1
fi

echo "WARNING: This will restore database to $BACKUP_FILE"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    if [[ $BACKUP_FILE == *.db ]]; then
        # SQLite restore
        cp "$BACKUP_FILE" /var/opt/senzing/sqlite/G2C.db
        echo "SQLite database restored"
    elif [[ $BACKUP_FILE == *.sql ]]; then
        # PostgreSQL restore
        psql -h localhost -U senzing -d senzing < "$BACKUP_FILE"
        echo "PostgreSQL database restored"
    fi
fi
```

**Recovery Procedures**:

Create docs/recovery_procedures.md:
```markdown
# Recovery Procedures

## Failed Transformation
**Symptom**: Transformation program crashes or produces invalid output

**Recovery**:
1. Check logs/transform.log for errors
2. Fix transformation logic in src/transform/
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
   ./scripts/rollback.sh data/backups/G2C_YYYYMMDD_HHMMSS.db
   ```
4. Fix data quality issues
5. Resume loading from last successful record

## Data Quality Issues
**Symptom**: Poor match rates or unexpected results

**Recovery**:
1. Don't load more data - stop and analyze
2. Review data quality reports from Module 3
3. Check mapping specifications
4. Test with small sample (100 records)
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
# Restore specific file
git checkout HEAD -- src/transform/transform_customer.py

# Restore to previous commit
git log  # Find commit hash
git checkout <commit-hash> -- src/

# Undo last commit (keep changes)
git reset --soft HEAD~1
```
```

**Agent behavior**: Create backup before Module 5 (loading). Remind users to backup before major operations. Provide rollback instructions if errors occur.

### Collaboration Features

For team projects, establish collaboration workflows:

**Multi-User Workflow**:

1. **Code Review Checkpoints**:
   - Module 3: Review transformation logic before committing
   - Module 5: Review loading programs before production
   - Module 6: Review query logic and results

2. **Git Branching Strategy**:
```bash
# Feature branches for each data source
git checkout -b feature/customer-crm-mapping
# Work on transformation
git add src/transform/transform_customer_crm.py
git commit -m "Add customer CRM transformation"
git push origin feature/customer-crm-mapping
# Create pull request for review
```

3. **Documentation Standards**:
   - All programs must have docstrings
   - README updated with setup instructions
   - Mapping decisions documented in docs/
   - Code comments for complex logic

4. **Handoff Procedures** (create docs/handoff_checklist.md):
```markdown
# Project Handoff Checklist

## Knowledge Transfer
- [ ] Business problem explained
- [ ] Data sources documented
- [ ] Transformation logic reviewed
- [ ] Loading procedures demonstrated
- [ ] Query programs explained

## Access and Credentials
- [ ] Repository access granted
- [ ] Database credentials shared (securely)
- [ ] API keys transferred
- [ ] Environment setup documented

## Documentation Review
- [ ] README.md complete
- [ ] All docs/ files up to date
- [ ] Code comments adequate
- [ ] Known issues documented

## Testing and Validation
- [ ] All tests passing
- [ ] Sample queries demonstrated
- [ ] Performance benchmarks shared
- [ ] Data quality validated

## Ongoing Support
- [ ] Contact information provided
- [ ] Support schedule defined
- [ ] Escalation procedures documented
```

**Agent behavior**: For team projects, remind about code review checkpoints. Generate documentation that facilitates handoffs.

### Cost Estimation

Understand the costs involved in your entity resolution project.

**Infrastructure Costs**:

Create docs/cost_estimation.md:
```markdown
# Cost Estimation

## Development Phase (Modules 1-6)
- **Time**: 3-6 hours for single data source
- **Personnel**: 1 developer
- **Infrastructure**: Minimal (local development)
  - SQLite: Free
  - Docker: Free
  - Development tools: Free

## Production Deployment

### Option 1: On-Premise
**One-time costs**:
- Senzing license: [Contact Senzing for pricing]
- Server hardware: $5,000 - $20,000
- Setup and configuration: 40-80 hours

**Ongoing costs**:
- Maintenance: 10-20 hours/month
- Hardware refresh: $2,000/year
- Power and cooling: $500/month

### Option 2: Cloud (AWS example)
**Monthly costs** (estimated for 1M records):
- EC2 instance (m5.2xlarge): $280/month
- RDS PostgreSQL (db.m5.large): $200/month
- EBS storage (500 GB): $50/month
- Data transfer: $50/month
- **Total**: ~$580/month

**Scaling costs** (10M records):
- EC2 instance (m5.4xlarge): $560/month
- RDS PostgreSQL (db.m5.2xlarge): $400/month
- EBS storage (2 TB): $200/month
- Data transfer: $100/month
- **Total**: ~$1,260/month

### Senzing Licensing
- Contact Senzing for pricing based on:
  - Number of records
  - Number of data sources
  - Deployment type (on-premise vs cloud)
  - Support level

## Cost Optimization Tips
1. Start with SQLite for evaluation (free)
2. Use spot instances for batch processing (70% savings)
3. Implement data retention policies (reduce storage)
4. Optimize queries to reduce compute time
5. Use reserved instances for production (40% savings)

## ROI Considerations
**Benefits**:
- Reduced duplicate records → Cost savings
- Improved data quality → Better decisions
- Faster customer lookup → Improved service
- Fraud detection → Loss prevention

**Example ROI**:
- Duplicate mailings eliminated: $50,000/year saved
- Fraud prevented: $200,000/year saved
- Customer service efficiency: 20% improvement
- **Total benefit**: $250,000+/year
- **Cost**: $20,000/year
- **ROI**: 1,150%
```

**Agent behavior**: Discuss costs during Module 1 (problem definition) and Module 4 (SDK setup). Help users choose appropriate deployment options based on scale and budget.

### Monitoring and Alerting

Set up monitoring to ensure ongoing system health.

**Monitoring Dashboard** (create monitoring/dashboard.html):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Senzing Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Entity Resolution Monitoring</h1>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Records Loaded</h3>
            <p id="total-records">Loading...</p>
        </div>
        <div class="metric-card">
            <h3>Entities Created</h3>
            <p id="total-entities">Loading...</p>
        </div>
        <div class="metric-card">
            <h3>Match Rate</h3>
            <p id="match-rate">Loading...</p>
        </div>
        <div class="metric-card">
            <h3>Error Rate</h3>
            <p id="error-rate">Loading...</p>
        </div>
    </div>
    
    <canvas id="loadingChart"></canvas>
    <canvas id="qualityChart"></canvas>
    
    <script src="dashboard.js"></script>
</body>
</html>
```

**Monitoring Configuration** (create config/monitoring_config.yaml):
```yaml
monitoring:
  enabled: true
  interval_seconds: 300  # Check every 5 minutes
  
  metrics:
    - name: records_loaded
      query: "SELECT COUNT(*) FROM records"
      threshold: 1000000
      alert_on: exceeds
      
    - name: error_rate
      query: "SELECT COUNT(*) FROM errors / COUNT(*) FROM records"
      threshold: 0.05  # 5%
      alert_on: exceeds
      
    - name: loading_throughput
      query: "SELECT COUNT(*) FROM records WHERE loaded_at > NOW() - INTERVAL '1 hour'"
      threshold: 1000
      alert_on: below
      
    - name: data_quality_score
      query: "SELECT AVG(quality_score) FROM data_quality_metrics"
      threshold: 70
      alert_on: below

  alerts:
    email:
      enabled: true
      recipients:
        - admin@example.com
      smtp_server: smtp.example.com
      
    slack:
      enabled: false
      webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      
    log:
      enabled: true
      log_file: logs/monitoring.log

  health_checks:
    - name: database_connection
      type: database
      connection_string: ${DATABASE_URL}
      
    - name: senzing_engine
      type: senzing
      config: ${SENZING_CONFIG}
      
    - name: disk_space
      type: system
      path: /var/opt/senzing
      threshold_gb: 10
```

**Automated Health Checks** (create src/utils/health_check.py):
```python
import psutil
import json
from datetime import datetime

def check_system_health():
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # Disk space
    disk = psutil.disk_usage('/')
    health["checks"]["disk_space"] = {
        "free_gb": disk.free / (1024**3),
        "percent_used": disk.percent,
        "status": "ok" if disk.percent < 90 else "warning"
    }
    
    # Memory
    memory = psutil.virtual_memory()
    health["checks"]["memory"] = {
        "available_gb": memory.available / (1024**3),
        "percent_used": memory.percent,
        "status": "ok" if memory.percent < 90 else "warning"
    }
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    health["checks"]["cpu"] = {
        "percent_used": cpu_percent,
        "status": "ok" if cpu_percent < 80 else "warning"
    }
    
    # Overall status
    if any(check["status"] == "warning" for check in health["checks"].values()):
        health["status"] = "warning"
    
    return health

if __name__ == "__main__":
    health = check_system_health()
    print(json.dumps(health, indent=2))
    
    # Save to monitoring directory
    with open("monitoring/health_status.json", "w") as f:
        json.dump(health, f, indent=2)
```

**Agent behavior**: Set up monitoring during Module 5 (loading). Create dashboard showing loading progress, entity counts, match rates, and error rates. Alert on anomalies.

### Lessons Learned Template

Document insights for future projects and continuous improvement.

**Create docs/lessons_learned.md** (to be filled out after Module 6):
```markdown
# Lessons Learned

**Project**: [Project Name]
**Date Completed**: [Date]
**Team Members**: [Names]

## Executive Summary
[2-3 sentence summary of the project and outcomes]

## What Worked Well

### Data Mapping (Module 3)
- **Success**: [What went smoothly]
- **Why**: [Reasons for success]
- **Recommendation**: [How to replicate]

### Loading Performance (Module 5)
- **Success**: [What worked]
- **Metrics**: [Performance numbers]
- **Recommendation**: [Best practices identified]

### Query Results (Module 6)
- **Success**: [Accurate results, good performance, etc.]
- **Impact**: [Business value delivered]

## Challenges Encountered

### Challenge 1: [Description]
- **Impact**: [How it affected the project]
- **Root Cause**: [Why it happened]
- **Resolution**: [How we solved it]
- **Prevention**: [How to avoid in future]
- **Time Lost**: [Estimate]

### Challenge 2: [Description]
[Same structure]

## Key Decisions

### Decision 1: [e.g., "Used PostgreSQL instead of SQLite"]
- **Context**: [Why this decision was needed]
- **Options Considered**: [Alternatives]
- **Decision**: [What we chose]
- **Rationale**: [Why we chose it]
- **Outcome**: [How it worked out]

### Decision 2: [e.g., "Prioritized name matching over address matching"]
[Same structure]

## Metrics and Outcomes

### Data Quality
- **Before**: [Baseline metrics]
- **After**: [Final metrics]
- **Improvement**: [Percentage or absolute]

### Performance
- **Transformation**: [Records/second]
- **Loading**: [Records/second]
- **Query**: [Response time]

### Business Impact
- **Duplicates Found**: [Number]
- **Data Quality Improvement**: [Percentage]
- **Time Saved**: [Hours/week]
- **Cost Savings**: [Dollar amount]
- **ROI**: [Percentage]

## Technical Insights

### Data Quality Patterns
- [Pattern 1]: [Description and frequency]
- [Pattern 2]: [Description and frequency]

### Matching Behavior
- [Observation 1]: [What we learned about how Senzing matches]
- [Observation 2]: [Unexpected matching behavior]

### Performance Optimization
- [Optimization 1]: [What we did and impact]
- [Optimization 2]: [What we did and impact]

## Recommendations for Future Projects

### Do More Of
1. [Practice or approach that worked well]
2. [Another successful practice]

### Do Less Of
1. [Practice or approach that didn't work]
2. [Another unsuccessful practice]

### Start Doing
1. [New practice to adopt]
2. [Another new practice]

### Stop Doing
1. [Practice to eliminate]
2. [Another practice to eliminate]

## Knowledge Gaps Identified
- [Gap 1]: [What we didn't know that we needed]
- [Gap 2]: [Another knowledge gap]

## Training Needs
- [Skill 1]: [Who needs training and why]
- [Skill 2]: [Another training need]

## Tools and Resources
- **Helpful**: [Tools that worked well]
- **Missing**: [Tools we wish we had]
- **Recommended**: [Tools to use in future]

## Timeline Retrospective
- **Estimated**: [Original estimate]
- **Actual**: [Actual time taken]
- **Variance**: [Difference and reasons]

## Team Feedback
- [Team member 1]: [Their perspective]
- [Team member 2]: [Their perspective]

## Action Items for Next Project
1. [ ] [Specific action based on lessons learned]
2. [ ] [Another action item]
3. [ ] [Another action item]

## Conclusion
[Final thoughts and overall assessment]
```

**Agent behavior**: Remind users to fill out lessons learned template after Module 6. Use insights to improve future boot camp experiences.

### Module 0: Quick Demo (Optional)

**Purpose**: Experience entity resolution in action before working with your own data.

**Time**: 10-15 minutes

**What you'll do**:
1. Load sample CORD data (Las Vegas, London, or Moscow datasets)
2. See how Senzing resolves duplicate records automatically
3. Query the results to see matched entities
4. Understand what entity resolution can do

**Success criteria**: ✅ You've seen entity resolution work and understand the basic concept

**Agent behavior**: Use `get_sample_data` to retrieve CORD datasets. Use `generate_scaffold` with `full_pipeline` to create a quick demo script. Show how duplicate records become resolved entities.

**Next**: Module 1 will help you define your specific business problem.

### Module 1: Understand the User's Business Problem

**Prerequisites**: None (or completed Module 0 if you did the quick demo)

**Time**: 15-30 minutes

**Purpose**: Clearly define the business problem that entity resolution will solve.

**Start here**: Ask the user to describe their business problem in their own words. Let them know they can use diagrams, flowcharts, or images to help explain their data sources, workflows, or the challenges they're facing.

**Guided discovery questions**:
1. **What problem are you trying to solve?**
   - Finding duplicate records?
   - Matching data across systems?
   - Identity verification?
   - Fraud detection?
   - Relationship discovery?
   - Master data management?

2. **What data sources are involved?**
   - List all systems, databases, files, or APIs
   - How many records in each source?
   - How often does the data change?

3. **What types of entities?**
   - People (customers, employees, patients)?
   - Organizations (companies, vendors, partners)?
   - Both?
   - Other (products, locations)?

4. **What matching criteria matter most?**
### Module 1: Understand the User's Business Problem

**Prerequisites**: None (or completed Module 0 if you did the quick demo)

**Time**: 15-30 minutes

**Purpose**: Clearly define the business problem that entity resolution will solve.

**Start here**: Ask the user to describe their business problem in their own words. Let them know they can use diagrams, flowcharts, or images to help explain their data sources, workflows, or the challenges they're facing.

**First, offer design pattern gallery**: Before diving into their specific problem, ask:

"Would you like to see examples of common business problems that entity resolution can solve? I can show you a gallery of entity resolution design patterns with real-world use cases."

**If user says yes**:
- Present the Entity Resolution Design Pattern Gallery (see below)
- Let them browse patterns and identify which ones match their situation
- Use the selected pattern as a starting point for their problem definition

**If user says no or after viewing patterns**:
- Proceed with guided discovery questions

**Entity Resolution Design Pattern Gallery**:

*Note: Full gallery implementation coming soon. For now, present these common patterns:*

1. **Customer 360 / Single Customer View**
   - **Problem**: Customer data scattered across CRM, billing, support, marketing systems
   - **Goal**: Unified view of each customer across all touchpoints
   - **Key Matching**: Names, emails, phone numbers, addresses, customer IDs
   - **Typical Data Sources**: CRM, billing system, support tickets, marketing database
   - **Business Value**: Better customer service, targeted marketing, reduced duplicate contacts

2. **Fraud Detection & Prevention**
   - **Problem**: Need to identify networks of related accounts indicating fraud
   - **Goal**: Detect fraud rings, synthetic identities, account takeovers
   - **Key Matching**: Names, addresses, phone numbers, device IDs, IP addresses
   - **Typical Data Sources**: Transaction logs, account data, device fingerprints, watchlists
   - **Business Value**: Reduced fraud losses, faster detection, compliance

3. **Data Migration & Consolidation**
   - **Problem**: Merging multiple legacy systems with duplicate records
   - **Goal**: Clean, deduplicated master dataset
   - **Key Matching**: All available identifiers and attributes
   - **Typical Data Sources**: Legacy databases, spreadsheets, archived systems
   - **Business Value**: Reduced storage costs, improved data quality, simplified operations

4. **Compliance & Watchlist Screening**
   - **Problem**: Must screen customers/transactions against sanctions lists
   - **Goal**: Identify matches to watchlists, PEPs, sanctioned entities
   - **Key Matching**: Names, dates of birth, nationalities, passport numbers
   - **Typical Data Sources**: Customer database, OFAC lists, PEP lists, sanctions databases
   - **Business Value**: Regulatory compliance, risk mitigation, audit trail

5. **Marketing Database Deduplication**
   - **Problem**: Sending multiple emails/mailings to same person
   - **Goal**: Deduplicated contact list, household grouping
   - **Key Matching**: Names, addresses, emails, phone numbers
   - **Typical Data Sources**: Email lists, purchased lists, event registrations, web forms
   - **Business Value**: Reduced mailing costs, better customer experience, improved metrics

6. **Healthcare Patient Matching**
   - **Problem**: Same patient has multiple medical records across facilities
   - **Goal**: Unified patient record, accurate medical history
   - **Key Matching**: Names, DOB, SSN, medical record numbers, addresses
   - **Typical Data Sources**: EHR systems, lab systems, billing systems, insurance records
   - **Business Value**: Patient safety, care coordination, reduced duplicate tests

7. **Vendor/Supplier Master Data Management**
   - **Problem**: Same vendor registered multiple times with variations
   - **Goal**: Clean vendor master, consolidated spend analysis
   - **Key Matching**: Company names, tax IDs, addresses, DUNS numbers
   - **Typical Data Sources**: AP systems, procurement systems, contract databases
   - **Business Value**: Better pricing, consolidated spend, compliance

8. **Insurance Claims Fraud Detection**
   - **Problem**: Detecting staged accidents, provider fraud, claimant fraud
   - **Goal**: Identify suspicious patterns and relationships
   - **Key Matching**: Names, addresses, vehicles, providers, claim details
   - **Typical Data Sources**: Claims data, policy data, provider networks, DMV records
   - **Business Value**: Reduced fraudulent payouts, faster investigation

9. **Know Your Customer (KYC) / Customer Onboarding**
   - **Problem**: Verify customer identity, check for existing accounts
   - **Goal**: Prevent duplicate accounts, verify identity, assess risk
   - **Key Matching**: Names, DOB, SSN, addresses, government IDs
   - **Typical Data Sources**: Application data, credit bureaus, government databases, existing customers
   - **Business Value**: Reduced fraud, regulatory compliance, better customer experience

10. **Supply Chain Entity Resolution**
    - **Problem**: Same supplier/manufacturer appears with different names
    - **Goal**: Unified view of supply chain entities
    - **Key Matching**: Company names, addresses, DUNS, GLNs, tax IDs
    - **Typical Data Sources**: ERP systems, supplier portals, logistics systems
    - **Business Value**: Supply chain visibility, risk management, optimization

**Agent behavior**: Present this gallery when user requests it. Help them identify which pattern(s) match their situation. Use the selected pattern to guide the problem definition. If the pattern gallery is enhanced in the future with more details, diagrams, or interactive elements, present those as well.

**Guided discovery questions**:m systems?

**Common scenarios** (examples to help users identify their use case):
- **Customer 360**: "I have customer data in CRM, billing, and support systems. I need a single view of each customer."
- **Fraud Detection**: "I need to find networks of related accounts that might indicate fraud rings."
- **Data Migration**: "I'm consolidating multiple legacy systems and need to deduplicate records."
- **Compliance**: "I need to match customer records against watchlists and sanctions lists."
- **Marketing**: "I want to deduplicate my marketing database to avoid sending multiple emails to the same person."

**Visual aids**: Encourage the use of diagrams to illustrate:
- Data flows between systems
- System architecture
- Business processes
- Example records or data structures
- Desired outcomes or workflows

**If an image is submitted**: Ask user to clarify any [variables] or unclear elements in the diagram.

**Deliverable**: Create a clear problem statement document that includes:
- Business problem description
- List of data sources
- Entity types
- Matching criteria
- Success metrics
- Desired outcomes

**Present proposal**: Based on the user's description, present a proposal for solving their business problem using Senzing entity resolution. Explain which modules will be most relevant to their use case.

**Success criteria**: ✅ Clear problem statement + identified data sources + defined success metrics

**Common issues**:
- Problem too vague → Ask more specific questions
- Too many data sources → Prioritize 1-2 sources to start
- Unclear success criteria → Help define measurable outcomes

**Next**: Module 2 will evaluate each data source to see if it needs mapping.

### Module 2: Verify Data Sources Against the Senzing Generic Entity Specification

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified)

**Time**: 10 minutes per data source

**Purpose**: Evaluate each data source to determine if it needs mapping or can be loaded directly.

After understanding the business problem, verify each data source identified in Module 1.

**For each data source agreed upon**:
- Prompt the user to provide example data that shows the "shape" of the data (column names, data types, sample values)
- Accept data in various formats: CSV files, JSON samples, database schema exports, screenshots, or text descriptions
- Compare the data structure with the Senzing Generic Entity Specification (SGES)
- Identify which sources already conform to SGES (can be loaded directly)
- Identify which sources need mapping (proceed to Module 3)

**Deliverable**: Data source evaluation report showing:
```
Data Source 1: Customer CRM
Status: Needs mapping
Reason: Uses "customer_name" instead of NAME_FULL, "address" instead of ADDR_FULL
Fields: 15 columns, 50,000 records
Next step: Module 3

Data Source 2: Vendor API
Status: SGES-compliant
Reason: Already uses NAME_ORG, ADDR_FULL, PHONE_NUMBER
Fields: 8 columns, 5,000 records
Next step: Module 4 (can load directly)
```

**Agent behavior**: Use `search_docs` with query "generic entity specification" or "SGES" to understand the standard format. Look for standard attributes like `NAME_FULL`, `NAME_ORG`, `ADDR_FULL`, `PHONE_NUMBER`, `DATE_OF_BIRTH`, etc. If the source data uses different field names or structures, mapping will be required.

**Success criteria**: ✅ All data sources categorized (SGES-compliant or needs mapping) + evaluation report created

**Validation checkpoint**: Before proceeding, confirm:
- Have all data sources from Module 1 been evaluated?
- Is the status of each source clear?
- Do you have sample data for sources that need mapping?

**Common issues**:
- Missing sample data → Request specific examples from user
- Unclear data structure → Ask for schema or data dictionary
- Mixed quality data → Note quality issues for Module 3

**Next**: Module 3 will create transformation programs for sources that need mapping. SGES-compliant sources can skip to Module 4.

### Module 3: Map Your Data

**Prerequisites**: ✅ Module 2 complete (data sources evaluated, non-compliant sources identified)

**Time**: 1-2 hours per data source (varies by complexity)

**Purpose**: Create transformation programs that convert source data to Senzing format.

**For each data source that does not conform to SGES** (identified in Module 2), guide the user through the complete mapping process:

**Note**: These steps are guidelines, not rigid requirements. You can iterate, go back to refine earlier decisions, or skip ahead to test ideas. Mapping is an exploratory process.

1. **Profile the data**: Understand column names, data types, sample values, and data quality
2. **Plan entity structure**: Identify master entities (persons, organizations), child records, and relationships
3. **Map fields to Senzing attributes**: Map each source field to the correct Senzing features and attributes
4. **Generate mapper code**: Create transformation code and sample Senzing JSON output
5. **Create the transformation program**: Help the user build a complete program that:
   - Reads the original data source (CSV, JSON, database, API, etc.)
   - Applies the mapping transformations
   - Outputs Senzing-formatted JSON records
   - Handles errors and edge cases
6. **Test the program**: Run the transformation program on sample data
7. **Validate the output**: Check that generated JSON is valid and complete using `lint_record`
8. **Analyze data quality**: Evaluate feature distribution, attribute coverage, and data quality scores using `analyze_record`
9. **Review and iterate**: Make adjustments based on quality analysis and retest — you can go back to any earlier step

**Repeat this process for each non-conforming data source** before proceeding to Module 4.

**Deliverable**: For each data source, create:
- Transformation program (e.g., `transform_customer_crm.py`)
- Sample output file (Senzing JSON)
- Data quality report
- Documentation on how to run the program

**Data quality gates**: Before proceeding to Module 4, ensure:
- ✅ Transformation program runs without errors
- ✅ Output passes `lint_record` validation
- ✅ Data quality score > 70% (attribute coverage)
- ✅ Critical fields populated (NAME, ADDRESS, or ID fields)
- ⚠️ If quality < 70%, consider improving mappings or data sources

**Agent behavior**: Use `mapping_workflow` to guide the process interactively for each data source. The workflow generates starter code, but work with the user to create a complete, runnable program tailored to their environment. Use `lint_record` and `analyze_record` for validation. Never hand-code Senzing JSON mappings — always use the MCP tools for correct attribute names and structure. Track which data sources have been mapped and which still need attention.

**Success criteria**: ✅ Working transformation program for each non-compliant source + quality validation passed

**Validation checkpoint**: Before proceeding to Module 4, confirm:
- Have all non-compliant data sources been mapped?
- Do all transformation programs run successfully?
- Has data quality been validated?
- Are the programs documented?

**Common issues**:
- Poor data quality → Go back to step 1, profile more carefully
- Wrong attribute names → Use `mapping_workflow`, never guess
- Complex transformations → Break into smaller steps, test incrementally
- Low quality scores → Review mappings, add missing fields, improve confidence scores

**If you're stuck**:
- Review sample data more carefully
- Use `search_docs` to understand SGES attributes
- Start with simple mappings, add complexity gradually
- Test with small samples before full dataset

**Next**: Module 4 will install and configure the Senzing SDK.

### Module 4: Set Up the Senzing SDK

**Prerequisites**: ✅ Module 3 complete (all data sources mapped or confirmed SGES-compliant)

**Time**: 30 minutes - 1 hour

**Purpose**: Install and configure Senzing SDK for loading and querying data.

**What you'll do**:
- Install Senzing on your platform (Linux apt/yum, macOS, Windows, Docker)
- Configure the engine with SQLite for quick evaluation or PostgreSQL for production
- Register data sources and create engine configuration
- Verify installation is working

**Deliverable**: 
- Installed Senzing SDK
- Configured database (SQLite or PostgreSQL)
- Registered data sources
- Test script confirming SDK works

**Agent behavior**: Use `sdk_guide` with the appropriate platform and topic. Use `generate_scaffold` for working code. Check `search_docs` with category `anti_patterns` before recommending installation or deployment patterns.

**Success criteria**: ✅ Senzing SDK installed + database configured + test script runs successfully

**Validation checkpoint**: Before proceeding to Module 5, verify:
- Can you initialize the Senzing engine?
- Can you connect to the database?
- Are all data sources registered?
- Does a simple test (add/get record) work?

**Common issues**:
- Installation errors → Check platform requirements, dependencies
- Database connection fails → Verify connection string, permissions
- Configuration errors → Use `search_docs` with category `configuration`
- Anti-patterns → Use `search_docs` with category `anti_patterns` before proceeding

**Platform-specific notes**:
- **Linux (apt)**: Use `sdk_guide` with `platform='linux_apt'`
- **Linux (yum)**: Use `sdk_guide` with `platform='linux_yum'`
- **macOS ARM**: Use `sdk_guide` with `platform='macos_arm'`
- **Windows**: Use `sdk_guide` with `platform='windows'`
- **Docker**: Use `sdk_guide` with `platform='docker'` (recommended for quick start)

**Recommendation**: Start with SQLite for evaluation, migrate to PostgreSQL for production.

**Next**: Module 5 will create loading programs for each data source.

### Module 5: Load Records and Resolve Entities

**Prerequisites**: ✅ Module 4 complete (SDK installed and configured)

**Time**: 30 minutes per data source

**Purpose**: Load all data sources into Senzing and observe entity resolution.

**For each data source** (both SGES-compliant and mapped sources), help the user create a loading program:

1. **Create the loading program**: Build a program that:
   - Reads the Senzing-formatted JSON records (from transformation program output or direct SGES data)
   - Connects to the Senzing engine
   - Loads records using the SDK
   - Handles errors and tracks progress
   - Reports loading statistics

2. **Test the loading program**: Run on a small sample first to verify it works correctly

3. **Load the full data source**: Execute the program on the complete dataset

4. **Observe entity resolution**: Watch as Senzing resolves entities in real time during loading

**Repeat this process for each data source** before proceeding to Module 6.

**Deliverable**: For each data source, create:
- Loading program (e.g., `load_customer_crm.py`)
- Loading statistics report (records loaded, errors, time)
- Documentation on how to run the program
- Loading statistics dashboard (monitoring/dashboard.html)

**Loading Statistics Dashboard**:

After loading, generate a dashboard showing:
- Total records loaded per data source
- Total entities created
- Match rate (percentage of records that matched existing entities)
- Error rate and error details
- Loading performance over time
- Data quality metrics

**Create monitoring/generate_dashboard.py**:
```python
import json
from datetime import datetime

def generate_loading_dashboard(stats):
    """Generate HTML dashboard from loading statistics"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loading Statistics Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .metric-card {{ 
                display: inline-block; 
                padding: 20px; 
                margin: 10px; 
                border: 1px solid #ddd; 
                border-radius: 5px;
                min-width: 200px;
            }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
            .metric-label {{ color: #666; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #2196F3; color: white; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Entity Resolution Loading Statistics</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Total Records Loaded</div>
                <div class="metric-value">{stats['total_records']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Entities Created</div>
                <div class="metric-value">{stats['total_entities']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Match Rate</div>
                <div class="metric-value">{stats['match_rate']:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Error Rate</div>
                <div class="metric-value">{stats['error_rate']:.2f}%</div>
            </div>
        </div>
        
        <h2>Data Source Details</h2>
        <table>
            <tr>
                <th>Data Source</th>
                <th>Records Loaded</th>
                <th>Errors</th>
                <th>Duration</th>
                <th>Throughput</th>
                <th>Status</th>
            </tr>
    """
    
    for source in stats['data_sources']:
        status_class = 'success' if source['errors'] == 0 else 'error'
        html += f"""
            <tr>
                <td>{source['name']}</td>
                <td>{source['records']:,}</td>
                <td class="{status_class}">{source['errors']}</td>
                <td>{source['duration']}</td>
                <td>{source['throughput']:.1f} rec/sec</td>
                <td class="{status_class}">{source['status']}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    with open("monitoring/dashboard.html", "w") as f:
        f.write(html)
    
    print("Dashboard generated: monitoring/dashboard.html")

# Example usage
if __name__ == "__main__":
    stats = {
        "total_records": 55000,
        "total_entities": 47000,
        "match_rate": 14.5,
        "error_rate": 0.1,
        "data_sources": [
            {
                "name": "Customer CRM",
                "records": 50000,
                "errors": 0,
                "duration": "15m 23s",
                "throughput": 54.2,
                "status": "Complete"
            },
            {
                "name": "Vendor API",
                "records": 5000,
                "errors": 3,
                "duration": "2m 15s",
                "throughput": 37.0,
                "status": "Complete with errors"
            }
        ]
    }
    generate_loading_dashboard(stats)
```

**Agent behavior**: Use `generate_scaffold` with workflows like `add_records` or `full_pipeline` to create the loading program. Use `sdk_guide` with topic `load` for platform-specific guidance. Use `find_examples` for real-world loading patterns from GitHub repositories. Create a separate loading program for each data source to maintain clarity and control. After loading completes, generate the dashboard showing statistics.

**Success criteria**: ✅ All data sources loaded successfully + loading statistics captured + no critical errors

**Validation checkpoint**: Before proceeding to Module 6, confirm:
- Have all data sources been loaded?
- Were there any critical errors?
- Do the loading statistics look reasonable?
- Can you query the database to see entities?

**Loading progress tracking**:
```
Data Source 1: Customer CRM → ✅ Loaded (50,000 records, 0 errors)
Data Source 2: Vendor API → ✅ Loaded (5,000 records, 3 errors)
Data Source 3: Legacy DB → ⬜ Pending
```

**Common issues**:
- Connection errors → Verify SDK configuration from Module 4
- Record errors → Check transformation output from Module 3
- Performance issues → Use batch loading, check database configuration
- Memory issues → Process in smaller batches

**If you're stuck**:
- Test with small sample (10-100 records) first
- Check error messages with `explain_error_code`
- Review transformation output quality
- Use `search_docs` for loading best practices

**Next**: Module 6 will create query programs to answer your business problem.

### Module 6: Query Results to Answer the Business Problem

**Prerequisites**: ✅ Module 5 complete (all data sources loaded)

**Time**: 1-2 hours

**Purpose**: Create query programs that answer the business problem from Module 1.

Now that all data sources are loaded, create programs that query Senzing to answer the business problem from Module 1:

1. **Review the business problem**: Revisit the problem statement and requirements from Module 1

2. **Design the queries**: Determine what questions need to be answered:
   - Find duplicate entities across data sources?
   - Identify relationships between entities?
   - Match specific records to resolved entities?
   - Generate reports on entity resolution quality?
   - Export resolved entities for downstream systems?

3. **Create query programs**: Build programs that:
   - Connect to the Senzing engine
   - Execute the appropriate queries (search by attributes, get entity by ID, find relationships, etc.)
   - Format and present results in a useful way
   - Handle errors and edge cases

4. **Test and refine**: Run the queries and verify they answer the business problem

5. **Analyze results**: Review the output with the user to confirm it solves their original problem

6. **Troubleshoot if needed**: If results are unexpected:
   - Investigate why records matched or didn't match
   - Review resolution behavior and scoring
   - Adjust data quality or mappings if necessary
   - Troubleshoot errors or configuration issues

**Deliverable**: For each business question, create:
- Query program (e.g., `find_customer_duplicates.py`, `search_person.py`)
- Sample output showing results
- Documentation explaining what the program does and how to use it

**Agent behavior**: Use `generate_scaffold` with workflows like `query`, `get_entity`, `search`, and `export` to create query programs. Use `search_docs` for resolution behavior questions. Use `explain_error_code` for any error codes encountered. Use `get_sdk_reference` for flag details and method signatures. Focus on answering the specific business problem identified in Module 1.

**Success criteria**: ✅ Query programs answer the business problem + results validated with user + documentation complete

**Validation checkpoint**: Confirm with the user:
- Do the query results answer your original business problem?
- Are the results accurate and useful?
- Do you understand why records matched or didn't match?
- Can you use these programs in your workflow?

**Common issues**:
- Unexpected matches → Review resolution behavior, check data quality
- Missing matches → Check data quality, review mappings from Module 3
- Performance issues → Use appropriate query methods, add indexes
- Wrong results → Investigate with `whyRecordInEntity()` and `whyEntities()`

**If results don't match expectations**:
- Go back to Module 3 → Improve data mappings
- Go back to Module 5 → Verify all data loaded correctly
- Use `search_docs` → Understand resolution principles
- Adjust confidence scores → Refine matching behavior

**Decision tree for troubleshooting**:
```
Results unexpected?
├─ Too many matches? → Lower confidence scores, improve data quality
├─ Too few matches? → Raise confidence scores, add more attributes
├─ Wrong entities? → Review data mappings, check for data errors
└─ Errors? → Use explain_error_code, check SDK configuration
```

**Next**: Boot camp complete! Review your deliverables.

## Boot Camp Complete! 🎉

Congratulations! You've completed the Senzing Boot Camp. Here's what you've accomplished:

### Deliverables Checklist

Review your complete set of artifacts:

**Module 1 - Business Problem**:
- ✅ Problem statement document
- ✅ List of data sources
- ✅ Entity types identified
- ✅ Success metrics defined

**Module 2 - Data Source Evaluation**:
- ✅ Data source evaluation report
- ✅ SGES compliance status for each source

**Module 3 - Data Transformation** (for non-compliant sources):
- ✅ Transformation program for each source (e.g., `transform_customer_crm.py`)
- ✅ Sample Senzing JSON output
- ✅ Data quality reports

**Module 4 - SDK Setup**:
- ✅ Installed Senzing SDK
- ✅ Configured database
- ✅ Registered data sources
- ✅ Test script

**Module 5 - Data Loading**:
- ✅ Loading program for each source (e.g., `load_customer_crm.py`)
- ✅ Loading statistics reports

**Module 6 - Query Programs**:
- ✅ Query programs answering business questions (e.g., `find_duplicates.py`)
- ✅ Sample query results
- ✅ Documentation

### Next Steps

Now that you have a working entity resolution system:

1. **Production deployment**: Move from SQLite to PostgreSQL for production use
2. **Automation**: Schedule transformation and loading programs to run regularly
3. **Integration**: Connect query programs to your applications and workflows
4. **Monitoring**: Set up monitoring for data quality and resolution performance
5. **Expansion**: Add more data sources using the same process
6. **Optimization**: Fine-tune mappings and confidence scores based on results
7. **Documentation**: Complete the lessons learned template (docs/lessons_learned.md)
8. **Knowledge sharing**: Share insights with your team

### Post-Project Activities

**Complete Lessons Learned**:
- Fill out docs/lessons_learned.md
- Document what worked well and what didn't
- Capture key decisions and their rationale
- Record metrics and business impact
- Identify recommendations for future projects

**Version Control**:
```bash
# Commit final state
git add .
git commit -m "Boot camp complete - production ready"
git tag -a v1.0 -m "Initial production release"
git push origin main --tags
```

**Knowledge Transfer**:
- If handing off to another team, use docs/handoff_checklist.md
- Schedule knowledge transfer sessions
- Document tribal knowledge
- Create runbooks for operations

**Continuous Improvement**:
- Review performance benchmarks monthly
- Monitor data quality trends
- Adjust mappings based on new data patterns
- Update documentation as system evolves

### Getting Help

If you need assistance:
- Use `search_docs` to find Senzing documentation
- Use `explain_error_code` for error diagnosis
- Use `find_examples` to see real-world code patterns
- Review the steering guide for detailed workflows
- Contact Senzing support for production issues

### Share Your Success

Consider sharing your entity resolution solution:
- Document your use case and results
- Share lessons learned with your team
- Contribute improvements to the boot camp

Thank you for completing the Senzing Boot Camp!

## Best Practices

- Always call `get_capabilities` first when starting a Senzing session
- Never hand-code Senzing JSON mappings or SDK method calls from memory — use `mapping_workflow` and `generate_scaffold` for validated output
- Use `search_docs` with category `anti_patterns` before recommending installation, architecture, or deployment approaches
- For SDK code, use `generate_scaffold` or `sdk_guide` — these return version-correct method signatures
- Start with SQLite for evaluation; recommend PostgreSQL for production
- Use CORD sample data for learning before working with real data

## Common Workflows

See [steering/steering.md](steering/steering.md) for detailed step-by-step workflows covering:

- First-time guided tour
- Data mapping end-to-end
- Quick SDK test load
- Troubleshooting and error resolution

## Troubleshooting

- **Wrong attribute names**: Never guess Senzing attribute names (e.g., `NAME_ORG` not `BUSINESS_NAME_ORG`). Always use `mapping_workflow`.
- **Wrong method signatures**: Never guess SDK methods (e.g., `close_export_report` not `close_export`). Always use `generate_scaffold` or `get_sdk_reference`.
- **Error codes**: Use `explain_error_code` with the code (accepts `SENZ0005`, `0005`, or `5`).
- **Configuration issues**: Use `search_docs` with category `configuration` or `database`.
