# Module Documentation Index

This directory contains detailed documentation for each boot camp module.

## Available Modules

### Module 2: Data Collection

**File**: [MODULE_2_DATA_COLLECTION.md](MODULE_2_DATA_COLLECTION.md)

**Purpose**: Collect data from identified sources and store in project structure

**Key Topics**:

- Data source collection strategies
- File organization in `data/raw/`
- Data lineage tracking
- Sample data creation
- Documentation requirements

**When to Use**: After Module 1 (business problem defined)

---

### Module 3: Data Quality Scoring

**File**: [MODULE_3_DATA_QUALITY_SCORING.md](MODULE_3_DATA_QUALITY_SCORING.md)

**Purpose**: Automated quality assessment before mapping

**Key Topics**:

- Completeness scoring (0-100)
- Consistency analysis
- Validity checks
- Uniqueness metrics
- HTML dashboard generation
- Quality recommendations

**When to Use**: After Module 2 (data collected)

---

### Module 6: Single Source Loading

**File**: [MODULE_6_SINGLE_SOURCE_LOADING.md](MODULE_6_SINGLE_SOURCE_LOADING.md)

**Purpose**: Load one data source and verify results

**Key Topics**:

- Loading program creation
- Incremental loading patterns
- Delta/CDC strategies
- Progress tracking
- Statistics generation
- Backup procedures

**When to Use**: After Module 5 (SDK installed)

---

### Module 7: Multi-Source Orchestration

**File**: [MODULE_7_MULTI_SOURCE_ORCHESTRATION.md](MODULE_7_MULTI_SOURCE_ORCHESTRATION.md)

**Purpose**: Orchestrate loading of multiple data sources with dependencies

**Key Topics**:

- Dependency management
- Load order optimization
- Parallel vs sequential loading
- Error handling per source
- Progress tracking across sources
- Multi-source validation

**When to Use**: After Module 6 (first source loaded successfully)

---

### Module 8: Query and Validation

**File**: [MODULE_8_QUERY_VALIDATION.md](MODULE_8_QUERY_VALIDATION.md)

**Purpose**: Create query programs and conduct user acceptance testing

**Key Topics**:

- Query program development
- UAT framework implementation
- Test case creation
- Issue tracking and resolution
- Stakeholder sign-off procedures
- Query specifications documentation

**When to Use**: After Module 7 (all sources loaded)

---

### Module 9: Performance Testing

**File**: [MODULE_9_PERFORMANCE_TESTING.md](MODULE_9_PERFORMANCE_TESTING.md)

**Purpose**: Benchmark and optimize for production performance

**Key Topics**:

- Transformation benchmarks
- Loading performance testing
- Query response time testing
- Concurrent user testing
- Resource profiling
- Scalability testing
- Performance report generation

**When to Use**: After Module 8 (queries working)

---

### Module 10: Security Hardening

**File**: [MODULE_10_SECURITY_HARDENING.md](MODULE_10_SECURITY_HARDENING.md)

**Purpose**: Implement production-grade security measures

**Key Topics**:

- Secrets management (AWS, Azure, env vars)
- API authentication (API keys, JWT)
- Role-based access control (RBAC)
- Encryption (at rest and in transit)
- PII handling and access logging
- Security scanning (safety, bandit, trivy)
- Security audit documentation

**When to Use**: After Module 9 (performance validated)

---

### Module 11: Monitoring and Observability

**File**: [MODULE_11_MONITORING_OBSERVABILITY.md](MODULE_11_MONITORING_OBSERVABILITY.md)

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

**When to Use**: After Module 10 (security hardened)

---

### Module 12: Package and Deploy

**File**: [MODULE_12_DEPLOYMENT_PACKAGING.md](MODULE_12_DEPLOYMENT_PACKAGING.md)

**Purpose**: Package code and deploy to production

**Key Topics**:

- Code refactoring into production structure
- Comprehensive test suite
- Language-specific packaging (pip, Maven, NuGet, Cargo)
- Deployment documentation
- Deployment artifacts (CI/CD, Kubernetes)
- Production validation
- Integration with Modules 9, 10, 11

**When to Use**: After Module 11 (monitoring configured)

---

## Module Dependencies

```text
Module 2 → Module 3 → Module 4 → Module 5 → Module 6
                                              ↓
                                         Module 7 (if multiple sources)
                                              ↓
                                         Module 8
                                              ↓
                                         Module 9 (for production)
                                              ↓
                                         Module 10 (for production)
                                              ↓
                                         Module 11 (for production)
                                              ↓
                                         Module 12 (for production)
```

## Quick Reference

| Module | Time             | Required For           |
|--------|------------------|------------------------|
| 2      | 10-15 min/source | All projects           |
| 3      | 15-20 min/source | All projects           |
| 6      | 30 min/source    | All projects           |
| 7      | 1-2 hours        | Multi-source projects  |
| 8      | 1-2 hours        | All projects           |
| 9      | 1-2 hours        | Production deployments |
| 10     | 1-2 hours        | Production deployments |
| 11     | 1-2 hours        | Production deployments |
| 12     | 2-3 hours        | Production deployments |

## Related Documentation

- **Main Guide**: `../../POWER.md`
- **Workflows**: `../../steering/module-*.md` (per-module steering files)
- **Policies**: `../policies/`
- **Guides**: `../guides/`

## Navigation

- [← Back to docs/](../)
- [→ Policies](../policies/)
- [→ Guides](../guides/)
- [→ Development](../development/)
