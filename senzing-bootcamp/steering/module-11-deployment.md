---
inclusion: manual
---

# Module 11: Deployment and Packaging

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_11_DEPLOYMENT_PACKAGING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` if already set.

**Prerequisites:** Module 10 complete, all tests passing.

**Before/After:** Everything works locally. After this module, your entity resolution system is packaged and ready for deployment — and optionally deployed to your target environment.

**Two distinct phases** — explain upfront:

1. **Packaging** (Steps 2-11): Containerization, configuration, CI/CD, documentation. Everyone does this.
2. **Deployment** (Steps 12-15): Actually deploying. Optional — only if the bootcamper wants to deploy now.

Tell the user: "Module 11 has two phases. First we'll package your code. I need to know your deployment target first because it shapes what we build. Once packaging is complete, I'll ask if you want to deploy now or later."

Before starting: call `search_docs(query='deployment', category='anti_patterns', version='current')`.

---

## Step 1: Deployment Target and Method — ASK FIRST

**Check `config/bootcamp_preferences.yaml` first.** If `cloud_provider` is set, confirm: "You chose [cloud_provider]. Still your target?"

**If not set**, ask (one at a time):

1. "Where do you plan to deploy? AWS, Azure, Google Cloud, on-premises, or local Docker?"
2. Ask about deployment method per platform:
   - **AWS:** Recommend AWS CDK; alternatives: CloudFormation, Console, Terraform. If CDK, recommend the CDK Kiro Power.
   - **Azure:** Azure CLI, ARM templates, Bicep, Terraform, or Portal.
   - **Google Cloud:** gcloud CLI, Terraform, Deployment Manager, or Console.
   - **On-premises:** Docker Compose, Kubernetes (Helm), or bare metal scripts.
   - **Local Docker:** Docker Compose.

Persist as `deployment_target` and `deployment_method` in `config/bootcamp_preferences.yaml`.

**Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

> **Agent instruction:** Call `search_docs(query='deployment <selected_platform>', version='current')`, then load the corresponding platform steering file (`deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md`). For AWS, use the "If AWS:" blocks in each step.

---

## Phase 1: Packaging (Steps 2-11)

## Step 2: Packaging Requirements

Ask about packaging needs: environments (dev/staging/prod), scaling needs, availability requirements (uptime SLA), rollback strategy.

Document in `docs/deployment_plan.md`.

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Step 3: Package Code

Refactor bootcamp code into a deployable structure:

- Separate config from code (env vars, config files per environment)
- Create entry points for each component (loader, query service, API)
- Add dependency lockfile for reproducible builds

Use `generate_scaffold` for packaging patterns. Save to `src/` with clear entry points.

**If AWS:** Also create an `infra/` directory for the CDK app. Initialize with `cdk init app --language <chosen_language>` to define all AWS resources (RDS/Aurora, ECS/EKS, ECR, Secrets Manager, CloudWatch, VPC) as code. **Other platforms:** See the platform steering file loaded in Step 1.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

## Step 4: Multi-Environment Config

Create `config/dev/`, `config/staging/`, `config/prod/` with environment-specific settings:

- Database connection strings
- Log levels
- Feature flags
- Resource limits

Use env vars for secrets (never in config files). Create `.env.example` for each environment.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

## Step 5: Containerization

Call `find_examples(query='Dockerfile')` for Senzing container patterns.

Create `Dockerfile` with: base image, SDK installation, dependency installation, code copy, health check, entry point. **Always create `docker-compose.yml` for local multi-service testing, regardless of deployment target.**

Save to project root.

**If AWS:** Add CDK constructs in `infra/` for `ecr.Repository`, `ecs.FargateService` (or `eks.Cluster`), and `ecs.TaskDefinition` with health check, resource limits, and Secrets Manager env vars. **Other platforms:** See the platform steering file loaded in Step 1.

**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

## Step 6: Database Migration (SQLite → PostgreSQL)

If still on SQLite: guide migration to PostgreSQL for production. Steps: install PostgreSQL, create database, update engine config, reload data (SQLite data doesn't transfer — must reload from JSONL files).

Call `search_docs(query='PostgreSQL configuration', version='current')` for setup guidance.

**If AWS:** Use CDK to provision RDS PostgreSQL or Aurora (`rds.DatabaseInstance`/`rds.DatabaseCluster`) with encryption, automated backups, Multi-AZ, a security group restricting access to ECS/EKS tasks, and connection string in Secrets Manager via `rds.DatabaseSecret`. **Other platforms:** See the platform steering file loaded in Step 1.

**Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

## Step 7: CI/CD Pipeline

Create pipeline config for user's platform (GitHub Actions, GitLab CI, Jenkins):

1. Test: run unit + integration tests
2. Build: build container image, push to registry
3. Deploy to staging: apply config, run smoke tests
4. Deploy to prod: apply config, run health checks

Save to `.github/workflows/` or equivalent.

**If AWS:** Use CDK Pipelines (`pipelines.CodePipeline`) in `infra/pipeline_stack.[ext]` — it auto-creates a self-mutating CodePipeline that synths, deploys to staging, runs smoke tests, then deploys to production. **Other platforms:** See the platform steering file loaded in Step 1 for registry push and deployment commands.

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

## Step 8: REST API Layer (If Requested)

If the project needs an API: generate via `generate_scaffold` or `find_examples(query='REST API')`.

Endpoints: `GET /health`, `GET /entity/{id}`, `POST /search`, `POST /load` (authenticated). Include JWT auth from Module 9, Prometheus metrics from Module 10.

Save to `src/api/`.

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Scaling Guidance

Call `search_docs(query='scaling', version='current')` for Senzing scaling patterns.

- Horizontal: multiple loader instances (PostgreSQL only), read replicas for queries
- Vertical: more CPU/RAM for single instance
- Kubernetes: HPA based on CPU/memory, pod disruption budgets

Document scaling strategy in `docs/scaling_plan.md`.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

## Step 10: Deployment Scripts

Create scripts for: deploy, rollback, health check, database backup/restore. Save to `deployment/scripts/`.

**If AWS:** Create wrapper scripts calling CDK: `deploy.sh` (`cdk deploy --all`), `rollback.sh` (previous CloudFormation stack), `diff.sh` (`cdk diff`). **Other platforms:** See the platform steering file loaded in Step 1 for platform-specific script patterns. Call `search_docs(query='deployment scripts <platform>', version='current')` for current guidance.

**Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

## Step 11: Pre-Deployment Checklist

Verify: all tests passing, security scan clean (Module 9), monitoring configured (Module 10), secrets in secrets manager, database backed up, rollback plan documented, stakeholder sign-off.

Tell the user the checklist results with ✅/⬜ status for each item. If all pass: "Ready to deploy to staging!" If any fail: "[X] items need attention first."

**Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

## Step 12: Rollback Plan

Document in `docs/rollback_plan.md`: how to revert to previous version, database rollback procedure, communication plan for failed deployments.

**Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

---

## ⛔ PHASE GATE — PACKAGING COMPLETE, DEPLOYMENT DECISION REQUIRED

Packaging (Steps 2–11) is complete. Present the deployment decision below.

Display: "📦 Packaging phase complete — code containerized, multi-env config set, CI/CD configured, checklist verified, rollback plan documented. Nothing has been deployed yet — it's safe to stop here."

Present the deployment decision: deploy now, or stop here and deploy later on their own.

- **Stop here** → Mark Module 11 complete (packaging only). Do NOT proceed to Step 13.
- **Deploy now** → Proceed to Phase 2 (Steps 13–15).
- **Unsure** → Reassure that stopping is fine; they can deploy later using the scripts and docs.

---

## Phase 2: Deployment (Steps 13-15) — Optional

Only proceed if the bootcamper explicitly wants to deploy now.

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

#[[file:senzing-bootcamp/templates/stakeholder_summary.md]]

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
