# Module Documentation Index

This directory contains detailed documentation for each bootcamp module.

## Available Modules

### Module 1: Understand Business Problem

**File**: [MODULE_1_BUSINESS_PROBLEM.md](MODULE_1_BUSINESS_PROBLEM.md)

**Purpose**: Define the business problem that entity resolution will solve

**Key Topics**:

- Problem definition and scoping
- Design pattern selection (10 patterns available)
- Success criteria definition
- Stakeholder identification

**When to Use**: Starting point for all projects

---

### Module 2: Set Up SDK

**File**: [MODULE_2_SDK_SETUP.md](MODULE_2_SDK_SETUP.md)

**Purpose**: Install and configure the Senzing SDK natively on your machine

**Key Topics**:

- Platform-specific installation
- Database configuration (SQLite or PostgreSQL)
- Installation verification
- Project directory structure creation

**When to Use**: First technical module — start here

---

### Module 3: Quick Demo (Optional)

**File**: [MODULE_3_QUICK_DEMO.md](MODULE_3_QUICK_DEMO.md)

**Purpose**: See Senzing entity resolution in action with sample data

**Key Topics**:

- Sample dataset selection (Las Vegas, London, Moscow)
- Live SDK demo with real entity resolution
- Match explanations and confidence scores
- Before/after comparison

**When to Use**: Optional — for first-time users who want to see ER working

---

### Module 4: Data Collection Policy

**File**: [MODULE_4_DATA_COLLECTION.md](MODULE_4_DATA_COLLECTION.md)

**Purpose**: Collect data from identified sources and store in project structure

**Key Topics**:

- Data source collection strategies
- File organization in `data/raw/`
- Data lineage tracking
- Sample data creation
- Documentation requirements

**When to Use**: After Module 1 (business problem defined)

---

### Module 5: Data Quality & Mapping

**File**: [MODULE_5_DATA_QUALITY_AND_MAPPING.md](MODULE_5_DATA_QUALITY_AND_MAPPING.md)

**Purpose**: Automated quality assessment and data mapping into Senzing format

**Key Topics**:

- Completeness scoring (0-100)
- Consistency analysis
- Validity checks
- Uniqueness metrics
- HTML dashboard generation
- Quality recommendations
- Senzing Entity Specification (SGES) format
- Interactive mapping workflow via MCP
- Transformation program creation
- Data quality validation with `analyze_record`
- Transformation lineage tracking

**When to Use**: After Module 4 (data collected)

---

### Module 6: Load Data

**File**: [MODULE_6_LOAD_DATA.md](MODULE_6_LOAD_DATA.md)

**Purpose**: Load all data sources, process redo records, and validate entity resolution results

**Key Topics**:

- Loading program creation
- Sequential source loading
- Redo queue processing
- Single-source and cross-source validation
- Multi-source orchestration (conditional)
- Error handling and recovery
- UAT and stakeholder sign-off

**When to Use**: After Module 2 (SDK installed) and Module 5 (data mapped)

---

### Module 7: Query and Visualize

**File**: [MODULE_7_QUERY_VALIDATION.md](MODULE_7_QUERY_VALIDATION.md)

**Purpose**: Create query programs, overlap reports, and visualizations

**Key Topics**:

- Query program development
- Search program creation
- Overlap report generation
- Entity visualization
- Query specifications documentation

**When to Use**: After Module 6 (all sources loaded)

---

### Module 8: Performance Testing and Benchmarking

**File**: [MODULE_8_PERFORMANCE_TESTING.md](MODULE_8_PERFORMANCE_TESTING.md)

**Purpose**: Benchmark and optimize for production performance

**Key Topics**:

- Transformation benchmarks
- Loading performance testing
- Query response time testing
- Concurrent user testing
- Resource profiling
- Scalability testing
- Performance report generation

**When to Use**: After Module 7 (queries working)

---

### Module 9: Security Hardening

**File**: [MODULE_9_SECURITY_HARDENING.md](MODULE_9_SECURITY_HARDENING.md)

**Purpose**: Implement production-grade security measures

**Key Topics**:

- Secrets management (AWS, Azure, env vars)
- API authentication (API keys, JWT)
- Role-based access control (RBAC)
- Encryption (at rest and in transit)
- PII handling and access logging
- Security scanning (safety, bandit, trivy)
- Security audit documentation

**When to Use**: After Module 8 (performance validated)

---

### Module 10: Monitoring and Observability

**File**: [MODULE_10_MONITORING_OBSERVABILITY.md](MODULE_10_MONITORING_OBSERVABILITY.md)

**Purpose**: Set up comprehensive monitoring for production operations

**Key Topics**:

- Monitoring stack selection (Prometheus/Grafana, ELK, Cloud, APM)
- Metrics collection
- Structured logging
- Distributed tracing
- Health check endpoints
- Alerting rules
- Monitoring dashboards
- Runbook creation

**When to Use**: After Module 9 (security hardened)

---

### Module 11: Package and Deploy

**File**: [MODULE_11_DEPLOYMENT_PACKAGING.md](MODULE_11_DEPLOYMENT_PACKAGING.md)

**Purpose**: Package code and deploy to production

**Key Topics**:

- Code refactoring into production structure
- Comprehensive test suite
- Language-specific packaging (pip, Maven, NuGet, Cargo)
- Deployment documentation
- Deployment artifacts (CI/CD, Kubernetes)
- Production validation
- Integration with Modules 8, 9, 10

**When to Use**: After Module 10 (monitoring configured)

---

## Module Dependencies

```text
Module 1 → Module 4 → Module 5
                         ↓
Module 2 ──────────→ Module 6 (requires Module 2 + Module 5)
                         ↓
                    Module 7
                         ↓
                    Module 8 (for production)
                         ↓
                    Module 9 (for production)
                         ↓
                    Module 10 (for production)
                         ↓
                    Module 11 (for production)
```

## Quick Reference

| Module | Required For           |
|--------|------------------------|
| 1      | All projects           |
| 2      | All projects           |
| 3      | Optional               |
| 4      | All projects           |
| 5      | All projects           |
| 6      | All projects           |
| 7      | All projects           |
| 8      | Production deployments |
| 9      | Production deployments |
| 10     | Production deployments |
| 11     | Production deployments |

## Related Documentation

- **Main Guide**: `../../POWER.md`
- **Workflows**: `../../steering/module-*.md` (per-module steering files)
- **Policies**: `../policies/`
- **Guides**: `../guides/`

## Navigation

- [← Back to docs/](../)
- [→ Policies](../policies/)
- [→ Guides](../guides/)
