# Requirements Document

## Introduction

The Senzing Bootcamp Power lacks reference performance baselines for different data volumes. Users starting Module 9 (Performance Testing) have no way to estimate expected throughput, resource requirements, or time commitments before running their own benchmarks. This feature adds a comprehensive performance baselines guide documenting typical throughput for transformation, loading, and querying at small (<1K), medium (1K-100K), and large (100K+) data volumes, including hardware requirements, SQLite vs PostgreSQL comparison, and scaling recommendations.

## Glossary

- **Performance_Baselines_Guide**: The markdown document at `senzing-bootcamp/docs/guides/PERFORMANCE_BASELINES.md` that provides reference benchmarks and resource estimates for Senzing entity resolution workloads
- **Throughput**: The number of records processed per second during transformation, loading, or querying operations
- **Data_Volume_Tier**: A classification of dataset size — small (<1K records), medium (1K-100K records), or large (100K+ records)
- **Module_9_Steering**: The agent steering file at `senzing-bootcamp/steering/module-09-performance.md` that guides agents through the performance testing module
- **Guides_README**: The index document at `senzing-bootcamp/docs/guides/README.md` that lists all available guides

## Requirements

### Requirement 1: Transformation Throughput Baselines

**User Story:** As a bootcamp user, I want to see typical transformation throughput at different data volumes, so that I can estimate how long data transformation will take for my dataset.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL document typical transformation throughput ranges in records per second for each Data_Volume_Tier (small, medium, large)
2. WHEN a user reads the transformation baselines section, THE Performance_Baselines_Guide SHALL present the data in a table format with columns for data volume tier, record count range, and expected throughput range
3. THE Performance_Baselines_Guide SHALL include a note that actual performance varies by hardware, data complexity, and transformation logic

### Requirement 2: Loading Throughput Baselines

**User Story:** As a bootcamp user, I want to see typical Senzing loading throughput at different data volumes, so that I can plan loading time for my entity resolution project.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL document typical loading throughput ranges in records per second for each Data_Volume_Tier
2. THE Performance_Baselines_Guide SHALL present loading baselines separately for SQLite and PostgreSQL database backends
3. THE Performance_Baselines_Guide SHALL include estimated wall-clock time for loading at each Data_Volume_Tier

### Requirement 3: Query Response Time Baselines

**User Story:** As a bootcamp user, I want to see typical query response times at different data volumes, so that I can set realistic latency expectations.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL document typical query response times (average and P95) for each Data_Volume_Tier
2. THE Performance_Baselines_Guide SHALL present query baselines for common query types: search by attributes, get entity by ID, and get entity by record
3. THE Performance_Baselines_Guide SHALL present query baselines separately for SQLite and PostgreSQL database backends

### Requirement 4: Hardware Requirements by Data Volume

**User Story:** As a bootcamp user, I want to know the recommended hardware for different data volumes, so that I can provision appropriate resources.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL document minimum and recommended hardware specifications for each Data_Volume_Tier
2. THE Performance_Baselines_Guide SHALL specify CPU cores, RAM, and disk type for each hardware recommendation
3. THE Performance_Baselines_Guide SHALL indicate which Data_Volume_Tiers are suitable for SQLite and which require PostgreSQL

### Requirement 5: SQLite vs PostgreSQL Comparison

**User Story:** As a bootcamp user, I want to understand the performance differences between SQLite and PostgreSQL, so that I can choose the right database for my workload.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL include a dedicated comparison section for SQLite and PostgreSQL
2. THE Performance_Baselines_Guide SHALL compare throughput, concurrency support, scalability limits, and recommended use cases for each database
3. THE Performance_Baselines_Guide SHALL provide a clear recommendation on when to migrate from SQLite to PostgreSQL based on data volume and concurrency needs

### Requirement 6: Scaling Recommendations

**User Story:** As a bootcamp user, I want scaling guidance for growing datasets, so that I can plan for production workloads beyond bootcamp volumes.

#### Acceptance Criteria

1. THE Performance_Baselines_Guide SHALL include scaling recommendations for datasets exceeding 100K records
2. THE Performance_Baselines_Guide SHALL document multi-threading recommendations for loading at scale
3. THE Performance_Baselines_Guide SHALL document database tuning parameters that improve performance at each Data_Volume_Tier
4. THE Performance_Baselines_Guide SHALL include guidance on redo processing for large-scale loads

### Requirement 7: Module 9 Steering Reference

**User Story:** As a bootcamp agent, I want the Module 9 steering file to reference the performance baselines guide, so that users are directed to baseline data before running their own benchmarks.

#### Acceptance Criteria

1. WHEN a user begins Module 9, THE Module_9_Steering SHALL reference the Performance_Baselines_Guide so users can review expected baselines before benchmarking
2. THE Module_9_Steering SHALL add the reference in the performance requirements step (Step 1) where users define their targets

### Requirement 8: Guides README Update

**User Story:** As a bootcamp user, I want the guides README to list the performance baselines guide, so that I can discover it when browsing available guides.

#### Acceptance Criteria

1. THE Guides_README SHALL include an entry for the Performance_Baselines_Guide with a brief description
2. THE Guides_README SHALL place the Performance_Baselines_Guide entry in the Reference Documentation section alongside other reference guides
