# Modules 7-12 Detailed Workflows

This document provides detailed agent workflows for Modules 7-12 (advanced modules).

## Module 7: Multi-Source Orchestration

**Purpose**: Coordinate loading of multiple data sources with dependencies and optimization.

**Prerequisites**:
- ✅ Module 6 complete (first source loaded successfully)
- ✅ Multiple data sources to orchestrate
- ✅ Loading statistics reviewed for first source

**Agent Workflow**:

1. **Analyze data sources and dependencies**:
   
   Ask: "Do any of your data sources depend on others being loaded first?"
   
   WAIT for response.
   
   Common dependency patterns:
   - Parent-child relationships (load parents first)
   - Reference data (load lookups first)
   - Temporal ordering (load historical first)

2. **Determine loading strategy**:
   
   Ask: "Would you like to load sources sequentially or in parallel?"
   
   Options:
   - **Sequential**: One at a time, safer, easier to debug
   - **Parallel**: Multiple at once, faster, requires more resources
   - **Hybrid**: Some parallel, some sequential based on dependencies
   
   WAIT for response.

3. **Create orchestration plan**:
   
   Document in `docs/loading_strategy.md`:
   ```markdown
   # Loading Strategy
   
   ## Load Order
   1. Reference data (COUNTRIES, STATES)
   2. Core entities (CUSTOMERS, PRODUCTS)
   3. Transactions (ORDERS, SUPPORT_TICKETS)
   
   ## Parallel Groups
   - Group 1: CUSTOMERS, PRODUCTS (no dependencies)
   - Group 2: ORDERS, SUPPORT_TICKETS (depend on Group 1)
   
   ## Resource Allocation
   - Max parallel loaders: 4
   - Memory per loader: 2GB
   - Expected duration: 2-3 hours
   ```

4. **Create orchestrator program**:
   
   Use `generate_scaffold` with `workflow='orchestration'` or create from template.
   
   Save to `src/load/orchestrator.py`.
   
   Key features:
   - Dependency management
   - Parallel execution (ThreadPoolExecutor or multiprocessing)
   - Progress tracking across sources
   - Error handling and recovery
   - Statistics aggregation

5. **Test orchestration with samples**:
   
   Before running on full data:
   ```bash
   # Test with small samples
   python src/load/orchestrator.py --test --limit 100
   ```

6. **Run full orchestration**:
   
   ```bash
   python src/load/orchestrator.py
   ```
   
   Monitor:
   - Progress for each source
   - Overall completion percentage
   - Error rates
   - Resource utilization

7. **Validate results**:
   
   After loading:
   - Check record counts for each source
   - Verify cross-source matches
   - Review error logs
   - Confirm no data loss

**Success Criteria**:
- ✅ All sources loaded successfully
- ✅ Dependencies respected
- ✅ Cross-source matches identified
- ✅ Error rate < 1%
- ✅ Loading statistics documented

**Common Issues**:
- Dependency cycles: Redesign load order
- Resource exhaustion: Reduce parallelism
- Slow performance: Optimize transformations or use PostgreSQL

---

## Module 8: Query and Validate Results

**Purpose**: Create query programs and conduct user acceptance testing.

**Prerequisites**:
- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source)
- ✅ No critical loading errors

**Agent Workflow**:

1. **Define query requirements**:
   
   Ask: "What questions do you need to answer with your data?"
   
   Common queries:
   - Find duplicates within a source
   - Find cross-source matches
   - Search for specific entities
   - Get entity 360 view
   - Export resolved entities
   
   WAIT for response.

2. **Create query programs**:
   
   For each query type, create a program in `src/query/`.
   
   Use `generate_scaffold` with `workflow='query'` or use query template.
   
   Example queries:
   - `find_duplicates.py` - Find entities with multiple records
   - `search_entities.py` - Search by name, email, phone
   - `customer_360.py` - Get complete customer view
   - `export_results.py` - Export to CSV/JSON

