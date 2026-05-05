---
inclusion: manual
---

# AWS Deployment Reference

Use this section when `deployment_target` is "AWS" or `cloud_provider` is "aws".

## Prerequisites

Before packaging for AWS deployment, verify:

- AWS account with appropriate permissions (IAM user or role with ECS, RDS, Secrets Manager, CloudWatch access)
- AWS CLI (`aws`) installed and configured with credentials — call `search_docs(query='AWS CLI setup', version='current')` for Senzing-specific guidance
- Target region selected and VPC provisioned (or default VPC available)
- ECR repository created for storing container images
- Familiarity with the chosen deployment method (CloudFormation, CDK, Terraform, or AWS Console)

👉 "Do you have an AWS account and the AWS CLI installed? Have you already selected a region and created a VPC for this deployment?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

WAIT for response.

## Architecture Overview

Call `search_docs(query='AWS deployment architecture', version='current')` for current Senzing AWS patterns.

The typical AWS architecture includes:

- **Compute:** ECS Fargate for serverless containers, or ECS on EC2 for more control over instance types. EKS for Kubernetes-based deployments.
- **Database:** Amazon RDS for PostgreSQL or Aurora PostgreSQL — encryption at rest via KMS, automated backups, Multi-AZ for high availability
- **Secrets:** AWS Secrets Manager for database credentials, API keys, and Senzing license — accessed via IAM roles (no hardcoded credentials)
- **Monitoring:** CloudWatch for metrics, logs, and alarms. X-Ray for distributed tracing. SNS for alert notifications.
- **Networking:** VPC with public and private subnets across multiple AZs, security groups for access control, NAT gateway for outbound internet from private subnets

## Key Configuration Steps

**Step 3 (Package Code):** Create an `infra/` directory for infrastructure definitions. Use CloudFormation, CDK (TypeScript or Python), or Terraform depending on the bootcamper's preference. Call `generate_scaffold` for the application entry points.

**Step 5 (Containerization):** Build the container image and push to ECR. The `Dockerfile` is the same regardless of platform. Call `find_examples(query='container deployment')` for Senzing container patterns. Use `docker build` + `docker push` to ECR, or configure CodeBuild for CI-based builds.

**Step 6 (Database):** Provision RDS PostgreSQL or Aurora PostgreSQL. Call `search_docs(query='PostgreSQL configuration', version='current')` for Senzing-specific database setup. Configure:

- Private subnet placement (database not publicly accessible)
- IAM authentication or Secrets Manager for credential rotation
- Encryption at rest via KMS (default or customer-managed key)
- Automated backups with configurable retention period
- Multi-AZ for production workloads

**Step 7 (CI/CD):** Use CodePipeline + CodeBuild, or GitHub Actions with OIDC federation for AWS access. Pipeline builds the container image, pushes to ECR, and updates the ECS service. Call `search_docs(query='AWS CI/CD deployment', version='current')` for current pipeline patterns.

**Step 8 (Monitoring):** Configure CloudWatch:

- Custom metrics from Senzing engine stats (records/sec, entity count, redo queue depth)
- Log groups for ECS task logs with structured JSON format
- CloudWatch Alarms for critical thresholds (error rate, latency, disk)
- SNS topics for alert routing to email, Slack, or PagerDuty
- X-Ray tracing for request flow visibility

**Step 10 (Scripts):** Create deployment scripts in `deployment/scripts/`:

- `deploy.sh` — runs `aws ecs update-service` or `cdk deploy` for the target environment
- `rollback.sh` — reverts to previous ECS task definition revision or CloudFormation stack
- `health-check.sh` — verifies service health via ALB target group health or direct HTTP probes
- `backup-db.sh` — triggers RDS snapshot or exports data to S3

## IAM Best Practices

- Use IAM roles (not access keys) for ECS tasks and Lambda functions
- Apply least-privilege: separate roles for loading (write), querying (read), and admin
- Enable MFA for console access to the AWS account
- Use service-linked roles where available
- Rotate Secrets Manager secrets on a schedule (30–90 days)

## Cost Optimization

- Use Fargate Spot for non-critical batch loading tasks (up to 70% savings)
- Right-size RDS instances based on Module 8 performance benchmarks
- Use Reserved Instances or Savings Plans for steady-state production workloads
- Enable S3 Intelligent-Tiering for backup storage
- Set CloudWatch log retention to match compliance requirements (avoid indefinite retention)

## MCP Tool References

- `search_docs(query='AWS deployment', version='current')` — Senzing AWS guidance
- `search_docs(query='PostgreSQL configuration', version='current')` — database setup
- `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — application code
- `find_examples(query='container deployment')` — containerization patterns
- `search_docs(query='AWS CI/CD deployment', version='current')` — pipeline patterns
- `search_docs(query='AWS security best practices', version='current')` — IAM and security
