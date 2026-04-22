---
inclusion: manual
---

# Module 12: Deployment and Packaging

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` if already set.

**Prerequisites:** Module 11 complete, all tests passing.

**Before/After:** Everything works locally. After this module, your entity resolution system is packaged and ready for deployment — and optionally deployed to your target environment.

**IMPORTANT — Two distinct phases:** This module has two phases that should be clearly explained to the bootcamper:

1. **Packaging** (Steps 2-11): Preparing your code for deployment — containerization, configuration, CI/CD, documentation. The deployment target (chosen in Step 1) shapes what artifacts get built. Everyone does this.
2. **Deployment** (Steps 12-15): Actually deploying to a target environment. This is optional and only happens if the bootcamper wants to deploy now.

Tell the user upfront: "Module 12 has two phases. First, we'll package your code so it's deployment-ready. But before we start packaging, I need to know where you plan to deploy — because the deployment target shapes what we build. Then once packaging is complete, I'll ask if you want to actually deploy it now or save that for later."

Before starting: call `search_docs(query='deployment', category='anti_patterns', version='current')`.

---

## Step 1: Deployment Target and Method — ASK FIRST

**Ask this before creating any packaging artifacts.** The deployment target fundamentally shapes what gets built — a CDK app for AWS is completely different from a Docker Compose setup for local deployment.

**Check `config/bootcamp_preferences.yaml` first.** If `cloud_provider` was already set at the 8→9 gate (via `cloud-provider-setup.md`), confirm rather than re-ask: "At the start of Module 9, you chose [cloud_provider]. Is that still your deployment target, or would you like to change it?" WAIT for response.

**If no cloud_provider is set**, ask two questions (one at a time, WAIT for each):

1. "Where do you plan to deploy this? For example: AWS, Azure, Google Cloud, on-premises, or local Docker?"

2. Based on their answer, ask about deployment method:
   - **AWS:** "What deployment method would you like to use? I'd recommend **AWS CDK** (infrastructure as code in your language), but other options include CloudFormation templates, AWS Console, or Terraform." If they choose CDK, recommend installing the "Build AWS infrastructure with CDK and CloudFormation" Kiro Power.
   - **Azure:** "What deployment method? Options include Azure CLI, ARM templates, Bicep, Terraform, or Azure Portal."
   - **Google Cloud:** "What deployment method? Options include gcloud CLI, Terraform, Deployment Manager, or Cloud Console."
   - **On-premises:** "What deployment method? Options include Docker Compose, Kubernetes (Helm charts), or bare metal scripts."
   - **Local Docker:** "We'll use Docker Compose."

Persist choices in `config/bootcamp_preferences.yaml` as `deployment_target` and `deployment_method`. When mentioning any third-party deployment tools, consult `search_docs` for Senzing-specific integration guidance.

> **Agent instruction:** After the bootcamper selects their deployment target, call `search_docs(query='deployment <selected_platform>', version='current')` to retrieve current Senzing guidance for that platform. Then load the corresponding platform steering file (`deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md`) and apply its guidance throughout the packaging and deployment phases. For AWS, continue using the existing "If AWS:" blocks in each step — no separate reference section is needed.

---

## Phase 1: Packaging (Steps 2-11)

## Step 2: Packaging Requirements

Ask about packaging needs: environments (dev/staging/prod), scaling needs, availability requirements (uptime SLA), rollback strategy.

Document in `docs/deployment_plan.md`.

## Step 3: Package Code

Refactor bootcamp code into a deployable structure:

- Separate config from code (env vars, config files per environment)
- Create entry points for each component (loader, query service, API)
- Add dependency lockfile for reproducible builds

Use `generate_scaffold` for packaging patterns. Save to `src/` with clear entry points.

**If AWS:** Also create an `infra/` directory for the CDK app. Initialize it with `cdk init app --language <chosen_language>`. The CDK app will define all AWS resources (RDS/Aurora, ECS/EKS, ECR, Secrets Manager, CloudWatch, VPC) as code in the bootcamper's language. This keeps infrastructure versioned alongside application code.

**If Azure / GCP / On-Premises / Kubernetes:** See the corresponding platform steering file for platform-specific project structure and infrastructure-as-code guidance.

## Step 4: Multi-Environment Config

Create `config/dev/`, `config/staging/`, `config/prod/` with environment-specific settings:

- Database connection strings
- Log levels
- Feature flags
- Resource limits

Use env vars for secrets (never in config files). Create `.env.example` for each environment.

## Step 5: Containerization

Call `find_examples(query='Dockerfile')` for Senzing container patterns.

Create `Dockerfile` with: base image, SDK installation, dependency installation, code copy, health check, entry point. **Always create `docker-compose.yml` for local multi-service testing, regardless of deployment target.**

Save to project root.

**If AWS:** The Dockerfile is also used by ECS/EKS. Add a CDK construct for an ECR repository to store the container image, and an ECS Fargate service (or EKS deployment) to run it. Define these in `infra/`. Example CDK resources to create:

- `ecr.Repository` — container image registry
- `ecs.FargateService` or `eks.Cluster` — compute
- `ecs.TaskDefinition` with health check, resource limits, and environment variables pointing to Secrets Manager ARNs

**If Azure / GCP / On-Premises / Kubernetes:** See the corresponding platform steering file for platform-specific container registry, compute service, and orchestration guidance.

## Step 6: Database Migration (SQLite → PostgreSQL)

If still on SQLite: guide migration to PostgreSQL for production. Steps: install PostgreSQL, create database, update engine config, reload data (SQLite data doesn't transfer — must reload from JSONL files).

Call `search_docs(query='PostgreSQL configuration', version='current')` for setup guidance.

**If AWS:** Use CDK to provision an RDS PostgreSQL or Aurora PostgreSQL instance instead of a local install. Define in `infra/`:

- `rds.DatabaseInstance` or `rds.DatabaseCluster` (Aurora) with encryption enabled, automated backups, and Multi-AZ for production
- `ec2.SecurityGroup` restricting access to the ECS/EKS tasks only
- Store the connection string in Secrets Manager (CDK can create the secret automatically with `rds.DatabaseSecret`)

**If Azure:** Use Azure Database for PostgreSQL — Flexible Server. See the **Azure Deployment Reference** section.

**If GCP:** Use Cloud SQL for PostgreSQL. See the **GCP Deployment Reference** section.

**If On-Premises / Kubernetes:** Install PostgreSQL locally or use a Kubernetes StatefulSet. See the corresponding platform steering file.

## Step 7: CI/CD Pipeline

Create pipeline config for user's platform (GitHub Actions, GitLab CI, Jenkins):

1. Test: run unit + integration tests
2. Build: build container image, push to registry
3. Deploy to staging: apply config, run smoke tests
4. Deploy to prod: apply config, run health checks

Save to `.github/workflows/` or equivalent.

**If AWS:** Use CDK Pipelines (`pipelines.CodePipeline`) to define the entire CI/CD pipeline as code. CDK Pipelines automatically creates a CodePipeline that:

1. Pulls from the source repo (CodeStar Connections or GitHub)
2. Runs `cdk synth` to produce CloudFormation templates
3. Self-mutates (updates the pipeline itself if the CDK code changes)
4. Deploys to staging, runs smoke tests, then deploys to production

Define the pipeline in `infra/pipeline_stack.[ext]`. This replaces manually configuring CodePipeline + CodeBuild — CDK Pipelines handles it declaratively.

**If Azure / GCP / On-Premises / Kubernetes:** Use the CI/CD platform of choice (GitHub Actions, GitLab CI, Jenkins, Azure DevOps, Cloud Build). The pipeline stages (test → build → deploy staging → deploy prod) remain the same regardless of platform. See the corresponding platform steering file for platform-specific registry push and deployment commands.

## Step 8: REST API Layer (If Requested)

If the project needs an API: generate via `generate_scaffold` or `find_examples(query='REST API')`.

Endpoints: `GET /health`, `GET /entity/{id}`, `POST /search`, `POST /load` (authenticated). Include JWT auth from Module 10, Prometheus metrics from Module 11.

Save to `src/api/`.

## Step 9: Scaling Guidance

Call `search_docs(query='scaling', version='current')` for Senzing scaling patterns.

- Horizontal: multiple loader instances (PostgreSQL only), read replicas for queries
- Vertical: more CPU/RAM for single instance
- Kubernetes: HPA based on CPU/memory, pod disruption budgets

Document scaling strategy in `docs/scaling_plan.md`.

## Step 10: Deployment Scripts

Create scripts for: deploy, rollback, health check, database backup/restore. Save to `deployment/scripts/`.

**If AWS:** The primary deployment mechanism is `cdk deploy`. Create wrapper scripts that call CDK with the right context:

- `deployment/scripts/deploy.sh` — runs `cdk deploy --all --require-approval never` for the target environment
- `deployment/scripts/rollback.sh` — rolls back to previous CloudFormation stack version
- `deployment/scripts/diff.sh` — runs `cdk diff` to preview changes before deploying

**If Azure / GCP / On-Premises / Kubernetes:** Create equivalent deploy, rollback, and health check scripts using the platform's native tooling. See the corresponding platform steering file for platform-specific script patterns. Call `search_docs(query='deployment scripts <platform>', version='current')` for current guidance.

## Step 11: Pre-Deployment Checklist

Verify before deploying:

- [ ] All tests passing
- [ ] Security scan clean (Module 10)
- [ ] Monitoring configured (Module 11)
- [ ] Secrets in secrets manager (not in code/config)
- [ ] Database backed up
- [ ] Rollback plan documented
- [ ] Stakeholder sign-off

**Tell the user the checklist results:**

```text
Pre-deployment checklist — here's where we stand:

✅ All tests passing — [X] tests, 0 failures
✅ Security scan clean — 0 critical/high findings (Module 10)
✅ Monitoring configured — dashboards, alerts, health checks (Module 11)
✅ Secrets managed — all credentials in [secrets manager], none in code
✅ Database backed up — backup at backups/[filename]
✅ Rollback plan — documented in docs/rollback_plan.md
⬜ Stakeholder sign-off — [pending/complete]

[If all pass]: Ready to deploy to staging!
[If any fail]: [X] items need attention before we can deploy. Let's fix those first.
```

## Step 12: Rollback Plan

Document in `docs/rollback_plan.md`: how to revert to previous version, database rollback procedure, communication plan for failed deployments.

**Packaging complete.** At this point, tell the user:

"Packaging is complete! Your code is containerized, configured for multiple environments, has a CI/CD pipeline, and is fully documented. Everything is deployment-ready."

Then ask: **"Would you like to actually deploy this now, or would you prefer to stop here and deploy later on your own?"**

WAIT for response. If they want to stop, mark Module 12 as complete with packaging only. If they want to deploy, proceed to Phase 2.

---

## Phase 2: Deployment (Steps 13-16) — Optional

Only proceed here if the bootcamper explicitly wants to deploy now. The deployment target and method were already chosen in Step 1.

## Step 13: Deploy to Staging

Deploy to staging environment using the chosen method. Run smoke tests. Verify monitoring dashboards and alerts. Fix any issues before production.

## Step 14: Deploy to Production

Deploy to production. Monitor closely for first 24 hours. Verify all health checks pass, alerts are quiet, performance matches Module 9 baselines.

**Tell the user the deployment status:**

```text
🚀 Production deployment complete!