3. **Run exploratory queries**:
   
   Execute queries to understand results:
   ```bash
   python src/query/find_duplicates.py
   python src/query/search_entities.py --name "John Smith"
   ```

4. **Create UAT test cases**:
   
   Document in `docs/uat_test_cases.md`:
   ```markdown
   # User Acceptance Test Cases
   
   ## Test Case 1: Duplicate Detection
   **Scenario**: Find John Smith duplicates
   **Expected**: 3 records resolve to 1 entity
   **Actual**: [To be filled]
   **Status**: [Pass/Fail]
   
   ## Test Case 2: Cross-Source Matching
   **Scenario**: Customer in CRM and E-commerce
   **Expected**: Records linked to same entity
   **Actual**: [To be filled]
   **Status**: [Pass/Fail]
   ```

5. **Execute UAT with business users**:
   
   Ask: "Would you like to involve business users in testing?"
   
   If yes:
   - Share query programs
   - Provide sample queries
   - Collect feedback
   - Document results

6. **Validate results quality**:
   
   Check:
   - Match accuracy (are correct records matched?)
   - False positives (are incorrect records matched?)
   - False negatives (are matches missed?)
   - Data completeness (is all data present?)

7. **Document findings**:
   
   Create `docs/results_validation.md`:
   ```markdown
   # Results Validation
   
   ## Match Quality
   - True positives: 95%
   - False positives: 2%
   - False negatives: 3%
   
   ## Business Validation
   - Test cases passed: 45/50
   - Issues identified: 5
   - Resolution plan: [describe]
   ```

**Success Criteria**:
- ✅ Query programs created and tested
- ✅ UAT test cases defined
- ✅ Business users validated results
- ✅ Match quality meets requirements (>90% accuracy)
- ✅ Issues documented with resolution plan

---

## Module 9: Performance Testing and Benchmarking

**Purpose**: Benchmark and optimize for production performance.

**Prerequisites**:
- ✅ Module 8 complete (queries working)
- ✅ Representative data loaded
- ✅ Test environment available

**Agent Workflow**:

1. **Define performance requirements**:
   
   Ask: "What are your performance requirements?"
   
   Common metrics:
   - Loading throughput (records/second)
   - Query latency (milliseconds)
   - Concurrent users
   - Data volume
   
   WAIT for response.

2. **Benchmark transformation**:
   
   Create `tests/performance/test_transform_performance.py`:
   ```python
   def benchmark_transformation(sample_size=10000):
       start = time.time()
       # Run transformation
       duration = time.time() - start
       rate = sample_size / duration
       print(f"Transformation rate: {rate:.1f} records/sec")
       return rate
   ```

3. **Benchmark loading**:
   
   Create `tests/performance/test_load_performance.py`:
   ```python
   def benchmark_loading(sample_size=10000):
       start = time.time()
       # Load records
       duration = time.time() - start
       rate = sample_size / duration
       print(f"Loading rate: {rate:.1f} records/sec")
       return rate
   ```

4. **Benchmark queries**:
   
   Create `tests/performance/test_query_performance.py`:
   ```python
   def benchmark_queries():
       queries = [
           ("search_by_name", lambda: search("John Smith")),
           ("get_entity", lambda: get_entity(12345)),
           ("find_duplicates", lambda: find_duplicates())
       ]
       
       for name, query_func in queries:
           start = time.time()
           query_func()
           duration = time.time() - start
           print(f"{name}: {duration*1000:.1f}ms")
   ```

5. **Profile resource usage**:
   
   Monitor:
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network I/O
   
   Use tools like `psutil`, `py-spy`, or system monitors.

6. **Scalability testing**:
   
   Test with increasing data volumes:
   - 10K records
   - 100K records
   - 1M records
   - 10M records (if applicable)
   
   Document how performance scales.

7. **Identify bottlenecks**:
   
   Common bottlenecks:
   - Slow transformations → Optimize code, use multiprocessing
   - Slow loading → Use PostgreSQL, increase batch size
   - Slow queries → Add indexes, optimize query logic
   - Memory issues → Reduce batch size, stream data

