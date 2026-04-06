---
inclusion: manual
---

# Module 11: Monitoring and Observability

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_11_MONITORING_OBSERVABILITY.md`.

## Workflow: Production Monitoring and Observability (Module 11)

Use this workflow to set up comprehensive monitoring, structured logging, dashboards, alerting, and health checks for a production Senzing entity resolution deployment. This module covers both general infrastructure monitoring and Senzing-specific observability patterns.

**Important**: Monitoring is not a one-time setup. As the system evolves — new data sources, changing volumes, configuration tuning — monitoring must evolve with it. Encourage the user to revisit and refine their monitoring setup as their deployment matures.

**Language**: Use the bootcamper's chosen programming language from the language selection step. All code generation, scaffold calls, and examples in this module must use that language. Reference it as `<chosen_language>` throughout.

**Prerequisites**:

- ✅ Module 10 complete (security hardened)
- ✅ Data loaded and entity resolution running (Modules 6-7 complete)
- ✅ Query and validation complete (Module 8 complete)
- ✅ Production environment identified or planned

**Before starting**: Confirm the user's deployment context. Monitoring choices depend heavily on environment:

- Cloud provider (AWS, Azure, GCP) or on-premises
- Container orchestration (Kubernetes, ECS, bare metal)
- Existing monitoring infrastructure (Prometheus, Datadog, CloudWatch, etc.)
- Team size and on-call structure

---

## Step 1: Assess Current Monitoring Landscape

Ask: "What monitoring tools and infrastructure do you already have in place? For example: Prometheus + Grafana, CloudWatch, Datadog, ELK stack, or nothing yet?"

WAIT for response.

Ask: "How is your Senzing deployment structured? Single process, multi-process, containerized, or serverless?"

WAIT for response.

Based on the user's answers, determine the monitoring stack. Common stacks:

- **Open source**: Prometheus + Grafana + Loki (logs) + Jaeger (traces)
- **AWS**: CloudWatch Metrics + CloudWatch Logs + X-Ray
- **Azure**: Azure Monitor + Application Insights + Log Analytics
- **GCP**: Cloud Monitoring + Cloud Logging + Cloud Trace
- **Commercial**: Datadog, New Relic, Dynatrace, Splunk

> **Agent instruction:** Call `search_docs(query='monitoring', version='current')` to retrieve
> Senzing-specific monitoring guidance. This provides context on what Senzing exposes natively
> and what you need to instrument yourself.

Document the chosen stack in `docs/monitoring_guide.md` before proceeding.

---

## Step 2: Implement Senzing-Specific Metrics Collection

This is the most critical step. Senzing provides engine-level statistics through the `get_stats()` method, but understanding its behavior is essential.

> **Agent instruction:** Call `get_sdk_reference(topic='functions', filter='get_stats', version='current')`
> to get the exact method signature and return format for the stats method. Do not guess the
> method name or response schema — it varies between V3 and V4.
> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='information', version='current')`
> to get version-correct code for retrieving engine statistics. Use this as the foundation for
> the metrics collector, not hand-coded SDK calls.

### Understanding `get_stats()` Behavior

Explain to the user:

- `get_stats()` returns per-process workload statistics since the last call
- Stats reset after each call — they are delta values, not cumulative totals
- Each Senzing engine instance (process) has its own stats — in multi-process deployments, you must collect from every process and aggregate
- Stats include: records added, entities created, redo records generated, and timing breakdowns

Ask: "How many Senzing engine processes will you run in production? This affects how we aggregate stats."

WAIT for response.

### Key Senzing Metrics to Track

Create `src/monitoring/metrics_collector.[ext]` using the scaffold output. The collector must track these metrics:

```text
Define the following metrics using your monitoring library
(e.g., Prometheus client, Micrometer, OpenTelemetry, CloudWatch SDK):

COUNTERS (monotonically increasing):
  - "senzing_records_loaded_total"
      Labels: data_source, process_id
      Description: Total records successfully loaded into Senzing

  - "senzing_records_failed_total"
      Labels: data_source, error_type, process_id
      Description: Total records that failed to load

  - "senzing_entities_created_total"
      Labels: process_id
      Description: Total new entities created by resolution

  - "senzing_redo_records_generated_total"
      Labels: process_id
      Description: Total redo records generated (deferred re-evaluation)

  - "senzing_redo_records_processed_total"
      Labels: process_id
      Description: Total redo records processed

HISTOGRAMS (distribution of values):
  - "senzing_add_record_duration_seconds"
      Labels: data_source
      Description: Time to add a single record (includes resolution)
      Buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0

  - "senzing_query_duration_seconds"
      Labels: query_type (search, get_entity, why_entity, how_entity)
      Description: Time to execute a query
      Buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0

GAUGES (point-in-time values):
  - "senzing_redo_queue_depth"
      Description: Current number of unprocessed redo records

  - "senzing_active_loaders"
      Description: Number of currently active loading processes

  - "senzing_entity_count"
      Description: Current total number of resolved entities

  - "senzing_throughput_records_per_second"
      Labels: process_id
      Description: Current loading throughput per process

DERIVED METRICS (calculated from the above):
  - Error rate = senzing_records_failed_total / senzing_records_loaded_total
  - Resolution ratio = senzing_entities_created_total / senzing_records_loaded_total
  - Redo backlog growth = redo_generated - redo_processed over time window
```

