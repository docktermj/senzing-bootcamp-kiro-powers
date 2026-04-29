```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 10: MONITORING AND OBSERVABILITY  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 10: Monitoring and Observability

> **Agent workflow:** The agent follows `steering/module-10-monitoring.md` for this module's step-by-step workflow.

## Overview

Module 10 focuses on setting up comprehensive monitoring, logging, and alerting for production operations.

## Purpose

After security hardening in Module 9, Module 10 helps you:

1. **Set up distributed tracing** (request flow visibility)
2. **Configure structured logging** (searchable, analyzable logs)
3. **Implement metrics collection** (performance, health)
4. **Integrate APM** (Application Performance Monitoring)
5. **Configure alerting rules** (proactive issue detection)
6. **Create health check endpoints**
7. **Build monitoring dashboards**

## The Three Pillars of Observability

### 1. Metrics (What is happening?)

Quantitative measurements over time:

```text
Define metrics:

  Counters (monotonically increasing):
    records_loaded_total    — "Total records loaded"
    errors_total            — "Total errors", labeled by error_type

  Histograms (distribution of values):
    query_duration_seconds  — "Query duration"
    load_duration_seconds   — "Load duration"

  Gauges (point-in-time values):
    active_connections      — "Active database connections"
    queue_size              — "Records in queue"
```

### 2. Logs (What happened?)

Structured, searchable event records:

```text
Define a JSON log formatter:
    For each log record, output a JSON object with:
        timestamp  — formatted time
        level      — log level (INFO, ERROR, etc.)
        message    — log message text
        module     — source module name
        function   — source function name
        user_id    — if available on the record
        request_id — if available on the record

Configure the logger to use this JSON formatter on standard output.
```

### 3. Traces (Why did it happen?)

Request flow through distributed systems:

```text
Initialize a tracer for the current module

Route GET /api/search:
    Start span "search_request":
        Set attribute "user.id" to current user ID

        Start child span "database_query":
            results = query the database

        Start child span "format_results":
            formatted = format results for response

        Return formatted results
```

## Monitoring Stack Options

### Option 1: Prometheus + Grafana (Open Source)

**Prometheus:** Metrics collection and storage
**Grafana:** Visualization and dashboards

Install Prometheus and Grafana natively on your system or use your organization's existing monitoring infrastructure. See the official documentation:

- Prometheus: <https://prometheus.io/docs/prometheus/latest/installation/>
- Grafana: <https://grafana.com/docs/grafana/latest/setup-grafana/installation/>

### Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)

**Elasticsearch:** Log storage and search
**Logstash:** Log processing
**Kibana:** Log visualization

### Option 3: Cloud-Native

**AWS:** CloudWatch, X-Ray
**Azure:** Application Insights, Monitor
**GCP:** Cloud Monitoring, Cloud Trace

### Option 4: Commercial APM

**DataDog:** Full-stack monitoring
**New Relic:** Application performance
**Dynatrace:** AI-powered monitoring

## Key Metrics to Monitor

### Application Metrics

```text
Transformation metrics:
    transformation_throughput   (Gauge)   — Records/second
    transformation_errors_total (Counter) — Transformation errors

Loading metrics:
    loading_throughput          (Gauge)   — Records/second
    loading_errors_total        (Counter) — Loading errors
    loading_queue_size          (Gauge)   — Records waiting to load

Query metrics:
    queries_total               (Counter)   — Total queries
    query_duration_seconds      (Histogram) — Query duration
    query_errors_total          (Counter)   — Query errors
```

### System Metrics

```text
Collect system resource metrics periodically:

    CPU:
        cpu_percent     (Gauge) — CPU utilization percentage

    Memory:
        memory_percent  (Gauge) — Memory utilization percentage

    Disk:
        disk_percent    (Gauge) — Disk utilization percentage

    Network:
        network_bytes_sent (Counter) — Network bytes sent
        network_bytes_recv (Counter) — Network bytes received
