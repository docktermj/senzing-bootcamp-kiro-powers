# Production Deployment Example: Enterprise Customer MDM

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, code patterns, and expected results. The actual source code files referenced below are generated during the boot camp using MCP tools (`generate_scaffold`, `mapping_workflow`). Use this README as an architectural reference when building your own project.

## Overview

This example demonstrates a complete production-ready deployment of Senzing for enterprise Customer Master Data Management (MDM). It covers all 13 modules (0-12) with production-grade implementations.

**Time to Complete:** 12-15 hours
**Difficulty:** Advanced
**Modules Covered:** 0-12 (complete boot camp)

## Business Problem

**Scenario:** A large enterprise with 5 million customer records across 6 systems needs a production-grade MDM solution with:

- High availability (99.9% uptime)
- Performance (1000+ records/sec)
- Security (SOC 2 compliant)
- Monitoring and alerting
- Disaster recovery
- Multi-environment deployment (dev, staging, prod)

**Expected Outcomes:**

- Process 5M records in < 2 hours
- Query response time < 100ms
- Zero data loss
- Automated deployment pipeline
- Complete observability

## Project Structure

```text
enterprise-customer-mdm/
├── data/
│   ├── raw/                           # Source data
│   ├── transformed/                   # Senzing JSON
│   └── backups/                       # Database backups
├── database/
│   └── .gitkeep                       # PostgreSQL used in production
├── src/
│   ├── transform/
│   │   ├── __init__.py
│   │   ├── base_transformer.py        # Base class
│   │   ├── crm_transformer.py
│   │   ├── erp_transformer.py
│   │   ├── web_transformer.py
│   │   ├── mobile_transformer.py
│   │   ├── partner_transformer.py
│   │   └── legacy_transformer.py
│   ├── load/
│   │   ├── __init__.py
│   │   ├── batch_loader.py            # Batch loading
│   │   ├── streaming_loader.py        # Real-time streaming
│   │   ├── incremental_loader.py      # Delta/CDC
│   │   └── orchestrator.py            # Multi-source orchestration
│   ├── query/
│   │   ├── __init__.py
│   │   ├── api_server.py              # REST API
│   │   ├── search_service.py
│   │   └── export_service.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics_collector.py       # Prometheus metrics
│   │   ├── health_checks.py
│   │   └── alerting.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── secrets_manager.py         # AWS Secrets Manager
│   │   ├── auth.py                    # JWT authentication
│   │   └── encryption.py              # Data encryption
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       ├── logging_config.py
│       └── db_manager.py
├── tests/
│   ├── unit/
│   │   ├── test_transformers.py
│   │   ├── test_loaders.py
│   │   └── test_queries.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_api.py
│   └── performance/
│       ├── test_load_performance.py
│       └── test_query_performance.py
├── deployment/
│   ├── scripts/
│       ├── entrypoint.sh
│       └── healthcheck.sh
├── deployment/
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── configmap.yaml
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── scripts/
│       ├── deploy.sh
│       ├── rollback.sh
│       └── health_check.sh
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   │       ├── loading_dashboard.json
│   │       ├── query_dashboard.json
│   │       └── system_dashboard.json
│   └── alerts/
│       └── alert_rules.yml
├── docs/
│   ├── architecture/
│   │   ├── system_architecture.md
│   │   ├── data_flow.md
│   │   └── security_architecture.md
│   ├── operations/
│   │   ├── deployment_guide.md
│   │   ├── monitoring_guide.md
│   │   ├── disaster_recovery.md
│   │   └── runbooks/
│   │       ├── high_cpu.md
│   │       ├── slow_queries.md
│   │       └── data_quality_issues.md
│   └── api/
│       └── api_documentation.md
├── config/
│   ├── dev/
│   │   ├── senzing_config.json
│   │   └── app_config.yaml
│   ├── staging/
│   │   ├── senzing_config.json
│   │   └── app_config.yaml
│   └── prod/
│       ├── senzing_config.json
│       └── app_config.yaml
├── scripts/
│   ├── setup_environment.sh
│   ├── run_tests.sh
│   ├── backup_database.sh
│   └── performance_test.sh
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Continuous Integration
│       ├── cd.yml                     # Continuous Deployment
│       └── security_scan.yml
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
└── README.md                          # This file
```

## Architecture

### System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (ALB)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌────────▼────────┐
│   API Server 1  │            │   API Server 2  │
│   (Container)   │            │   (Container)   │
└────────┬────────┘            └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
              ┌──────────▼──────────┐
              │  Senzing Engine     │
              │  (Embedded)         │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  PostgreSQL RDS     │
              │  (Multi-AZ)         │
              └─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
