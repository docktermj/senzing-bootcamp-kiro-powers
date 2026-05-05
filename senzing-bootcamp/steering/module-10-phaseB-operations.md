---
inclusion: manual
---

# Module 10 Phase B: Operations & Validation (Steps 6–10)

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
