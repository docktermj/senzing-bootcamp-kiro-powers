---
inclusion: manual
---

# Module 10: Monitoring and Observability

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_10_MONITORING_OBSERVABILITY.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use CloudWatch, SNS, X-Ray.

**Prerequisites:** Module 9 complete, security hardened.

**Before/After**: Your system is secure but you can't see what's happening inside it. After this module, you'll have dashboards, alerts, health checks, and runbooks — you'll know when something goes wrong and how to fix it.

## Step 1: Assess Monitoring Landscape

Ask: what monitoring tools do you already use? (Prometheus, Datadog, CloudWatch, Grafana, ELK, etc.) What alerting channels? (Email, Slack, PagerDuty, SNS)

If none: recommend Prometheus + Grafana for local, CloudWatch for AWS.

**Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

## Step 2: Senzing-Specific Metrics

Call `search_docs(query='monitoring get_stats', version='current')` for Senzing engine statistics.

Key metrics to collect:

- Records loaded (total, rate/sec, errors)
- Entity count and growth rate
- Redo queue depth (critical — growing queue means resolution is falling behind)
- Query latency (p50, p95, p99)
- Cross-source match rate
- Engine resource usage

Generate metrics collector via `generate_scaffold` or `find_examples(query='monitoring')`. Save to `src/monitoring/metrics_collector.[ext]`.

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Step 3: Structured Logging

Implement structured JSON logging for all components (loaders, queries, API). Include: timestamp, level, component, operation, duration_ms, record_count, error details. Save logger to `src/utils/logger.[ext]`.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

## Step 4: Dashboards

Define 4 dashboards:

1. **Loading:** records/sec, error rate, active loaders, redo queue depth
2. **Query:** request rate, latency percentiles, error rate
3. **Entity Resolution:** entity count, match rate, cross-source links
4. **System:** CPU, memory, disk, database connections

Save dashboard configs to `monitoring/dashboards/`. For Grafana: JSON. For CloudWatch: CloudFormation template.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

## Step 5: Alerting Rules

| Alert                | Condition                         | Severity | Action          |
|----------------------|-----------------------------------|----------|-----------------|
| Loading errors       | Error rate >5% for 5 min          | Critical | Page on-call    |
| Redo queue growing   | Queue depth increasing for 30 min | Warning  | Investigate     |
| Query latency        | p95 >500ms for 10 min             | Warning  | Check resources |
| Disk space           | <10% free                         | Critical | Expand or clean |
| Database connections | >80% pool used                    | Warning  | Scale or tune   |

Save alert configs to `monitoring/alerts/`.

**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

## Step 6: Health Checks

Implement liveness and readiness probes:

- Liveness: process alive, can respond to ping
- Readiness: Senzing engine initialized, database connected, can execute a test query

Save to `src/monitoring/health_check.[ext]`.

**Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

## Step 7: Senzing-Specific Monitoring

Call `search_docs(query='redo records monitoring', version='current')` for redo queue guidance. Redo queue is the most important Senzing-specific metric — if it grows unbounded, entity resolution quality degrades.

Monitor: redo queue depth trend, redo processing rate, time since last redo completion.

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

## Step 8: Runbooks

Create operational runbooks in `docs/runbooks/`:

- `high_error_rate.md`: diagnosis steps for loading errors
- `redo_queue_growing.md`: redo processing troubleshooting
- `slow_queries.md`: query performance diagnosis
- `disk_full.md`: emergency disk space recovery
- `database_recovery.md`: backup restore procedures

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Test the Monitoring Stack

Simulate failure scenarios: kill a loader, fill disk, spike query load. Verify alerts fire, dashboards update, runbooks are actionable.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

## Step 10: Document

Create `docs/monitoring_setup.md` with: architecture, metrics collected, dashboard locations, alert rules, escalation procedures, runbook index.

**Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

**Success:** Dashboards configured, alerts defined, health checks passing, runbooks created, monitoring tested.