### Stats Collection Loop

```text
Create a background stats collection function that runs on a timer:

function collect_senzing_stats(engine, interval_seconds = 30):
    loop forever:
        sleep(interval_seconds)

        raw_stats = engine.get_stats()
        parsed = parse_stats_json(raw_stats)

        // Update counters with delta values from get_stats()
        senzing_records_loaded_total.increment(parsed.addedRecords)
        senzing_records_failed_total.increment(parsed.failedRecords)

        // Update gauges with current values
        senzing_throughput_records_per_second.set(
            parsed.addedRecords / interval_seconds
        )

        // Query redo queue depth separately
        redo_depth = get_redo_queue_depth(engine)
        senzing_redo_queue_depth.set(redo_depth)

        // Log stats summary at INFO level
        log.info("Senzing stats collected",
            records_added=parsed.addedRecords,
            throughput=parsed.addedRecords / interval_seconds,
            redo_depth=redo_depth
        )
```

**Save**: `src/monitoring/metrics_collector.[ext]`

---

## Step 3: Implement Structured Logging

Structured logging is essential for production troubleshooting. Every log entry must be machine-parseable (JSON) and include correlation IDs for tracing operations across components.

Ask: "Do you have a centralized log aggregation system (e.g., ELK, Loki, CloudWatch Logs, Splunk)? This determines the log output format."

WAIT for response.

### Log Format and Levels

Create `src/monitoring/logging_config.[ext]`:

```text
Create a JSON log formatter that outputs each log entry as a structured object:

Required fields for EVERY log entry:
  - "timestamp":      ISO 8601 format with timezone (e.g., 2026-01-15T14:30:00.123Z)
  - "level":          Log severity: DEBUG, INFO, WARN, ERROR, FATAL
  - "message":        Human-readable description of the event
  - "service":        Service name (e.g., "senzing-loader", "senzing-query-api")
  - "process_id":     OS process ID
  - "correlation_id": Unique ID that ties related operations together

Optional contextual fields (add when available):
  - "data_source":    The Senzing DATA_SOURCE being processed
  - "record_id":      The RECORD_ID being processed
  - "entity_id":      The resolved entity ID
  - "duration_ms":    Operation duration in milliseconds
  - "error_code":     Senzing error code (if applicable)
  - "error_message":  Full error text (if applicable)
  - "batch_id":       Batch identifier for bulk operations
  - "user_id":        User who initiated the operation (for query APIs)

Configure the application logger to:
  1. Use JSON format for all output
  2. Set default level to INFO for production
  3. Set DEBUG level for development/troubleshooting
  4. Route ERROR and FATAL to stderr
  5. Route INFO and below to stdout
  6. Include stack traces for ERROR and FATAL entries
```

### What to Log at Each Level

```text
DEBUG (development and troubleshooting only):
  - Individual record processing details
  - SDK method call parameters and responses
  - Feature comparison details during resolution
  - Database query execution plans

INFO (normal production operations):
  - Service startup and shutdown
  - Batch loading started/completed with summary stats
  - Stats collection results (periodic)
  - Configuration changes applied
  - Redo processing cycles started/completed
  - Health check results

WARN (potential issues that don't stop processing):
  - Record load failures for individual records (with record_id)
  - Redo queue depth exceeding threshold
  - Slow queries exceeding latency threshold
  - Disk space below warning threshold
  - Database connection pool near capacity

ERROR (failures requiring attention):
  - Batch loading failures
  - Database connection failures
  - Senzing engine initialization failures
  - Unhandled exceptions in processing loops
  - Authentication/authorization failures

FATAL (system cannot continue):
  - Senzing engine cannot initialize
  - Database unreachable after retries
  - Out of memory
  - Disk full
```

### Logging During Loading Operations

```text
When loading records, log at these points:

BATCH START (INFO):
  log.info("Batch loading started",
      data_source="CUSTOMERS",
      batch_id="batch-2026-01-15-001",
      total_records=50000,
      correlation_id=generate_uuid()
  )

PROGRESS (INFO, every N records or every M seconds):
  log.info("Loading progress",
      data_source="CUSTOMERS",
      batch_id="batch-2026-01-15-001",
      records_processed=10000,
      records_failed=12,
      elapsed_seconds=45,
      throughput_rps=222,
      correlation_id=correlation_id
  )

RECORD FAILURE (WARN):
  log.warn("Record load failed",
      data_source="CUSTOMERS",
      record_id="CUST-99421",
      error_code="SENZ-0023",
      error_message="Invalid name format",
      correlation_id=correlation_id
  )

BATCH COMPLETE (INFO):
  log.info("Batch loading completed",
      data_source="CUSTOMERS",
      batch_id="batch-2026-01-15-001",
      total_records=50000,
      records_loaded=49988,
      records_failed=12,
      elapsed_seconds=225,
      throughput_rps=222,
      error_rate=0.00024,
      correlation_id=correlation_id
  )
```

