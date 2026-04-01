# Module 7: Multi-Source Orchestration

> **Agent workflow:** The agent follows `steering/module-07-multi-source.md` for this module's step-by-step workflow.

## Overview

Module 7 focuses on orchestrating the loading of multiple data sources with proper dependency management, load order optimization, and error handling.

## Purpose

After successfully loading a single data source in Module 6, Module 7 helps you:

1. **Manage dependencies** between data sources
2. **Optimize load order** for efficiency
3. **Implement parallel loading** strategies
4. **Handle errors** across multiple sources
5. **Track progress** for all sources
6. **Generate multi-source dashboard**

## When to Use This Module

- You have 2+ data sources to load
- Data sources have dependencies (e.g., customers before orders)
- You want to optimize loading performance
- You need coordinated error handling

**Skip this module if:** You only have one data source

## Key Concepts

### Load Order Optimization

Determine the optimal order to load sources:

```text
Priority 1: Reference data (countries, states, products)
Priority 2: Master data (customers, vendors, employees)
Priority 3: Transactional data (orders, claims, transactions)
Priority 4: Derived data (aggregations, summaries)
```

### Dependency Management

Track dependencies between sources:

```yaml
dependencies:
  orders:
    requires: [customers, products]
  shipments:
    requires: [orders]
  returns:
    requires: [orders, shipments]
```

### Parallel Loading

Load independent sources concurrently using your language's concurrency primitives (threads, async, goroutines, coroutines, etc.):

```text
Sequential (slow):
  load_source("customers")   -- 10 minutes
  load_source("vendors")     -- 10 minutes
  Total: 20 minutes

Parallel (fast):
  Start concurrent tasks:
    task 1: load_source("customers")
    task 2: load_source("vendors")
  Wait for all tasks to complete
  Total: 10 minutes
```

### Error Handling Strategies

1. **Fail Fast:** Stop all loading on first error
2. **Continue on Error:** Log errors, continue with other sources
3. **Retry with Backoff:** Retry failed sources with exponential backoff
4. **Partial Success:** Mark successful sources, retry only failed ones

## Orchestration Patterns

### Pattern 1: Sequential Loading

Simple, predictable, but slow:

```text
sources = ["customers", "vendors", "products", "orders"]
For each source in sources:
    load_source(source)
```

### Pattern 2: Parallel Loading (Independent Sources)

Fast for independent sources:

```text
independent_sources = ["customers", "vendors", "products"]
Run all of the following concurrently (up to 3 workers):
    For each source in independent_sources:
        load_source(source)
Wait for all to complete
```

### Pattern 3: Dependency-Aware Loading

Respects dependencies:

```text
Function load_with_dependencies(source, dependencies, loaded_set):
    For each dep in dependencies[source]:
        If dep is NOT in loaded_set:
            load_with_dependencies(dep, dependencies, loaded_set)

    load_source(source)
    Add source to loaded_set
```

### Pattern 4: Pipeline Loading

Streaming pipeline for large datasets:

```text
Producer-consumer pattern using a thread-safe queue:

Producer (one per source):
    For each record in source:
        transformed = transform(record)
        Put transformed record onto queue

Consumer (one or more):
    Loop:
        Take record from queue
        If record is a stop signal, exit loop
        load_record(record)
```

## Multi-Source Dashboard

Track progress across all sources:

```text
╔══════════════════════════════════════════════════════════╗
║           MULTI-SOURCE LOADING DASHBOARD                 ║
╠══════════════════════════════════════════════════════════╣
║ Source      │ Status    │ Progress │ Records │ Errors   ║
╠═════════════╪═══════════╪══════════╪═════════╪══════════╣
║ customers   │ ✅ Done   │ 100%     │ 50,000  │ 0        ║
║ vendors     │ ✅ Done   │ 100%     │ 2,500   │ 0        ║
║ products    │ 🔄 Loading│  67%     │ 33,500  │ 12       ║
║ orders      │ ⏸️ Waiting│   0%     │ 0       │ 0        ║
║ shipments   │ ⏸️ Waiting│   0%     │ 0       │ 0        ║
╚═════════════╧═══════════╧══════════╧═════════╧══════════╝

Total: 86,000 / 250,000 records (34%)
Estimated completion: 15 minutes
```

