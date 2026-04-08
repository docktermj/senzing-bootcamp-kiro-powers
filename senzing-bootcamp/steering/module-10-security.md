---
inclusion: manual
---

# Module 10: Security Hardening

> **User reference:** See `docs/modules/MODULE_10_SECURITY_HARDENING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use Secrets Manager, IAM, KMS, CloudTrail.

**Prerequisites**: Module 9 complete, working Senzing deployment to harden.

Before starting: call `search_docs(query='security best practices', version='current')`. Also load `security-privacy.md` for PII handling guidance.

## Step 1: Assess Security Requirements

Ask about compliance requirements (SOC 2, GDPR, CCPA, HIPAA, PCI-DSS, etc.). Categorize:

- **Minimal**: No regulations → general best practices
- **Standard**: SOC 2/ISO 27001 → documented controls, audit logging, encryption
- **Strict**: GDPR/HIPAA/PCI → field-level encryption, retention policies, right-to-erasure

Ask about security stakeholders. Document in `docs/security_compliance.md`.

## Step 2: Secrets Management

Never hard-code credentials. Ask which secrets manager they use (env vars, AWS Secrets Manager, Vault, etc.).

Generate secrets management code via `generate_scaffold`. For AWS: use Secrets Manager with IAM roles. For local: use `.env` files (gitignored) with `.env.example` template.

Audit existing code for hardcoded secrets. Save utility to `src/security/secrets_manager.[ext]`.

## Step 3: Authentication

If the project has an API layer (Module 12): implement JWT or API key authentication. Generate via `generate_scaffold` or `find_examples(query='authentication')`. Save to `src/security/auth.[ext]`.

## Step 4: Authorization (RBAC)

Define roles: admin (full access), analyst (read + query), loader (write data), viewer (read-only). Implement role checks on all API endpoints and SDK operations.

## Step 5: Encryption

- At rest: database encryption (PostgreSQL: `pgcrypto`; SQLite: SQLCipher). AWS: RDS encryption, KMS.
- In transit: TLS for all database connections and API endpoints.
- Field-level: encrypt PII fields if compliance requires it (HIPAA, PCI).

## Step 6: Audit Logging

Log all data access, modifications, queries, and admin actions with timestamp, user, action, and result. For AWS: CloudTrail. Save audit logger to `src/security/audit_log.[ext]`.

## Step 7: Input Validation

Validate all inputs before passing to Senzing SDK. Sanitize record data, reject malformed JSON, validate DATA_SOURCE and RECORD_ID formats. Prevent injection in any SQL or API layer.

## Step 8: Network Security

Database connections: use TLS, restrict to known IPs/VPCs. API endpoints: rate limiting, CORS configuration. AWS: security groups, VPC, private subnets for database.

## Step 9: Senzing-Specific Security

Call `search_docs(query='security', version='current')` for Senzing-specific guidance. Key areas: engine configuration file protection, license file access control, database credential rotation.

## Step 10: Vulnerability Scanning

Run language-appropriate security scanners:

- Python: `bandit`, `safety`
- Java: `spotbugs`, OWASP dependency-check
- C#: Roslyn security analyzers, `dotnet list package --vulnerable`
- Rust: `cargo audit`, `cargo clippy`
- TypeScript: `npm audit`, `eslint-plugin-security`

Fix critical/high findings before proceeding.

## Step 11: Security Checklist

Create `docs/security_checklist.md` with pass/fail for each area above. All critical items must pass.

## Step 12: Security Review

Present checklist to stakeholders identified in Step 1. Document sign-off or remediation items.

**Success**: No critical vulnerabilities, secrets managed, audit logging active, checklist complete, stakeholder sign-off documented.