### Logging During Query Operations

```text
For query/search API endpoints, log:

QUERY START (DEBUG):
  log.debug("Query started",
      query_type="search_by_attributes",
      user_id="api-user-42",
      correlation_id=request_correlation_id
  )

QUERY COMPLETE (INFO):
  log.info("Query completed",
      query_type="search_by_attributes",
      user_id="api-user-42",
      duration_ms=87,
      results_count=3,
      correlation_id=request_correlation_id
  )

SLOW QUERY (WARN):
  log.warn("Slow query detected",
      query_type="search_by_attributes",
      user_id="api-user-42",
      duration_ms=3500,
      threshold_ms=1000,
      correlation_id=request_correlation_id
  )
```

**Save**: `src/monitoring/logging_config.[ext]`

---

## Step 4: Create Monitoring Dashboards

Dashboards provide at-a-glance visibility into system health and performance. The specific implementation depends on the monitoring stack chosen in Step 1, but the panels and queries are universal.

> **Agent instruction:** Call `reporting_guide(topic='dashboard', language='<chosen_language>')` to get
> visualization concepts, recommended chart types, and data source patterns for Senzing dashboards.
> **Agent instruction:** Call `reporting_guide(topic='reports')` to get SQL analytics queries that
> power dashboard panels. These queries run against the Senzing database and provide entity-level
> aggregate metrics.

Ask: "Which dashboard tool are you using? Grafana, CloudWatch Dashboards, Azure Dashboards, Datadog, or something else?"

WAIT for response.

### Dashboard 1: Loading Operations (`monitoring/dashboards/loading_dashboard.[ext]`)

Create a dashboard with these panels:

```text
Panel 1: Loading Throughput Over Time
  Type: Time series line chart
  Query: rate(senzing_records_loaded_total[5m]) by data_source
  Purpose: Shows records/second over time, broken down by data source
  Alert threshold line: Draw horizontal line at expected minimum throughput

Panel 2: Cumulative Records Loaded
  Type: Stat panel or counter
  Query: sum(senzing_records_loaded_total) by data_source
  Purpose: Total records loaded per data source since deployment

Panel 3: Error Rate
  Type: Time series line chart with threshold
  Query: rate(senzing_records_failed_total[5m]) / rate(senzing_records_loaded_total[5m])
  Purpose: Percentage of records failing, should stay below 1%
  Threshold: Red line at 1%, orange line at 0.5%

Panel 4: Load Duration Distribution
  Type: Heatmap or histogram
  Query: histogram_quantile(0.50, senzing_add_record_duration_seconds)
         histogram_quantile(0.95, senzing_add_record_duration_seconds)
         histogram_quantile(0.99, senzing_add_record_duration_seconds)
  Purpose: Shows p50, p95, p99 latency for record loading

Panel 5: Active Loaders
  Type: Gauge
  Query: senzing_active_loaders
  Purpose: How many loading processes are currently running

Panel 6: Failed Records Table
  Type: Table (last 50 failures)
  Query: Log query for level=WARN AND message="Record load failed"
  Columns: timestamp, data_source, record_id, error_code, error_message
  Purpose: Quick view of recent failures for investigation
```

### Dashboard 2: Entity Resolution Health (`monitoring/dashboards/resolution_dashboard.[ext]`)

```text
Panel 1: Entity Count Growth Over Time
  Type: Time series line chart
  Query: senzing_entity_count over time
  Purpose: Shows how entity count grows as records are loaded
  Insight: Flattening curve means more records are matching existing entities

Panel 2: Resolution Ratio
  Type: Time series line chart
  Query: senzing_entities_created_total / senzing_records_loaded_total
  Purpose: Ratio of entities to records — lower means more deduplication
  Insight: A ratio of 0.6 means 40% of records matched existing entities

Panel 3: Cross-Source Overlap
  Type: Bar chart or Sankey diagram
  Query: SQL query from reporting_guide — count entities with records from multiple sources
  Purpose: Shows how many entities span multiple data sources
  Insight: High overlap validates that cross-source matching is working

Panel 4: Redo Queue Depth
  Type: Time series with threshold
  Query: senzing_redo_queue_depth
  Purpose: Unprocessed redo records — should trend toward zero
  Threshold: Warning at 1000, critical at 10000

Panel 5: Redo Processing Rate
  Type: Time series line chart
  Query: rate(senzing_redo_records_processed_total[5m])
  Purpose: How fast redo records are being consumed
  Insight: Should exceed generation rate to prevent backlog growth
```

### Dashboard 3: Query Performance (`monitoring/dashboards/query_dashboard.[ext]`)

