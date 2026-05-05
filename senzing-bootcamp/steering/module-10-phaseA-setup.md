---
inclusion: manual
---

# Module 10 Phase A: Monitoring Setup (Steps 1–5)

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use CloudWatch, SNS, X-Ray.

## Step 1: Assess Monitoring Landscape

### Step 1a: Monitoring Tools

"What monitoring tools are you currently using? (e.g., Prometheus, Grafana, CloudWatch, Datadog, or none)"

If none: recommend Prometheus + Grafana for local, CloudWatch for AWS.

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1a to `config/bootcamp_progress.json`.

### Step 1b: Alerting Channels

"What alerting channels do you want to use? (e.g., email, Slack, PagerDuty, or none)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1b to `config/bootcamp_progress.json`.

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
