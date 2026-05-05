---
inclusion: manual
---

# Module 9 Phase B: Hardening & Validation (Steps 5–12)

## Step 5: Encryption

- At rest: database encryption (PostgreSQL: `pgcrypto`; SQLite: SQLCipher). AWS: RDS encryption, KMS.
- In transit: TLS for all database connections and API endpoints.
- Field-level: encrypt PII fields if compliance requires it (HIPAA, PCI).

**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

## Step 6: Audit Logging

Log all data access, modifications, queries, and admin actions with timestamp, user, action, and result. For AWS: CloudTrail. Save audit logger to `src/security/audit_log.[ext]`.

**Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

## Step 7: Input Validation

Validate all inputs before passing to Senzing SDK. Sanitize record data, reject malformed JSON, validate DATA_SOURCE and RECORD_ID formats. Prevent injection in any SQL or API layer.

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

## Step 8: Network Security

Database connections: use TLS, restrict to known IPs/VPCs. API endpoints: rate limiting, CORS configuration. AWS: security groups, VPC, private subnets for database.

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Senzing-Specific Security

Call `search_docs(query='security', version='current')` for Senzing-specific guidance. Key areas: engine configuration file protection, license file access control, database credential rotation.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

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

**Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

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

**Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

## Step 12: Security Review

Present checklist to stakeholders identified in Step 1. Document sign-off or remediation items.

**Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

**Success:** No critical vulnerabilities, secrets managed, audit logging active, checklist complete, stakeholder sign-off documented.