```text
Panel 1: Query Latency Percentiles
  Type: Time series with multiple lines
  Query: histogram_quantile(0.50, senzing_query_duration_seconds)
         histogram_quantile(0.95, senzing_query_duration_seconds)
         histogram_quantile(0.99, senzing_query_duration_seconds)
  Purpose: p50, p95, p99 query latency over time

Panel 2: Query Volume
  Type: Time series bar chart
  Query: rate(senzing_query_total[5m]) by query_type
  Purpose: Queries per second by type (search, get_entity, why, how)

Panel 3: Query Error Rate
  Type: Stat panel
  Query: rate(senzing_query_errors_total[5m]) / rate(senzing_query_total[5m])
  Purpose: Percentage of queries failing

Panel 4: Slow Queries Log
  Type: Table
  Query: Log query for level=WARN AND message="Slow query detected"
  Columns: timestamp, query_type, duration_ms, user_id
  Purpose: Identify slow query patterns
```

### Dashboard 4: System Resources (`monitoring/dashboards/system_dashboard.[ext]`)

```text
Panel 1: CPU Usage
  Type: Time series line chart
  Query: System CPU utilization per process/container
  Threshold: Warning at 80%, critical at 95%

Panel 2: Memory Usage
  Type: Time series line chart
  Query: System memory utilization
  Threshold: Warning at 85%, critical at 95%

Panel 3: Disk Usage
  Type: Gauge
  Query: Disk utilization for database volume
  Threshold: Warning at 75%, critical at 90%

Panel 4: Database Connections
  Type: Time series line chart
  Query: Active database connections vs. pool maximum
  Purpose: Detect connection pool exhaustion

Panel 5: Database Size Growth
  Type: Time series line chart
  Query: Database size in GB over time
  Purpose: Capacity planning — predict when disk will fill
```

Save dashboard definitions in `monitoring/dashboards/` using the format appropriate for the chosen tool (JSON for Grafana, YAML for others, or infrastructure-as-code templates).

---

## Step 5: Configure Alerting Rules

Alerts must be actionable. Every alert should have a clear threshold, a defined severity, and a runbook that tells the on-call engineer exactly what to do.

Ask: "How does your team handle alerts? PagerDuty, OpsGenie, Slack, email, or another system?"

WAIT for response.

Ask: "Who should be notified for critical vs. warning alerts? Is there an on-call rotation?"

WAIT for response.

### Alert Definitions

Create `monitoring/alerts/alert_rules.[ext]` (YAML for Prometheus, JSON for CloudWatch, etc.):

```text
CRITICAL ALERTS (page on-call immediately, requires response within 15 minutes):

  Alert: SenzingEngineDown
    Condition: Senzing engine health check fails for > 2 minutes
    Threshold: health_check_senzing == false for 2m
    Runbook: docs/runbooks/engine_down.md
    Action: Check engine logs, verify database connectivity, restart engine

  Alert: DatabaseUnreachable
    Condition: Database connection fails for > 1 minute
    Threshold: health_check_database == false for 1m
    Runbook: docs/runbooks/database_down.md
    Action: Check database status, verify network, check connection pool

  Alert: HighErrorRate
    Condition: Record loading error rate exceeds 5%
    Threshold: error_rate > 0.05 for 5m
    Runbook: docs/runbooks/high_error_rate.md
    Action: Check recent record failures, identify bad data source, pause loading

  Alert: DiskSpaceCritical
    Condition: Database disk usage exceeds 90%
    Threshold: disk_usage_percent > 90
    Runbook: docs/runbooks/disk_space.md
    Action: Expand storage, archive old data, check for runaway growth

WARNING ALERTS (investigate within 1 hour, Slack/email notification):

  Alert: RedoQueueBacklog
    Condition: Redo queue depth exceeds 10,000 and growing
    Threshold: senzing_redo_queue_depth > 10000 AND
               delta(senzing_redo_queue_depth[10m]) > 0
    Runbook: docs/runbooks/redo_backlog.md
    Action: Scale up redo processors, check for resolution loops

  Alert: SlowQueryLatency
    Condition: p95 query latency exceeds 2 seconds
    Threshold: histogram_quantile(0.95, senzing_query_duration_seconds) > 2.0 for 10m
    Runbook: docs/runbooks/slow_queries.md
    Action: Check database performance, review query patterns, check for table bloat

  Alert: LoadingThroughputDrop
    Condition: Loading throughput drops below 50% of baseline
    Threshold: rate(senzing_records_loaded_total[5m]) < (baseline_rps * 0.5) for 10m
    Runbook: docs/runbooks/throughput_drop.md
    Action: Check for resource contention, database locks, network issues

  Alert: HighMemoryUsage
    Condition: Memory usage exceeds 85%
    Threshold: memory_usage_percent > 85 for 10m
    Runbook: docs/runbooks/high_memory.md
    Action: Check for memory leaks, review Senzing engine configuration

  Alert: DiskSpaceWarning
    Condition: Database disk usage exceeds 75%
    Threshold: disk_usage_percent > 75
    Runbook: docs/runbooks/disk_space.md
    Action: Plan capacity expansion, review data retention

INFORMATIONAL ALERTS (logged, reviewed daily):

  Alert: LoadingBatchCompleted
    Condition: A batch loading job finishes
    Threshold: Event-based (log pattern match)
    Action: Review batch summary stats, check error count

  Alert: RedoProcessingComplete
    Condition: Redo queue reaches zero
    Threshold: senzing_redo_queue_depth == 0
    Action: Log completion, update status dashboard
```