Deployment summary:
- Target: [deployment target]
- Method: [deployment method]
- Version: [version/tag]
- Deployed at: [timestamp]
- Health checks: all passing ✅
- Monitoring: dashboards active, alerts configured

First 24 hours — watch for:
- Loading error rate (should stay <1%)
- Query latency (should match Module 9 baselines)
- Redo queue depth (should not grow unbounded)
- Disk usage (should not spike unexpectedly)

If anything goes wrong: follow docs/rollback_plan.md
```

## Step 15: Operations Documentation

Create `docs/operations_guide.md` with: architecture overview, deployment procedures, monitoring locations, escalation contacts, maintenance schedule, disaster recovery.

### Disaster Recovery Section

The operations guide MUST include a disaster recovery section. Guide the bootcamper through defining:

**Recovery Objectives:**
- **RTO (Recovery Time Objective):** How long can the system be down? (Critical: <1hr, Production: <4hr, Dev: <24hr)
- **RPO (Recovery Point Objective):** How much data can be lost? (Critical: <5min, Production: <1hr, Dev: <24hr)

**Backup Strategy (3-2-1 Rule):** 3 copies of data, 2 different media types, 1 offsite copy.

**What to back up:**
1. Database (CRITICAL) — continuous WAL archiving + daily full backups for PostgreSQL; file copy for SQLite
2. Configuration files — version-controlled in Git
3. Source data in `data/raw/` and `data/transformed/` — on receipt
4. Application code — version-controlled in Git

**DR Scenarios to document:**
- Database corruption → restore from latest backup, replay WAL logs
- Accidental data deletion → PITR to point before deletion, or reload from source
- Bad data load → restore database to pre-load backup, fix transformation, reload
- Server failure → provision new server, restore from backups, update DNS
- Complete site outage → activate DR site, restore from offsite backup

**Backup scripts:** Create `deployment/scripts/backup-db.sh` and `deployment/scripts/restore-db.sh`. For PostgreSQL, use `pg_dump` for full backups. For SQLite, use file copy or the SQLite backup API.

> **Agent instruction:** Use `search_docs(query='backup disaster recovery', version='current')` for current Senzing DR guidance. The operations guide should be specific to the bootcamper's deployment target and database backend.

👉 "What are your recovery objectives? How long can the system be down (RTO), and how much data can you afford to lose (RPO)?" WAIT for response.

Offer stakeholder summary: "Would you like me to create a one-page executive summary of this deployment to share with your team? It covers the problem, approach, data sources, key findings, next steps, and ROI considerations."

If yes, read the template at `senzing-bootcamp/templates/stakeholder_summary.md`. Follow the **MODULE 12** guidance block in the template to fill each placeholder with Module 12 context (deployment status, production metrics, operational readiness, architecture summary). Save the filled summary to `docs/stakeholder_summary_module12.md`.

Remind user about bootcamp feedback: "You've completed the full bootcamp! Say 'bootcamp feedback' to document your experience."

**Success:** Code packaged (always). If deployed: CI/CD pipeline working, staging verified, production deployed, operations documented.


---

## Platform Reference Sections

Load the file matching the bootcamper's deployment target:

- **On-Premises / Local Docker:** Load `deployment-onpremises.md`
- **Azure:** Load `deployment-azure.md`
- **GCP / Google Cloud:** Load `deployment-gcp.md`
- **Kubernetes:** Load `deployment-kubernetes.md`
- **AWS:** Use the "If AWS:" blocks in each step above (no separate file needed)