```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 7: MULTI-SOURCE ORCHESTRATION  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

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

## Validation Phase

After all sources are loaded and orchestration is complete, validate the cross-source entity resolution results. This is the comprehensive validation phase — multi-source loading is where cross-source matching happens, so this is where you confirm match accuracy across all sources, run full UAT with business users, and obtain stakeholder sign-off.

### Cross-Source Match Accuracy

With multiple sources loaded, verify that records from different sources are resolving correctly:

1. **Sample cross-source entities** — Pick 15–25 entities that contain records from multiple data sources and verify they represent the same real-world person or organization
2. **Check cross-source matches** — Review entities where Senzing matched records across different sources (e.g., a CRM customer matched to an ERP vendor)
3. **Check single-source entities** — Spot-check entities that only contain records from one source to confirm no cross-source matches were missed

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> to generate code that retrieves cross-source entities for review. Use
> `get_sdk_reference(topic='functions', filter='why_entities', version='current')` to explain
> why records from different sources matched.

### False Positive / False Negative Review

- **False positives** — Records from different sources that matched but should not have (different people merged into one entity). Pay special attention to cross-source merges where matching evidence may be weaker.
- **False negatives** — Records from different sources that should have matched but did not (same person appears as separate entities across sources). Search for known cross-source duplicates to confirm they resolved together.

### Full UAT with Business Users

Create and execute User Acceptance Testing with business stakeholders:

1. **Define UAT test cases** — Create test cases based on the business problem (Module 1) that verify cross-source resolution meets business requirements
2. **Execute UAT tests** — Run each test case and document pass/fail results
3. **Review failures** — For any failing test cases, determine if the issue is data quality, matching configuration, or expected behavior
4. **Iterate if needed** — If critical test cases fail, adjust data quality or matching configuration and re-run

Document UAT results:

```markdown
# UAT Results - Multi-Source Validation

**Date:** 2026-03-17
**Sources Validated:** CUSTOMERS_CRM, VENDORS_ERP, PRODUCTS_CATALOG

## Test Case Results

| Test Case | Description | Result | Notes |
|-----------|-------------|--------|-------|
| TC-001 | Known customer-vendor matches resolve | ✅ Pass | 15/15 matched |
| TC-002 | Distinct people stay separate | ✅ Pass | Spot-checked 20 |
| TC-003 | Cross-source duplicates found | ✅ Pass | 342 cross-source merges |
| TC-004 | No false merges on common names | ⚠️ Review | 2 borderline cases |

## Summary

- **Total Test Cases:** 12
- **Passed:** 10
- **Failed:** 0
- **Needs Review:** 2
- **UAT Pass Rate:** 83% (10/12 clear pass)
```

Save this in `docs/uat_results.md`.

### Stakeholder Sign-Off

After UAT is complete and issues are resolved:

1. **Prepare summary** — Create a stakeholder summary showing entity resolution results, match accuracy, and UAT outcomes
2. **Review with stakeholders** — Walk through results with business users and data stewards
3. **Obtain sign-off** — Get formal acknowledgment that results meet business requirements
4. **Document sign-off** — Record who signed off, when, and any conditions or caveats

```markdown
# Stakeholder Sign-Off

**Date:** 2026-03-17
**Project:** [Project Name]

## Resolution Summary

- **Total Records:** 62,500 (across 3 sources)
- **Total Entities:** 58,200
- **Cross-Source Matches:** 4,300
- **UAT Pass Rate:** 100% (after issue resolution)

## Sign-Off

- [ ] Business owner confirms results meet requirements
- [ ] Data steward confirms match accuracy is acceptable
- [ ] Technical lead confirms system is ready for query development

## Conditions

(Document any conditions or caveats noted during sign-off)
```

Save this in `docs/uat_signoff.md`.

### Results Validation Summary

Document the overall validation findings:

```markdown
# Results Validation - Multi-Source

**Date:** 2026-03-17
**Sources:** CUSTOMERS_CRM, VENDORS_ERP, PRODUCTS_CATALOG

## Cross-Source Match Accuracy

- **Entities Sampled:** 25
- **Correct Cross-Source Matches:** 23
- **False Positives Found:** 2
- **False Negatives Found:** 0

## UAT Summary

- **Test Cases Executed:** 12
- **Pass Rate:** 100% (after iteration)
- **Issues Found and Resolved:** 2

## Stakeholder Sign-Off

- **Status:** Complete
- **Date:** 2026-03-17

## Disposition

- [ ] Cross-source match accuracy acceptable
- [ ] False positives documented and reviewed
- [ ] False negatives checked
- [ ] UAT complete with acceptable pass rate
- [ ] Stakeholder sign-off obtained
```

Save this in `docs/results_validation.md`.

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
- [ ] Cross-source match accuracy reviewed
- [ ] False positives and false negatives reviewed
- [ ] UAT test cases created and executed
- [ ] All critical UAT tests pass
- [ ] Issues documented and resolved
- [ ] Stakeholder sign-off obtained
- [ ] Results validation documented

## Success Indicators

Module 7 is complete when:

- All data sources loaded successfully
- Dependencies respected
- Error handling working
- Progress tracking functional
- Multi-source dashboard generated
- Loading statistics documented
- Cross-source match accuracy validated
- UAT completed with acceptable pass rate
- Stakeholder sign-off obtained
- Results validation documented and approved

## Output Files

- `src/orchestration/load_all_sources.[ext]` - Orchestration script
- `docs/orchestration_strategy.md` - Strategy documentation
- `docs/multi_source_dashboard.html` - Progress dashboard
- `logs/orchestration.log` - Loading logs
- `docs/uat_test_cases.md` - UAT test cases for cross-source validation
- `docs/uat_results.md` - UAT execution results
- `docs/uat_signoff.md` - Stakeholder sign-off documentation
- `docs/results_validation.md` - Cross-source match accuracy and validation results

## Related Documentation

- `POWER.md` - Module 7 overview
- `steering/module-07-multi-source.md` - Module 7 workflow
- `MODULE_6_SINGLE_SOURCE_LOADING.md` - Single source loading

## Version History

- **v3.0.0** (2026-03-17): Module 7 created for multi-source orchestration
- **v4.0.0** (2026-04-17): Renumbered from Module 7 to Module 7 (merge of old Modules 4+5)