### Escalation Path

```text
Define escalation for unacknowledged alerts:

  Level 1 (0-15 min):  Primary on-call engineer
  Level 2 (15-30 min): Secondary on-call engineer
  Level 3 (30-60 min): Team lead / engineering manager
  Level 4 (60+ min):   VP Engineering / incident commander

For Senzing-specific issues:
  - Check Senzing documentation first: search_docs(query='error troubleshooting')
  - Use explain_error_code() for Senzing error codes
  - Escalate to Senzing support if engine-level issues persist
```

**Save**: `monitoring/alerts/alert_rules.[ext]`

---

## Step 6: Implement Health Checks

Health checks serve two purposes: automated orchestration (Kubernetes liveness/readiness probes, load balancer health checks) and manual verification during incidents.

Create `src/monitoring/health_checks.[ext]`:

```text
function check_database_health():
    // Verify database connectivity and basic query execution
    try:
        connect to database
        execute simple query (e.g., SELECT 1 or SELECT count(*) FROM sys_cfg)
        measure response time
        return {
            "status": "healthy",
            "response_time_ms": measured_time,
            "connection_pool_active": active_connections,
            "connection_pool_max": max_connections
        }
    catch exception:
        return {
            "status": "unhealthy",
            "error": exception.message
        }

function check_senzing_engine_health():
    // Verify Senzing engine is responsive
    try:
        stats = engine.get_stats()
        parse stats to verify valid JSON response
        return {
            "status": "healthy",
            "stats_available": true,
            "last_stats": summary of parsed stats
        }
    catch exception:
        return {
            "status": "unhealthy",
            "error": exception.message
        }

function check_disk_space():
    // Check available disk space on database volume
    usage = get_disk_usage(database_volume_path)
    return {
        "status": "healthy" if usage.percent < 75 else
                  "warning" if usage.percent < 90 else
                  "unhealthy",
        "used_percent": usage.percent,
        "free_gb": usage.free / (1024^3),
        "total_gb": usage.total / (1024^3)
    }

function check_redo_queue():
    // Check redo queue depth and trend
    depth = get_redo_queue_depth(engine)
    return {
        "status": "healthy" if depth < 1000 else
                  "warning" if depth < 10000 else
                  "unhealthy",
        "queue_depth": depth,
        "threshold_warning": 1000,
        "threshold_critical": 10000
    }

function comprehensive_health_check():
    results = {
        "timestamp": current_time_iso8601(),
        "service": "senzing-entity-resolution",
        "checks": {
            "database": check_database_health(),
            "senzing_engine": check_senzing_engine_health(),
            "disk_space": check_disk_space(),
            "redo_queue": check_redo_queue()
        }
    }

    // Overall status is the worst status of any check
    statuses = [check.status for check in results.checks.values()]
    if "unhealthy" in statuses:
        results.overall_status = "unhealthy"
    else if "warning" in statuses:
        results.overall_status = "warning"
    else:
        results.overall_status = "healthy"

    return results

// If running as an HTTP service, expose endpoints:
//   GET /health        → comprehensive_health_check()
//   GET /health/live   → { "status": "alive" }  (process is running)
//   GET /health/ready  → check_database + check_senzing (can accept work)
```

**Save**: `src/monitoring/health_checks.[ext]`

---

## Step 7: Senzing-Specific Monitoring Patterns

This section covers monitoring patterns unique to Senzing entity resolution that generic infrastructure monitoring won't capture.

> **Agent instruction:** Call `reporting_guide(topic='quality')` to get precision/recall monitoring
> patterns, split/merge detection strategies, and review queue approaches. These are essential for
> ongoing entity resolution quality monitoring.

### 7a: Monitoring Entity Count Growth

Entity count growth over time reveals the health of your resolution process:

```text
Track entity count at regular intervals (e.g., hourly):

function track_entity_growth():
    // Query current entity count
    // This can come from get_stats() or a direct database query
    current_count = get_entity_count()
    current_time = now()

    // Store in time series database or log
    emit_metric("senzing_entity_count", current_count, timestamp=current_time)

    // Calculate growth rate
    previous_count = get_previous_entity_count(1_hour_ago)
    growth_rate = (current_count - previous_count) / previous_count

    // Alert on anomalies
    if growth_rate > 0.10:  // More than 10% growth in 1 hour
        log.warn("Unusual entity count growth",
            current=current_count,
            previous=previous_count,
            growth_rate=growth_rate
        )

What to watch for:
  - Steady growth during loading: Normal — new entities being created
  - Flattening curve: Good — more records matching existing entities
  - Sudden spike: Investigate — possible data quality issue or new source with no overlap
  - Sudden drop: CRITICAL — entities being deleted or database issue
```

