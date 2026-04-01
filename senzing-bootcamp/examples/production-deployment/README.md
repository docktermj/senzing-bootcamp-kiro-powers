# Production Deployment Example: Enterprise Customer MDM

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, data flow, and expected results. The actual source code files are generated during the boot camp using MCP tools (`generate_scaffold`, `mapping_workflow`) in your chosen programming language (Python, Java, C#, Rust, or TypeScript).

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
├── database/                          # PostgreSQL used in production
├── src/
│   ├── transform/                     # One transformer per source (6 total)
│   ├── load/
│   │   ├── batch_loader               # Batch loading
│   │   ├── streaming_loader           # Real-time streaming
│   │   ├── incremental_loader         # Delta/CDC
│   │   └── orchestrator               # Multi-source orchestration
│   ├── query/
│   │   ├── api_server                 # REST API
│   │   ├── search_service             # Entity search
│   │   └── export_service             # Data export
│   ├── monitoring/
│   │   ├── metrics_collector          # Prometheus metrics
│   │   ├── health_checks              # Liveness/readiness
│   │   └── alerting                   # Alert rules
│   ├── security/
│   │   ├── secrets_manager            # AWS Secrets Manager
│   │   ├── auth                       # JWT authentication
│   │   └── encryption                 # Data encryption
│   └── utils/                         # Config, logging, DB management
├── tests/
│   ├── unit/                          # Transformer, loader, query tests
│   ├── integration/                   # End-to-end, API tests
│   └── performance/                   # Load and query benchmarks
├── deployment/
│   ├── kubernetes/                    # K8s manifests (deployment, service, ingress)
│   ├── terraform/                     # Infrastructure as code
│   └── scripts/                       # Deploy, rollback, health check scripts
├── monitoring/
│   ├── prometheus/                    # Metrics collection config
│   ├── grafana/dashboards/            # Loading, query, system dashboards
│   └── alerts/                        # Alert rules
├── docs/
│   ├── architecture/                  # System, data flow, security docs
│   ├── operations/                    # Deployment, monitoring, DR, runbooks
│   └── api/                           # API documentation
├── config/
│   ├── dev/                           # Development config
│   ├── staging/                       # Staging config
│   └── prod/                          # Production config
├── scripts/                           # Setup, test, backup, perf scripts
├── .github/workflows/                 # CI/CD and security scan pipelines
├── .env.example
├── .gitignore
├── <language-specific dependency file> # e.g. requirements.txt, pom.xml, etc.
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

Document system architecture requirements including:

- 5M customer records across 6 systems
- Real-time and batch processing
- 99.9% availability, SOC 2 compliance
- Throughput: 1000+ records/sec, query latency < 100ms p95
- DR targets: RTO 4 hours, RPO 15 minutes

### Module 3-5: Data Collection, Quality, Mapping (4-6 hours)

Implement transformers for each of the 6 sources (CRM, ERP, Web, Mobile, Partner, Legacy) with comprehensive error handling and logging. Each transformer maps source-specific fields to Senzing attributes.

> The agent generates this code in your chosen language using `generate_scaffold` and `mapping_workflow` during the bootcamp.

### Module 0: SDK Setup (1 hour)

Configure the Senzing engine for production with PostgreSQL (Multi-AZ RDS) and optional Redis caching for high-throughput scenarios. Use environment-specific config files under `config/dev/`, `config/staging/`, and `config/prod/`.

### Module 6-7: Loading with Orchestration (2-3 hours)

The production orchestrator loads all 6 sources in parallel with:

- **Parallel loading** using a configurable thread pool (default: 6 workers)
- **Batch processing** (configurable batch size, default: 1000 records)
- **Prometheus metrics** — records loaded, load duration, errors, active loaders
- **Error recovery** — per-record error handling with logging, no batch-level failures
- **Progress reporting** — periodic log output every 10,000 records per source

Data sources loaded: CRM, ERP, Web, Mobile, Partner, Legacy.

Run the loading program using the appropriate command for your chosen language.

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

### Module 8: Query with REST API (2 hours)

The REST API provides:

- `GET /health` — health check endpoint
- `GET /entity/{entity_id}` — get entity by ID (JWT-authenticated)
- `POST /search` — search by name, email, phone (JWT-authenticated)
- Prometheus metrics on every endpoint (request count, duration, errors)

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

### Module 9: Performance Testing (1-2 hours)

Benchmark loading and query performance against production targets:

- Loading: target 1000+ records/sec
- Query: target < 100ms p95 latency

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

### Module 10: Security Hardening (1-2 hours)

Implement secrets management (e.g., AWS Secrets Manager), JWT authentication for API endpoints, and data encryption. No credentials stored in code or config files.

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

### Module 11: Monitoring (1-2 hours)

Set up Grafana dashboards tracking:

- Records loaded per second
- Load error rates
- Active loader count
- API request rates and latency
- System resource utilization

Configure alert rules for error rate spikes, slow queries, and resource exhaustion.

### Module 12: Deployment (2-3 hours)

Deploy using Kubernetes with:

- 3 API server replicas behind a load balancer
- Resource requests/limits (2-4 GB memory, 1-2 CPU per pod)
- Liveness and readiness probes on `/health`
- Secrets injected via Kubernetes secrets
- CI/CD pipeline (test → build → deploy → smoke test)
- Rollback scripts for failed deployments

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

## What You'll Learn

1. **Scalability:** Horizontal scaling with load balancers
2. **Reliability:** Multi-AZ deployment, automated failover
3. **Security:** Secrets management, encryption, authentication
4. **Observability:** Comprehensive monitoring and alerting
5. **Automation:** CI/CD pipeline, automated testing

## Production Checklist

- [ ] All tests passing (unit, integration, performance)
- [ ] Security scan completed
- [ ] Secrets configured in secrets manager
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