---
inclusion: manual
---

# Module 10: Security Hardening

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_10_SECURITY_HARDENING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use Secrets Manager, IAM, KMS, CloudTrail.

**Prerequisites:** Module 9 complete, working Senzing deployment to harden.

**Before/After:** Your system works and performs well, but it's not secure. After this module, secrets are managed, access is controlled, data is encrypted, and you have a security checklist signed off by stakeholders.

Before starting: call `search_docs(query='security best practices', version='current')`. Also load `security-privacy.md` for PII handling guidance.

## Step 1: Assess Security Requirements

Ask about compliance requirements (SOC 2, GDPR, CCPA, HIPAA, PCI-DSS, etc.). Categorize:

- **Minimal:** No regulations → general best practices
- **Standard:** SOC 2/ISO 27001 → documented controls, audit logging, encryption
- **Strict:** GDPR/HIPAA/PCI → field-level encryption, retention policies, right-to-erasure

Ask about security stakeholders. Document in `docs/security_compliance.md`.

**Tell the user what was assessed:**

```text
Here's your security profile based on what you described:

Compliance level: [Minimal/Standard/Strict]
Applicable regulations: [list or "none specific"]
Key requirements:
- [requirement 1 — e.g., "All PII must be encrypted at rest (HIPAA)"]
- [requirement 2 — e.g., "Audit logs must be retained for 7 years (SOC 2)"]
- [requirement 3]

What this means for your project:
- [impact — e.g., "We'll need field-level encryption for name and address fields"]
- [impact — e.g., "Every data access will be logged with user identity and timestamp"]

Stakeholders who should review the security checklist: [names/roles]

I've documented this in docs/security_compliance.md. Next, let's secure your credentials.
```

## Step 2: Secrets Management

Never hard-code credentials. Ask which secrets manager they use (env vars, AWS Secrets Manager, Vault, etc.).

Generate secrets management code via `generate_scaffold`. For AWS: use Secrets Manager with IAM roles. For local: use `.env` files (gitignored) with `.env.example` template.

Audit existing code for hardcoded secrets. Save utility to `src/security/secrets_manager.[ext]`.

**Tell the user what was found and fixed:**

```text
I audited your existing code for hardcoded secrets. Here's what I found:

Files checked: [count] files in src/, config/, scripts/
Issues found: [count]
- src/load/load_customers.py line 12: database path hardcoded → moved to environment variable
- config/senzing_config.json: no secrets found ✅

What I created:
- src/security/secrets_manager.[ext] — utility for loading secrets from [their chosen method]
- .env.example — template showing required environment variables (no actual secrets)
- .env added to .gitignore ✅

Next: Let's set up authentication if your project has an API layer.
```

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

**Tell the user the scan results:**

```text
Vulnerability scan results:

Scanner used: [scanner name]
Files scanned: [count]

Findings:
- Critical: [count] — [must fix before proceeding]
- High: [count] — [should fix before production]
- Medium: [count] — [fix when convenient]
- Low/Info: [count] — [informational only]

Critical/High issues:
1. [description] in [file:line] → Fix: [what to do]
2. [description] in [file:line] → Fix: [what to do]

I've fixed [count] issues automatically. [count] remaining issues need your input.
Files modified: [list paths]
```

## Step 11: Security Checklist

Create `docs/security_checklist.md` with pass/fail for each area above. All critical items must pass.

**Tell the user the checklist summary:**

```text
Security checklist — docs/security_checklist.md:

✅ Secrets management: No hardcoded credentials, .env files gitignored
✅ Authentication: [JWT/API key] configured for API endpoints
✅ Authorization: RBAC with [N] roles defined
✅ Encryption at rest: [database encryption method]
✅ Encryption in transit: TLS configured
⚠️ Audit logging: Configured but not yet tested with production load
✅ Input validation: All SDK inputs sanitized
✅ Network security: [firewall/VPC/security groups] configured
✅ Vulnerability scan: 0 critical, 0 high findings remaining

Overall: [X/Y] items passing. [list any blockers]
```

## Step 12: Security Review

Present checklist to stakeholders identified in Step 1. Document sign-off or remediation items.

**Success:** No critical vulnerabilities, secrets managed, audit logging active, checklist complete, stakeholder sign-off documented.