### 7b: Monitoring Redo Queue Depth

The redo queue contains records that need re-evaluation after new information arrives. A growing redo queue means resolution is falling behind.

```text
function monitor_redo_queue():
    depth = get_redo_queue_depth(engine)

    emit_metric("senzing_redo_queue_depth", depth)

    // Track trend over last 10 minutes
    previous_depth = get_metric_value("senzing_redo_queue_depth", 10_minutes_ago)
    trend = depth - previous_depth

    if depth > 10000 AND trend > 0:
        log.warn("Redo queue growing",
            depth=depth,
            trend=trend,
            action="Consider scaling redo processors"
        )

    if depth == 0:
        log.info("Redo queue empty — resolution is current")

Redo queue health indicators:
  - Depth = 0: Fully caught up, all re-evaluations complete
  - Depth < 1000: Healthy, processing keeping pace
  - Depth 1000-10000: Warning, may need more redo processing capacity
  - Depth > 10000: Critical, redo processing is falling behind
  - Depth growing steadily: Need to scale redo processors
  - Depth shrinking: Redo processing is catching up
```

### 7c: Cross-Source Resolution Metrics

Tracking how records from different data sources resolve together is a key quality indicator.

```text
Periodically run cross-source analysis (e.g., daily):

function analyze_cross_source_resolution():
    // Use SQL analytics from reporting_guide(topic='reports')
    // Count entities that have records from multiple data sources

    results = query_database("""
        Count entities by number of distinct data sources they contain.
        Group into: single-source entities, 2-source, 3-source, etc.
    """)

    emit_metric("senzing_single_source_entities", results.single_source)
    emit_metric("senzing_multi_source_entities", results.multi_source)
    emit_metric("senzing_cross_source_ratio",
        results.multi_source / results.total_entities)

    log.info("Cross-source resolution summary",
        total_entities=results.total_entities,
        single_source=results.single_source,
        multi_source=results.multi_source,
        cross_source_ratio=results.cross_source_ratio
    )

What to watch for:
  - Cross-source ratio increasing: Good — sources are linking together
  - Cross-source ratio near zero: Sources may have no overlap, or matching criteria need tuning
  - Sudden change in ratio: Investigate — data quality issue or configuration change
```

### 7d: Resolution Quality Monitoring

> **Agent instruction:** Call `reporting_guide(topic='quality')` for precision/recall monitoring
> patterns. This provides sampling strategies, split/merge detection, and review queue approaches.

```text
Set up periodic quality sampling:

function sample_resolution_quality(sample_size=100):
    // Randomly sample resolved entities
    sample_entities = get_random_entity_sample(sample_size)

    for each entity in sample_entities:
        record_count = entity.record_count
        source_count = entity.distinct_sources

        // Flag potential issues for human review
        if record_count > 10:
            flag_for_review(entity, reason="Large entity — possible over-matching")

        if record_count == 1 AND expected_overlap:
            flag_for_review(entity, reason="Singleton — possible under-matching")

    // Track review queue metrics
    emit_metric("senzing_review_queue_size", review_queue.size)
    emit_metric("senzing_flagged_over_match", over_match_count)
    emit_metric("senzing_flagged_under_match", under_match_count)

Quality indicators to track over time:
  - Over-matching rate: Entities with too many records (false positives)
  - Under-matching rate: Records that should match but don't (false negatives)
  - Average records per entity: Should stabilize after initial loading
  - Entity size distribution: Most entities should have 1-5 records
```

---

## Step 8: Create Operational Runbooks

Runbooks turn alerts into action. Every alert defined in Step 5 should have a corresponding runbook.

Ask: "Does your team use a specific runbook format or template? Or should I create a standard format?"

WAIT for response.

Create runbooks in `docs/runbooks/`:

```text
Each runbook should follow this structure:

docs/runbooks/[alert_name].md:

  # Runbook: [Alert Name]

  ## Alert Description
  What this alert means and why it fires.

  ## Severity
  Critical / Warning / Informational

  ## Impact
  What is affected if this issue is not resolved.

  ## Diagnosis Steps
  1. Check [specific metric/log/dashboard]
  2. Run [specific command or query]
  3. Look for [specific pattern or symptom]

  ## Resolution Steps
  1. [First action to take]
  2. [Second action to take]
  3. [Escalation if not resolved]

  ## Prevention
  How to prevent this alert from firing in the future.

  ## Related Alerts
  Other alerts that may fire alongside this one.

Create these runbooks:
  - docs/runbooks/engine_down.md
  - docs/runbooks/database_down.md
  - docs/runbooks/high_error_rate.md
  - docs/runbooks/disk_space.md
  - docs/runbooks/redo_backlog.md
  - docs/runbooks/slow_queries.md
  - docs/runbooks/throughput_drop.md
  - docs/runbooks/high_memory.md
```

---

## Step 9: Test the Monitoring Stack