## Orchestrator Design

The orchestrator is responsible for coordinating the loading of all data sources. Rather than prescribing a specific implementation, here is what the orchestrator must do:

### Inputs

- **Source list:** An ordered list of data source names to load (e.g., `["customers", "vendors", "products", "orders"]`)
- **Dependency map:** A mapping from each source to its prerequisite sources (e.g., `orders` depends on `["customers", "products"]`)
- **Strategy:** One of `sequential`, `parallel`, or `dependency-aware`

### Internal State

- **loaded:** Set of sources that have been successfully loaded
- **failed:** Set of sources that failed to load
- **stats:** Per-source statistics (status, duration, record count, error message)

### Algorithm

```text
Function load_all(strategy):
    If strategy is "sequential":
        For each source in source_list:
            load_source(source)

    If strategy is "parallel":
        Run all sources concurrently (limit concurrency to ~4 workers)
        For each completed task:
            If it failed, log the error and add source to failed set

    If strategy is "dependency-aware":
        For each source in source_list:
            Recursively ensure all dependencies are loaded first
            Then load the source

Function load_source(source):
    Log "Loading source: <source>"
    Record start time
    Try:
        Load all records from source using the Senzing SDK
        Record duration and record count in stats
        Add source to loaded set
        Log success with duration
    On error:
        Log failure with error message
        Add source to failed set
        Record error in stats

Function print_summary():
    Print total sources, loaded count, failed count
    For each loaded source: print name, record count, duration
    For each failed source: print name and error message
```

### Outputs

- Console log of per-source load status (success/failure, duration, record count)
- A summary report showing total sources, successes, failures, and per-source statistics

### Configuration

```yaml
sources:
  - customers
  - vendors
  - products
  - orders
dependencies:
  orders: [customers, products]
strategy: dependency-aware
```

> **Agent instruction:** Use `generate_scaffold` with the bootcamper's chosen language and `find_examples(query='multi-source')` to generate orchestration code.

## Agent Behavior

When a user is in Module 7, the agent should:

1. **Identify all data sources** from previous modules
2. **Determine dependencies** between sources
3. **Recommend load order** based on dependencies
4. **Generate orchestration script** in `src/orchestration/`
5. **Configure parallel loading** if sources are independent
6. **Set up error handling** strategy
7. **Create progress dashboard**
8. **Test orchestration** with small samples first
9. **Document orchestration** in `docs/orchestration_strategy.md`

## Validation Gates

Before completing Module 7:

- [ ] All data sources identified
- [ ] Dependencies documented
- [ ] Load order determined
- [ ] Orchestration script created
- [ ] Error handling configured
- [ ] Progress tracking implemented
- [ ] Tested with sample data
- [ ] All sources loaded successfully

## Success Indicators

Module 7 is complete when:

- All data sources loaded successfully
- Dependencies respected
- Error handling working
- Progress tracking functional
- Multi-source dashboard generated
- Loading statistics documented

## Output Files

- `src/orchestration/load_all_sources.[ext]` - Orchestration script
- `docs/orchestration_strategy.md` - Strategy documentation
- `docs/multi_source_dashboard.html` - Progress dashboard
- `logs/orchestration.log` - Loading logs

## Related Documentation

- `POWER.md` - Module 7 overview
- `steering/module-07-multi-source.md` - Module 7 workflow
- `MODULE_6_SINGLE_SOURCE_LOADING.md` - Single source loading

## Version History

- **v3.0.0** (2026-03-17): Module 7 created for multi-source orchestration
