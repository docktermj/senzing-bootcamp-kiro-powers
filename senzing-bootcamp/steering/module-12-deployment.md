---
inclusion: manual
---

# Module 12: Deployment and Packaging

> **User reference:** See `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use CDK to define infrastructure (ECS/EKS, ECR, RDS/Aurora, CodePipeline) as code in the bootcamper's language.

**Prerequisites:** Module 11 complete, all tests passing, deployment target confirmed.

**Before/After:** Everything works locally. After this module, your entity resolution system is packaged, containerized, deployed to your target environment, and running in production with CI/CD.

Before starting: call `search_docs(query='deployment', category='anti_patterns', version='current')`.

**If AWS:** Before starting the deployment steps, recommend the bootcamper install the "Build AWS infrastructure with CDK and CloudFormation" Kiro Power. Tell them: "Since you're deploying to AWS, I'd recommend installing the **Build AWS infrastructure with CDK and CloudFormation** Kiro Power — it provides guided CDK workflows that will help us define your infrastructure as code. You can install it from the Kiro Powers panel." This power complements the bootcamp by providing CDK-specific steering, templates, and best practices.

## Step 1: Deployment Requirements

Ask: deployment target (Kubernetes, ECS, Docker Compose, bare metal), environments (dev/staging/prod), scaling needs, availability requirements (uptime SLA), rollback strategy.

Document in `docs/deployment_plan.md`.

## Step 2: Package Code

Refactor bootcamp code into a deployable structure:

- Separate config from code (env vars, config files per environment)
- Create entry points for each component (loader, query service, API)
- Add dependency lockfile for reproducible builds

Use `generate_scaffold` for packaging patterns. Save to `src/` with clear entry points.

**If AWS:** Also create an `infra/` directory for the CDK app. Initialize it with `cdk init app --language <chosen_language>`. The CDK app will define all AWS resources (RDS/Aurora, ECS/EKS, ECR, Secrets Manager, CloudWatch, VPC) as code in the bootcamper's language. This keeps infrastructure versioned alongside application code.

## Step 3: Multi-Environment Config

Create `config/dev/`, `config/staging/`, `config/prod/` with environment-specific settings:

- Database connection strings
- Log levels
- Feature flags
- Resource limits

Use env vars for secrets (never in config files). Create `.env.example` for each environment.

## Step 4: Containerization

Call `find_examples(query='Dockerfile')` for Senzing container patterns.

Create `Dockerfile` with: base image, SDK installation, dependency installation, code copy, health check, entry point. Create `docker-compose.yml` for local multi-service testing.

Save to project root.

**If AWS:** The Dockerfile is also used by ECS/EKS. Add a CDK construct for an ECR repository to store the container image, and an ECS Fargate service (or EKS deployment) to run it. Define these in `infra/`. Example CDK resources to create:

- `ecr.Repository` — container image registry
- `ecs.FargateService` or `eks.Cluster` — compute
- `ecs.TaskDefinition` with health check, resource limits, and environment variables pointing to Secrets Manager ARNs

## Step 5: Database Migration (SQLite → PostgreSQL)

If still on SQLite: guide migration to PostgreSQL for production. Steps: install PostgreSQL, create database, update engine config, reload data (SQLite data doesn't transfer — must reload from JSONL files).

Call `search_docs(query='PostgreSQL configuration', version='current')` for setup guidance.

**If AWS:** Use CDK to provision an RDS PostgreSQL or Aurora PostgreSQL instance instead of a local install. Define in `infra/`:

- `rds.DatabaseInstance` or `rds.DatabaseCluster` (Aurora) with encryption enabled, automated backups, and Multi-AZ for production
- `ec2.SecurityGroup` restricting access to the ECS/EKS tasks only
- Store the connection string in Secrets Manager (CDK can create the secret automatically with `rds.DatabaseSecret`)

## Step 6: CI/CD Pipeline

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

## Step 7: REST API Layer (If Requested)

If the project needs an API: generate via `generate_scaffold` or `find_examples(query='REST API')`.

Endpoints: `GET /health`, `GET /entity/{id}`, `POST /search`, `POST /load` (authenticated). Include JWT auth from Module 10, Prometheus metrics from Module 11.

Save to `src/api/`.

## Step 8: Scaling Guidance

Call `search_docs(query='scaling', version='current')` for Senzing scaling patterns.

- Horizontal: multiple loader instances (PostgreSQL only), read replicas for queries
- Vertical: more CPU/RAM for single instance
- Kubernetes: HPA based on CPU/memory, pod disruption budgets

Document scaling strategy in `docs/scaling_plan.md`.

## Step 9: Deployment Scripts

Create scripts for: deploy, rollback, health check, database backup/restore. Save to `deployment/scripts/`.

**If AWS:** The primary deployment mechanism is `cdk deploy`. Create wrapper scripts that call CDK with the right context:

- `deployment/scripts/deploy.sh` — runs `cdk deploy --all --require-approval never` for the target environment
- `deployment/scripts/rollback.sh` — rolls back to previous CloudFormation stack version
- `deployment/scripts/diff.sh` — runs `cdk diff` to preview changes before deploying

## Step 10: Pre-Deployment Checklist

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

## Step 11: Rollback Plan

Document in `docs/rollback_plan.md`: how to revert to previous version, database rollback procedure, communication plan for failed deployments.

## Step 12: Deploy to Staging

Deploy to staging environment. Run smoke tests. Verify monitoring dashboards and alerts. Fix any issues before production.

## Step 13: Deploy to Production

Deploy to production. Monitor closely for first 24 hours. Verify all health checks pass, alerts are quiet, performance matches Module 9 baselines.

**Tell the user the deployment status:**

```text
🚀 Production deployment complete!

Deployment summary:
- Environment: [production target]
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

Files produced in this module:
- Dockerfile, docker-compose.yml
- [CI/CD config file]
- config/[dev|staging|prod]/ environment configs
- deployment/scripts/ — deploy, rollback, health check scripts
- docs/deployment_plan.md, docs/rollback_plan.md, docs/operations_guide.md
```

## Step 14: Operations Documentation

Create `docs/operations_guide.md` with: architecture overview, deployment procedures, monitoring locations, escalation contacts, maintenance schedule, disaster recovery.

Remind user about bootcamp feedback: "You've completed the full bootcamp! Say 'bootcamp feedback' to document your experience."

**Success:** Code packaged, CI/CD pipeline working, staging deployment verified, production deployment successful, operations documented.