Monitoring that hasn't been tested is monitoring you can't trust. Deliberately trigger each alert to verify the full chain: metric → alert → notification → runbook.

Ask: "Are you ready to test the monitoring setup? We'll intentionally trigger some alerts to verify they work end-to-end."

WAIT for response.

### Test Plan

```text
Test 1: Health Check Verification
  Action: Run comprehensive_health_check() and verify all checks pass
  Expected: All checks return "healthy"
  Verify: Response includes all check components

Test 2: Metrics Collection
  Action: Load 100 test records and verify metrics update
  Expected: senzing_records_loaded_total increases by 100
  Verify: Dashboard panels show the loading activity

Test 3: Error Rate Alert
  Action: Submit 10 intentionally malformed records
  Expected: senzing_records_failed_total increases, error rate alert fires
  Verify: Alert notification received, runbook link included

Test 4: Slow Query Alert (if applicable)
  Action: Execute a complex search query on a large dataset
  Expected: If query exceeds threshold, slow query alert fires
  Verify: Alert includes query details

Test 5: Redo Queue Monitoring
  Action: Load records that trigger redo processing
  Expected: senzing_redo_queue_depth increases, then decreases as redo processes
  Verify: Dashboard shows redo queue activity

Test 6: Health Check Failure
  Action: Temporarily make database unreachable (e.g., wrong connection string)
  Expected: Database health check returns "unhealthy", critical alert fires
  Verify: Alert fires within expected timeframe, runbook is actionable
  Cleanup: Restore correct connection string

Test 7: Log Verification
  Action: Review log output during tests above
  Expected: All log entries are valid JSON with required fields
  Verify: Logs are searchable in aggregation system, correlation IDs link related entries

Test 8: Dashboard Verification
  Action: Review all dashboard panels during and after tests
  Expected: All panels show data, no "no data" panels
  Verify: Time ranges work, drill-down links function
```

Document test results in `docs/monitoring_test_results.md`.

---

## Step 10: Document the Monitoring Setup

Create comprehensive documentation so the operations team can maintain and extend the monitoring.

Create `docs/monitoring_guide.md`:

```text
# Monitoring Guide

## Architecture
  - Monitoring stack: [chosen stack]
  - Metrics endpoint: [URL/port]
  - Dashboard URL: [URL]
  - Alert notification channels: [list]
  - Log aggregation: [system and URL]

## Senzing-Specific Metrics
  - How get_stats() works (per-process, resets after each call)
  - Stats collection interval: [N seconds]
  - Multi-process aggregation approach: [description]

## Dashboards
  - Loading Operations: [URL]
  - Entity Resolution Health: [URL]
  - Query Performance: [URL]
  - System Resources: [URL]

## Alerts
  - Critical alerts: [list with thresholds]
  - Warning alerts: [list with thresholds]
  - Escalation path: [description]
  - On-call schedule: [link]

## Runbooks
  - Location: docs/runbooks/
  - Index: [list of runbooks with descriptions]

## Health Checks
  - Endpoint: [URL]
  - Components checked: database, senzing engine, disk space, redo queue
  - Integration: [Kubernetes probes, load balancer, etc.]

## Maintenance
  - How to add new metrics
  - How to create new dashboard panels
  - How to add new alerts
  - How to update runbooks
```

**Save**: `docs/monitoring_guide.md`

---

## Validation Gates

Before completing Module 11, verify all of the following:

- [ ] Monitoring stack selected and documented
- [ ] Senzing `get_stats()` collection implemented with correct reset-after-read behavior
- [ ] All key metrics defined and being collected (records loaded, entities created, redo depth, error rate, throughput)
- [ ] Structured JSON logging implemented with correlation IDs
- [ ] Loading, resolution, query, and system dashboards created
- [ ] Critical and warning alerts configured with thresholds
- [ ] Health checks implemented (database, engine, disk, redo queue)
- [ ] Runbooks created for every alert
- [ ] Monitoring tested end-to-end (alerts fire, notifications arrive, runbooks are actionable)
- [ ] `docs/monitoring_guide.md` created with complete setup documentation
- [ ] `docs/monitoring_test_results.md` created with test evidence

---

## Agent Behavior

When running Module 11, the agent must:

- **Use MCP tools for all Senzing-specific code**: Call `generate_scaffold` for engine stats code, `get_sdk_reference` for method signatures, and `reporting_guide` for dashboard and quality patterns. Never hand-code SDK method calls.
- **Ask and WAIT at every interaction point**: Do not assume monitoring stack, alert channels, deployment structure, or team preferences. Each "Ask/WAIT" point is mandatory.
- **Generate code in `<chosen_language>`**: All metrics collectors, logging configs, health checks, and monitoring utilities must be in the bootcamper's chosen language.
- **Save files to correct locations**: Source code in `src/monitoring/`, dashboards in `monitoring/dashboards/`, alerts in `monitoring/alerts/`, runbooks in `docs/runbooks/`, documentation in `docs/`.
- **Explain Senzing-specific behavior**: Especially `get_stats()` reset-after-read semantics, redo queue significance, and cross-source resolution metrics. These are not obvious to users coming from other systems.
- **Test everything**: Do not mark the module complete until alerts have been triggered and verified.
- **Connect to business context**: Relate monitoring metrics back to the user's business problem from Module 2. For example, "This cross-source overlap metric shows how well your CRM and billing data are linking together."

