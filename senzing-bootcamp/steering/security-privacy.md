---
inclusion: auto
---

# Data Privacy — Bootcamp-Specific Rules

## Bootcamp Data Handling

- Raw data in `data/raw/` — gitignored, never committed
- Use anonymized/synthetic data for testing when possible
- `.env` for credentials (gitignored), `.env.example` as template
- SQLite DB in `database/` — gitignored, never committed
- License files in `licenses/` — gitignored

## When Generating Code

- Never hardcode credentials — use environment variables or secrets manager
- Never log PII values in plain text — mask or redact in log output
- Sanitize all user input before passing to Senzing SDK

## When User Mentions Compliance

If GDPR, CCPA, HIPAA, PCI-DSS, or similar comes up: load Module 9 (`module-09-security.md`) for the full security hardening workflow. Create `docs/security_compliance.md` to document requirements.

## Anonymization for Samples

When creating sample data from real data: replace names, mask identifiers (keep last 4 digits), use fake addresses/phones. Use language-appropriate faker library (Python: Faker, Java: Faker, C#: Bogus, Rust: fake-rs, TypeScript: @faker-js/faker).
