# Design Document

## Overview

This feature creates a performance baselines reference guide for the Senzing Bootcamp Power. The guide provides users with expected throughput, hardware requirements, database comparisons, and scaling recommendations across three data volume tiers. Two existing files are updated to reference the new guide.

## Architecture

### Files Created

1. `senzing-bootcamp/docs/guides/PERFORMANCE_BASELINES.md` — The main performance baselines guide

### Files Modified

1. `senzing-bootcamp/steering/module-09-performance.md` — Add reference to the baselines guide in Step 1
2. `senzing-bootcamp/docs/guides/README.md` — Add entry for the new guide in Reference Documentation section

### Document Structure

The `PERFORMANCE_BASELINES.md` guide follows this structure:

```
# Performance Baselines Guide
## Overview
## Important Disclaimers
## Data Volume Tiers
## Transformation Throughput Baselines (table per tier)
## Loading Throughput Baselines (tables: SQLite and PostgreSQL per tier, wall-clock estimates)
## Query Response Time Baselines (tables: by query type, by database, per tier)
## Hardware Requirements (table: minimum and recommended per tier)
## SQLite vs PostgreSQL Comparison (comparison table, migration guidance)
## Scaling Recommendations (multi-threading, database tuning, redo processing)
## Related Documentation
```

### Data Volume Tier Definitions

| Tier   | Record Count | Typical Use Case          |
|--------|-------------|---------------------------|
| Small  | <1K         | Bootcamp demos, learning  |
| Medium | 1K-100K     | Pilot projects, POCs      |
| Large  | 100K+       | Production workloads      |

### Baseline Data Approach

All throughput and latency numbers are presented as ranges (not exact values) with clear disclaimers that actual performance depends on hardware, Senzing version, data complexity, and configuration. The guide directs users to use MCP `search_docs` for the most current benchmarks, consistent with the existing Module 9 documentation approach.

## Correctness Properties

### Property 1: Guide contains all three data volume tiers

Verify that `PERFORMANCE_BASELINES.md` contains sections or table rows for small (<1K), medium (1K-100K), and large (100K+) data volume tiers.

Derived from: Requirements 1 (AC 1), 2 (AC 1), 3 (AC 1), 4 (AC 1)

### Property 2: Guide contains separate SQLite and PostgreSQL data

Verify that `PERFORMANCE_BASELINES.md` presents loading and query baselines separately for SQLite and PostgreSQL backends.

Derived from: Requirements 2 (AC 2), 3 (AC 3), 5 (AC 1)

### Property 3: Hardware recommendations include CPU, RAM, and disk

Verify that the hardware requirements section specifies CPU cores, RAM, and disk type for each tier.

Derived from: Requirement 4 (AC 2)

### Property 4: SQLite vs PostgreSQL comparison section exists with required dimensions

Verify that a dedicated comparison section covers throughput, concurrency, scalability limits, use cases, and migration guidance.

Derived from: Requirement 5 (AC 1, 2, 3)

### Property 5: Scaling section covers multi-threading, tuning, and redo processing

Verify that the scaling recommendations section addresses multi-threading, database tuning parameters, and redo processing.

Derived from: Requirement 6 (AC 2, 3, 4)

### Property 6: Module 9 steering references the guide in Step 1

Verify that `module-09-performance.md` contains a reference to `PERFORMANCE_BASELINES.md` within the Step 1 section.

Derived from: Requirement 7 (AC 1, 2)

### Property 7: Guides README lists the performance baselines guide in Reference Documentation

Verify that `README.md` contains an entry for `PERFORMANCE_BASELINES.md` in the Reference Documentation section.

Derived from: Requirement 8 (AC 1, 2)
