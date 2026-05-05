---
inclusion: manual
---

# Module 11 Phase 2: Deployment (Steps 13-15)

Optional phase — only proceed if the bootcamper explicitly wants to deploy now.

## Step 13: Deploy to Staging

Deploy to staging environment using the chosen method. Run smoke tests. Verify monitoring dashboards and alerts. Fix any issues before production.

**Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

## Step 14: Deploy to Production

Deploy to production. Monitor closely for first 24 hours. Verify health checks pass, alerts are quiet, performance matches Module 8 baselines.

Tell the user: deployment summary (target, method, version, timestamp, health check status, monitoring status), plus first-24-hour watch items (loading error rate <1%, query latency, redo queue depth, disk usage). Reference `docs/rollback_plan.md` for issues.

**Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

## Step 15: Operations Documentation

Create `docs/operations_guide.md` with: architecture overview, deployment procedures, monitoring locations, escalation contacts, maintenance schedule, disaster recovery.

### Disaster Recovery Section

The operations guide MUST include a disaster recovery section:

- **Recovery Objectives:** Ask the bootcamper for RTO (how long down?) and RPO (how much data loss?). Tiers: Critical <1hr/<5min, Production <4hr/<1hr, Dev <24hr/<24hr.
- **Backup Strategy (3-2-1 Rule):** 3 copies, 2 media types, 1 offsite. Back up: database (WAL + daily full for PostgreSQL, file copy for SQLite), config files (Git), source data, application code (Git).
- **DR Scenarios:** Database corruption, accidental deletion, bad data load, server failure, complete site outage — document restore procedure for each.
- **Backup scripts:** Create `deployment/scripts/backup-db.sh` and `restore-db.sh` (PostgreSQL: `pg_dump`; SQLite: file copy).

> **Agent instruction:** Use `search_docs(query='backup disaster recovery', version='current')` for Senzing DR guidance.

Ask the bootcamper about their recovery objectives: how long the system can be down (RTO) and how much data they can afford to lose (RPO).

Offer stakeholder summary: "Would you like me to create a one-page executive summary of this deployment to share with your team? It covers the problem, approach, data sources, key findings, next steps, and ROI considerations."

# [[file:senzing-bootcamp/templates/stakeholder_summary.md]]

If yes, follow the **MODULE 11** guidance block in the template to fill each placeholder with Module 11 context (deployment status, production metrics, operational readiness, architecture summary). Save the filled summary to `docs/stakeholder_summary_module11.md`.

Remind user about bootcamp feedback: "You've completed the full bootcamp! Say 'bootcamp feedback' to document your experience."

**Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

**Success:** Code packaged (always). If deployed: CI/CD pipeline working, staging verified, production deployed, operations documented.

---

## Platform Reference Sections

Load the file matching the bootcamper's deployment target:

- **On-Premises / Local Docker:** Load `deployment-onpremises.md`
- **Azure:** Load `deployment-azure.md`
- **GCP / Google Cloud:** Load `deployment-gcp.md`
- **Kubernetes:** Load `deployment-kubernetes.md`
- **AWS:** Use the "If AWS:" blocks in each step above (no separate file needed)