8. **Optimize and retest**:
   
   Apply optimizations and re-run benchmarks.
   
   Document improvements in `docs/performance_optimization.md`.

9. **Create performance report**:
   
   Document in `docs/performance_report.md`:
   ```markdown
   # Performance Report
   
   ## Transformation
   - Rate: 5,000 records/sec
   - Bottleneck: JSON parsing
   - Optimization: Used ujson library
   
   ## Loading
   - Rate: 1,200 records/sec
   - Database: PostgreSQL
   - Batch size: 1000
   
   ## Queries
   - Search by name: 45ms p95
   - Get entity: 12ms p95
   - Find duplicates: 2.3 seconds (100K entities)
   
   ## Scalability
   - Linear scaling up to 1M records
   - Recommend horizontal scaling beyond 5M records
   ```

**Success Criteria**:
- ✅ Performance benchmarks completed
- ✅ Requirements met or optimization plan created
- ✅ Bottlenecks identified and addressed
- ✅ Scalability tested
- ✅ Performance report documented

---

## Module 10: Security Hardening

**Purpose**: Implement production-grade security measures.

**Prerequisites**:
- ✅ Module 9 complete (performance validated)
- ✅ Security requirements identified
- ✅ Compliance needs documented

**Agent Workflow**:

1. **Assess security requirements**:
   
   Ask: "What are your security and compliance requirements?"
   
   Common requirements:
   - SOC 2, ISO 27001
   - GDPR, CCPA
   - HIPAA, PCI-DSS
   - Industry-specific regulations
   
   WAIT for response.

2. **Implement secrets management**:
   
   Never hard-code credentials!
   
   Options:
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Environment variables (minimum)
   
   Create `src/security/secrets_manager.py`:
   ```python
   import boto3
   
   def get_database_password():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='prod/db/password')
       return response['SecretString']
   ```

3. **Implement authentication**:
   
   For APIs and services:
   - JWT tokens
   - OAuth 2.0
   - API keys with rotation
   - Multi-factor authentication
   
   Create `src/security/auth.py`.

4. **Implement authorization**:
   
   Role-based access control (RBAC):
   - Admin: Full access
   - Analyst: Read-only
   - Service: API access only
   
   Create `src/security/rbac.py`.

5. **Encrypt sensitive data**:
   
   - Data at rest: Database encryption
   - Data in transit: TLS/SSL
   - PII fields: Field-level encryption
   
   Create `src/security/encryption.py`.

6. **Implement audit logging**:
   
   Log all access and changes:
   - Who accessed what
   - When
   - What changed
   - Why (if available)
   
   Create `src/security/audit_log.py`.

7. **Scan for vulnerabilities**:
   
   Run security scans:
   ```bash
   # Python dependencies
   pip install safety
   safety check
   
   # Code scanning
   bandit -r src/
   
   # Container scanning (if using Docker)
   trivy image your-image:latest
   ```

8. **Create security checklist**:
   
   Document in `docs/security_checklist.md`:
   ```markdown
   # Security Checklist
   
   ## Secrets Management
   - [ ] No hard-coded credentials
   - [ ] Secrets in vault/manager
   - [ ] Regular secret rotation
   
   ## Authentication
   - [ ] Strong password policy
   - [ ] MFA enabled
   - [ ] Session timeout configured
   
   ## Authorization
   - [ ] RBAC implemented
   - [ ] Least privilege principle
   - [ ] Regular access reviews
   
   ## Encryption
   - [ ] TLS/SSL for all connections
   - [ ] Database encryption enabled
   - [ ] PII fields encrypted
   
   ## Audit Logging
   - [ ] All access logged
   - [ ] Logs retained per policy
   - [ ] Log monitoring enabled
   
   ## Vulnerability Management
   - [ ] Regular security scans
   - [ ] Patch management process
   - [ ] Incident response plan
   ```

9. **Conduct security review**:
   
   If possible, have security team review:
   - Architecture
   - Code
   - Configuration
   - Access controls