│  Prometheus + Grafana + CloudWatch + PagerDuty              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```text
Source Systems → ETL/Transform → Senzing Load → PostgreSQL
                                       ↓
                                 Entity Resolution
                                       ↓
                              REST API / Export
                                       ↓
                            Consuming Applications
```

## Module-by-Module Implementation

### Module 2: Define Business Problem

**docs/architecture/system_architecture.md**:

```markdown
# System Architecture

## Business Requirements
- 5M customer records across 6 systems
- Real-time and batch processing
- 99.9% availability
- SOC 2 compliance
- Multi-region deployment

## Technical Requirements
- Throughput: 1000+ records/sec
- Query latency: < 100ms p95
- Data retention: 7 years
- Backup: Daily with 30-day retention
- DR RTO: 4 hours, RPO: 15 minutes
```

### Module 3-5: Data Collection, Quality, Mapping (4-6 hours)

Implement transformers for each source with comprehensive error handling and logging.

### Module 0: SDK Setup (1 hour)

**Production Configuration:**

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:${DB_PASSWORD}@prod-db.region.rds.amazonaws.com:5432/senzing",
    "BACKEND": "HYBRID"
  },
  "HYBRID": {
    "RES_FEAT_EKEY": "REDIS",
    "RES_FEAT_LKEY": "REDIS",
    "RES_FEAT_STAT": "REDIS"
  },
  "REDIS": {
    "CONNECTION": "redis://prod-redis.region.cache.amazonaws.com:6379"
  }
}
```

### Module 6-7: Loading with Orchestration (2-3 hours)

```python
#!/usr/bin/env python3
"""Production-grade multi-source orchestrator with monitoring"""

import json
import time
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from senzing import G2Engine
from prometheus_client import Counter, Histogram, Gauge

# Metrics
records_loaded = Counter('senzing_records_loaded_total', 'Total records loaded', ['data_source'])
load_duration = Histogram('senzing_load_duration_seconds', 'Load duration', ['data_source'])
load_errors = Counter('senzing_load_errors_total', 'Load errors', ['data_source', 'error_type'])
active_loaders = Gauge('senzing_active_loaders', 'Number of active loaders')

class ProductionOrchestrator:
    """Production orchestrator with monitoring, error handling, and recovery"""

    def __init__(self, config_file: str, max_workers: int = 4):
        self.config_file = config_file
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

        with open(config_file) as f:
            self.config = json.load(f)

    def load_source_parallel(self, data_source: str, input_file: str,
                            batch_size: int = 1000) -> Dict:
        """Load source with batching and error recovery"""

        engine = G2Engine()
        engine.init(f"Loader-{data_source}", json.dumps(self.config), False)

        active_loaders.inc()

        try:
            start_time = time.time()
            success_count = 0
            error_count = 0
            batch = []

            with open(input_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line)
                        batch.append(record)

                        if len(batch) >= batch_size:
                            # Process batch
                            for rec in batch:
                                try:
                                    engine.addRecord(
                                        data_source,
                                        rec['RECORD_ID'],
                                        json.dumps(rec)
                                    )
                                    success_count += 1
                                    records_loaded.labels(data_source=data_source).inc()
                                except Exception as e:
                                    error_count += 1
                                    load_errors.labels(
                                        data_source=data_source,
                                        error_type=type(e).__name__
                                    ).inc()
                                    self.logger.error(f"Error loading {rec['RECORD_ID']}: {e}")

                            batch = []

                            if line_num % 10000 == 0:
                                self.logger.info(f"{data_source}: Loaded {line_num:,} records")

                    except json.JSONDecodeError as e:
                        error_count += 1
                        self.logger.error(f"JSON error on line {line_num}: {e}")

                # Process remaining batch
                for rec in batch:
                    try:
                        engine.addRecord(data_source, rec['RECORD_ID'], json.dumps(rec))
                        success_count += 1
                        records_loaded.labels(data_source=data_source).inc()
                    except Exception as e:
                        error_count += 1
                        load_errors.labels(
                            data_source=data_source,
                            error_type=type(e).__name__
                        ).inc()

            duration = time.time() - start_time
            load_duration.labels(data_source=data_source).observe(duration)

            return {
                'data_source': data_source,
                'success': success_count,
                'errors': error_count,
                'duration': duration,
                'rate': success_count / duration if duration > 0 else 0
            }

        finally:
            engine.destroy()
            active_loaders.dec()

    def load_all_parallel(self, sources: List[tuple]) -> List[Dict]:
        """Load all sources in parallel"""

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.load_source_parallel, ds, file): ds
                for ds, file in sources
            }

            for future in as_completed(futures):
                data_source = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"✅ {data_source} completed: {result['success']:,} records")
                except Exception as e:
                    self.logger.error(f"❌ {data_source} failed: {e}")
                    results.append({
                        'data_source': data_source,
                        'success': 0,
                        'errors': -1,
                        'error': str(e)
                    })

        return results

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Start metrics server
    from prometheus_client import start_http_server
    start_http_server(8000)

    # Load all sources
    orchestrator = ProductionOrchestrator('config/prod/senzing_config.json', max_workers=6)

    sources = [
        ('CRM', 'data/transformed/crm.jsonl'),
        ('ERP', 'data/transformed/erp.jsonl'),
        ('WEB', 'data/transformed/web.jsonl'),
        ('MOBILE', 'data/transformed/mobile.jsonl'),
        ('PARTNER', 'data/transformed/partner.jsonl'),
        ('LEGACY', 'data/transformed/legacy.jsonl')
    ]

    results = orchestrator.load_all_parallel(sources)

    # Print summary
    total_success = sum(r['success'] for r in results)
    total_errors = sum(r['errors'] for r in results if r['errors'] > 0)

    print(f"\n{'='*60}")
    print(f"PRODUCTION LOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total Records: {total_success:,}")
    print(f"Total Errors: {total_errors:,}")
    print(f"Success Rate: {(total_success/(total_success+total_errors)*100):.2f}%")
