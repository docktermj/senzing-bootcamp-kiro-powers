---
inclusion: manual
---

# Module 12: Deployment and Packaging

> **User reference:** See `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use CDK to define infrastructure (ECS/EKS, ECR, RDS/Aurora, CodePipeline) as code in the bootcamper's language.

**Prerequisites**: Module 11 complete, all tests passing, deployment target confirmed.

Before starting: call `search_docs(query='deployment', category='anti_patterns', version='current')`.

## Step 1: Deployment Requirements

Ask: deployment target (Kubernetes, ECS, Docker Compose, bare metal), environments (dev/staging/prod), scaling needs, availability requirements (uptime SLA), rollback strategy.

Document in `docs/deployment_plan.md`.

## Step 2: Package Code

Refactor bootcamp code into a deployable structure:

- Separate config from code (env vars, config files per environment)
- Create entry points for each component (loader, query service, API)
- Add dependency lockfile for reproducible builds

Use `generate_scaffold` for packaging patterns. Save to `src/` with clear entry points.

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

## Step 5: Database Migration (SQLite → PostgreSQL)

If still on SQLite: guide migration to PostgreSQL for production. Steps: install PostgreSQL, create database, update engine config, reload data (SQLite data doesn't transfer — must reload from JSONL files).

Call `search_docs(query='PostgreSQL configuration', version='current')` for setup guidance.

## Step 6: CI/CD Pipeline

Create pipeline config for user's platform (GitHub Actions, GitLab CI, Jenkins):

1. Test: run unit + integration tests
2. Build: build container image, push to registry
3. Deploy to staging: apply config, run smoke tests
4. Deploy to prod: apply config, run health checks

Save to `.github/workflows/` or equivalent. For AWS: CodePipeline + CodeBuild (define via CDK if the bootcamper chose AWS at the 8→9 gate).

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

## Step 10: Pre-Deployment Checklist

Verify before deploying:

- [ ] All tests passing
- [ ] Security scan clean (Module 10)
- [ ] Monitoring configured (Module 11)
- [ ] Secrets in secrets manager (not in code/config)
- [ ] Database backed up
- [ ] Rollback plan documented
- [ ] Stakeholder sign-off

## Step 11: Rollback Plan

Document in `docs/rollback_plan.md`: how to revert to previous version, database rollback procedure, communication plan for failed deployments.

## Step 12: Deploy to Staging

Deploy to staging environment. Run smoke tests. Verify monitoring dashboards and alerts. Fix any issues before production.

## Step 13: Deploy to Production

Deploy to production. Monitor closely for first 24 hours. Verify all health checks pass, alerts are quiet, performance matches Module 9 baselines.

## Step 14: Operations Documentation

Create `docs/operations_guide.md` with: architecture overview, deployment procedures, monitoring locations, escalation contacts, maintenance schedule, disaster recovery.

Remind user about bootcamp feedback: "You've completed the full bootcamp! Say 'bootcamp feedback' to document your experience."

**Success**: Code packaged, CI/CD pipeline working, staging deployment verified, production deployment successful, operations documented.