**Success Criteria**:
- ✅ Secrets management implemented
- ✅ Authentication and authorization in place
- ✅ Encryption configured
- ✅ Audit logging enabled
- ✅ Security scans passed
- ✅ Security checklist completed

---

## Module 11: Monitoring and Observability

**Purpose**: Set up comprehensive monitoring for production operations.

**Prerequisites**:
- ✅ Module 10 complete (security hardened)
- ✅ Monitoring tools selected
- ✅ Production environment identified

**Agent Workflow**:

1. **Select monitoring stack**:
   
   Ask: "What monitoring tools do you want to use?"
   
   Common stacks:
   - Prometheus + Grafana
   - CloudWatch (AWS)
   - Azure Monitor
   - Datadog
   - New Relic
   
   WAIT for response.

2. **Implement metrics collection**:
   
   Create `src/monitoring/metrics_collector.py`:
   ```python
   from prometheus_client import Counter, Histogram, Gauge
   
   # Define metrics
   records_loaded = Counter('records_loaded_total', 'Total records loaded')
   load_duration = Histogram('load_duration_seconds', 'Load duration')
   active_loaders = Gauge('active_loaders', 'Active loaders')
   
   # Use in code
   records_loaded.inc()
   load_duration.observe(duration)
   active_loaders.set(count)
   ```

3. **Implement structured logging**:
   
   Create `src/utils/logging_config.py`:
   ```python
   import logging
   import json
   
   class JSONFormatter(logging.Formatter):
       def format(self, record):
           log_data = {
               'timestamp': self.formatTime(record),
               'level': record.levelname,
               'message': record.getMessage(),
               'module': record.module,
               'function': record.funcName
           }
           return json.dumps(log_data)
   ```

4. **Create dashboards**:
   
   Create Grafana dashboards in `monitoring/grafana/dashboards/`:
   - `loading_dashboard.json` - Loading metrics
   - `query_dashboard.json` - Query performance
   - `system_dashboard.json` - System resources
   - `error_dashboard.json` - Error rates

5. **Configure alerts**:
   
   Create alert rules in `monitoring/alerts/alert_rules.yml`:
   ```yaml
   groups:
     - name: senzing_alerts
       rules:
         - alert: HighErrorRate
           expr: rate(load_errors_total[5m]) > 0.01
           annotations:
             summary: "High error rate detected"
         
         - alert: SlowQueries
           expr: query_duration_seconds > 1.0
           annotations:
             summary: "Queries are slow"
         
         - alert: HighMemoryUsage
           expr: memory_usage_percent > 90
           annotations:
             summary: "Memory usage critical"
   ```

6. **Implement health checks**:
   
   Create `src/monitoring/health_checks.py`:
   ```python
   def check_database():
       """Check database connectivity"""
       try:
           # Test connection
           return True
       except:
           return False
   
   def check_senzing():
       """Check Senzing engine"""
       try:
           # Test engine
           return True
       except:
           return False
   
   def health_check():
       """Overall health check"""
       checks = {
           'database': check_database(),
           'senzing': check_senzing()
       }
       return all(checks.values()), checks
   ```

7. **Set up distributed tracing** (optional):
   
   For microservices:
   - OpenTelemetry
   - Jaeger
   - Zipkin

8. **Create runbooks**:
   
   Document in `docs/operations/runbooks/`:
   - `high_cpu.md` - What to do when CPU is high
   - `slow_queries.md` - How to diagnose slow queries
   - `data_quality_issues.md` - Handling data quality problems
   - `system_outage.md` - Incident response

9. **Test monitoring**:
   
   Trigger alerts intentionally:
   - Cause high error rate
   - Generate slow queries
   - Simulate resource exhaustion
   
   Verify alerts fire and runbooks work.

**Success Criteria**:
- ✅ Metrics collection implemented
- ✅ Dashboards created
- ✅ Alerts configured
- ✅ Health checks working
- ✅ Runbooks documented
- ✅ Monitoring tested

---

## Module 12: Package and Deploy

**Purpose**: Package code and deploy to production.