---

## Troubleshooting

Common issues during Module 11:

```text
Problem: get_stats() returns empty or zero values
  Cause: Stats reset after each call — if nothing happened between calls, values are zero
  Fix: Ensure stats collection interval is long enough for meaningful activity
  Fix: Verify the engine instance being queried is the one doing work

Problem: Redo queue depth keeps growing
  Cause: Redo processing is not running or is too slow
  Fix: Start a dedicated redo processing loop
  Fix: Scale up redo processing threads/processes
  Reference: search_docs(query='redo processing', version='current')

Problem: Metrics not appearing in dashboard
  Cause: Metrics endpoint not scraped, wrong metric names, or firewall blocking
  Fix: Verify metrics endpoint is accessible from monitoring system
  Fix: Check metric names match exactly between collector and dashboard queries

Problem: Alerts not firing
  Cause: Alert rules not loaded, thresholds too high, or notification channel misconfigured
  Fix: Test with artificially low thresholds first
  Fix: Verify alert manager configuration and notification channel connectivity

Problem: Health check shows "unhealthy" for Senzing engine
  Cause: Engine not initialized, database connection lost, or license expired
  Fix: Check engine initialization logs
  Fix: Verify database connectivity independently
  Reference: explain_error_code() for any Senzing error codes in logs

Problem: Structured logs not parsing in aggregation system
  Cause: Log format doesn't match expected schema, or multiline stack traces break parsing
  Fix: Verify JSON output is valid (no extra newlines within entries)
  Fix: Configure log aggregation to handle multiline patterns for stack traces
```

---

## Transition

When all validation gates are met:

"Module 11 is complete. You now have comprehensive monitoring and observability for your Senzing deployment.

### Module 11 Complete ✅

- ✅ Metrics collection running (Senzing stats + application + system)
- ✅ Structured logging with correlation IDs
- ✅ Dashboards showing real-time operational data
- ✅ Alerts configured with escalation paths
- ✅ Health checks verifying all components
- ✅ Runbooks documented for every alert
- ✅ Monitoring tested end-to-end

**What you can now observe:**

- Loading throughput and error rates in real time
- Entity resolution health (entity growth, redo queue, cross-source overlap)
- Query performance (latency percentiles, error rates)
- System resource utilization and capacity trends

**Common Issues to Watch For:**

- If redo queue grows continuously, scale up redo processing before it impacts resolution quality
- If entity count growth rate changes suddenly, investigate data quality in the most recent source
- If query latency increases over time, check database maintenance (vacuum, reindex)

Ready to move to Module 12 (Deployment) to take this to production?"

---

## Output Files

After completing Module 11, the following files should exist:

- `src/monitoring/metrics_collector.[ext]` — Senzing and application metrics collection
- `src/monitoring/logging_config.[ext]` — Structured JSON logging configuration
- `src/monitoring/health_checks.[ext]` — Comprehensive health check implementation
- `monitoring/dashboards/loading_dashboard.[ext]` — Loading operations dashboard
- `monitoring/dashboards/resolution_dashboard.[ext]` — Entity resolution health dashboard
- `monitoring/dashboards/query_dashboard.[ext]` — Query performance dashboard
- `monitoring/dashboards/system_dashboard.[ext]` — System resources dashboard
- `monitoring/alerts/alert_rules.[ext]` — Alert definitions with thresholds
- `docs/runbooks/engine_down.md` — Runbook for engine failures
- `docs/runbooks/database_down.md` — Runbook for database failures
- `docs/runbooks/high_error_rate.md` — Runbook for high error rates
- `docs/runbooks/disk_space.md` — Runbook for disk space issues
- `docs/runbooks/redo_backlog.md` — Runbook for redo queue backlog
- `docs/runbooks/slow_queries.md` — Runbook for slow queries
- `docs/runbooks/throughput_drop.md` — Runbook for throughput drops
- `docs/runbooks/high_memory.md` — Runbook for high memory usage
- `docs/monitoring_guide.md` — Complete monitoring documentation
- `docs/monitoring_test_results.md` — Test evidence and results

---

## Important Rules for Monitoring

- NEVER hand-code Senzing SDK method calls — use `generate_scaffold` and `get_sdk_reference` for correct method names and signatures.
- NEVER assume `get_stats()` returns cumulative values — stats reset after each call. Always document this for the user.
- ALWAYS use `reporting_guide` for SQL analytics queries and dashboard patterns — these are tested against the actual Senzing database schema.
- ALWAYS test alerts end-to-end before marking the module complete.
- ALWAYS create runbooks for every alert — an alert without a runbook is just noise.