```

### Database Metrics

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('senzing'));

-- Slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## Alerting Rules

### Critical Alerts (Page immediately)

```yaml
# Prometheus alerting rules
groups:
  - name: critical
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate: {{ $value }} errors/sec"

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
```

### Warning Alerts (Investigate soon)

```yaml
  - name: warnings
    rules:
      - alert: HighCPU
        expr: cpu_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage: {{ $value }}%"

      - alert: HighMemory
        expr: memory_percent > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage: {{ $value }}%"

      - alert: SlowQueries
        expr: query_duration_seconds > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow queries detected"
```

## Health Check Endpoints

```text
Route GET /health:
    Return { "status": "healthy" } with HTTP 200

Route GET /health/ready:
    checks = {
        "database": check_database(),
        "senzing":  check_senzing()
    }
    If all checks pass:
        Return { "status": "ready", "checks": checks } with HTTP 200
    Else:
        Return { "status": "not ready", "checks": checks } with HTTP 503

Route GET /health/live:
    Return { "status": "alive" } with HTTP 200

function check_database():
    Try to open and close a database connection
    Return true on success, false on failure

function check_senzing():
    Try to verify Senzing engine is responsive
    Return true on success, false on failure
```

## Monitoring Dashboard

Create Grafana dashboard:

```json
{
  "dashboard": {
    "title": "Senzing Entity Resolution",
    "panels": [
      {
        "title": "Records Loaded",
        "targets": [
          {
            "expr": "rate(records_loaded_total[5m])"
          }
        ]
      },
      {
        "title": "Query Performance",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, query_duration_seconds)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      },
      {
        "title": "System Resources",
        "targets": [
          {
            "expr": "cpu_percent"
          },
          {
            "expr": "memory_percent"
          }
        ]
      }
    ]
  }
}
```

## Log Aggregation

### Structured Logging Example

```text
Define a StructuredLogger class:
    Initialize with a logger name

    function log(level, message, extra_fields...):
        Build a JSON object:
            timestamp — current UTC time in ISO format
            level     — the log level
            message   — the log message
            (include any additional key-value fields)
        Write the JSON string to the underlying logger

    Convenience methods: info(), error(), warning()
        Each calls log() with the appropriate level

Usage:
    logger = new StructuredLogger("senzing")
    logger.info("Record loaded",
        record_id="12345",
        data_source="CUSTOMERS",
        duration_ms=25)
```

## Agent Behavior

When a user is in Module 10, the agent should:

1. **Choose monitoring stack** (Prometheus/Grafana, ELK, Cloud, APM)
2. **Implement metrics collection**
3. **Configure structured logging**
4. **Set up distributed tracing** (if applicable)
5. **Create health check endpoints**
6. **Configure alerting rules**
7. **Build monitoring dashboards**
8. **Test alerts** (trigger test alerts)
9. **Document monitoring setup** in `docs/monitoring_guide.md`
10. **Create runbooks** for common alerts

## Validation Gates

Before completing Module 10:

- [ ] Monitoring stack deployed
- [ ] Metrics being collected
- [ ] Logs being aggregated
- [ ] Tracing configured (if applicable)
- [ ] Health checks working
- [ ] Alerts configured
- [ ] Dashboards created
- [ ] Runbooks documented
- [ ] Monitoring tested

## Success Indicators

Module 10 is complete when:

- All metrics being collected
- Logs searchable and analyzable
- Dashboards showing real-time data
- Alerts triggering correctly
- Health checks responding
- Runbooks documented
- Team trained on monitoring tools

## Output Files

- `config/prometheus.yml` - Prometheus configuration
- `config/grafana_dashboards/` - Dashboard definitions
- `config/alerting_rules.yml` - Alert rules
- `docs/monitoring_guide.md` - Monitoring documentation
- `docs/runbooks/` - Alert runbooks

## Related Documentation

- `POWER.md` - Module 10 overview
- `steering/module-10-monitoring.md` - Module 10 workflow
- Use MCP: `search_docs(query="performance monitoring", category="performance")` for performance monitoring details

## Version History

- **v3.0.0** (2026-03-17): Module 10 created for monitoring and observability
- **v4.0.0** (2026-04-17): Renumbered from Module 11 to Module 10 (merge of old Modules 6+7)