**Prerequisites**:
- ✅ Module 11 complete (monitoring configured)
- ✅ All tests passing
- ✅ Deployment target confirmed

**Agent Workflow**:

1. **Refactor code into package**:
   
   Organize code:
   ```
   senzing_mdm/
   ├── __init__.py
   ├── transform/
   │   ├── __init__.py
   │   └── transformers.py
   ├── load/
   │   ├── __init__.py
   │   └── loaders.py
   ├── query/
   │   ├── __init__.py
   │   └── queries.py
   └── utils/
       ├── __init__.py
       └── config.py
   ```

2. **Create setup.py**:
   
   ```python
   from setuptools import setup, find_packages
   
   setup(
       name='senzing-mdm',
       version='1.0.0',
       packages=find_packages(),
       install_requires=[
           'senzing>=4.0.0',
           'pandas>=1.5.0',
           # Add dependencies
       ]
   )
   ```

3. **Create multi-environment configs**:
   
   ```
   config/
   ├── dev/
   │   ├── senzing_config.json
   │   └── app_config.yaml
   ├── staging/
   │   ├── senzing_config.json
   │   └── app_config.yaml
   └── prod/
       ├── senzing_config.json
       └── app_config.yaml
   ```

4. **Create Dockerfile** (if using containers):
   
   Create `docker/Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   CMD ["python", "src/load/orchestrator.py"]
   ```
   
   Create `docker/docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     senzing-api:
       build:
         context: ..
         dockerfile: docker/Dockerfile
       ports:
         - "8080:8080"
       environment:
         - CONFIG_FILE=/app/config/prod/senzing_config.json
   ```

5. **Create deployment scripts**:
   
   Create `deployment/scripts/deploy.sh`:
   ```bash
   #!/bin/bash
   set -e
   
   ENVIRONMENT=$1
   VERSION=$2
   
   echo "Deploying version $VERSION to $ENVIRONMENT"
   
   # Run tests
   pytest tests/
   
   # Build package
   python setup.py sdist bdist_wheel
   
   # Deploy (customize for your platform)
   # ...
   
   echo "Deployment complete!"
   ```

6. **Create CI/CD pipeline**:
   
   Create `.github/workflows/ci.yml`:
   ```yaml
   name: CI
   
   on: [push, pull_request]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: pytest tests/
         - name: Security scan
           run: bandit -r src/
   ```

7. **Create disaster recovery plan**:
   
   Document in `docs/operations/disaster_recovery.md`:
   - Backup procedures
   - Recovery procedures
   - RTO/RPO targets
   - Failover process

8. **Deploy to staging**:
   
   ```bash
   ./deployment/scripts/deploy.sh staging 1.0.0
   ```
   
   Test in staging:
   - Run smoke tests
   - Verify monitoring
   - Check performance

9. **Deploy to production**:
   
   ```bash
   ./deployment/scripts/deploy.sh prod 1.0.0
   ```
   
   Monitor closely:
   - Watch dashboards
   - Check error rates
   - Verify functionality

10. **Create operations documentation**:
    
    Document in `docs/operations/`:
    - `deployment_guide.md` - How to deploy
    - `monitoring_guide.md` - How to monitor
    - `troubleshooting_guide.md` - Common issues
    - `maintenance_procedures.md` - Regular maintenance

**Success Criteria**:
- ✅ Code packaged and organized
- ✅ Multi-environment configs created
- ✅ Deployment scripts working
- ✅ CI/CD pipeline configured
- ✅ Deployed to staging successfully
- ✅ Deployed to production successfully
- ✅ Operations documentation complete

---

## When to Load This Guide

Load this guide when:
- User reaches Module 7 or beyond
- User asks about advanced modules
- User needs detailed workflows for Modules 7-12

## Related Documentation

- [steering.md](steering.md) - Modules 0-6 workflows
- [agent-instructions.md](agent-instructions.md) - Agent behavior guide
- Module documentation in `docs/modules/`

## Version History

- **v1.0.0** (2026-03-17): Modules 7-12 workflows created
