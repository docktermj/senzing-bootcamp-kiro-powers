---
inclusion: manual
---

# Module 9 Phase A: Security Assessment & Secrets (Steps 1–4)

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, use Secrets Manager, IAM, KMS, CloudTrail.

Before starting: call `search_docs(query='security best practices', version='current')`. Also load `security-privacy.md` for PII handling guidance.

## Hardware Target (On-Premises Only)

**Condition:** `deployment_target == "on_premises"` (read from `config/bootcamp_preferences.yaml`).

If the condition is true, read `hardware_target` from `config/bootcamp_preferences.yaml`:

- **If `hardware_target` is "different_server":** Use `production_specs` from `config/bootcamp_preferences.yaml` for all hardware-dependent security recommendations (encryption performance, network configuration, resource allocation). Note: "Benchmarks were run on your dev machine; recommendations target your production hardware."
- **If `hardware_target` is "current_machine":** Use the current machine's specs for security recommendations.

Do NOT re-ask the hardware question — it was already answered in Module 8.

If `deployment_target` is NOT "on_premises", skip this section entirely.

## Step 1: Assess Security Requirements

Categorize the bootcamper's compliance level based on their answers:

- **Minimal:** No regulations → general best practices
- **Standard:** SOC 2/ISO 27001 → documented controls, audit logging, encryption
- **Strict:** GDPR/HIPAA/PCI → field-level encryption, retention policies, right-to-erasure

### Step 1a: Compliance Requirements

👉 "Do you have any compliance requirements? (e.g., SOC 2, GDPR, CCPA, HIPAA, PCI-DSS, or none)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1a to `config/bootcamp_progress.json`.

### Step 1b: Security Stakeholders

👉 "Who are the security stakeholders for this project? (e.g., security team, compliance officer, or just you)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

After both answers: apply the categorization logic above (Minimal/Standard/Strict) and document in `docs/security_compliance.md`.

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

**Checkpoint:** Write step 1b to `config/bootcamp_progress.json`.

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

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Step 3: Authentication

If the project has an API layer (Module 11): implement JWT or API key authentication. Generate via `generate_scaffold` or `find_examples(query='authentication')`. Save to `src/security/auth.[ext]`.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

## Step 4: Authorization (RBAC)

Define roles: admin (full access), analyst (read + query), loader (write data), viewer (read-only). Implement role checks on all API endpoints and SDK operations.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.