```

### Module 8: Query with REST API (2 hours)

**src/query/api_server.py**:

```python
#!/usr/bin/env python3
"""Production REST API with authentication and monitoring"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json
import jwt
from senzing import G2Engine
from prometheus_client import Counter, Histogram
import time

app = FastAPI(title="Senzing MDM API", version="1.0.0")
security = HTTPBearer()

# Metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
api_duration = Histogram('api_duration_seconds', 'API request duration', ['endpoint'])
api_errors = Counter('api_errors_total', 'API errors', ['endpoint', 'error_type'])

# Initialize Senzing
with open('config/prod/senzing_config.json') as f:
    config = json.load(f)

engine = G2Engine()
engine.init("APIServer", json.dumps(config), False)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class SearchRequest(BaseModel):
    name: str
    email: str = None
    phone: str = None

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/entity/{entity_id}")
def get_entity(entity_id: int, user=Depends(verify_token)):
    """Get entity by ID"""
    api_requests.labels(endpoint='/entity', method='GET').inc()

    start = time.time()
    try:
        entity_json = engine.getEntityByEntityID(entity_id)
        api_duration.labels(endpoint='/entity').observe(time.time() - start)
        return json.loads(entity_json)
    except Exception as e:
        api_errors.labels(endpoint='/entity', error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search_entities(request: SearchRequest, user=Depends(verify_token)):
    """Search for entities"""
    api_requests.labels(endpoint='/search', method='POST').inc()

    start = time.time()
    try:
        search_json = json.dumps({
            "NAME_FULL": request.name,
            "EMAIL_ADDRESS": request.email,
            "PHONE_NUMBER": request.phone
        })

        result_json = engine.searchByAttributes(search_json)
        api_duration.labels(endpoint='/search').observe(time.time() - start)
        return json.loads(result_json)
    except Exception as e:
        api_errors.labels(endpoint='/search', error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Module 9: Performance Testing (1-2 hours)

**tests/performance/test_load_performance.py**:

```python
#!/usr/bin/env python3
"""Performance benchmarking suite"""

import time
import json
from senzing import G2Engine

def benchmark_loading(sample_size=10000):
    """Benchmark loading performance"""

    with open('config/prod/senzing_config.json') as f:
        config = json.load(f)

    engine = G2Engine()
    engine.init("Benchmark", json.dumps(config), False)

    start = time.time()

    for i in range(sample_size):
        record = {
            "DATA_SOURCE": "BENCHMARK",
            "RECORD_ID": f"BENCH-{i:06d}",
            "PRIMARY_NAME_FULL": f"Test Person {i}",
            "EMAIL_ADDRESS": f"test{i}@example.com"
        }
        engine.addRecord("BENCHMARK", record['RECORD_ID'], json.dumps(record))

    duration = time.time() - start
    rate = sample_size / duration

    print(f"Loaded {sample_size:,} records in {duration:.1f} seconds")
    print(f"Rate: {rate:.1f} records/second")

    engine.destroy()

    return rate

if __name__ == '__main__':
    rate = benchmark_loading(10000)

    # Assert performance requirements
    assert rate > 1000, f"Performance below threshold: {rate:.1f} < 1000 records/sec"
    print("✅ Performance test PASSED")
```

### Module 10: Security Hardening (1-2 hours)

**src/security/secrets_manager.py**:

```python
#!/usr/bin/env python3
"""AWS Secrets Manager integration"""

import boto3
import json
from typing import Dict

class SecretsManager:
    """Manage secrets from AWS Secrets Manager"""

    def __init__(self, region='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region)

    def get_secret(self, secret_name: str) -> Dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            raise Exception(f"Failed to retrieve secret {secret_name}: {e}")

    def get_database_credentials(self) -> Dict:
        """Get database credentials"""
        return self.get_secret('prod/senzing/database')

    def get_api_keys(self) -> Dict:
        """Get API keys"""
        return self.get_secret('prod/senzing/api-keys')

# Usage
secrets = SecretsManager()
db_creds = secrets.get_database_credentials()
```

### Module 11: Monitoring (1-2 hours)

**monitoring/grafana/dashboards/loading_dashboard.json**:

```json
{
  "dashboard": {
    "title": "Senzing Loading Dashboard",
    "panels": [
      {
        "title": "Records Loaded per Second",
        "targets": [
          {
            "expr": "rate(senzing_records_loaded_total[5m])"
          }
        ]
      },
      {
        "title": "Load Errors",
        "targets": [
          {
            "expr": "rate(senzing_load_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Active Loaders",
        "targets": [
          {
            "expr": "senzing_active_loaders"
          }
        ]
      }
    ]
  }
}
```

### Module 12: Deployment (2-3 hours)

**deployment/kubernetes/deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: senzing-api
  labels:
    app: senzing-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: senzing-api
  template:
    metadata:
      labels:
        app: senzing-api
    spec:
      containers:
      - name: api
        image: company/senzing-api:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: CONFIG_FILE
          value: /config/senzing_config.json
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: senzing-secrets
              key: db-password
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

**deployment/scripts/deploy.sh**:

```bash
#!/bin/bash
# Production deployment script

set -e

ENVIRONMENT=${1:-prod}
VERSION=${2:-latest}

echo "Deploying Senzing MDM to $ENVIRONMENT (version: $VERSION)"

# Run tests
echo "Running tests..."
pytest tests/ -v

# Package application
echo "Packaging application..."
python setup.py sdist bdist_wheel

# Deploy to target environment
echo "Deploying version $VERSION..."

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f deployment/kubernetes/

# Wait for rollout
echo "Waiting for rollout..."
kubectl rollout status deployment/senzing-api

# Run smoke tests
echo "Running smoke tests..."
./deployment/scripts/health_check.sh

echo "✅ Deployment complete!"
```

## Expected Results

### Performance Metrics

- Loading: 1200+ records/sec
- Query latency: 50ms p95, 80ms p99
- API throughput: 500+ requests/sec
- Uptime: 99.95%

### Business Metrics

- 5M records processed in 90 minutes
- 3.8M unique entities (24% reduction)
- 1.2M cross-source matches
- 99.2% data quality score

## Key Learnings

1. **Scalability:** Horizontal scaling with load balancers
2. **Reliability:** Multi-AZ deployment, automated failover
3. **Security:** Secrets management, encryption, authentication
4. **Observability:** Comprehensive monitoring and alerting
5. **Automation:** CI/CD pipeline, automated testing

## Production Checklist

- [ ] All tests passing (unit, integration, performance)
- [ ] Security scan completed
- [ ] Secrets configured in AWS Secrets Manager
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Disaster recovery tested
- [ ] Documentation complete
- [ ] Runbooks created
- [ ] On-call rotation established
- [ ] Stakeholder sign-off

## Troubleshooting

See `docs/operations/runbooks/` for detailed troubleshooting guides.

## Related Documentation

- [POWER.md](../../POWER.md) - Boot camp overview
- [MODULE_12_DEPLOYMENT_PACKAGING.md](../../docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md)
- [multi-source-project](../multi-source-project/README.md) - Simpler multi-source example

## Version History

- **v1.0.0** (2026-03-17): Initial production deployment example created
