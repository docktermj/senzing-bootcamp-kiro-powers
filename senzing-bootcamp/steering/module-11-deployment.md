---
inclusion: manual
---

# Module 11: Packaging and Deployment

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_11_PACKAGING_DEPLOYMENT.md` for background.

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

**Check `config/bootcamp_preferences.yaml` first for `deployment_target`.** If `deployment_target` is set and not `undecided`, confirm: "You indicated [deployment_target]. Still your target?" If confirmed, proceed to deployment method below.

**If `deployment_target` is `undecided` or not set**, fall through to the full question below.

**Also check `cloud_provider`** in `config/bootcamp_preferences.yaml`. If `cloud_provider` is set, confirm: "You chose [cloud_provider]. Still your target?"

**If neither is set**, ask (one at a time):

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

**Phase 2 (Steps 13–15) and Platform Reference:** Loaded from `module-11-phase2-deploy.md` via the phase system.
