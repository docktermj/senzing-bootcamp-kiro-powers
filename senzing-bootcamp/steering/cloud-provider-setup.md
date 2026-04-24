---
inclusion: manual
---

# Cloud Provider Setup (7→8 Gate)

Load this steering file at the Module 7→8 validation gate, before starting Module 8.

## Cloud Provider Selection

Ask the bootcamper about their production infrastructure:

> "Now that your entity resolution is working, let's talk about production infrastructure. Modules 8-11 cover performance, security, monitoring, and deployment. Would you like to use AWS for your production environment? AWS options include RDS/Aurora for PostgreSQL, Secrets Manager for credentials, CloudWatch for monitoring, and ECS/EKS for deployment. Or would you prefer a different cloud provider, on-premises, or just continue with local development for now?"

**WAIT for response.**

Persist the choice in `config/bootcamp_preferences.yaml` as `cloud_provider` (e.g., `aws`, `azure`, `gcp`, `on-premises`, or `local`). When writing to this file, always read the existing content first and merge — never overwrite fields set by a previous action.

## If the User Chooses AWS

Modules 8-11 should use AWS-specific guidance when calling MCP tools:

- `sdk_guide` with AWS context
- RDS/Aurora for database tuning (Module 8)
- Secrets Manager for security (Module 9)
- CloudWatch for monitoring (Module 10)
- ECS/EKS for deployment (Module 11)

**Guide the bootcamper toward using AWS CDK for infrastructure deployment.** CDK lets them define AWS resources (RDS, ECS/EKS, Secrets Manager, CloudWatch alarms, etc.) as code in their chosen programming language, which aligns naturally with the bootcamp's code-first approach. Mention this early so they can plan for it:

> "Since you're going with AWS, I'd recommend using **AWS Cloud Development Kit (CDK)** to define and deploy your infrastructure as code. CDK lets you provision RDS/Aurora, ECS/EKS, Secrets Manager, CloudWatch, and other resources using the same programming language you've been using throughout the bootcamp. We'll build up the CDK stack as we work through Modules 8-11."

Also recommend that they install the "Build AWS infrastructure with CDK and CloudFormation" Kiro Power for infrastructure-as-code support:

> "I'd also recommend installing the **Build AWS infrastructure with CDK and CloudFormation** Kiro Power — it provides guided workflows for CDK that will help as we provision resources in Modules 8-11."

## If the User Chooses Another Provider

Use generic cloud guidance in Modules 8-11. The MCP tools provide cloud-agnostic patterns that can be adapted to any provider. Note specific services the user should look into:

- **Azure**: Azure SQL, Key Vault, Azure Monitor, AKS
- **GCP**: Cloud SQL, Secret Manager, Cloud Monitoring, GKE
- **On-premises**: PostgreSQL, HashiCorp Vault, Prometheus/Grafana, Kubernetes or Docker Compose

## If the User Chooses Local

Modules 8-11 will use local development patterns:

- SQLite or local PostgreSQL for performance testing
- Environment variables or `.env` files for secrets
- File-based logging and metrics
- Docker Compose for local deployment

Inform the user that Modules 8-11 are optional for local/evaluation use and they can stop after Module 7 if they prefer.
